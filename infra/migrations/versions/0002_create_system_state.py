from alembic import op
import sqlalchemy as sa


revision = "0002_create_system_state"
down_revision = "0001_create_journal_events"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_state",
        sa.Column("key", sa.String(length=128), primary_key=True),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_by", sa.String(length=128), nullable=True),
    )
    op.create_index("ix_system_state_updated_at", "system_state", ["updated_at"])


def downgrade():
    op.drop_index("ix_system_state_updated_at", table_name="system_state")
    op.drop_table("system_state")
