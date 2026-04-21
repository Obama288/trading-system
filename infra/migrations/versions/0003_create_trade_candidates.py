from alembic import op
import sqlalchemy as sa


revision = "0003_create_trade_candidates"
down_revision = "0002_create_system_state"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "trade_candidates",
        sa.Column("candidate_id", sa.String(length=128), primary_key=True),
        sa.Column("signal_id", sa.String(length=128), nullable=False),
        sa.Column("risk_id", sa.String(length=128), nullable=False),
        sa.Column("review_id", sa.String(length=128), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("side", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("execution_payload_json", sa.JSON(), nullable=True),
        sa.Column("ttl_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_trade_candidates_signal_id", "trade_candidates", ["signal_id"])
    op.create_index("ix_trade_candidates_risk_id", "trade_candidates", ["risk_id"])
    op.create_index("ix_trade_candidates_review_id", "trade_candidates", ["review_id"])
    op.create_index("ix_trade_candidates_symbol", "trade_candidates", ["symbol"])
    op.create_index("ix_trade_candidates_status", "trade_candidates", ["status"])
    op.create_index("ix_trade_candidates_ttl_expires_at", "trade_candidates", ["ttl_expires_at"])
    op.create_index("ix_trade_candidates_execution_id", "trade_candidates", ["execution_id"])
    op.create_index("ix_trade_candidates_created_at", "trade_candidates", ["created_at"])


def downgrade():
    op.drop_index("ix_trade_candidates_created_at", table_name="trade_candidates")
    op.drop_index("ix_trade_candidates_execution_id", table_name="trade_candidates")
    op.drop_index("ix_trade_candidates_ttl_expires_at", table_name="trade_candidates")
    op.drop_index("ix_trade_candidates_status", table_name="trade_candidates")
    op.drop_index("ix_trade_candidates_symbol", table_name="trade_candidates")
    op.drop_index("ix_trade_candidates_review_id", table_name="trade_candidates")
    op.drop_index("ix_trade_candidates_risk_id", table_name="trade_candidates")
    op.drop_index("ix_trade_candidates_signal_id", table_name="trade_candidates")
    op.drop_table("trade_candidates")
