"""add exam_comparisons table

Revision ID: 0002_exam_comparisons
Revises: 0001_initial
Create Date: 2026-06-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, BYTEA, JSONB

revision: str = "0002_exam_comparisons"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exam_comparisons",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("exam_before_id", UUID(as_uuid=True), sa.ForeignKey("medical_exams.id"), nullable=False),
        sa.Column("exam_after_id", UUID(as_uuid=True), sa.ForeignKey("medical_exams.id"), nullable=False),
        sa.Column("comparison_result_encrypted", BYTEA()),
        sa.Column("comparison_nonce", sa.String(255)),
        sa.Column("comparison_tag", sa.String(255)),
        sa.Column("differences", JSONB()),
        sa.Column("generated_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    op.create_index("idx_comparisons_patient", "exam_comparisons", ["patient_id"])


def downgrade() -> None:
    op.drop_table("exam_comparisons")
