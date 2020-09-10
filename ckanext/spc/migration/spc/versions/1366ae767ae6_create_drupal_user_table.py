"""create drupal_user table

Revision ID: 1366ae767ae6
Revises: 062894bc6271
Create Date: 2020-01-17 12:08:57.809860

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1366ae767ae6'
down_revision = '062894bc6271'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
    'spc_drupal_user',
        sa.Column('ckan_user', sa.String, primary_key=True),
        sa.Column('drupal_user', sa.Integer)
    )


def downgrade():
    op.drop_table('spc_drupal_user')
