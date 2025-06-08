"""Add overlay_configs table

Run this migration to add the overlay_configs table to the database.
Execute: python add_overlay_configs.py
"""

import sys
import os

# Add parent directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_dir = os.path.dirname(backend_dir)
sys.path.insert(0, project_dir)
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
import json

# Directly define the database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./nano_dlna.db"

def run_migration():
    """Add overlay_configs table to the database"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Create overlay_configs table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS overlay_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR NOT NULL,
        video_id INTEGER NOT NULL,
        video_transform JSON NOT NULL,
        widgets JSON NOT NULL,
        api_configs JSON NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (video_id) REFERENCES videos (id) ON DELETE CASCADE
    );
    """
    
    # Create indexes
    create_index_query = """
    CREATE INDEX IF NOT EXISTS idx_overlay_configs_video_id ON overlay_configs(video_id);
    """
    
    try:
        with engine.connect() as conn:
            # Create table
            conn.execute(text(create_table_query))
            print("✓ Created overlay_configs table")
            
            # Create index
            conn.execute(text(create_index_query))
            print("✓ Created index on video_id")
            
            # Verify table creation
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='overlay_configs';"
            ))
            if result.fetchone():
                print("✓ Verified overlay_configs table exists")
                
                # Get table info
                info = conn.execute(text("PRAGMA table_info(overlay_configs);"))
                print("\nTable structure:")
                for row in info:
                    print(f"  - {row[1]} ({row[2]})")
            else:
                print("✗ Failed to verify table creation")
                
            conn.commit()
            
    except Exception as e:
        print(f"✗ Error running migration: {e}")
        raise

if __name__ == "__main__":
    print("Running overlay_configs migration...")
    run_migration()
    print("\n✓ Migration completed successfully!")