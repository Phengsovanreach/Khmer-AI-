"""
Unit tests for the three primary notification categories required by the Master Prompt:
  Type 1: Bug Detection and Automatic Fix (Bug Alert & AI Fix Report)
  Type 2: Hourly Website Health Report
  Type 3: User Activity and Operation Results (Privacy-conscious audit tracking)
"""
import pytest
from self_healing.notifications import (
    format_bug_detected_alert,
    format_ai_fix_report,
    format_hourly_health_report,
    format_user_activity_alert,
)


def test_notification_type_1_bug_detected():
    alert = format_bug_detected_alert(
        severity="HIGH",
        incident_id="INC-2026-001",
        component="Video Dubbing API",
        issue="Dubbing request failed.",
        error="RuntimeError in the media processing pipeline.",
        impact="Some users cannot generate dubbed videos.",
        ai_root_cause="The media-processing path is not initialized in one execution branch.",
        action="Analyzing the relevant code and reproducing the failure.",
    )
    assert "BUG DETECTED" in alert
    assert "INC-2026-001" in alert
    assert "Video Dubbing API" in alert
    assert "RuntimeError" in alert
    assert "HIGH" in alert


def test_notification_type_1_ai_fix_report():
    report = format_ai_fix_report(
        incident_id="INC-2026-001",
        root_cause="Verified media-processing initialization bug",
        code_changed="backend/app/dubbing.py",
        fix_applied="Added guard and initialized path before synthesis",
        tests_passed=True,
        deployment_status="SUCCESS",
        health_verified=True,
        rollback_occurred=False,
        result_summary="Verified and healthy in production.",
    )
    assert "AI FIX REPORT" in report
    assert "INC-2026-001" in report
    assert "PASS" in report
    assert "SUCCESS" in report
    assert "<b>Rollback:</b> NO" in report


def test_notification_type_2_hourly_health_report():
    hourly = format_hourly_health_report(
        website_url="https://khmer-ai-16c.pages.dev",
        frontend_online=True,
        backend_online=True,
        database_connected=True,
        auth_pass=True,
        core_api_pass=True,
        video_processing_status="HEALTHY",
        ai_provider_status="AVAILABLE",
        response_time_ms=135.2,
        error_rate_pct=0.0,
        active_users=5,
        background_worker_status="RUNNING",
        latest_deployment_status="LIVE",
        open_incidents_count=0,
        overall_status="HEALTHY",
        ai_analysis_text="All microservices and database query pools are operating within normal parameters.",
    )
    assert "HOURLY HEALTH REPORT" in hourly
    assert "<b>Frontend:</b> ONLINE" in hourly
    assert "<b>Backend:</b> ONLINE" in hourly
    assert "<b>Database:</b> CONNECTED" in hourly
    assert "<b>Authentication:</b> PASS" in hourly
    assert "<b>Video Processing:</b> HEALTHY" in hourly
    assert "<b>AI Provider:</b> AVAILABLE" in hourly
    assert "135.2 ms" in hourly
    assert "HEALTHY" in hourly



def test_notification_type_3_user_activity_success():
    activity = format_user_activity_alert(
        event="Video Translation",
        user_id="usr_98a72b14c0ef",
        operation_id="op_7f21a88c",
        status="SUCCESS",
        duration_sec=2.15,
        result_summary="The requested operation completed successfully.",
    )
    assert "USER ACTIVITY" in activity
    assert "Video Translation" in activity
    assert "usr_98a72b14c0ef" in activity
    assert "op_7f21a88c" in activity
    assert "SUCCESS" in activity
    assert "2.15s" in activity


def test_notification_type_3_operation_failed():
    failed = format_user_activity_alert(
        event="Video Dubbing",
        user_id="usr_98a72b14c0ef",
        operation_id="op_7f21a88d",
        status="FAILED",
        error_category="Network Timeout",
        ai_action="Investigation initiated by telemetry worker.",
    )
    assert "OPERATION FAILED" in failed
    assert "Video Dubbing" in failed
    assert "Network Timeout" in failed
    assert "FAILED" in failed
