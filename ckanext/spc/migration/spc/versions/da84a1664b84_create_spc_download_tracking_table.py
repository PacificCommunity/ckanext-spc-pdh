"""Create spc_download_tracking table

Revision ID: da84a1664b84
Revises: 101c131e6f8c
Create Date: 2020-08-31 09:24:07.997077

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'da84a1664b84'
down_revision = '101c131e6f8c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "spc_download_tracking",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id", sa.String, sa.ForeignKey("user.id", ondelete="CASCADE")
        ),
        sa.Column(
            "resource_id",
            sa.String,
            sa.ForeignKey("resource.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "downloaded_at",
            sa.DateTime,
            server_default=sa.func.current_timestamp(),
        ),
    )



def downgrade():
    op.drop_table('spc_download_tracking')
