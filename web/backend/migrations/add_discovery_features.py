"""
Database migration to add new discovery system features.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# Revision identifiers
revision = 'add_discovery_features'
down_revision = 'add_user_control_mode'
branch_labels = None
depends_on = None


def upgrade():
    """Add new columns for unified discovery system."""
    
    # Add discovery method tracking
    op.add_column('devices', 
        sa.Column('discovery_method', sa.String(50), nullable=True)
    )
    
    # Add last discovered timestamp
    op.add_column('devices',
        sa.Column('last_discovered', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Add capabilities JSON field
    op.add_column('devices',
        sa.Column('capabilities', sa.JSON, nullable=True)
    )
    
    # Add group and zone fields
    op.add_column('devices',
        sa.Column('device_group', sa.String(100), nullable=True)
    )
    
    op.add_column('devices',
        sa.Column('device_zone', sa.String(100), nullable=True)
    )
    
    # Add schedule configuration
    op.add_column('devices',
        sa.Column('schedule_config', sa.JSON, nullable=True)
    )
    
    # Create configuration versions table
    op.create_table(
        'config_versions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('config', sa.JSON, nullable=False),
        sa.Column('version', sa.Integer, nullable=False),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True)
    )
    
    # Create device groups table
    op.create_table(
        'device_groups',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('config', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 onupdate=sa.func.now())
    )
    
    # Create device zones table
    op.create_table(
        'device_zones',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('config', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                 onupdate=sa.func.now())
    )
    
    # Create casting sessions table
    op.create_table(
        'casting_sessions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.String(36), unique=True, nullable=False),
        sa.Column('device_id', sa.Integer, sa.ForeignKey('devices.id'), nullable=False),
        sa.Column('content_url', sa.String(500), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), 
                 server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_paused', sa.Boolean, default=False),
        sa.Column('position', sa.Float, default=0.0),
        sa.Column('duration', sa.Float, default=0.0),
        sa.Column('metadata', sa.JSON, nullable=True)
    )
    
    # Create discovery events table for logging
    op.create_table(
        'discovery_events',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('device_id', sa.Integer, sa.ForeignKey('devices.id'), nullable=True),
        sa.Column('backend', sa.String(50), nullable=True),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), 
                 server_default=sa.func.now())
    )
    
    # Add indexes for performance
    op.create_index('idx_devices_discovery_method', 'devices', ['discovery_method'])
    op.create_index('idx_devices_group', 'devices', ['device_group'])
    op.create_index('idx_devices_zone', 'devices', ['device_zone'])
    op.create_index('idx_casting_sessions_device', 'casting_sessions', ['device_id'])
    op.create_index('idx_casting_sessions_active', 'casting_sessions', ['is_active'])
    op.create_index('idx_discovery_events_device', 'discovery_events', ['device_id'])
    op.create_index('idx_discovery_events_type', 'discovery_events', ['event_type'])
    
    # Update existing DLNA devices
    op.execute("""
        UPDATE devices 
        SET discovery_method = 'dlna' 
        WHERE type = 'dlna' AND discovery_method IS NULL
    """)
    
    # Update existing Transcreen devices
    op.execute("""
        UPDATE devices 
        SET discovery_method = 'dlna' 
        WHERE type = 'transcreen' AND discovery_method IS NULL
    """)


def downgrade():
    """Remove discovery system features."""
    
    # Drop indexes
    op.drop_index('idx_discovery_events_type', 'discovery_events')
    op.drop_index('idx_discovery_events_device', 'discovery_events')
    op.drop_index('idx_casting_sessions_active', 'casting_sessions')
    op.drop_index('idx_casting_sessions_device', 'casting_sessions')
    op.drop_index('idx_devices_zone', 'devices')
    op.drop_index('idx_devices_group', 'devices')
    op.drop_index('idx_devices_discovery_method', 'devices')
    
    # Drop tables
    op.drop_table('discovery_events')
    op.drop_table('casting_sessions')
    op.drop_table('device_zones')
    op.drop_table('device_groups')
    op.drop_table('config_versions')
    
    # Drop columns
    op.drop_column('devices', 'schedule_config')
    op.drop_column('devices', 'device_zone')
    op.drop_column('devices', 'device_group')
    op.drop_column('devices', 'capabilities')
    op.drop_column('devices', 'last_discovered')
    op.drop_column('devices', 'discovery_method')