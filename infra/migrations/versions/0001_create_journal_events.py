from alembic import op
import sqlalchemy as sa


revision = "0001_create_journal_events"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "journal_events",
        sa.Column("event_id", sa.String(length=128), primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_journal_events_event_type", "journal_events", ["event_type"])
    op.create_index("ix_journal_events_severity", "journal_events", ["severity"])
    op.create_index("ix_journal_events_correlation_id", "journal_events", ["correlation_id"])
    op.create_index("ix_journal_events_created_at", "journal_events", ["created_at"])


def downgrade():
    op.drop_index("ix_journal_events_created_at", table_name="journal_events")
    op.drop_index("ix_journal_events_correlation_id", table_name="journal_events")
    op.drop_index("ix_journal_events_severity", table_name="journal_events")
    op.drop_index("ix_journal_events_event_type", table_name="journal_events")
    op.drop_table("journal_events")
