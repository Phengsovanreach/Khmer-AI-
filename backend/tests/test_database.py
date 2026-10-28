"""
Unit and integration tests for production database engine, models, and connection pooling.
"""
import pytest
from app.db.database import check_db_health, init_db, db_session_scope, SessionLocal
from app.db.models import User, Session as UserSession, AuditLog, IncidentRecord, AIFixRecord
from datetime import datetime, timezone


def test_database_connectivity_and_health():
    health = check_db_health()
    assert health["status"] == "CONNECTED"
    assert health["is_healthy"] is True
    assert health["latency_ms"] >= 0
    assert health["error"] is None


def test_database_tables_initialization():
    init_db()
    with db_session_scope() as session:
        # Verify tables are queryable
        users = session.query(User).all()
        assert isinstance(users, list)
        incidents = session.query(IncidentRecord).all()
        assert isinstance(incidents, list)
        audit = session.query(AuditLog).all()
        assert isinstance(audit, list)


def test_audit_log_persistence():
    now = datetime.now(timezone.utc)
    op_id = f"op_test_{now.timestamp()}"
    with db_session_scope() as session:
        log = AuditLog(
            operation_id=op_id,
            user_id="usr_test123",
            event_type="Video Dubbing",
            status="SUCCESS",
            duration_ms=450.5,
            details_json='{"voices": 2}',
            created_at=now,
        )
        session.add(log)

    session = SessionLocal()
    try:
        found = session.query(AuditLog).filter(AuditLog.operation_id == op_id).first()
        assert found is not None
        assert found.event_type == "Video Dubbing"
        assert found.duration_ms == 450.5
        assert found.get_details() == {"voices": 2}
    finally:
        session.close()
