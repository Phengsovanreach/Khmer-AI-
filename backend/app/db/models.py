"""
Khmer Translator AI — Production SQLAlchemy Database Models.
Defines persistent relational schemas for Users, Sessions, Audit Logs, Incidents, and AI Fix History.
Compatible with PostgreSQL (production) and SQLite (local dev).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", server_default="user", nullable=True)
    status = Column(String(20), default="active", server_default="active", nullable=False)
    email_verified = Column(Boolean, default=True, server_default="1", nullable=False)
    avatar_color = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "email_verified": self.email_verified,
            "avatar_color": self.avatar_color,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }


class Session(Base):
    __tablename__ = "sessions"

    token = Column(String(128), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    user = relationship("User", back_populates="sessions")

    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    event_type = Column(String(50), index=True, nullable=False)
    status = Column(String(20), nullable=False)  # SUCCESS, FAILED
    duration_ms = Column(Float, default=0.0, nullable=False)
    details_json = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)

    user = relationship("User", back_populates="audit_logs")

    def get_details(self) -> dict[str, Any]:
        if not self.details_json:
            return {}
        try:
            return json.loads(self.details_json)
        except Exception:
            return {"raw": self.details_json}


class IncidentRecord(Base):
    __tablename__ = "incidents"

    incident_id = Column(String(64), primary_key=True, index=True)
    service = Column(String(30), nullable=False)  # FRONTEND, BACKEND, CI
    status = Column(String(30), nullable=False)
    severity = Column(String(20), default="WARNING", nullable=False)
    consecutive_failures = Column(Integer, default=1, nullable=False)
    error_summary = Column(Text, nullable=False)
    first_detected_utc = Column(DateTime(timezone=True), nullable=False)
    last_detected_utc = Column(DateTime(timezone=True), nullable=False)
    diagnostics_json = Column(Text, nullable=True)
    repair_attempts = Column(Integer, default=0, nullable=False)
    pull_request_url = Column(String(255), nullable=True)
    recovery_confirmations = Column(Integer, default=0, nullable=False)
    notified_states = Column(Text, nullable=True)

    fixes = relationship("AIFixRecord", back_populates="incident", cascade="all, delete-orphan")


class AIFixRecord(Base):
    __tablename__ = "ai_fix_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(64), ForeignKey("incidents.incident_id", ondelete="CASCADE"), index=True, nullable=False)
    root_cause = Column(Text, nullable=False)
    target_files = Column(Text, nullable=False)
    diff_content = Column(Text, nullable=False)
    tests_passed = Column(Boolean, default=False, nullable=False)
    test_results = Column(Text, nullable=True)
    deployment_status = Column(String(50), default="NOT_DEPLOYED", nullable=False)
    health_verified = Column(Boolean, default=False, nullable=False)
    rollback_occurred = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("IncidentRecord", back_populates="fixes")
