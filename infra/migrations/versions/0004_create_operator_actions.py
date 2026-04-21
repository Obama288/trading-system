from alembic import op
import sqlalchemy as sa


revision = "0004_create_operator_actions"
down_revision = "0003_create_trade_candidates"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "operator_actions",
        sa.Column("action_id", sa.String(length=128), primary_key=True),
        sa.Column("operator_user_id", sa.BigInteger(), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_operator_actions_operator_user_id", "operator_actions", ["operator_user_id"])
    op.create_index("ix_operator_actions_action_type", "operator_actions", ["action_type"])
    op.create_index("ix_operator_actions_target_type", "operator_actions", ["target_type"])
    op.create_index("ix_operator_actions_target_id", "operator_actions", ["target_id"])
    op.create_index("ix_operator_actions_correlation_id", "operator_actions", ["correlation_id"])
    op.create_index("ix_operator_actions_created_at", "operator_actions", ["created_at"])


def downgrade():
    op.drop_index("ix_operator_actions_created_at", table_name="operator_actions")
    op.drop_index("ix_operator_actions_correlation_id", table_name="operator_actions")
    op.drop_index("ix_operator_actions_target_id", table_name="operator_actions")
    op.drop_index("ix_operator_actions_target_type", table_name="operator_actions")
    op.drop_index("ix_operator_actions_action_type", table_name="operator_actions")
    op.drop_index("ix_operator_actions_operator_user_id", table_name="operator_actions")
    op.drop_table("operator_actions")
