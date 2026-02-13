"""add want_to_listen table

Revision ID: a1b2c3d4e5f6
Revises: 79c301fb3909
Create Date: 2026-02-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '79c301fb3909'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('want_to_listen',
    sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('album_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('album_mbid', sa.String(length=36), nullable=False),
    sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['album_id'], ['albums.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'album_id', name='uq_want_to_listen_user_album')
    )
    op.create_index(op.f('ix_want_to_listen_user_id'), 'want_to_listen', ['user_id'], unique=False)
    op.create_index(op.f('ix_want_to_listen_album_id'), 'want_to_listen', ['album_id'], unique=False)
    op.create_index(op.f('ix_want_to_listen_album_mbid'), 'want_to_listen', ['album_mbid'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_want_to_listen_album_mbid'), table_name='want_to_listen')
    op.drop_index(op.f('ix_want_to_listen_album_id'), table_name='want_to_listen')
    op.drop_index(op.f('ix_want_to_listen_user_id'), table_name='want_to_listen')
    op.drop_table('want_to_listen')
