from alembic import op
import sqlalchemy as sa


revision = "0007_create_executions"
down_revision = "0006_create_incidents"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "executions",
        sa.Column("execution_id", sa.String(length=128), primary_key=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("candidate_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_executions_idempotency_key"),
    )
    op.create_index("ix_executions_idempotency_key", "executions", ["idempotency_key"])
    op.create_index("ix_executions_candidate_id", "executions", ["candidate_id"])
    op.create_index("ix_executions_status", "executions", ["status"])
    op.create_index("ix_executions_created_at", "executions", ["created_at"])


def downgrade():
    op.drop_index("ix_executions_created_at", table_name="executions")
    op.drop_index("ix_executions_status", table_name="executions")
    op.drop_index("ix_executions_candidate_id", table_name="executions")
    op.drop_index("ix_executions_idempotency_key", table_name="executions")
    op.drop_table("executions")
