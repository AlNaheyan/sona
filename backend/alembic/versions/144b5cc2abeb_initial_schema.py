"""initial schema

Revision ID: 144b5cc2abeb
Revises:
Create Date: 2026-01-17 00:57:39.397606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '144b5cc2abeb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # Artists table
    op.create_table(
        'artists',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('mbid', sa.String(36), nullable=True),
        sa.Column('genres', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mbid'),
    )
    op.create_index('ix_artists_name', 'artists', ['name'])

    # Albums table
    op.create_table(
        'albums',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('mbid', sa.String(36), nullable=True),
        sa.Column('release_year', sa.Integer(), nullable=True),
        sa.Column('cover_url', sa.String(500), nullable=True),
        sa.Column('genres', sa.String(500), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rating_sum', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('bayesian_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mbid'),
    )
    op.create_index('ix_albums_title', 'albums', ['title'])
    op.create_index('ix_albums_bayesian_score', 'albums', ['bayesian_score'])

    # Album-Artists association table
    op.create_table(
        'album_artists',
        sa.Column('album_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('artist_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(['album_id'], ['albums.id']),
        sa.ForeignKeyConstraint(['artist_id'], ['artists.id']),
        sa.PrimaryKeyConstraint('album_id', 'artist_id'),
    )

    # Numeric ratings table
    op.create_table(
        'numeric_ratings',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('album_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('mood', sa.String(100), nullable=True),
        sa.Column('notes', sa.String(1000), nullable=True),
        sa.ForeignKeyConstraint(['album_id'], ['albums.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'album_id', name='uq_numeric_rating_user_album'),
    )
    op.create_index('ix_numeric_ratings_user_id', 'numeric_ratings', ['user_id'])
    op.create_index('ix_numeric_ratings_album_id', 'numeric_ratings', ['album_id'])

    # Pairwise comparisons table
    op.create_table(
        'pairwise_comparisons',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('album_a_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('album_b_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('winner_is_a', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['album_a_id'], ['albums.id']),
        sa.ForeignKeyConstraint(['album_b_id'], ['albums.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pairwise_comparisons_user_id', 'pairwise_comparisons', ['user_id'])

    # User album Elo table
    op.create_table(
        'user_album_elo',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('album_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('elo', sa.Float(), nullable=False, server_default='1500.0'),
        sa.Column('rating_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comparison_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['album_id'], ['albums.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'album_id', name='uq_elo_user_album'),
    )
    op.create_index('ix_user_album_elo_user_id', 'user_album_elo', ['user_id'])
    op.create_index('ix_user_album_elo_album_id', 'user_album_elo', ['album_id'])


def downgrade() -> None:
    op.drop_table('user_album_elo')
    op.drop_table('pairwise_comparisons')
    op.drop_table('numeric_ratings')
    op.drop_table('album_artists')
    op.drop_table('albums')
    op.drop_table('artists')
    op.drop_table('users')
