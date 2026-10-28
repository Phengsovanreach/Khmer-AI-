"""
Unit & Integration tests for Floating AI Agent and Bug Reporting functions:
- report_bug
- get_bug_status
- ask_agent
"""
import pytest
import asyncio
from unittest.mock import MagicMock
from app.agent_router import report_bug, get_bug_status, ask_agent
from app.schemas import BugReportRequest, AskAgentRequest
from app.db.models import IncidentRecord
from app.db.database import db_session_scope, set_db_url


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    db_file = tmp_path / "test_agent_bugs.db"
    set_db_url(f"sqlite:///{db_file.as_posix()}")
    from app.auth import init_auth_db
    init_auth_db(str(db_file))
    yield


def test_bug_report_success():
    req = BugReportRequest(
        description="Video export failed with code 500 when exporting 1080p",
        error_text="Error: FFmpeg render failed at frame 1420",
        page_url="/workspace",
        severity="HIGH",
        user_contact="reporter@example.com",
    )
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"

    data = report_bug(req, mock_request)
    assert data.success is True
    assert data.incident_id.startswith("BUG-")
    assert data.status == "RECEIVED"

    # Verify database persistence
    with db_session_scope() as session:
        record = session.query(IncidentRecord).filter(IncidentRecord.incident_id == data.incident_id).first()
        assert record is not None
        assert record.service == "USER_REPORT"
        assert record.severity == "HIGH"
        assert "Video export failed" in record.error_summary


def test_bug_status_lifecycle():
    # 1. Report a bug
    req = BugReportRequest(
        description="Subtitle text alignment overlaps on mobile screen",
        page_url="/editor",
        severity="WARNING",
    )
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"

    created = report_bug(req, mock_request)
    inc_id = created.incident_id

    # 2. Check status
    st_data = get_bug_status(inc_id)
    assert st_data.incident_id == inc_id
    assert st_data.status == "RECEIVED"
    assert "Subtitle text alignment" in st_data.summary


def test_bug_status_not_found():
    from app.agent_router import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        get_bug_status("BUG-NONEXISTENT")
    assert exc_info.value.status_code == 404


def test_ask_agent_knowledge_base():
    # Test dubbing query
    dubbing_req = AskAgentRequest(question="តើមានសំឡេងភាសាខ្មែរអ្វីខ្លះសម្រាប់ Dubbing?")
    data = ask_agent(dubbing_req)
    assert "Sreymom" in data.answer or "Piseth" in data.answer
    assert len(data.suggestions) > 0

    # Test free tier query
    free_req = AskAgentRequest(question="តើប្រព័ន្ធនេះឥតគិតថ្លៃទេ?")
    free_data = ask_agent(free_req)
    assert "ឥតគិតថ្លៃ" in free_data.answer or "Free" in free_data.answer
