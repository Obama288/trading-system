from alembic import op
import sqlalchemy as sa


revision = "0006_create_incidents"
down_revision = "0005_create_positions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "incidents",
        sa.Column("incident_id", sa.String(length=128), primary_key=True),
        sa.Column("incident_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("source_service", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_incidents_incident_type", "incidents", ["incident_type"])
    op.create_index("ix_incidents_severity", "incidents", ["severity"])
    op.create_index("ix_incidents_source_service", "incidents", ["source_service"])
    op.create_index("ix_incidents_correlation_id", "incidents", ["correlation_id"])
    op.create_index("ix_incidents_created_at", "incidents", ["created_at"])


def downgrade():
    op.drop_index("ix_incidents_created_at", table_name="incidents")
    op.drop_index("ix_incidents_correlation_id", table_name="incidents")
    op.drop_index("ix_incidents_source_service", table_name="incidents")
    op.drop_index("ix_incidents_severity", table_name="incidents")
    op.drop_index("ix_incidents_incident_type", table_name="incidents")
    op.drop_table("incidents")
