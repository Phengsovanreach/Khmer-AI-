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
from .ai.hourly_inspector import HourlyAIInspector
from .config import Config, redact_secrets
from .diagnostics import DiagnosticCollector
from .models import EventCategory, IncidentStatus, Severity
from .monitors import check_backend_health, check_frontend_health
from .notifications import (
    TelegramNotifier,
    format_ci_report,
    format_heartbeat_report,
    format_hourly_ai_report,
    format_recovery_alert,
    format_telegram_alert,
)
from .repair import PullRequestCreator, RepairWorker
from .state import IncidentTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("self_healing.cli")


def run_hourly_ai_report(fe_latency_ms: float = 0.0, be_latency_ms: float = 0.0) -> dict[str, Any]:
    """
    Executes deep telemetry inspection of live backend capabilities and dubbing models,
    generates structured insights using Gemini AI, and dispatches an hourly report to Telegram.
    """
    notifier = TelegramNotifier()
    inspector = HourlyAIInspector()

    logger.info("Gathering live telemetry from backend engines...")
    telemetry = inspector.collect_live_telemetry()

    logger.info("Querying Gemini AI for hourly intelligence assessment...")
    ai_insights = inspector.analyze_with_ai(telemetry, fe_latency_ms=fe_latency_ms, be_latency_ms=be_latency_ms)

    report_msg = format_hourly_ai_report(
        telemetry=telemetry,
        ai_insights=ai_insights,
        fe_latency_ms=fe_latency_ms,
        be_latency_ms=be_latency_ms,
    )

    logger.info("Dispatching Hourly AI Intelligence Report to Telegram...")
    res = notifier.send_message(report_msg)
    return res


def run_health_checks(notify_always: Optional[bool] = None, force_hourly: bool = False) -> int:
    """
    Executes full cloud synthetic health checks against frontend and backend.
    Updates incident state, triggers Telegram alerts, and initiates diagnosis on confirmed outages.
    If notify_always is True (or Config.ALWAYS_NOTIFY is True):
      - Dispatches Type 2 (Hourly AI Inspection Report) if 1 hour has elapsed (or force_hourly=True).
      - Dispatches Type 1 (Routine Health Heartbeat Report) for routine interim checks.
    Returns: 0 if all services healthy/recovering, 1 if confirmed failure detected.
    """
    tracker = IncidentTracker()
    notifier = TelegramNotifier()
    analyzer = FailureAnalyzer()

    should_always_notify = Config.ALWAYS_NOTIFY if notify_always is None else notify_always

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
    has_alert_dispatched = False

    # Process results through state tracker
    for res in (fe_res, be_res):
        incident, notify_event = tracker.process_check_result(res)

        if notify_event == "CONFIRMED_FAILURE" and incident:
            has_confirmed_failure = True
            has_alert_dispatched = True
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
            has_alert_dispatched = True
            logger.info("SERVICE RECOVERED: Incident %s on %s resolved", incident.incident_id, incident.service.value)
            rec_msg = format_recovery_alert(incident)
            notifier.send_message(rec_msg)

    # If all services are healthy and notification is requested:
    if not has_alert_dispatched and should_always_notify:
        active_count = len(tracker._state.get("active_incidents", {}))

        # Check if 1 hour has elapsed or if explicitly requested to send hourly AI inspection
        if force_hourly or tracker.should_run_hourly_report():
            logger.info("Hourly window reached (every 1 hour). Dispatching Hourly AI Inspection Report...")
            run_hourly_ai_report(fe_latency_ms=fe_res.latency_ms, be_latency_ms=be_res.latency_ms)
            tracker.record_hourly_report_run()
        else:
            # Routine 30-min heartbeat report
            heartbeat_msg = format_heartbeat_report(fe_res, be_res, active_count=active_count)
            logger.info("Dispatching routine healthy heartbeat report to Telegram...")
            notifier.send_message(heartbeat_msg)

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


def send_ci_notification(status: str, branch: str, commit_sha: str, commit_msg: str, details_json: Optional[str] = None) -> None:
    """Sends CI test pipeline status report to Telegram."""
    notifier = TelegramNotifier()
    details = {}
    if details_json:
        try:
            details = json.loads(details_json)
        except Exception:
            pass

    msg = format_ci_report(
        status=status,
        branch=branch,
        commit_sha=commit_sha,
        commit_msg=commit_msg,
        details=details if details else None,
    )
    res = notifier.send_message(msg)
    logger.info("CI Notification dispatched: %s", res)


def main() -> None:
    parser = argparse.ArgumentParser(description="Khmer Translator AI Self-Healing System CLI")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Run health probes and process state machine")
    check_parser.add_argument("--always-notify", action="store_true", help="Send Telegram status report even if all services are healthy")
    check_parser.add_argument("--hourly", action="store_true", help="Force dispatch of the Hourly AI Deep Telemetry Report")

    subparsers.add_parser("hourly-ai-report", help="Force immediate generation and dispatch of Hourly AI Inspection Report")
    status_parser = subparsers.add_parser("status", help="Print active incidents and health status")
    test_notify_parser = subparsers.add_parser("test-notify", help="Test Telegram alert formatting")

    ci_parser = subparsers.add_parser("ci-notify", help="Send CI pipeline execution notification")
    ci_parser.add_argument("--status", required=True, choices=["SUCCESS", "FAILURE"], help="CI build status")
    ci_parser.add_argument("--branch", required=True, help="Git branch name")
    ci_parser.add_argument("--commit", required=True, help="Commit SHA")
    ci_parser.add_argument("--message", default="", help="Commit message")
    ci_parser.add_argument("--details", default="", help="JSON string with details")

    args = parser.parse_args()

    if args.command in (None, "check"):
        always_flag = getattr(args, "always_notify", False)
        hourly_flag = getattr(args, "hourly", False)
        exit_code = run_health_checks(
            notify_always=always_flag if always_flag else None,
            force_hourly=hourly_flag,
        )
        sys.exit(exit_code)
    elif args.command == "hourly-ai-report":
        res = run_hourly_ai_report()
        print(f"Hourly AI Report Result: {res}")
    elif args.command == "status":
        print_status()
    elif args.command == "ci-notify":
        send_ci_notification(
            status=args.status,
            branch=args.branch,
            commit_sha=args.commit,
            commit_msg=args.message,
            details_json=args.details,
        )
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
