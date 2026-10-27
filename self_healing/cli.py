"""
Khmer Translator AI — Autonomous Self-Healing CLI.
Command-line orchestrator for synthetic health monitoring, automated diagnosis, repair, and alerts.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Optional

from .ai import FailureAnalyzer
from .config import Config, redact_secrets
from .diagnostics import DiagnosticCollector
from .models import EventCategory, IncidentStatus, Severity
from .monitors import check_backend_health, check_frontend_health
from .notifications import TelegramNotifier, format_recovery_alert, format_telegram_alert
from .repair import PullRequestCreator, RepairWorker
from .state import IncidentTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("self_healing.cli")


def run_health_checks(auto_diagnose: bool = True) -> int:
    """
    Executes full cloud synthetic health checks against frontend and backend.
    Updates incident state, triggers Telegram alerts, and initiates diagnosis on confirmed outages.
    Returns: 0 if all services healthy/recovering, 1 if confirmed failure detected.
    """
    tracker = IncidentTracker()
    notifier = TelegramNotifier()
    analyzer = FailureAnalyzer()

    logger.info("Executing cloud synthetic probes...")
    logger.info("Target Frontend: %s", Config.FRONTEND_URL)
    logger.info("Target Backend Health: %s", Config.BACKEND_HEALTH_URL)

    # 1. Probe Frontend
    fe_res = check_frontend_health()
    logger.info("Frontend Check: %s (Status: %s, Latency: %.1fms)", "OK" if fe_res.is_healthy else "FAIL", fe_res.status_code, fe_res.latency_ms)

    # 2. Probe Backend
    be_res = check_backend_health()
    logger.info("Backend Check:  %s (Status: %s, Latency: %.1fms)", "OK" if be_res.is_healthy else "FAIL", be_res.status_code, be_res.latency_ms)

    has_confirmed_failure = False

    # Process results through state tracker
    for res in (fe_res, be_res):
        incident, notify_event = tracker.process_check_result(res)

        if notify_event == "CONFIRMED_FAILURE" and incident:
            has_confirmed_failure = True
            logger.warning("CONFIRMED OUTAGE: Incident %s on %s", incident.incident_id, incident.service.value)

            # Collect diagnostic evidence
            evidence = DiagnosticCollector.collect_incident_evidence(incident, latest_result=res)

            # Perform AI diagnosis if enabled
            diagnosis = analyzer.diagnose_incident(incident, evidence)

            # Send Telegram Alert
            alert_msg = format_telegram_alert(
                event=EventCategory.FRONTEND_OUTAGE if incident.service.value == "FRONTEND" else EventCategory.BACKEND_OUTAGE,
                severity=Severity.CRITICAL,
                affected_service=incident.service.value,
                incident_id=incident.incident_id,
                problem=incident.error_summary,
                evidence=str(evidence.get("raw_error", "No details")),
                root_cause=diagnosis.probable_root_cause,
                action_taken="Confirmed after repeated failures; AI diagnosis generated.",
                test_results="Synthetics failed",
                next_action="Review incident details or run automated repair",
            )
            notifier.send_message(alert_msg)

        elif notify_event == "RECOVERED" and incident:
            logger.info("SERVICE RECOVERED: Incident %s on %s resolved", incident.incident_id, incident.service.value)
            rec_msg = format_recovery_alert(incident)
            notifier.send_message(rec_msg)

    return 1 if has_confirmed_failure else 0


def print_status() -> None:
    """Displays active incidents and service health history."""
    tracker = IncidentTracker()
    print("\n=== KHMER TRANSLATOR AI — SELF-HEALING STATUS ===")
    active_incidents = tracker._state.get("active_incidents", {})
    if not active_incidents:
        print("✅ Status: ALL SERVICES HEALTHY (No active incidents)")
    else:
        print(f"⚠️ Active Incidents: {len(active_incidents)}")
        for svc, inc in active_incidents.items():
            print(f"  - [{svc}] ID: {inc.get('incident_id')} | Status: {inc.get('status')} | Failures: {inc.get('consecutive_failures')}")
            print(f"    Summary: {inc.get('error_summary')}")
            print(f"    Detected: {inc.get('first_detected_cambodia')}")

    history = tracker._state.get("history", [])
    print(f"\nResolved Incidents in History: {len(history)}")
    print("=================================================\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Khmer Translator AI Self-Healing System CLI")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Run health probes and process state machine")
    status_parser = subparsers.add_parser("status", help="Print active incidents and health status")
    test_notify_parser = subparsers.add_parser("test-notify", help="Test Telegram alert formatting")

    args = parser.parse_args()

    if args.command in (None, "check"):
        exit_code = run_health_checks()
        sys.exit(exit_code)
    elif args.command == "status":
        print_status()
    elif args.command == "test-notify":
        notifier = TelegramNotifier()
        sample_msg = format_telegram_alert(
            event=EventCategory.FRONTEND_OUTAGE,
            severity=Severity.WARNING,
            affected_service="FRONTEND",
            incident_id="TEST-INC-001",
            problem="Synthetic test failure simulation",
            evidence="HTTP 500 Internal Server Error returned by mock test",
            root_cause="Test simulation verification",
            action_taken="Sent test notification probe",
            test_results="Passed verification",
            next_action="Verify receipt in designated channel",
        )
        print("Sample Telegram Alert Output:")
        print("--------------------------------------------------")
        print(sample_msg)
        print("--------------------------------------------------")
        res = notifier.send_message(sample_msg)
        print(f"Notification Result: {res}")


if __name__ == "__main__":
    main()
