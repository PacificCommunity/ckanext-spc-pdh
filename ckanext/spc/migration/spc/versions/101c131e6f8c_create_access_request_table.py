"""create access_request table

Revision ID: 101c131e6f8c
Revises: 1366ae767ae6
Create Date: 2020-08-13 09:11:19.864567

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '101c131e6f8c'
down_revision = '1366ae767ae6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('spc_access_request',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('package_id', sa.String(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('state', sa.String(), nullable=False),
        sa.Column('data_modified', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('spc_access_request')