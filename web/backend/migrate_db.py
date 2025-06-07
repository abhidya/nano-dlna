import os
import sqlite3
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment variable or use default SQLite database
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./nanodlna.db")

def migrate_sqlite_db():
    """
    Migrate the SQLite database to add missing columns
    """
    try:
        # Extract the database path from the URL
        if DATABASE_URL.startswith("sqlite:///"):
            db_path = DATABASE_URL.replace("sqlite:///", "")
            if db_path.startswith("./"):
                db_path = db_path[2:]
        else:
            logger.error(f"Unsupported database URL: {DATABASE_URL}")
            return False
        
        logger.info(f"Migrating database at {db_path}")
        
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the devices table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='devices'")
        if not cursor.fetchone():
            logger.error("Devices table does not exist")
            conn.close()
            return False
        
        # Get the current columns in the devices table
        cursor.execute("PRAGMA table_info(devices)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing columns
        if "playback_position" not in columns:
            logger.info("Adding playback_position column")
            cursor.execute("ALTER TABLE devices ADD COLUMN playback_position TEXT")
        
        if "playback_duration" not in columns:
            logger.info("Adding playback_duration column")
            cursor.execute("ALTER TABLE devices ADD COLUMN playback_duration TEXT")
        
        if "playback_progress" not in columns:
            logger.info("Adding playback_progress column")
            cursor.execute("ALTER TABLE devices ADD COLUMN playback_progress INTEGER")
        
        # Commit the changes
        conn.commit()
        conn.close()
        
        logger.info("Database migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error migrating database: {e}")
        return False

def migrate_sqlalchemy_db():
    """
    Migrate the database using SQLAlchemy
    """
    try:
        # Create SQLAlchemy engine
        engine = create_engine(
            DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
        )
        
        # Create inspector
        inspector = inspect(engine)
        
        # Check if the devices table exists
        if not inspector.has_table("devices"):
            logger.error("Devices table does not exist")
            return False
        
        # Get the current columns in the devices table
        columns = [column["name"] for column in inspector.get_columns("devices")]
        
        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Add missing columns using raw SQL
        if "playback_position" not in columns:
            logger.info("Adding playback_position column")
            session.execute("ALTER TABLE devices ADD COLUMN playback_position TEXT")
        
        if "playback_duration" not in columns:
            logger.info("Adding playback_duration column")
            session.execute("ALTER TABLE devices ADD COLUMN playback_duration TEXT")
        
        if "playback_progress" not in columns:
            logger.info("Adding playback_progress column")
            session.execute("ALTER TABLE devices ADD COLUMN playback_progress INTEGER")
        
        # Commit the changes
        session.commit()
        session.close()
        
        logger.info("Database migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error migrating database: {e}")
        return False

if __name__ == "__main__":
    if DATABASE_URL.startswith("sqlite"):
        success = migrate_sqlite_db()
    else:
        success = migrate_sqlalchemy_db()
    
    if success:
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
