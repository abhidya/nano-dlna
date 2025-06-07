#!/usr/bin/env python3
"""
Add streaming_url and streaming_port fields to devices table
"""
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from web.backend.database.database import SQLALCHEMY_DATABASE_URL

logger = logging.getLogger(__name__)

def upgrade():
    """Add streaming fields to devices table"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add streaming_url column
            conn.execute(text("""
                ALTER TABLE devices 
                ADD COLUMN streaming_url VARCHAR
            """))
            conn.commit()
            logger.info("Added streaming_url column to devices table")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                logger.info("streaming_url column already exists")
            else:
                raise
        
        try:
            # Add streaming_port column
            conn.execute(text("""
                ALTER TABLE devices 
                ADD COLUMN streaming_port INTEGER
            """))
            conn.commit()
            logger.info("Added streaming_port column to devices table")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                logger.info("streaming_port column already exists")
            else:
                raise

def downgrade():
    """Remove streaming fields from devices table"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE devices DROP COLUMN streaming_url"))
        conn.execute(text("ALTER TABLE devices DROP COLUMN streaming_port"))
        conn.commit()

if __name__ == "__main__":
    upgrade()
    print("Migration completed successfully")