"""refactor

Revision ID: 004
Revises: 003
Create Date: 2024-02-19 11:01:18.157396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chatmessage', sa.Column('user_first_name', sa.Text(), nullable=True))
    op.add_column('chatmessage', sa.Column('user_last_name', sa.Text(), nullable=True))
    op.add_column('chatmessage', sa.Column('username', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('chatmessage', 'username')
    op.drop_column('chatmessage', 'user_last_name')
    op.drop_column('chatmessage', 'user_first_name')
    # ### end Alembic commands ###
