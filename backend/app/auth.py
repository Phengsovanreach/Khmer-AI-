"""Khmer Translator — Production Authentication Engine (Angkor Nexus & SQLAlchemy).

Provides secure user registration, credential verification, OWASP Argon2id password hashing
(with seamless PBKDF2 migration), cryptographic session tokens, brute-force rate limiting,
cross-device session management, audit logging, and PostgreSQL/SQLite persistence.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from pathlib import Path
from typing import Any, Optional



from .db.database import SessionLocal, init_db, db_session_scope, set_db_url
from .db.models import User, Session as UserSession, AuditLog

logger = logging.getLogger(__name__)

# Legacy database file paths for SQLite testing compatibility
AUTH_DB_PATH = Path(__file__).resolve().parents[1] / "auth.db"
AUTH_DB_FILE = AUTH_DB_PATH


def init_auth_db(db_path: Any = None) -> None:
    """Initialize auth tables in database (supporting backward compatibility with SQLite test fixtures)."""
    target_path = Path(db_path) if db_path else AUTH_DB_FILE
    target_path.parent.mkdir(parents=True, exist_ok=True)
    import sqlite3
    conn = sqlite3.connect(str(target_path), check_same_thread=False)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                status TEXT DEFAULT 'active',
                email_verified INTEGER DEFAULT 1,
                avatar_color TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                last_login_at TEXT
            )
        """)
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT UNIQUE NOT NULL,
                user_id TEXT,
                event_type TEXT NOT NULL,
                status TEXT NOT NULL,
                duration_ms REAL DEFAULT 0.0,
                details_json TEXT,
                ip_address TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users(LOWER(email))")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_name_lower ON users(LOWER(name))")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_op ON audit_logs(operation_id)")
        conn.commit()
    conn.close()

    # Rebind SQLAlchemy to target SQLite database
    set_db_url(f"sqlite:///{target_path.resolve().as_posix()}")


# Email regex validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def normalize_email(email: str | None) -> str:
    """Normalize email address consistently (strip whitespace, lowercase)."""
    return (email or "").strip().lower()


def normalize_username(name: str | None) -> str:
    """Normalize username/display name (strip whitespace)."""
    return (name or "").strip()


def mask_email(email: str | None) -> str:
    """Mask email address for privacy-safe logs and Telegram alerts (e.g. j***e@domain.com)."""
    clean = normalize_email(email)
    if not clean or "@" not in clean:
        return "***"
    local_part, domain = clean.split("@", 1)
    if len(local_part) <= 1:
        masked_local = "*"
    elif len(local_part) == 2:
        masked_local = f"{local_part[0]}*"
    else:
        masked_local = f"{local_part[0]}***{local_part[-1]}"
    return f"{masked_local}@{domain}"



try:
    import argon2
    argon2_hasher = argon2.PasswordHasher(
        time_cost=2,
        memory_cost=32768,
        parallelism=2,
        hash_len=32,
        type=argon2.Type.ID,
    )
    HAS_ARGON2 = True
except ImportError:
    argon2 = None
    argon2_hasher = None
    HAS_ARGON2 = False
    logger.info("argon2-cffi not installed; using standard PBKDF2-HMAC-SHA256 fallback")


# Legacy & fallback PBKDF2 parameters for backward-compatibility verification
PBKDF2_ITERATIONS = 600_000


# Rate Limiting configuration (5 failed attempts per 5 minutes per identifier)
_RATE_LIMIT_LOCK = threading.Lock()
_FAILED_LOGIN_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 300.0  # 5 minutes


# Initialize database at module load
try:
    init_auth_db()
except Exception as e:
    logger.warning("Auth DB initial load warning (will retry on demand): %s", e)


def hash_password(password: str) -> str:
    """Hash password using state-of-the-art Argon2id (or secure PBKDF2 fallback if argon2-cffi unavailable)."""
    if HAS_ARGON2 and argon2_hasher:
        return argon2_hasher.hash(password)
    # Secure PBKDF2 fallback
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"


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
        if HAS_ARGON2 and argon2_hasher:
            try:
                argon2_hasher.verify(stored_hash, password)
                needs_rehash = argon2_hasher.check_needs_rehash(stored_hash)
                return True, needs_rehash
            except argon2.exceptions.VerifyMismatchError:
                return False, False
            except Exception as exc:
                logger.error("Argon2 verification exception: %s", exc)
                return False, False
        else:
            logger.warning("Stored hash is Argon2id, but argon2-cffi is not installed in this environment.")
            return False, False

    # Check if hash is legacy/fallback PBKDF2
    if stored_hash.startswith("pbkdf2_sha256$"):
        if _verify_pbkdf2_legacy(password, stored_hash):
            return True, HAS_ARGON2  # Upgrade to Argon2id when argon2 is available
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


# -----------------------------------------------------------------------------
# AUDIT LOGGING & USER NOTIFICATIONS
# -----------------------------------------------------------------------------

def record_audit_event(
    event_type: str,
    status: str,
    user_id: Optional[str] = None,
    operation_id: Optional[str] = None,
    duration_ms: float = 0.0,
    details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    notify_telegram: bool = True,
) -> str:
    """
    Persists an audit log event into the database and dispatches a privacy-conscious
    Type 3 User Activity notification to Telegram if enabled.
    """
    import json
    op_id = operation_id or f"op_{secrets.token_hex(8)}"
    now = datetime.now(timezone.utc)

    # Save to database
    try:
        with db_session_scope() as session:
            log_entry = AuditLog(
                operation_id=op_id,
                user_id=user_id,
                event_type=event_type,
                status=status.upper(),
                duration_ms=round(duration_ms, 2),
                details_json=json.dumps(details or {}),
                ip_address=ip_address,
                created_at=now,
            )
            session.add(log_entry)
    except Exception as exc:
        logger.error("Failed to persist audit log: %s", exc)

    # Dispatch Telegram User Activity Alert
    if notify_telegram:
        try:
            from self_healing.notifications import TelegramNotifier, format_user_activity_alert
            notifier = TelegramNotifier()
            username = details.get("username") if details else None
            masked_email = details.get("masked_email") if details else None
            environment = details.get("environment") if details else ("production" if os.getenv("RENDER") else "development")
            msg = format_user_activity_alert(
                event=event_type,
                user_id=user_id or "anonymous",
                operation_id=op_id,
                status=status.upper(),
                duration_sec=duration_ms / 1000.0,
                error_category=details.get("error_category") if details else None,
                result_summary=details.get("summary") if details else None,
                username=username,
                masked_email=masked_email,
                environment=environment,
            )
            notifier.send_message(msg)
        except Exception as exc:
            logger.debug("Failed to dispatch Telegram audit notification (non-fatal): %s", exc)

    return op_id


# -----------------------------------------------------------------------------
# USER REGISTRATION & AUTHENTICATION
# -----------------------------------------------------------------------------

def register_user(
    name: str,
    email: str,
    password: str,
    db_file: Path | str | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Register a new user account with Argon2id hashed password and create session."""
    t0 = time.perf_counter()
    clean_name = normalize_username(name)
    clean_email = normalize_email(email)

    if len(clean_name) < 2:
        raise ValueError("Name must be at least 2 characters long / ឈ្មោះត្រូវមានយ៉ាងហោចណាស់ ២ តួអក្សរ")
    if not EMAIL_REGEX.match(clean_email):
        raise ValueError("Invalid email address format / ទម្រង់អ៊ីមែលមិនត្រឹមត្រូវ")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long / ពាក្យសម្ងាត់ត្រូវមានយ៉ាងហោចណាស់ ៨ តួអក្សរ")

    p_hash = hash_password(password)
    user_id = f"usr_{secrets.token_hex(12)}"
    now = datetime.now(timezone.utc)
    avatar_color = _generate_avatar_color(clean_name)

    from sqlalchemy import func
    from sqlalchemy.exc import IntegrityError
    import sqlite3

    try:
        with db_session_scope() as session:
            existing = session.query(User).filter(
                (func.lower(User.email) == clean_email) | (func.lower(User.name) == clean_name.lower())
            ).first()
            if existing:
                record_audit_event(
                    event_type="User Registration",
                    status="FAILED",
                    user_id=None,
                    duration_ms=(time.perf_counter() - t0) * 1000,
                    details={
                        "error_category": "Duplicate Account",
                        "summary": "Registration attempted with existing email or username",
                        "username": clean_name,
                        "masked_email": mask_email(clean_email),
                    },
                    ip_address=client_ip,
                    notify_telegram=False,
                )
                raise ValueError("An account with this email address or username already exists. Please log in / គណនីជាមួយអ៊ីមែលឬឈ្មោះនេះមានរួចហើយ សូមចូលប្រើប្រាស់។")

            new_user = User(
                id=user_id,
                name=clean_name,
                email=clean_email,
                password_hash=p_hash,
                role="user",
                status="active",
                email_verified=True,
                avatar_color=avatar_color,
                created_at=now,
                updated_at=now,
                last_login_at=now,
            )
            session.add(new_user)
    except (IntegrityError, sqlite3.IntegrityError) as err:
        logger.warning("Concurrent duplicate user registration caught by DB constraint: %s", err)
        record_audit_event(
            event_type="User Registration",
            status="FAILED",
            user_id=None,
            duration_ms=(time.perf_counter() - t0) * 1000,
            details={
                "error_category": "Concurrent Duplicate",
                "summary": "Duplicate user caught by database unique constraint",
                "username": clean_name,
                "masked_email": mask_email(clean_email),
            },
            ip_address=client_ip,
            notify_telegram=False,
        )
        raise ValueError("An account with this email address or username already exists. Please log in / គណនីជាមួយអ៊ីមែលឬឈ្មោះនេះមានរួចហើយ សូមចូលប្រើប្រាស់។")

    user_dict = {
        "id": user_id,
        "name": clean_name,
        "email": clean_email,
        "role": "user",
        "status": "active",
        "email_verified": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "last_login_at": now.isoformat(),
        "avatar_color": avatar_color,
    }

    token = create_session(
        user_id,
        remember_me=True,
        db_file=db_file,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    duration_ms = (time.perf_counter() - t0) * 1000
    record_audit_event(
        event_type="User Registration",
        status="SUCCESS",
        user_id=user_id,
        duration_ms=duration_ms,
        details={
            "summary": "New user account registered successfully",
            "username": clean_name,
            "masked_email": mask_email(clean_email),
            "environment": os.getenv("ENVIRONMENT", "production" if os.getenv("RENDER") else "development"),
        },
        ip_address=client_ip,
        notify_telegram=True,
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
    """Authenticate user with email or username and password, returning user profile and session token."""
    t0 = time.perf_counter()
    clean_ident = (email or "").strip()
    clean_ident_lower = clean_ident.lower()
    rate_key = f"{client_ip or 'ip'}:{clean_ident_lower}"
    _check_rate_limit(rate_key)

    from sqlalchemy import func

    session = SessionLocal()
    try:
        user = session.query(User).filter(
            (func.lower(User.email) == clean_ident_lower) | (func.lower(User.name) == clean_ident_lower)
        ).first()
        if not user:
            _record_failed_attempt(rate_key)
            duration_ms = (time.perf_counter() - t0) * 1000
            record_audit_event(
                event_type="User Login",
                status="FAILED",
                user_id=None,
                duration_ms=duration_ms,
                details={
                    "error_category": "Invalid Credentials",
                    "summary": "Identifier not found",
                    "username": clean_ident if "@" not in clean_ident else None,
                    "masked_email": mask_email(clean_ident) if "@" in clean_ident else None,
                },
                ip_address=client_ip,
                notify_telegram=False,
            )
            raise ValueError("Invalid email or password / អ៊ីមែល ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ")

        if user.status != "active":
            raise ValueError("This account has been deactivated / គណនីនេះត្រូវបានផ្អាកដំណើរការ")

        is_valid, needs_rehash = verify_password(password, user.password_hash)
        if not is_valid:
            _record_failed_attempt(rate_key)
            duration_ms = (time.perf_counter() - t0) * 1000
            record_audit_event(
                event_type="User Login",
                status="FAILED",
                user_id=user.id,
                duration_ms=duration_ms,
                details={
                    "error_category": "Password Mismatch",
                    "summary": "Incorrect password entered",
                    "username": user.name,
                    "masked_email": mask_email(user.email),
                },
                ip_address=client_ip,
                notify_telegram=False,
            )
            raise ValueError("Invalid email or password / អ៊ីមែល ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ")

        # Login succeeded: clear rate limits
        _clear_rate_limit(rate_key)

        now = datetime.now(timezone.utc)
        user.last_login_at = now
        if needs_rehash:
            user.password_hash = hash_password(password)
            user.updated_at = now
            logger.info("Upgraded password hash to Argon2id for user %s", user.id)

        session.commit()
        user_dict = user.to_dict()
    finally:
        session.close()

    token = create_session(
        user_dict["id"],
        remember_me=remember_me,
        db_file=db_file,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    duration_ms = (time.perf_counter() - t0) * 1000
    record_audit_event(
        event_type="User Login",
        status="SUCCESS",
        user_id=user_dict["id"],
        duration_ms=duration_ms,
        details={
            "summary": "User logged in successfully via web interface",
            "username": user_dict["name"],
            "masked_email": mask_email(user_dict["email"]),
            "environment": os.getenv("ENVIRONMENT", "production" if os.getenv("RENDER") else "development"),
        },
        ip_address=client_ip,
        notify_telegram=True,
    )

    return user_dict, token


def create_session(
    user_id: str,
    remember_me: bool = False,
    db_file: Path | str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> str:
    """Generate a secure cryptographic session token with expiration and save to database."""
    token = secrets.token_urlsafe(36)
    now = datetime.now(timezone.utc)
    duration = timedelta(days=30) if remember_me else timedelta(hours=24)
    expires_at = now + duration

    with db_session_scope() as session:
        user_session = UserSession(
            token=token,
            user_id=user_id,
            created_at=now,
            expires_at=expires_at,
            ip_address=client_ip_clean(ip_address),
            user_agent=user_agent[:500] if user_agent else None,
        )
        session.add(user_session)

    return token


def client_ip_clean(ip: Optional[str]) -> Optional[str]:
    if not ip:
        return None
    return ip.split(",")[0].strip()[:45]


def get_user_by_token(token: str, db_file: Path | str | None = None) -> Optional[dict[str, Any]]:
    """Retrieve user details for a valid session token, verifying expiration."""
    if not token or len(token) < 20:
        return None

    clean_token = token.strip()
    now = datetime.now(timezone.utc)

    session = SessionLocal()
    try:
        user_session = (
            session.query(UserSession)
            .join(User, UserSession.user_id == User.id)
            .filter(
                UserSession.token == clean_token,
                UserSession.expires_at > now,
                User.status == "active",
            )
            .first()
        )
        if not user_session or not user_session.user:
            return None

        return user_session.user.to_dict()
    finally:
        session.close()


def revoke_session(token: str, db_file: Path | str | None = None) -> None:
    """Revoke and delete a session token upon logout."""
    if not token:
        return
    clean_token = token.strip()
    with db_session_scope() as session:
        user_session = session.query(UserSession).filter(UserSession.token == clean_token).first()
        user_id = user_session.user_id if user_session else None
        if user_session:
            session.delete(user_session)

    if user_id:
        record_audit_event(
            event_type="User Logout",
            status="SUCCESS",
            user_id=user_id,
            details={"summary": "User session ended normally"},
            notify_telegram=False,
        )


def revoke_all_user_sessions(user_id: str, db_file: Path | str | None = None) -> None:
    """Revoke all active sessions for a user."""
    if not user_id:
        return
    with db_session_scope() as session:
        session.query(UserSession).filter(UserSession.user_id == user_id).delete()


def cleanup_expired_sessions(db_file: Path | str | None = None) -> int:
    """Clean up expired sessions from database."""
    now = datetime.now(timezone.utc)
    with db_session_scope() as session:
        count = session.query(UserSession).filter(UserSession.expires_at <= now).delete()
        return count


def get_current_user_optional(request: Any, authorization: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Extract and authenticate user from Bearer header or HttpOnly cookie."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    elif authorization and authorization.strip():
        token = authorization.strip()
    if not token and hasattr(request, "cookies"):
        token = request.cookies.get("auth_token")

    if not token:
        return None
    return get_user_by_token(token)
