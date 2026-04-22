from alembic import op
import sqlalchemy as sa


revision = "0005_create_positions"
down_revision = "0004_create_operator_actions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "positions",
        sa.Column("position_id", sa.String(length=128), primary_key=True),
        sa.Column("execution_id", sa.String(length=128), nullable=False),
        sa.Column("candidate_id", sa.String(length=128), nullable=True),
        sa.Column("signal_id", sa.String(length=128), nullable=True),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("side", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("stop_loss", sa.Float(), nullable=True),
        sa.Column("take_profit", sa.JSON(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("close_price", sa.Float(), nullable=True),
        sa.Column("close_reason", sa.String(length=32), nullable=True),
        sa.Column("ttl_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("execution_id", name="uq_positions_execution_id"),
    )
    op.create_index("ix_positions_execution_id", "positions", ["execution_id"])
    op.create_index("ix_positions_candidate_id", "positions", ["candidate_id"])
    op.create_index("ix_positions_signal_id", "positions", ["signal_id"])
    op.create_index("ix_positions_symbol", "positions", ["symbol"])
    op.create_index("ix_positions_status", "positions", ["status"])
    op.create_index("ix_positions_opened_at", "positions", ["opened_at"])
    op.create_index("ix_positions_ttl_expires_at", "positions", ["ttl_expires_at"])
    op.create_index("ix_positions_created_at", "positions", ["created_at"])

    op.create_table(
        "position_events",
        sa.Column("event_id", sa.String(length=128), primary_key=True),
        sa.Column("position_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_position_events_position_id", "position_events", ["position_id"])
    op.create_index("ix_position_events_event_type", "position_events", ["event_type"])
    op.create_index("ix_position_events_correlation_id", "position_events", ["correlation_id"])
    op.create_index("ix_position_events_created_at", "position_events", ["created_at"])


def downgrade():
    op.drop_index("ix_position_events_created_at", table_name="position_events")
    op.drop_index("ix_position_events_correlation_id", table_name="position_events")
    op.drop_index("ix_position_events_event_type", table_name="position_events")
    op.drop_index("ix_position_events_position_id", table_name="position_events")
    op.drop_table("position_events")

    op.drop_index("ix_positions_created_at", table_name="positions")
    op.drop_index("ix_positions_ttl_expires_at", table_name="positions")
    op.drop_index("ix_positions_opened_at", table_name="positions")
    op.drop_index("ix_positions_status", table_name="positions")
    op.drop_index("ix_positions_symbol", table_name="positions")
    op.drop_index("ix_positions_signal_id", table_name="positions")
    op.drop_index("ix_positions_candidate_id", table_name="positions")
    op.drop_index("ix_positions_execution_id", table_name="positions")
    op.drop_table("positions")
