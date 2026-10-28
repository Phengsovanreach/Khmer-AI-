"""
Unit tests for user registration, login, rate limiting, and session management.
"""
import pytest
import uuid
from app.auth import (
    register_user,
    login_user,
    get_user_by_token,
    revoke_session,
    hash_password,
    verify_password,
)


def test_password_hashing_and_verification():
    raw_pass = "MySecretPass999#!"
    h = hash_password(raw_pass)
    assert len(h) > 20
    is_valid, _ = verify_password(raw_pass, h)
    assert is_valid is True
    wrong_valid, _ = verify_password("WrongPassword123!", h)
    assert wrong_valid is False


def test_user_registration_and_login_lifecycle():
    unique_email = f"user_{uuid.uuid4().hex[:8]}@angkor-test.com"
    user_dict, token = register_user("Angkor Explorer", unique_email, "StrongPass7788!@")
    
    assert user_dict["email"] == unique_email
    assert user_dict["name"] == "Angkor Explorer"
    assert user_dict["status"] == "active"
    assert len(token) > 25

    # Retrieve by session token
    fetched = get_user_by_token(token)
    assert fetched is not None
    assert fetched["id"] == user_dict["id"]
    assert fetched["email"] == unique_email

    # Login with credentials
    logged_user, login_token = login_user(unique_email, "StrongPass7788!@")
    assert logged_user["id"] == user_dict["id"]
    assert len(login_token) > 25

    # Revoke session
    revoke_session(login_token)
    revoked_user = get_user_by_token(login_token)
    assert revoked_user is None


def test_duplicate_registration_fails():
    unique_email = f"dup_{uuid.uuid4().hex[:8]}@angkor-test.com"
    register_user("User One", unique_email, "Password1234#@")
    with pytest.raises(ValueError, match="already exists"):
        register_user("User Two", unique_email, "Password5678#@")


def test_invalid_login_fails():
    with pytest.raises(ValueError, match="Invalid email or password"):
        login_user("nonexistent_user_999@test.com", "SomePassword123!")
