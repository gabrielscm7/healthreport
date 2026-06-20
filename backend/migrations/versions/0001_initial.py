"""init: all tables, indexes, constraints and audit policies

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-19
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB, ARRAY, BYTEA, BIGINT

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "doctor", "patient", "auditor", name="userrole"),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(255)),
        sa.Column("crm", sa.String(20)),
        sa.Column("phone", sa.String(20)),
        sa.Column("two_fa_enabled", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("two_fa_secret", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_crm", "users", ["crm"])

    # ------------------------------------------------------------------
    # 2. patients
    # ------------------------------------------------------------------
    op.create_table(
        "patients",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("cpf_hash", sa.String(255), unique=True),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("contact_phone", sa.String(20)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("idx_patients_cpf_hash", "patients", ["cpf_hash"])
    op.create_check_constraint("no_plain_text", "patients", "full_name != ''")

    # ------------------------------------------------------------------
    # 3. patient_consents
    # ------------------------------------------------------------------
    op.create_table(
        "patient_consents",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "patient_id",
            UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column(
            "doctor_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "consent_type",
            sa.Enum("ai_analysis", "data_storage", "research", name="consenttype"),
            nullable=False,
        ),
        sa.Column("consent_text", sa.Text(), nullable=False),
        sa.Column("signed_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("ip_address", INET()),
        sa.Column("user_agent", sa.Text()),
        sa.Column("signature_hash", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("idx_consents_patient", "patient_consents", ["patient_id"])
    op.create_index("idx_consents_expiry", "patient_consents", ["expires_at"])
    op.create_check_constraint(
        "consent_must_be_explicit", "patient_consents", "signed_at IS NOT NULL"
    )

    # ------------------------------------------------------------------
    # 4. medical_exams
    # ------------------------------------------------------------------
    op.create_table(
        "medical_exams",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "patient_id",
            UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column("exam_type", sa.String(100), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("content_encrypted", BYTEA(), nullable=False),
        sa.Column("content_nonce", sa.String(255), nullable=False),
        sa.Column("content_tag", sa.String(255), nullable=False),
        sa.Column("google_doc_id", sa.String(255)),
        sa.Column("markdown_content_encrypted", BYTEA()),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_exams_patient", "medical_exams", ["patient_id"])
    op.create_index("idx_exams_date", "medical_exams", ["exam_date"])

    # ------------------------------------------------------------------
    # 5. medical_reports
    # ------------------------------------------------------------------
    op.create_table(
        "medical_reports",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "patient_id",
            UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column(
            "requesting_doctor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("exams_used", ARRAY(UUID(as_uuid=True)), nullable=False),
        sa.Column("report_content_encrypted", BYTEA(), nullable=False),
        sa.Column("report_nonce", sa.String(255), nullable=False),
        sa.Column("report_tag", sa.String(255), nullable=False),
        sa.Column(
            "report_format",
            sa.Enum("json", "pdf", "markdown", name="reportformat"),
            server_default="json",
        ),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("model_confidence", sa.Float()),
        sa.Column("generated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("generating", "success", "error", name="reportstatus"),
            server_default="generating",
        ),
        sa.Column("error_message", sa.Text()),
    )
    op.create_index("idx_reports_patient", "medical_reports", ["patient_id"])
    op.create_index("idx_reports_doctor", "medical_reports", ["requesting_doctor_id"])

    # ------------------------------------------------------------------
    # 6. audit_logs (BIGSERIAL + imutável)
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", BIGINT(), primary_key=True, autoincrement=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("patient_id", UUID(as_uuid=True), sa.ForeignKey("patients.id")),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50)),
        sa.Column("resource_id", UUID(as_uuid=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("ip_address", INET(), nullable=False),
        sa.Column("user_agent", sa.Text()),
        sa.Column(
            "timestamp", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("request_id", sa.String(255)),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.create_index("idx_audit_patient", "audit_logs", ["patient_id"])
    op.create_index("idx_audit_user", "audit_logs", ["user_id"])
    op.create_index("idx_audit_timestamp", "audit_logs", ["timestamp"])
    op.create_index("idx_audit_action", "audit_logs", ["action_type"])

    # RLS policies for audit immutability
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY audit_no_update ON audit_logs FOR UPDATE USING (false)")
    op.execute("CREATE POLICY audit_no_delete ON audit_logs FOR DELETE USING (false)")

    # ------------------------------------------------------------------
    # 7. async_tasks
    # ------------------------------------------------------------------
    op.create_table(
        "async_tasks",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("task_type", sa.String(100), nullable=False),
        sa.Column("patient_id", UUID(as_uuid=True), sa.ForeignKey("patients.id")),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("input_data", JSONB()),
        sa.Column("output_data", JSONB()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("max_retries", sa.Integer(), server_default=sa.text("3")),
    )
    op.create_index("idx_tasks_status", "async_tasks", ["status"])
    op.create_index("idx_tasks_patient", "async_tasks", ["patient_id"])

    # ------------------------------------------------------------------
    # 8. doctor_patient_access
    # ------------------------------------------------------------------
    op.create_table(
        "doctor_patient_access",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "doctor_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "patient_id",
            UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column("access_level", sa.String(50), nullable=False),
        sa.Column("access_granted_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("access_revoked_at", sa.DateTime(), nullable=True),
        sa.Column("granted_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
    )
    op.create_unique_constraint(
        "uq_doctor_patient", "doctor_patient_access", ["doctor_id", "patient_id"]
    )
    op.create_index("idx_access_doctor", "doctor_patient_access", ["doctor_id"])
    op.create_index("idx_access_patient", "doctor_patient_access", ["patient_id"])


def downgrade() -> None:
    op.drop_table("doctor_patient_access")
    op.drop_table("async_tasks")
    op.drop_table("audit_logs")
    op.drop_table("medical_reports")
    op.drop_table("medical_exams")
    op.drop_table("patient_consents")
    op.drop_table("patients")
    op.drop_table("users")

    # Drop custom ENUM types
    op.execute("DROP TYPE IF EXISTS reportstatus")
    op.execute("DROP TYPE IF EXISTS reportformat")
    op.execute("DROP TYPE IF EXISTS consenttype")
    op.execute("DROP TYPE IF EXISTS userrole")
