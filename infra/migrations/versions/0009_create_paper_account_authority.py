from alembic import op
import sqlalchemy as sa


revision = "0009_create_paper_account_authority"
down_revision = "0008_unique_tc_signal_id"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "paper_account_authority",
        sa.Column("account_key", sa.String(length=64), primary_key=True),
        sa.Column("equity_usdt", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
    )


def downgrade():
    op.drop_table("paper_account_authority")
