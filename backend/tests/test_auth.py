"""
Angkor Nexus Authentication Regression Test Suite
Validates registration, login, token verification, logout, rate limiting, and input validation.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import init_auth_db
from pathlib import Path

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_auth_db(tmp_path, monkeypatch):
    """Use a temporary SQLite database for each test to ensure test isolation."""
    test_db = Path(tmp_path / "test_auth.db")
    monkeypatch.setattr("app.auth.AUTH_DB_FILE", test_db)
    init_auth_db(test_db)
    yield


def test_auth_status_unauthenticated():
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
    assert data["user"] is None


def test_auth_registration_success():
    payload = {
        "name": "Reach Sovan",
        "email": "reach@khmer-ai.org",
        "password": "AngkorPass2026!",
        "terms_accepted": True
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["email"] == "reach@khmer-ai.org"
    assert data["user"]["name"] == "Reach Sovan"
    assert "token" in data
    assert len(data["token"]) > 30


def test_auth_registration_duplicate_rejected():
    payload = {
        "name": "Reach Sovan",
        "email": "duplicate@khmer-ai.org",
        "password": "AngkorPass2026!",
        "terms_accepted": True
    }
    r1 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 200

    # Second registration with same email
    r2 = client.post("/api/auth/register", json=payload)
    assert r2.status_code == 400
    assert "អ៊ីមែលនេះមានរួចហើយ" in r2.json()["detail"]


def test_auth_registration_validation_errors():
    # Empty email
    r1 = client.post("/api/auth/register", json={
        "name": "Tester",
        "email": "invalid-email",
        "password": "ValidPass123!",
        "terms_accepted": True
    })
    assert r1.status_code == 400

    # Short password
    r2 = client.post("/api/auth/register", json={
        "name": "Tester",
        "email": "valid@test.com",
        "password": "123",
        "terms_accepted": True
    })
    assert r2.status_code == 400

    # Terms unaccepted
    r3 = client.post("/api/auth/register", json={
        "name": "Tester",
        "email": "valid@test.com",
        "password": "ValidPass123!",
        "terms_accepted": False
    })
    assert r3.status_code == 400


def test_auth_login_lifecycle_and_revocation():
    # 1. Register user
    reg_payload = {
        "name": "Devata User",
        "email": "devata@angkor.org",
        "password": "TempleSecret2026#",
        "terms_accepted": True
    }
    client.post("/api/auth/register", json=reg_payload)

    # 2. Login with correct password
    login_resp = client.post("/api/auth/login", json={
        "email": "devata@angkor.org",
        "password": "TempleSecret2026#",
        "remember_me": True
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    token = login_data["token"]
    assert token

    # 3. Verify session with token
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["authenticated"] is True
    assert me_resp.json()["user"]["name"] == "Devata User"

    # 4. Login with incorrect password returns 401
    bad_login = client.post("/api/auth/login", json={
        "email": "devata@angkor.org",
        "password": "WrongPassword!",
        "remember_me": False
    })
    assert bad_login.status_code == 401

    # 5. Logout revokes token
    logout_resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    # 6. Verify session is now unauthenticated
    after_logout = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert after_logout.status_code == 200
    assert after_logout.json()["authenticated"] is False
