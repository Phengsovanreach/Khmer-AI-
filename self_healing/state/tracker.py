"""
Khmer Translator AI — Incident State Machine & Deduplication Tracker.
Persists incident state across cloud worker runs and prevents notification spam.
"""
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..config import Config
from ..models import CheckResult, Incident, IncidentStatus, ServiceType, format_cambodia_time

logger = logging.getLogger(__name__)
_TRACKER_LOCK = threading.Lock()


class IncidentTracker:
    def __init__(self, state_file: Optional[Path] = None):
        self.state_file = state_file or Config.STATE_FILE
        self._state: dict[str, Any] = {"active_incidents": {}, "history": []}
        self.load()

    def load(self) -> None:
        """Loads incident state from disk atomically."""
        with _TRACKER_LOCK:
            if not self.state_file.exists():
                return
            try:
                raw = self.state_file.read_text(encoding="utf-8")
                data = json.loads(raw)
                if isinstance(data, dict):
                    self._state = data
            except Exception as exc:
                logger.warning("Could not read incident state file: %s", exc)

    def save(self) -> None:
        """Writes incident state to disk atomically using temporary file replacement."""
        with _TRACKER_LOCK:
            try:
                self.state_file.parent.mkdir(parents=True, exist_ok=True)
                temp_file = self.state_file.with_suffix(".tmp")
                temp_file.write_text(json.dumps(self._state, indent=2), encoding="utf-8")
                temp_file.replace(self.state_file)
            except Exception as exc:
                logger.error("Failed to persist incident state: %s", exc)

    def get_active_incident(self, service: ServiceType) -> Optional[Incident]:
        """Returns the active incident for a service if one exists."""
        raw = self._state.get("active_incidents", {}).get(service.value)
        if raw:
            try:
                return Incident.from_dict(raw)
            except Exception:
                return None
        return None

    def process_check_result(self, result: CheckResult) -> tuple[Optional[Incident], Optional[str]]:
        """
        Processes a health check result through the state machine.
        Returns: (incident, event_to_notify_or_None)
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        now_kh = format_cambodia_time()
        active = self.get_active_incident(result.service)

        if not result.is_healthy:
            # FAILURE PATH
            if active is None:
                # New suspected failure
                new_id = f"INC-{result.service.value[:3]}-{uuid.uuid4().hex[:6].upper()}"
                active = Incident(
                    incident_id=new_id,
                    service=result.service,
                    status=IncidentStatus.SUSPECTED_FAILURE,
                    consecutive_failures=1,
                    first_detected_utc=now_utc,
                    last_detected_utc=now_utc,
                    first_detected_cambodia=now_kh,
                    last_detected_cambodia=now_kh,
                    error_summary=result.error_message or "Health check returned unhealthy",
                    diagnostics=[{"timestamp": now_utc, "error": result.error_message, "details": result.details}],
                )
                self._state.setdefault("active_incidents", {})[result.service.value] = active.to_dict()
                self.save()
                return active, None  # Do not notify on 1st transient failure

            else:
                # Continuing failure
                active.consecutive_failures += 1
                active.last_detected_utc = now_utc
                active.last_detected_cambodia = now_kh
                active.recovery_confirmations = 0
                active.diagnostics.append({"timestamp": now_utc, "error": result.error_message, "details": result.details})
                if len(active.diagnostics) > 20:
                    active.diagnostics = active.diagnostics[-20:]

                # Transition to CONFIRMED_FAILURE once confirmation threshold is reached
                if (
                    active.status == IncidentStatus.SUSPECTED_FAILURE
                    and active.consecutive_failures >= Config.CONFIRMATION_THRESHOLD
                ):
                    active.status = IncidentStatus.CONFIRMED_FAILURE
                    self._state["active_incidents"][result.service.value] = active.to_dict()
                    self.save()
                    if "CONFIRMED_FAILURE" not in active.notified_states:
                        active.notified_states.append("CONFIRMED_FAILURE")
                        self._state["active_incidents"][result.service.value] = active.to_dict()
                        self.save()
                        return active, "CONFIRMED_FAILURE"

                self._state["active_incidents"][result.service.value] = active.to_dict()
                self.save()
                return active, None

        else:
            # HEALTHY PATH
            if active is None:
                return None, None

            # There was an active incident, now service is responding healthy
            active.recovery_confirmations += 1
            if active.status in (IncidentStatus.CONFIRMED_FAILURE, IncidentStatus.AWAITING_HUMAN_REVIEW, IncidentStatus.PULL_REQUEST_CREATED):
                active.status = IncidentStatus.RECOVERY_VERIFICATION

            # Verify consecutive recovery checks before closing incident
            if active.recovery_confirmations >= Config.RECOVERY_THRESHOLD:
                active.status = IncidentStatus.RECOVERED
                # Archive to history
                self._state.setdefault("history", []).append(active.to_dict())
                if len(self._state["history"]) > 50:
                    self._state["history"] = self._state["history"][-50:]
                del self._state["active_incidents"][result.service.value]
                self.save()

                if "RECOVERED" not in active.notified_states:
                    active.notified_states.append("RECOVERED")
                    return active, "RECOVERED"
                return active, None

            self._state["active_incidents"][result.service.value] = active.to_dict()
            self.save()
            return active, None

    def update_incident_status(self, incident: Incident, new_status: IncidentStatus, extra: Optional[dict] = None) -> None:
        """Updates incident status and persists changes."""
        incident.status = new_status
        if extra:
            if "pull_request_url" in extra:
                incident.pull_request_url = extra["pull_request_url"]
            if "repair_attempts" in extra:
                incident.repair_attempts = extra["repair_attempts"]
        self._state.setdefault("active_incidents", {})[incident.service.value] = incident.to_dict()
        self.save()

    def should_run_hourly_report(self, interval_seconds: int = 3600) -> bool:
        """Determines if 1 hour has elapsed since the last hourly AI inspection report."""
        last_str = self._state.get("last_hourly_ai_report_utc")
        if not last_str:
            return True
        try:
            last_dt = datetime.fromisoformat(last_str)
            now_dt = datetime.now(timezone.utc)
            return (now_dt - last_dt).total_seconds() >= interval_seconds
        except Exception:
            return True

    def record_hourly_report_run(self) -> None:
        """Records the timestamp of the hourly AI inspection report."""
        self._state["last_hourly_ai_report_utc"] = datetime.now(timezone.utc).isoformat()
        self.save()
