"""
Unit tests for the three primary notification categories required by the Master Prompt:
  Type 1: Bug Detection and Automatic Fix (Bug Alert & AI Fix Report)
  Type 2: Hourly Website Health Report
  Type 3: User Activity and Operation Results (Privacy-conscious audit tracking)
Verifies polished Khmer typography, mobile readability, and secret redaction.
"""
import pytest
from self_healing.notifications import (
    format_bug_detected_alert,
    format_ai_fix_report,
    format_hourly_health_report,
    format_user_activity_alert,
    format_recovery_alert,
    format_ci_report,
    format_hourly_ai_report,
)
from self_healing.models import Incident, ServiceType, IncidentStatus


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
    assert "រកឃើញបញ្ហាប្រព័ន្ធ" in alert
    assert "INC-2026-001" in alert
    assert "Video Dubbing API" in alert
    assert "RuntimeError" in alert
    assert "HIGH" in alert
    assert "កម្រិតធ្ងន់ធ្ងរ" in alert
    assert "ផ្នែករងផលប៉ះពាល់" in alert


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
    assert "របាយការណ៍ជួសជុលកូដស្វ័យប្រវត្តិ" in report
    assert "INC-2026-001" in report
    assert "PASS" in report
    assert "SUCCESS" in report
    assert "Rollback" in report
    assert "គ្មាន (NO)" in report
    assert "កូដដែលបានកែសម្រួល" in report
    assert "ការតេស្តកូដ" in report


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
    assert "របាយការណ៍សុខភាពប្រព័ន្ធប្រចាំម៉ោង" in hourly
    assert "Frontend" in hourly
    assert "ONLINE" in hourly
    assert "ដំណើរការប្រក្រតី (ONLINE)" in hourly
    assert "Backend" in hourly
    assert "Database" in hourly
    assert "មូលដ្ឋានទិន្នន័យ (Database)" in hourly
    assert "បានតភ្ជាប់ (CONNECTED)" in hourly
    assert "ការផ្ទៀងផ្ទាត់គណនី (Authentication)" in hourly
    assert "ត្រឹមត្រូវ (PASS)" in hourly
    assert "Video Processing" in hourly
    assert "AI Provider" in hourly
    assert "135.2 ms" in hourly
    assert "HEALTHY" in hourly
    assert "ល្អប្រសើរប្រក្រតី (HEALTHY)" in hourly


def test_notification_type_3_user_activity_success():
    activity = format_user_activity_alert(
        event="Video Translation",
        user_id="usr_98a72b14c0ef",
        operation_id="op_7f21a88c",
        status="SUCCESS",
        duration_sec=2.15,
        result_summary="The requested operation completed successfully.",
        username="reach_dev",
        masked_email="r***h@gmail.com",
        environment="production",
    )
    assert "USER ACTIVITY" in activity
    assert "សកម្មភាពអ្នកប្រើប្រាស់" in activity
    assert "Video Translation" in activity
    assert "បកប្រែវីដេអូ" in activity
    assert "usr_98a72b14c0ef" in activity
    assert "op_7f21a88c" in activity
    assert "SUCCESS" in activity
    assert "ជោគជ័យ (SUCCESS)" in activity
    assert "2.15s" in activity
    assert "reach_dev" in activity
    assert "r***h@gmail.com" in activity
    assert "Production" in activity


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
    assert "ប្រតិបត្តិការមិនជោគជ័យ" in failed
    assert "Video Dubbing" in failed
    assert "Network Timeout" in failed
    assert "ដាច់ការតភ្ជាប់បណ្តាញ" in failed
    assert "FAILED" in failed
    assert "បរាជ័យ (FAILED)" in failed


def test_notification_no_secrets_leaked():
    """Verify that credentials, passwords, and tokens are never leaked in formatted alerts."""
    secret_pass = "MySecretPass!2026"
    argon_hash = "$argon2id$v=19$m=65536,t=3,p=4$somehashstringhere"
    bot_token = "9125016671:AAEvM_UP5tYvFuBLQfryX_aY6_dzgL9GIII"

    alert = format_user_activity_alert(
        event="User Registration",
        user_id="usr_abc123",
        operation_id="op_reg999",
        status="SUCCESS",
        username="sreang_ai",
        masked_email="s***g@example.com",
        result_summary=f"Created account with token {bot_token} and hash {argon_hash}",
    )
    assert secret_pass not in alert
    assert bot_token not in alert
    assert "[REDACTED_CREDENTIAL]" in alert
    assert "ចុះឈ្មោះគណនីថ្មី (User Registration)" in alert
    assert "sreang_ai" in alert
    assert "s***g@example.com" in alert


def test_recovery_and_ci_notifications_khmer():
    """Verify recovery and CI alert formatters support polished Khmer typography."""
    inc = Incident(
        incident_id="INC-REC-101",
        service=ServiceType.FRONTEND,
        status=IncidentStatus.RECOVERED,
        consecutive_failures=0,
        first_detected_utc="2026-10-28T10:00:00Z",
        last_detected_utc="2026-10-28T10:05:00Z",
        first_detected_cambodia="2026-10-28 17:00:00 ICT",
        last_detected_cambodia="2026-10-28 17:05:00 ICT",
        error_summary="Frontend edge recovered successfully",
        recovery_confirmations=3,
        pull_request_url="https://github.com/Phengsovanreach/Khmer-AI-/pull/1",
    )
    rec_msg = format_recovery_alert(inc)
    assert "RECOVERY VERIFIED" in rec_msg
    assert "ប្រព័ន្ធដំណើរការប្រក្រតីឡើងវិញ" in rec_msg
    assert "INC-REC-101" in rec_msg
    assert "3 ដងជាប់គ្នា" in rec_msg

    ci_msg = format_ci_report(
        status="SUCCESS",
        branch="feature/self-healing-system",
        commit_sha="09b0a8b987654321",
        commit_msg="feat: update telegram bot templates to polished khmer typography",
    )
    assert "CI PIPELINE" in ci_msg
    assert "ការតេស្តកូដស្វ័យប្រវត្តិ" in ci_msg
    assert "feature/self-healing-system" in ci_msg
    assert "09b0a8b9" in ci_msg
    assert "ជោគជ័យ (PASSED)" in ci_msg
