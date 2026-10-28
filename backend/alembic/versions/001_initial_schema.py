"""initial schema: users, sessions, audit_logs, incidents, ai_fix_history

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-28 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Users Table
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=20), server_default="user", nullable=False),
            sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
            sa.Column("email_verified", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("avatar_color", sa.String(length=20), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("idx_users_email", "users", ["email"], unique=True)

    # 2. Sessions Table
    if "sessions" not in tables:
        op.create_table(
            "sessions",
            sa.Column("token", sa.String(length=128), primary_key=True),
            sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
        )
        op.create_index("idx_sessions_user_id", "sessions", ["user_id"])
        op.create_index("idx_sessions_token", "sessions", ["token"])

    # 3. Audit Logs Table
    if "audit_logs" not in tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("operation_id", sa.String(length=64), nullable=False),
            sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("duration_ms", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("details_json", sa.Text(), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("idx_audit_logs_operation_id", "audit_logs", ["operation_id"], unique=True)
        op.create_index("idx_audit_logs_event_type", "audit_logs", ["event_type"])
        op.create_index("idx_audit_logs_user_id", "audit_logs", ["user_id"])

    # 4. Incidents Table
    if "incidents" not in tables:
        op.create_table(
            "incidents",
            sa.Column("incident_id", sa.String(length=64), primary_key=True),
            sa.Column("service", sa.String(length=30), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("severity", sa.String(length=20), server_default="WARNING", nullable=False),
            sa.Column("consecutive_failures", sa.Integer(), server_default="1", nullable=False),
            sa.Column("error_summary", sa.Text(), nullable=False),
            sa.Column("first_detected_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_detected_utc", sa.DateTime(timezone=True), nullable=False),
            sa.Column("diagnostics_json", sa.Text(), nullable=True),
            sa.Column("repair_attempts", sa.Integer(), server_default="0", nullable=False),
            sa.Column("pull_request_url", sa.String(length=255), nullable=True),
            sa.Column("recovery_confirmations", sa.Integer(), server_default="0", nullable=False),
            sa.Column("notified_states", sa.Text(), nullable=True),
        )

    # 5. AI Fix History Table
    if "ai_fix_history" not in tables:
        op.create_table(
            "ai_fix_history",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("incident_id", sa.String(length=64), sa.ForeignKey("incidents.incident_id", ondelete="CASCADE"), nullable=False),
            sa.Column("root_cause", sa.Text(), nullable=False),
            sa.Column("target_files", sa.Text(), nullable=False),
            sa.Column("diff_content", sa.Text(), nullable=False),
            sa.Column("tests_passed", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("test_results", sa.Text(), nullable=True),
            sa.Column("deployment_status", sa.String(length=50), server_default="NOT_DEPLOYED", nullable=False),
            sa.Column("health_verified", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("rollback_occurred", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("idx_ai_fix_history_incident_id", "ai_fix_history", ["incident_id"])


def downgrade() -> None:
    op.drop_table("ai_fix_history")
    op.drop_table("incidents")
    op.drop_table("audit_logs")
    op.drop_table("sessions")
    op.drop_table("users")
