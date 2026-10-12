"""Khmer Translator — Production Authentication Engine (Angkor Nexus).

Provides secure user registration, credential verification, OWASP Argon2id password hashing
(with seamless PBKDF2 migration), cryptographic session tokens, brute-force rate limiting,
cross-device session management, and SQLite persistence.
"""
from __future__ import annotations

import hmac
import hashlib
import logging
import os
import re
import secrets
import sqlite3
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

import argon2

from .config import AUTH_DB_PATH, BASE_DIR

logger = logging.getLogger(__name__)

_DB_LOCK = threading.Lock()

# Email regex validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

AUTH_DB_FILE = AUTH_DB_PATH

# OWASP & RFC 9106 Recommended Cloud Standard for Argon2id:
# Memory: 32 MiB (32768 KiB), Iterations/Time cost: 2, Parallelism: 2, Hash length: 32 bytes
argon2_hasher = argon2.PasswordHasher(
    time_cost=2,
    memory_cost=32768,
    parallelism=2,
    hash_len=32,
    type=argon2.Type.ID,
)

# Legacy PBKDF2 parameters for backward-compatibility verification
PBKDF2_ITERATIONS = 600_000

# Rate Limiting configuration (5 failed attempts per 5 minutes per identifier)
_RATE_LIMIT_LOCK = threading.Lock()
_FAILED_LOGIN_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 300.0  # 5 minutes


def _get_connection(db_file: Path | str | None = None) -> sqlite3.Connection:
    target = Path(db_file) if db_file else AUTH_DB_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db(db_file: Path | str | None = None) -> None:
    """Initialize or migrate the SQLite tables for users and authentication sessions."""
    with _DB_LOCK:
        conn = _get_connection(db_file)
        try:
            with conn:
                # 1. Base users table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'active',
                        email_verified INTEGER NOT NULL DEFAULT 1,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_login_at TEXT,
                        avatar_color TEXT NOT NULL
                    )
                """)

                # 2. Base sessions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        token TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)

                # 3. Safe Schema Migrations: add missing columns if upgrading existing database
                cursor = conn.execute("PRAGMA table_info(users)")
                user_cols = {row["name"] for row in cursor.fetchall()}

                if "status" not in user_cols:
                    conn.execute("ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")
                if "email_verified" not in user_cols:
                    conn.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 1")
                if "updated_at" not in user_cols:
                    conn.execute("ALTER TABLE users ADD COLUMN updated_at TEXT")
                    conn.execute("UPDATE users SET updated_at = created_at WHERE updated_at IS NULL")
                if "last_login_at" not in user_cols:
                    conn.execute("ALTER TABLE users ADD COLUMN last_login_at TEXT")

                # Check sessions table columns
                cursor_s = conn.execute("PRAGMA table_info(sessions)")
                session_cols = {row["name"] for row in cursor_s.fetchall()}
                if "ip_address" not in session_cols:
                    conn.execute("ALTER TABLE sessions ADD COLUMN ip_address TEXT")
                if "user_agent" not in session_cols:
                    conn.execute("ALTER TABLE sessions ADD COLUMN user_agent TEXT")

                # 4. Indexes for fast lookup
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        finally:
            conn.close()
    logger.info("Auth database verified/migrated at %s", db_file or AUTH_DB_PATH)


# Call initialization at module load
init_auth_db()


def hash_password(password: str) -> str:
    """Hash password using state-of-the-art Argon2id with unique cryptographic salt."""
    return argon2_hasher.hash(password)


def _verify_pbkdf2_legacy(password: str, stored_hash: str) -> bool:
    """Fallback verifier for legacy PBKDF2 hashes."""
    try:
        parts = stored_hash.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_key = bytes.fromhex(parts[3])
        calculated_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(calculated_key, expected_key)
    except Exception as exc:
        logger.error("Error verifying PBKDF2 hash: %s", exc)
        return False


def verify_password(password: str, stored_hash: str) -> tuple[bool, bool]:
    """
    Verify password against stored hash.
    Returns (is_valid, needs_rehash).
    Handles both modern Argon2id and legacy PBKDF2 hashes.
    """
    if not stored_hash or not password:
        return False, False

    # Check if hash is Argon2 (starts with $argon2)
    if stored_hash.startswith("$argon2"):
        try:
            argon2_hasher.verify(stored_hash, password)
            needs_rehash = argon2_hasher.check_needs_rehash(stored_hash)
            return True, needs_rehash
        except argon2.exceptions.VerifyMismatchError:
            return False, False
        except Exception as exc:
            logger.error("Argon2 verification exception: %s", exc)
            return False, False

    # Check if hash is legacy PBKDF2
    if stored_hash.startswith("pbkdf2_sha256$"):
        if _verify_pbkdf2_legacy(password, stored_hash):
            return True, True  # Match found, upgrade to Argon2id
        return False, False

    return False, False


def _check_rate_limit(key: str) -> None:
    now = time.time()
    with _RATE_LIMIT_LOCK:
        attempts = [t for t in _FAILED_LOGIN_ATTEMPTS[key] if now - t < LOCKOUT_WINDOW_SECONDS]
        _FAILED_LOGIN_ATTEMPTS[key] = attempts
        if len(attempts) >= MAX_FAILED_ATTEMPTS:
            wait_seconds = int(LOCKOUT_WINDOW_SECONDS - (now - attempts[0]))
            raise ValueError(
                f"Too many failed login attempts. Please wait {max(wait_seconds, 1)} seconds before trying again / ការប៉ុនប៉ងចូលបរាជ័យច្រើនដងពេក សូមរង់ចាំមួយភ្លែត។"
            )


def _record_failed_attempt(key: str) -> None:
    now = time.time()
    with _RATE_LIMIT_LOCK:
        _FAILED_LOGIN_ATTEMPTS[key].append(now)


def _clear_rate_limit(key: str) -> None:
    with _RATE_LIMIT_LOCK:
        _FAILED_LOGIN_ATTEMPTS.pop(key, None)


def _generate_avatar_color(name: str) -> str:
    palette = ["#D6B46A", "#C88C9D", "#426B59", "#77D5A3", "#5C7CFA", "#E599F7", "#F59F00"]
    h = sum(ord(c) for c in name)
    return palette[h % len(palette)]


def register_user(
    name: str,
    email: str,
    password: str,
    db_file: Path | str | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Register a new user account with Argon2id hashed password and create session."""
    clean_name = name.strip()
    clean_email = email.strip().lower()

    if len(clean_name) < 2:
        raise ValueError("Name must be at least 2 characters long / ឈ្មោះត្រូវមានយ៉ាងហោចណាស់ ២ តួអក្សរ")
    if not EMAIL_REGEX.match(clean_email):
        raise ValueError("Invalid email address format / ទម្រង់អ៊ីមែលមិនត្រឹមត្រូវ")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long / ពាក្យសម្ងាត់ត្រូវមានយ៉ាងហោចណាស់ ៨ តួអក្សរ")

    p_hash = hash_password(password)
    user_id = f"usr_{secrets.token_hex(12)}"
    now = datetime.now(timezone.utc).isoformat()
    avatar_color = _generate_avatar_color(clean_name)

    with _DB_LOCK:
        conn = _get_connection(db_file)
        try:
            with conn:
                existing = conn.execute("SELECT id FROM users WHERE email = ?", (clean_email,)).fetchone()
                if existing:
                    raise ValueError("An account with this email address already exists / អ៊ីមែលនេះមានរួចហើយ")

                conn.execute(
                    """INSERT INTO users (
                        id, name, email, password_hash, status, email_verified,
                        created_at, updated_at, last_login_at, avatar_color
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, clean_name, clean_email, p_hash, "active", 1, now, now, now, avatar_color),
                )
        finally:
            conn.close()

    user_dict = {
        "id": user_id,
        "name": clean_name,
        "email": clean_email,
        "status": "active",
        "email_verified": True,
        "created_at": now,
        "updated_at": now,
        "last_login_at": now,
        "avatar_color": avatar_color,
    }
    token = create_session(
        user_id,
        remember_me=True,
        db_file=db_file,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return user_dict, token


def login_user(
    email: str,
    password: str,
    remember_me: bool = False,
    db_file: Path | str | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Authenticate user with email and password, returning user profile and session token."""
    clean_email = email.strip().lower()
    rate_key = f"{client_ip or 'ip'}:{clean_email}"
    _check_rate_limit(rate_key)

    with _DB_LOCK:
        conn = _get_connection(db_file)
        try:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (clean_email,)).fetchone()
        finally:
            conn.close()

    if not row:
        _record_failed_attempt(rate_key)
        raise ValueError("Invalid email or password / អ៊ីមែល ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ")

    if row["status"] != "active":
        raise ValueError("This account has been deactivated / គណនីនេះត្រូវបានផ្អាកដំណើរការ")

    is_valid, needs_rehash = verify_password(password, row["password_hash"])
    if not is_valid:
        _record_failed_attempt(rate_key)
        raise ValueError("Invalid email or password / អ៊ីមែល ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ")

    # Login succeeded: clear rate limits
    _clear_rate_limit(rate_key)

    now = datetime.now(timezone.utc).isoformat()

    # Rehash password to modern Argon2id if it was legacy PBKDF2 or needs upgrading
    new_hash = hash_password(password) if needs_rehash else None

    with _DB_LOCK:
        conn = _get_connection(db_file)
        try:
            with conn:
                if new_hash:
                    conn.execute(
                        "UPDATE users SET password_hash = ?, updated_at = ?, last_login_at = ? WHERE id = ?",
                        (new_hash, now, now, row["id"]),
                    )
                    logger.info("Upgraded password hash to Argon2id for user %s", row["id"])
                else:
                    conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now, row["id"]))
        finally:
            conn.close()

    user_dict = {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "status": row["status"],
        "email_verified": bool(row["email_verified"]),
        "created_at": row["created_at"],
        "updated_at": now if new_hash else row["updated_at"],
        "last_login_at": now,
        "avatar_color": row["avatar_color"],
    }
    token = create_session(
        row["id"],
        remember_me=remember_me,
        db_file=db_file,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    return user_dict, token


def create_session(
    user_id: str,
    remember_me: bool = False,
    db_file: Path | str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> str:
    """Generate a secure cryptographic session token with expiration."""
    token = secrets.token_urlsafe(36)
    now = datetime.now(timezone.utc)
    # If remember_me: 30 days. Otherwise: 24 hours.
    duration = timedelta(days=30) if remember_me else timedelta(hours=24)
    expires_at = (now + duration).isoformat()

    with _DB_LOCK:
        conn = _get_connection(db_file)
        try:
            with conn:
                conn.execute(
                    """INSERT INTO sessions (
                        token, user_id, created_at, expires_at, ip_address, user_agent
                    ) VALUES (?, ?, ?, ?, ?, ?)""",
                    (token, user_id, now.isoformat(), expires_at, ip_address, user_agent),
                )
        finally:
            conn.close()
    return token


def get_user_by_token(token: str, db_file: Path | str | None = None) -> Optional[dict[str, Any]]:
    """Retrieve user details for a valid session token, verifying expiration."""
    if not token or len(token) < 20:
        return None

    clean_token = token.strip()
    now_iso = datetime.now(timezone.utc).isoformat()

    with _DB_LOCK:
        conn = _get_connection(db_file)
        try:
            query = """
                SELECT u.id, u.name, u.email, u.status, u.email_verified,
                       u.created_at, u.updated_at, u.last_login_at, u.avatar_color, s.expires_at
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = ? AND s.expires_at > ? AND u.status = 'active'
            """
            row = conn.execute(query, (clean_token, now_iso)).fetchone()
            if not row:
                return None

            return {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "status": row["status"],
                "email_verified": bool(row["email_verified"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "last_login_at": row["last_login_at"],
                "avatar_color": row["avatar_color"],
            }
        finally:
            conn.close()


def revoke_session(token: str, db_file: Path | str | None = None) -> None:
    """Revoke and delete a session token upon logout."""
    if not token:
        return
    with _DB_LOCK:
        conn = _get_connection(db_file)
        try:
            with conn:
                conn.execute("DELETE FROM sessions WHERE token = ?", (token.strip(),))
        finally:
            conn.close()


def revoke_all_user_sessions(user_id: str, db_file: Path | str | None = None) -> None:
    """Revoke all active sessions for a user."""
    if not user_id:
        return
    with _DB_LOCK:
        conn = _get_connection(db_file)
        try:
            with conn:
                conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        finally:
            conn.close()


def cleanup_expired_sessions(db_file: Path | str | None = None) -> int:
    """Clean up expired sessions from SQLite database."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with _DB_LOCK:
        conn = _get_connection(db_file)
        try:
            with conn:
                cursor = conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now_iso,))
                return cursor.rowcount
        finally:
            conn.close()
