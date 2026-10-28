"""
Unit tests for user registration, login, duplicate account prevention,
password hashing security, privacy-conscious Telegram audit alerts, and session management.
"""
import pytest
import uuid
from unittest.mock import MagicMock, patch

from app.auth import (
    register_user,
    login_user,
    get_user_by_token,
    revoke_session,
    hash_password,
    verify_password,
    normalize_email,
    normalize_username,
    mask_email,
)


def test_password_hashing_and_verification():
    raw_pass = "MySecretPass999#!"
    h = hash_password(raw_pass)
    assert len(h) > 20
    assert raw_pass not in h  # Plaintext password is NEVER stored directly
    is_valid, _ = verify_password(raw_pass, h)
    assert is_valid is True
    wrong_valid, _ = verify_password("WrongPassword123!", h)
    assert wrong_valid is False


def test_user_registration_and_login_lifecycle():
    unique_suffix = uuid.uuid4().hex[:8]
    unique_email = f"user_{unique_suffix}@angkor-test.com"
    unique_name = f"Angkor Explorer {unique_suffix}"
    user_dict, token = register_user(unique_name, unique_email, "StrongPass7788!@")
    
    assert user_dict["email"] == unique_email
    assert user_dict["name"] == unique_name
    assert user_dict["status"] == "active"
    assert len(token) > 25

    # Retrieve by session token (cross-device session verification)
    fetched = get_user_by_token(token)
    assert fetched is not None
    assert fetched["id"] == user_dict["id"]
    assert fetched["email"] == unique_email

    # Login with email
    logged_user, login_token = login_user(unique_email, "StrongPass7788!@")
    assert logged_user["id"] == user_dict["id"]
    assert len(login_token) > 25

    # Login with username across another session/device
    logged_user2, login_token2 = login_user(unique_name, "StrongPass7788!@")
    assert logged_user2["id"] == user_dict["id"]
    assert len(login_token2) > 25

    # Revoke session
    revoke_session(login_token)
    revoked_user = get_user_by_token(login_token)
    assert revoked_user is None


def test_duplicate_registration_fails_case_insensitive():
    unique_suffix = uuid.uuid4().hex[:8]
    unique_email = f"dup_{unique_suffix}@angkor-test.com"
    register_user(f"User Original {unique_suffix}", unique_email, "Password1234#@")

    # Duplicate with different casing and whitespace
    with pytest.raises(ValueError, match="already exists"):
        register_user(f"User Second {unique_suffix}", f"  {unique_email.upper()}  ", "Password5678#@")


def test_duplicate_username_fails():
    unique_suffix = uuid.uuid4().hex[:8]
    unique_name = f"UniqueUser_{unique_suffix}"
    email_one = f"user1_{unique_suffix}@test.com"
    email_two = f"user2_{unique_suffix}@test.com"

    register_user(unique_name, email_one, "Password1234#@")

    # Attempting to register another account with the same username (case-insensitive)
    with pytest.raises(ValueError, match="already exists"):
        register_user(f"  {unique_name.lower()}  ", email_two, "Password5678#@")


def test_invalid_login_fails():
    with pytest.raises(ValueError, match="Invalid email or password"):
        login_user("nonexistent_user_999@test.com", "SomePassword123!")


def test_email_masking():
    assert mask_email("phengsovanreach@gmail.com") == "p***h@gmail.com"
    assert mask_email("reach@angkor.com") == "r***h@angkor.com"
    assert mask_email("ab@domain.com") == "a*@domain.com"
    assert mask_email("a@domain.com") == "*@domain.com"
    assert mask_email("") == "***"


def test_telegram_alert_contains_no_secrets():
    unique_suffix = uuid.uuid4().hex[:8]
    unique_email = f"audit_{unique_suffix}@test.com"
    unique_name = f"AuditUser_{unique_suffix}"
    raw_pass = "SuperSecretPassword1234!"

    sent_messages = []

    def mock_send_message(self, text, *args, **kwargs):
        sent_messages.append(text)
        return {"status": "DELIVERED", "delivered": True}

    with patch("self_healing.notifications.telegram.TelegramNotifier.send_message", mock_send_message):
        # 1. Register User
        user_dict, token = register_user(unique_name, unique_email, raw_pass)
        assert len(sent_messages) >= 1
        reg_msg = sent_messages[-1]
        assert "USER ACTIVITY" in reg_msg
        assert unique_name in reg_msg
        # Ensure raw password, hash, or token is NEVER leaked
        assert raw_pass not in reg_msg
        assert token not in reg_msg
        assert "password_hash" not in reg_msg

        # 2. Login User
        logged_user, login_token = login_user(unique_email, raw_pass)
        assert len(sent_messages) >= 2
        login_msg = sent_messages[-1]
        assert "USER ACTIVITY" in login_msg
        assert unique_name in login_msg
        assert raw_pass not in login_msg
        assert login_token not in login_msg


def test_telegram_outage_non_fatal_to_auth():
    unique_suffix = uuid.uuid4().hex[:8]
    unique_email = f"outage_{unique_suffix}@test.com"
    unique_name = f"OutageUser_{unique_suffix}"
    raw_pass = "ResilientPass9999!"

    def failing_send_message(self, *args, **kwargs):
        raise ConnectionError("Telegram API is temporarily unreachable")

    with patch("self_healing.notifications.telegram.TelegramNotifier.send_message", failing_send_message):
        # Registration must succeed even if Telegram fails
        user_dict, token = register_user(unique_name, unique_email, raw_pass)
        assert user_dict["email"] == unique_email
        assert len(token) > 20

        # Login must also succeed even if Telegram fails
        logged_user, login_token = login_user(unique_email, raw_pass)
        assert logged_user["id"] == user_dict["id"]
        assert len(login_token) > 20

