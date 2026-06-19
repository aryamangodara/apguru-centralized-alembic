"""Add spaced_repetition_processed_quiz idempotency marker table.

One row per (student_id, quiz_id) whose SR write-back has been applied.
Guards record_submission against double-advancing SM-2 intervals when a
quiz's background SR commit is dispatched more than once (retry / race).

Revision ID: 029
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa

revision = "029"
down_revision = "028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "spaced_repetition_processed_quiz",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.BigInteger, nullable=False),
        sa.Column("quiz_id", sa.BigInteger, nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "uq_sr_processed_student_quiz",
        "spaced_repetition_processed_quiz",
        ["student_id", "quiz_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_sr_processed_student_quiz",
        table_name="spaced_repetition_processed_quiz",
    )
    op.drop_table("spaced_repetition_processed_quiz")
