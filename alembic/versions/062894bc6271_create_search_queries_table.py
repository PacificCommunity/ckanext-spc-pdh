"""Create search_queries table

Revision ID: 062894bc6271
Revises:
Create Date: 2019-01-11 15:47:54.578826

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '062894bc6271'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'spc_search_queries',
        sa.Column('query', sa.UnicodeText, primary_key=True),
        sa.Column('count', sa.Integer, server_default='0')
    )


def downgrade():
    op.drop_table('spc_search_queries')
