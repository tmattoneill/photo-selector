"""Update existing schema to Elo+sigma rating system

Revision ID: 002_update_elo_sigma
Revises: 001_elo_sigma
Create Date: 2024-08-31 09:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_elo_sigma_update'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update existing schema to match algo-update.yaml specification."""
    
    # First, check if tables exist and update them
    
    # Update images table - add missing Elo+σ columns if they don't exist
    connection = op.get_bind()
    
    # Check if mu column exists
    result = connection.execute(sa.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'images' AND column_name = 'mu'
    """)).fetchone()
    
    if not result:
        # Add Elo+σ rating fields
        op.add_column('images', sa.Column('mu', sa.Float(), nullable=False, server_default=sa.text('1500.0')))
        op.add_column('images', sa.Column('sigma', sa.Float(), nullable=False, server_default=sa.text('350.0')))
        
        # Add missing fields
        op.add_column('images', sa.Column('last_seen_round', sa.Integer(), nullable=True))
        op.add_column('images', sa.Column('is_archived_hard_no', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        
        # Add indexes
        op.create_index('idx_images_mu_sigma', 'images', ['mu', 'sigma'])
        op.create_index('idx_images_exposures', 'images', ['exposures'])
        
        # Drop old created_at column if it exists
        try:
            op.drop_column('images', 'created_at')
        except:
            pass
    
    # Update choices table structure
    result = connection.execute(sa.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'choices' AND column_name = 'winner_sha256'
    """)).fetchone()
    
    if not result:
        # Add new columns
        op.add_column('choices', sa.Column('winner_sha256', sa.String(64), nullable=True))
        op.add_column('choices', sa.Column('skipped', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        op.add_column('choices', sa.Column('decided_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')))
        
        # Migrate data: convert selection to winner_sha256 and skipped
        op.execute("""
            UPDATE choices SET 
                winner_sha256 = CASE 
                    WHEN selection = 'LEFT' THEN left_sha256
                    WHEN selection = 'RIGHT' THEN right_sha256
                    ELSE NULL
                END,
                skipped = CASE 
                    WHEN selection = 'SKIP' THEN true
                    ELSE false
                END,
                decided_at = COALESCE(created_at, NOW())
        """)
        
        # Drop old columns if they exist
        try:
            op.drop_constraint('choices_user_id_fkey', 'choices', type_='foreignkey')
            op.drop_column('choices', 'user_id')
        except:
            pass
        
        try:
            op.drop_column('choices', 'selection')
        except:
            pass
        
        try:
            op.drop_column('choices', 'created_at')
        except:
            pass
        
        # Change id from UUID to BIGSERIAL
        try:
            op.execute('ALTER TABLE choices DROP CONSTRAINT choices_pkey')
            op.drop_column('choices', 'id')
            op.add_column('choices', sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True))
            op.create_primary_key('choices_pkey', 'choices', ['id'])
        except:
            pass
    
    # Update app_state table to singleton pattern
    result = connection.execute(sa.text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'app_state' AND column_name = 'round'
    """)).fetchone()
    
    if not result:
        # Drop existing app_state and recreate
        op.drop_table('app_state')
        
        # Create new app_state table
        op.create_table('app_state',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('round', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.CheckConstraint('id = 1', name='app_state_singleton'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Insert initial row
        op.execute("INSERT INTO app_state (id, round) VALUES (1, 0)")
    
    # Create new tables if they don't exist
    
    # duplicates table
    result = connection.execute(sa.text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name = 'duplicates'
    """)).fetchone()
    
    if not result:
        op.create_table('duplicates',
            sa.Column('duplicate_sha256', sa.String(length=64), nullable=False),
            sa.Column('canonical_sha256', sa.String(length=64), nullable=False),
            sa.CheckConstraint('duplicate_sha256 <> canonical_sha256', name='dup_not_self'),
            sa.ForeignKeyConstraint(['canonical_sha256'], ['images.sha256'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['duplicate_sha256'], ['images.sha256'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('duplicate_sha256')
        )
    
    # galleries table
    result = connection.execute(sa.text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_name = 'galleries'
    """)).fetchone()
    
    if not result:
        op.create_table('galleries',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('selection_policy', sa.String(), nullable=False),
            sa.Column('selection_params', sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('duplicates_policy', sa.String(), nullable=False),
            sa.Column('engine_version', sa.String(), nullable=False, server_default=sa.text("'duel-engine Elo+σ v1'")),
            sa.Column('app_round_at_creation', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
        
        # gallery_images table
        op.create_table('gallery_images',
            sa.Column('gallery_id', sa.Integer(), nullable=False),
            sa.Column('sha256', sa.String(length=64), nullable=False),
            sa.Column('rank', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['gallery_id'], ['galleries.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['sha256'], ['images.sha256'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('gallery_id', 'sha256')
        )
        op.create_index('idx_gallery_images_rank', 'gallery_images', ['gallery_id', 'rank'], unique=False)


def downgrade() -> None:
    """Downgrade back to original schema (not fully reversible)."""
    # This is not fully reversible since we're migrating data
    pass