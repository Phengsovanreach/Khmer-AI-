"""
Tests for Controlled Repair Worker, Safety Boundaries, and PR Creator.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

from self_healing.config import Config
from self_healing.models import DiagnosticReport, Incident, IncidentStatus, RepairProposal, ServiceType
from self_healing.repair.worker import RepairWorker
from self_healing.repair.pr_creator import PullRequestCreator


def test_repair_rejects_forbidden_paths(tmp_path: Path):
    worker = RepairWorker(repo_dir=tmp_path)
    inc = Incident(
        incident_id="INC-BE-001",
        service=ServiceType.BACKEND,
        status=IncidentStatus.CONFIRMED_FAILURE,
        consecutive_failures=2,
        first_detected_utc="2026-10-28T00:00:00Z",
        last_detected_utc="2026-10-28T00:02:00Z",
        first_detected_cambodia="2026-10-28 07:00:00 ICT",
        last_detected_cambodia="2026-10-28 07:02:00 ICT",
        error_summary="Failure",
    )
    diag = DiagnosticReport(
        incident_id="INC-BE-001",
        detected_at_utc="2026-10-28T00:00:00Z",
        detected_at_cambodia="2026-10-28 07:00:00 ICT",
        affected_component="BACKEND",
        failure_category="CONFIG",
        evidence="Error",
        probable_root_cause="Bad workflow",
        confidence=0.8,
        proposed_fix="Disable checks",
        tests_required=[],
        safety_risks=[],
    )

    # Attempting to edit a GitHub workflow file must be rejected!
    ok, proposal, msg = worker.execute_repair_proposal(
        incident=inc,
        diagnosis=diag,
        target_file_rel=".github/workflows/ci.yml",
        proposed_code="broken",
    )
    assert ok is False
    assert proposal is None
    assert "Security violation" in msg


def test_repair_rejects_after_max_attempts(tmp_path: Path):
    worker = RepairWorker(repo_dir=tmp_path)
    inc = Incident(
        incident_id="INC-BE-002",
        service=ServiceType.BACKEND,
        status=IncidentStatus.CONFIRMED_FAILURE,
        consecutive_failures=4,
        first_detected_utc="2026-10-28T00:00:00Z",
        last_detected_utc="2026-10-28T00:02:00Z",
        first_detected_cambodia="2026-10-28 07:00:00 ICT",
        last_detected_cambodia="2026-10-28 07:02:00 ICT",
        error_summary="Failure",
        repair_attempts=Config.MAX_REPAIR_ATTEMPTS,  # Max reached!
    )
    diag = MagicMock()

    ok, proposal, msg = worker.execute_repair_proposal(
        incident=inc,
        diagnosis=diag,
        target_file_rel="backend/app/main.py",
        proposed_code="pass",
    )
    assert ok is False
    assert "Max repair attempts" in msg


def test_repair_lock_prevents_concurrency(tmp_path: Path):
    worker1 = RepairWorker(repo_dir=tmp_path)
    worker2 = RepairWorker(repo_dir=tmp_path)

    assert worker1.acquire_lock() is True
    # Second worker cannot acquire lock while worker1 holds it
    assert worker2.acquire_lock() is False
    worker1.release_lock()
    assert worker2.acquire_lock() is True
    worker2.release_lock()


def test_pr_creator_unconfigured_token():
    creator = PullRequestCreator(token=None, repository="Phengsovanreach/Khmer-AI-")
    prop = RepairProposal(
        incident_id="INC-TEST-001",
        branch_name="ai-repair/inc-test-001-fix",
        target_files=["backend/app/main.py"],
        diff_content="+ # fix",
        validation_commands=["pytest"],
        pr_title="Fix title",
        pr_body="Fix body",
    )

    with patch("subprocess.run") as mock_push:
        mock_push.return_value = MagicMock(returncode=0)
        url = creator.create_pull_request(prop)
        assert url is not None
        assert "pull/new/ai-repair/inc-test-001-fix" in url
