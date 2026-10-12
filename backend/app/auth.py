"""Khmer Translator — Production Authentication Engine (Angkor Nexus).

Provides secure user registration, credential verification, PBKDF2 password hashing,
cryptographic session tokens, and SQLite persistence.
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
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

from .config import BASE_DIR

logger = logging.getLogger(__name__)

AUTH_DB_FILE = (BASE_DIR / "auth.db").resolve()
_DB_LOCK = threading.Lock()

# Email regex validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PBKDF2_ITERATIONS = 600_000  # OWASP recommended standard for SHA-256


def _get_connection(db_file: Path | str | None = None) -> sqlite3.Connection:
    target = db_file or AUTH_DB_FILE
    conn = sqlite3.connect(str(target), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db(db_file: Path | str | None = None) -> None:
    """Initialize the SQLite tables for users and authentication sessions."""
    with _DB_LOCK:
        conn = _get_connection(db_file)
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        avatar_color TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        token TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
        finally:
            conn.close()
    logger.info("Auth database initialized at %s", AUTH_DB_FILE)


# Call initialization at module load
init_auth_db()


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique cryptographic salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored PBKDF2 hash using constant-time comparison."""
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
        logger.error("Error verifying password hash: %s", exc)
        return False


def _generate_avatar_color(name: str) -> str:
    palette = ["#D6B46A", "#C88C9D", "#426B59", "#77D5A3", "#5C7CFA", "#E599F7", "#F59F00"]
    h = sum(ord(c) for c in name)
    return palette[h % len(palette)]


def register_user(name: str, email: str, password: str) -> tuple[dict[str, Any], str]:
    """Register a new user account with hashed password and create session."""
    clean_name = name.strip()
    clean_email = email.strip().lower()

    if len(clean_name) < 2:
        raise ValueError("Name must be at least 2 characters long")
    if not EMAIL_REGEX.match(clean_email):
        raise ValueError("Invalid email address format")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    p_hash = hash_password(password)
    user_id = f"usr_{secrets.token_hex(12)}"
    now = datetime.now(timezone.utc).isoformat()
    avatar_color = _generate_avatar_color(clean_name)

    with _DB_LOCK:
        conn = _get_connection()
        try:
            with conn:
                existing = conn.execute("SELECT id FROM users WHERE email = ?", (clean_email,)).fetchone()
                if existing:
                    raise ValueError("An account with this email address already exists / អ៊ីមែលនេះមានរួចហើយ")

                conn.execute(
                    "INSERT INTO users (id, name, email, password_hash, created_at, avatar_color) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, clean_name, clean_email, p_hash, now, avatar_color),
                )
        finally:
            conn.close()

    user_dict = {
        "id": user_id,
        "name": clean_name,
        "email": clean_email,
        "created_at": now,
        "avatar_color": avatar_color,
    }
    token = create_session(user_id, remember_me=True)
    return user_dict, token


def login_user(email: str, password: str, remember_me: bool = False) -> tuple[dict[str, Any], str]:
    """Authenticate user with email and password, returning user profile and session token."""
    clean_email = email.strip().lower()

    with _DB_LOCK:
        conn = _get_connection()
        try:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (clean_email,)).fetchone()
        finally:
            conn.close()

    if not row:
        raise ValueError("Invalid email or password")

    if not verify_password(password, row["password_hash"]):
        raise ValueError("Invalid email or password")

    user_dict = {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "created_at": row["created_at"],
        "avatar_color": row["avatar_color"],
    }
    token = create_session(row["id"], remember_me=remember_me)
    return user_dict, token


def create_session(user_id: str, remember_me: bool = False) -> str:
    """Generate a secure cryptographic session token with expiration."""
    token = secrets.token_urlsafe(36)
    now = datetime.now(timezone.utc)
    duration_days = 30 if remember_me else 7
    expires_at = (now + timedelta(days=duration_days)).isoformat()

    with _DB_LOCK:
        conn = _get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                    (token, user_id, now.isoformat(), expires_at),
                )
        finally:
            conn.close()
    return token


def get_user_by_token(token: str) -> Optional[dict[str, Any]]:
    """Retrieve user details for a valid session token, verifying expiration."""
    if not token or len(token) < 20:
        return None

    clean_token = token.strip()
    now_iso = datetime.now(timezone.utc).isoformat()

    with _DB_LOCK:
        conn = _get_connection()
        try:
            query = """
                SELECT u.id, u.name, u.email, u.created_at, u.avatar_color, s.expires_at
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = ? AND s.expires_at > ?
            """
            row = conn.execute(query, (clean_token, now_iso)).fetchone()
            if not row:
                return None

            return {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "created_at": row["created_at"],
                "avatar_color": row["avatar_color"],
            }
        finally:
            conn.close()


def revoke_session(token: str) -> None:
    """Revoke and delete a session token upon logout."""
    if not token:
        return
    with _DB_LOCK:
        conn = _get_connection()
        try:
            with conn:
                conn.execute("DELETE FROM sessions WHERE token = ?", (token.strip(),))
        finally:
            conn.close()


def cleanup_expired_sessions() -> int:
    """Clean up expired sessions from SQLite database."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with _DB_LOCK:
        conn = _get_connection()
        try:
            with conn:
                cursor = conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now_iso,))
                return cursor.rowcount
        finally:
            conn.close()
