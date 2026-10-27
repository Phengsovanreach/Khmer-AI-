"""
Khmer Translator AI — Self-Healing System Data Models
Defines core data structures for incidents, health checks, diagnostic reports, and repair proposals.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional


class ServiceType(str, Enum):
    FRONTEND = "FRONTEND"
    BACKEND = "BACKEND"
    CI = "CI"


class IncidentStatus(str, Enum):
    HEALTHY = "HEALTHY"
    SUSPECTED_FAILURE = "SUSPECTED_FAILURE"
    CONFIRMED_FAILURE = "CONFIRMED_FAILURE"
    DIAGNOSING = "DIAGNOSING"
    REPAIR_PROPOSED = "REPAIR_PROPOSED"
    TESTING_REPAIR = "TESTING_REPAIR"
    PULL_REQUEST_CREATED = "PULL_REQUEST_CREATED"
    AWAITING_HUMAN_REVIEW = "AWAITING_HUMAN_REVIEW"
    RECOVERY_VERIFICATION = "RECOVERY_VERIFICATION"
    RECOVERED = "RECOVERED"
    NEEDS_MANUAL_INTERVENTION = "NEEDS_MANUAL_INTERVENTION"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class EventCategory(str, Enum):
    FRONTEND_OUTAGE = "FRONTEND"
    BACKEND_OUTAGE = "BACKEND"
    RECOVERY_VERIFIED = "RECOVERY"
    CI_FAILURE = "CI"
    AI_DIAGNOSIS_COMPLETED = "AI REPAIR"
    REPAIR_PROPOSED = "AI REPAIR"
    REPAIR_TESTS_FAILED = "AI REPAIR"
    PULL_REQUEST_CREATED = "AI REPAIR"
    MONITORING_ERROR = "MONITORING"
    SAFETY_LIMIT_REACHED = "SAFETY"


def get_cambodia_time(utc_dt: Optional[datetime] = None) -> datetime:
    """Converts a UTC datetime (or current time) to Cambodia Local Time (Asia/Phnom_Penh, UTC+7)."""
    cambodia_tz = timezone(timedelta(hours=7))
    if utc_dt is None:
        return datetime.now(cambodia_tz)
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(cambodia_tz)


def format_cambodia_time(utc_dt: Optional[datetime] = None) -> str:
    """Formats datetime as Cambodia Local Time string: YYYY-MM-DD HH:MM:SS (UTC+7 Phnom Penh)."""
    kh_time = get_cambodia_time(utc_dt)
    return kh_time.strftime("%Y-%m-%d %H:%M:%S ICT (UTC+7)")


@dataclass
class CheckResult:
    service: ServiceType
    url: str
    is_healthy: bool
    status_code: Optional[int]
    latency_ms: float
    error_message: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    timestamp_cambodia: str = field(default_factory=lambda: format_cambodia_time())


@dataclass
class DiagnosticReport:
    incident_id: str
    detected_at_utc: str
    detected_at_cambodia: str
    affected_component: str
    failure_category: str
    evidence: str
    probable_root_cause: str
    confidence: float  # 0.0 to 1.0
    proposed_fix: str
    tests_required: list[str]
    safety_risks: list[str]
    status: str = "COMPLETED"


@dataclass
class RepairProposal:
    incident_id: str
    branch_name: str
    target_files: list[str]
    diff_content: str
    validation_commands: list[str]
    pr_title: str
    pr_body: str
    tests_passed: bool = False
    pull_request_url: Optional[str] = None


@dataclass
class Incident:
    incident_id: str
    service: ServiceType
    status: IncidentStatus
    consecutive_failures: int
    first_detected_utc: str
    last_detected_utc: str
    first_detected_cambodia: str
    last_detected_cambodia: str
    error_summary: str
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    repair_attempts: int = 0
    pull_request_url: Optional[str] = None
    recovery_confirmations: int = 0
    notified_states: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["service"] = self.service.value
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Incident:
        d = dict(data)
        d["service"] = ServiceType(d["service"])
        d["status"] = IncidentStatus(d["status"])
        return cls(**d)
