"""
Tests for Incident State Machine, Deduplication, and Recovery Verification.
"""
from pathlib import Path
from self_healing.models import CheckResult, IncidentStatus, ServiceType
from self_healing.state.tracker import IncidentTracker


def test_incident_state_machine_and_deduplication(tmp_path: Path):
    state_file = tmp_path / "test_state.json"
    tracker = IncidentTracker(state_file=state_file)

    # 1. First failure -> SUSPECTED_FAILURE (no notification)
    fail_res = CheckResult(
        service=ServiceType.BACKEND,
        url="https://api.example.com",
        is_healthy=False,
        status_code=502,
        latency_ms=120.0,
        error_message="HTTP 502 Bad Gateway",
    )
    inc, notify = tracker.process_check_result(fail_res)
    assert inc is not None
    assert inc.status == IncidentStatus.SUSPECTED_FAILURE
    assert notify is None  # Suppress single transient fail

    # 2. Second failure -> CONFIRMED_FAILURE (notify triggered)
    inc, notify = tracker.process_check_result(fail_res)
    assert inc is not None
    assert inc.status == IncidentStatus.CONFIRMED_FAILURE
    assert notify == "CONFIRMED_FAILURE"

    # 3. Third failure -> Remains CONFIRMED_FAILURE (deduplicated, NO second notification!)
    inc, notify = tracker.process_check_result(fail_res)
    assert inc is not None
    assert inc.status == IncidentStatus.CONFIRMED_FAILURE
    assert notify is None  # Deduplicated!

    # 4. First success -> RECOVERY_VERIFICATION (not yet confirmed recovered)
    ok_res = CheckResult(
        service=ServiceType.BACKEND,
        url="https://api.example.com",
        is_healthy=True,
        status_code=200,
        latency_ms=95.0,
    )
    inc, notify = tracker.process_check_result(ok_res)
    assert inc is not None
    assert inc.status == IncidentStatus.RECOVERY_VERIFICATION
    assert notify is None  # Wait for 2nd confirmation

    # 5. Second success -> RECOVERED (triggers recovery alert!)
    inc, notify = tracker.process_check_result(ok_res)
    assert inc is not None
    assert inc.status == IncidentStatus.RECOVERED
    assert notify == "RECOVERED"

    # Active incident is closed
    assert tracker.get_active_incident(ServiceType.BACKEND) is None

    # Incident archived in history
    assert len(tracker._state["history"]) == 1
    assert tracker._state["history"][0]["incident_id"] == inc.incident_id
