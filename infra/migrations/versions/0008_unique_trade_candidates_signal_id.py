from alembic import op


revision = "0008_unique_tc_signal_id"
down_revision = "0007_create_executions"
branch_labels = None
depends_on = None


def upgrade():
    # TD-13: make signal_id idempotent for /v1/pipeline/evaluate retries.
    # Drop the non-unique index from 0003 and replace it with a unique index.
    op.drop_index("ix_trade_candidates_signal_id", table_name="trade_candidates")
    op.create_index(
        "ux_trade_candidates_signal_id",
        "trade_candidates",
        ["signal_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("ux_trade_candidates_signal_id", table_name="trade_candidates")
    op.create_index("ix_trade_candidates_signal_id", "trade_candidates", ["signal_id"])

