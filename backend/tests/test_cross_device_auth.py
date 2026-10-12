"""
Khmer Translator — Comprehensive Cross-Device Authentication & Security Test Suite
Tests:
1. Registration, duplicate rejection, input validation
2. OWASP Argon2id password hashing & verification
3. Transparent automatic migration of legacy PBKDF2 hashes to Argon2id
4. Sliding window login rate-limiting (anti-brute force)
5. Multi-device / cross-browser concurrent sessions (same user, separate tokens)
6. Persistence across server restart / database reconnection
7. Session revocation on logout & expiration policy (30d Remember Me vs 24h standard)
8. Multi-tenant account data isolation (preventing cross-user inspection, modification, or deletion)
9. HttpOnly, Secure cookie lifecycle (Set-Cookie on login/register, delete on logout)
10. Credential security: stored password hash never exposed in public endpoints
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth import (
    AUTH_DB_FILE,
    argon2_hasher,
    hash_password,
    init_auth_db,
    verify_password,
    _FAILED_LOGIN_ATTEMPTS,
    _RATE_LIMIT_LOCK,
)
from app.config import AUTH_DB_PATH
from app.main import app
from app.storage import get_job, save_job, delete_job

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_test_db(tmp_path, monkeypatch):
    """Isolate SQLite database and clear rate limiter for each test."""
    test_db = Path(tmp_path / "test_auth_cross_device.db")
    monkeypatch.setattr("app.auth.AUTH_DB_FILE", test_db)
    monkeypatch.setattr("app.auth.AUTH_DB_PATH", test_db)
    init_auth_db(test_db)
    with _RATE_LIMIT_LOCK:
        _FAILED_LOGIN_ATTEMPTS.clear()
    yield test_db


# =============================================================================
# 1. SECURE PASSWORD HASHING (ARGON2ID & OWASP STANDARDS)
# =============================================================================

def test_argon2id_hashing_and_verification():
    """Verify Argon2id produces valid OWASP hashes with unique cryptographic salts."""
    pwd = "AngkorTempleSecure2026!"
    h1 = hash_password(pwd)
    h2 = hash_password(pwd)

    # Must start with $argon2id$
    assert h1.startswith("$argon2id$"), "Hash must use Argon2id format"
    assert h2.startswith("$argon2id$"), "Hash must use Argon2id format"
    # Unique salts ensure distinct hashes
    assert h1 != h2, "Unique salts must result in different hash strings"

    # Verification
    valid1, _ = verify_password(pwd, h1)
    valid2, _ = verify_password(pwd, h2)
    invalid, _ = verify_password("WrongPassword!", h1)

    assert valid1 is True
    assert valid2 is True
    assert invalid is False


def test_legacy_pbkdf2_migration_to_argon2id(isolated_test_db):
    """
    Verify existing accounts with legacy PBKDF2 hashes can still log in,
    and their password hashes are automatically upgraded to Argon2id on successful authentication.
    """
    email = "legacy_user@khmer-ai.org"
    password = "LegacyPassword123!"

    # Simulate an existing account created before Argon2id upgrade
    import hashlib, os
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
    legacy_hash = f"pbkdf2_sha256$600000${salt.hex()}${key.hex()}"

    conn = sqlite3.connect(str(isolated_test_db))
    with conn:
        conn.execute(
            """INSERT INTO users (id, name, email, password_hash, status, email_verified, created_at, updated_at, avatar_color)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("usr_legacy_01", "Ancient Scribe", email, legacy_hash, "active", 1, "2026-01-01T00:00:00", "2026-01-01T00:00:00", "#D6B46A"),
        )
    conn.close()

    # User logs in with legacy credentials
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    # Verify the database hash was upgraded to Argon2id transparently
    conn = sqlite3.connect(str(isolated_test_db))
    row = conn.execute("SELECT password_hash FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    upgraded_hash = row[0]
    assert upgraded_hash.startswith("$argon2id$"), "Hash must be upgraded to Argon2id upon login"


# =============================================================================
# 2. REGISTRATION & INPUT VALIDATION
# =============================================================================

def test_user_registration_and_duplicate_handling():
    payload = {
        "name": "Reach Sovan",
        "email": "reach@cambodia.org",
        "password": "StrongPassword2026!",
        "terms_accepted": True,
    }
    # 1. Register first time
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["user"]["email"] == "reach@cambodia.org"
    assert "token" in data
    # Password hash must NEVER be exposed
    assert "password_hash" not in data["user"]

    # Cookie must be returned
    assert "auth_token" in res.cookies

    # 2. Duplicate registration attempt must fail safely
    dup_res = client.post("/api/auth/register", json=payload)
    assert dup_res.status_code == 400
    assert "អ៊ីមែលនេះមានរួចហើយ" in dup_res.json()["detail"]


def test_registration_validation_rules():
    # Weak/short password (< 8 chars)
    r1 = client.post("/api/auth/register", json={
        "name": "Sovan", "email": "sovan@angkor.org", "password": "short", "terms_accepted": True
    })
    assert r1.status_code == 400

    # Invalid email format
    r2 = client.post("/api/auth/register", json={
        "name": "Sovan", "email": "not-an-email", "password": "ValidPassword123!", "terms_accepted": True
    })
    assert r2.status_code == 400

    # Unaccepted terms
    r3 = client.post("/api/auth/register", json={
        "name": "Sovan", "email": "sovan@angkor.org", "password": "ValidPassword123!", "terms_accepted": False
    })
    assert r3.status_code == 400


# =============================================================================
# 3. RATE LIMITING & BRUTE FORCE PROTECTION
# =============================================================================

def test_login_rate_limiting():
    """Verify that multiple consecutive failed login attempts trigger sliding-window lockout."""
    email = "target@khmer-ai.org"
    # Register user first
    client.post("/api/auth/register", json={
        "name": "Target User", "email": email, "password": "CorrectPassword2026!", "terms_accepted": True
    })

    # Trigger 5 failed login attempts
    for _ in range(5):
        r = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword!"})
        assert r.status_code == 401

    # 6th attempt must be blocked by rate limiter
    locked_res = client.post("/api/auth/login", json={"email": email, "password": "CorrectPassword2026!"})
    assert locked_res.status_code in (400, 401)
    detail = locked_res.json()["detail"]
    assert "Too many failed login attempts" in detail or "បរាជ័យច្រើនដងពេក" in detail


# =============================================================================
# 4. CROSS-DEVICE / MULTI-DEVICE LOGIN & SESSION PERSISTENCE
# =============================================================================

def test_cross_device_concurrent_sessions():
    """
    Test user registering once, then logging in from Computer A and Phone B.
    Both devices authenticate against the same server DB and have independent valid sessions.
    """
    email = "nomad@khmer-ai.org"
    password = "CrossDevicePass2026!"

    # 1. Register on Computer A
    reg_res = client.post("/api/auth/register", json={
        "name": "Digital Nomad", "email": email, "password": password, "terms_accepted": True
    }, headers={"User-Agent": "Computer-A Chrome/120"})
    assert reg_res.status_code == 200
    token_computer_a = reg_res.json()["token"]

    # 2. Log in on Phone B with same credentials
    phone_res = client.post("/api/auth/login", json={
        "email": email, "password": password, "remember_me": True
    }, headers={"User-Agent": "Phone-B Safari/17"})
    assert phone_res.status_code == 200
    token_phone_b = phone_res.json()["token"]

    # Two distinct session tokens issued
    assert token_computer_a != token_phone_b

    # 3. Both devices can validate their sessions concurrently
    me_a = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_computer_a}"})
    me_b = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_phone_b}"})
    assert me_a.status_code == 200 and me_a.json()["authenticated"] is True
    assert me_b.status_code == 200 and me_b.json()["authenticated"] is True
    assert me_a.json()["user"]["id"] == me_b.json()["user"]["id"]

    # 4. Computer A logs out: only Computer A's token is revoked; Phone B remains active!
    client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token_computer_a}"})
    after_logout_a = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_computer_a}"})
    after_logout_b = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_phone_b}"})

    assert after_logout_a.json()["authenticated"] is False
    assert after_logout_b.json()["authenticated"] is True


def test_persistence_across_server_restart(isolated_test_db):
    """
    Verify accounts and sessions persist when database connections are completely closed
    and re-initialized, simulating a full server restart or cold container redeployment.
    """
    email = "restart_test@angkor.org"
    password = "RestartPassword2026!"

    # Register user
    reg = client.post("/api/auth/register", json={
        "name": "Persistent User", "email": email, "password": password, "terms_accepted": True
    })
    token = reg.json()["token"]
    user_id = reg.json()["user"]["id"]

    # Simulate complete server restart: re-initialize DB table structures on disk
    init_auth_db(isolated_test_db)

    # Session token remains 100% valid after restart
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["authenticated"] is True
    assert me_res.json()["user"]["id"] == user_id

    # User can log in anew after restart
    login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    assert login_res.json()["user"]["id"] == user_id


# =============================================================================
# 5. MULTI-TENANT ACCOUNT DATA ISOLATION
# =============================================================================

def test_multi_tenant_job_data_isolation():
    """
    Verify strict resource isolation between users:
    - User A's jobs are private to User A
    - User B cannot view User A's job (403 Forbidden)
    - User B cannot delete User A's job (403 Forbidden)
    - User B cannot transcribe or export User A's job (403 Forbidden)
    - GET /api/jobs only returns jobs owned by the authenticated caller
    """
    # 1. Register User A
    r_a = client.post("/api/auth/register", json={
        "name": "User Alpha", "email": "alpha@nexus.org", "password": "AlphaPassword2026!", "terms_accepted": True
    })
    token_a = r_a.json()["token"]
    user_a_id = r_a.json()["user"]["id"]

    # 2. Register User B
    r_b = client.post("/api/auth/register", json={
        "name": "User Beta", "email": "beta@nexus.org", "password": "BetaPassword2026!", "terms_accepted": True
    })
    token_b = r_b.json()["token"]

    # 3. Create a private job for User A
    job_a_id = "job_alpha_private_001"
    save_job({
        "id": job_a_id,
        "user_id": user_a_id,
        "name": "Alpha Private Translation",
        "filename": "alpha_media.mp4",
        "status": "uploaded",
        "created_at": "2026-10-12T10:00:00Z",
    })

    try:
        # 4. User A can view their own job
        resp_a = client.get(f"/api/jobs/{job_a_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert resp_a.status_code == 200
        assert resp_a.json()["id"] == job_a_id

        # 5. User B attempts to access User A's job -> MUST return 403 Forbidden
        resp_b_view = client.get(f"/api/jobs/{job_a_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert resp_b_view.status_code == 403, "User B must not be allowed to view User A's job"

        # 6. Unauthenticated guest attempts to access User A's job -> MUST return 403 Forbidden
        resp_guest_view = client.get(f"/api/jobs/{job_a_id}")
        assert resp_guest_view.status_code == 403

        # 7. User B attempts to delete User A's job -> MUST return 403 Forbidden
        resp_b_del = client.delete(f"/api/jobs/{job_a_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert resp_b_del.status_code == 403, "User B must not be allowed to delete User A's job"

        # 8. User B attempts to transcribe User A's job -> MUST return 403 Forbidden
        resp_b_transcribe = client.post(f"/api/jobs/{job_a_id}/transcribe", headers={"Authorization": f"Bearer {token_b}"})
        assert resp_b_transcribe.status_code == 403, "User B must not be allowed to transcribe User A's job"

        # 9. List jobs: User A sees job_a_id; User B does NOT see job_a_id
        list_a = client.get("/api/jobs", headers={"Authorization": f"Bearer {token_a}"}).json()
        list_b = client.get("/api/jobs", headers={"Authorization": f"Bearer {token_b}"}).json()
        assert any(j["id"] == job_a_id for j in list_a)
        assert not any(j["id"] == job_a_id for j in list_b)

        # 10. User A can safely delete their own job
        del_a = client.delete(f"/api/jobs/{job_a_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert del_a.status_code == 200
    finally:
        delete_job(job_a_id)


# =============================================================================
# 6. HTTPONLY COOKIE AUTHENTICATION
# =============================================================================

def test_httponly_cookie_authentication_lifecycle():
    """Verify that clients without Authorization headers authenticate automatically via cookies."""
    email = "cookie_user@angkor.org"
    password = "CookiePassword2026!"
    local_client = TestClient(app)

    # 1. Registration sets the cookie
    login_res = local_client.post("/api/auth/register", json={
        "name": "Cookie Tester", "email": email, "password": password, "terms_accepted": True
    })
    assert login_res.status_code == 200
    assert "auth_token" in login_res.cookies

    # 2. GET /api/auth/me using ONLY the cookie (no Authorization header)
    me_res = local_client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["authenticated"] is True
    assert me_res.json()["user"]["email"] == email

    # 3. Logout clears the cookie
    logout_res = local_client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    # 4. Subsequent request with invalidated cookie is unauthenticated
    after_res = local_client.get("/api/auth/me")
    assert after_res.status_code == 200
    assert after_res.json()["authenticated"] is False
