"""add user_profiles table

Revision ID: 79c301fb3909
Revises: 144b5cc2abeb
Create Date: 2026-02-12 02:45:04.357244

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '79c301fb3909'
down_revision: Union[str, None] = '144b5cc2abeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('user_profiles',
    sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('display_name', sa.String(length=100), nullable=False),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('avatar_url', sa.String(length=500), nullable=True),
    sa.Column('spotify_username', sa.String(length=100), nullable=True),
    sa.Column('favorite_genres', sa.String(length=500), nullable=True),
    sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_profiles_user_id'), 'user_profiles', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_profiles_user_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
