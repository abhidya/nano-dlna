import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment variable or use default SQLite database
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./nanodlna.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a single MetaData instance
# This will be shared across all modules that import Base
metadata_obj = MetaData()

# Pass the shared MetaData instance to declarative_base
Base = declarative_base(metadata=metadata_obj)

# Models will be imported in init_db() to avoid circular imports

def get_db():
    """
    Get a database session
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize the database
    """
    # Import models here to ensure they are registered with Base.metadata
    # This avoids circular imports since this function is called after all modules are loaded
    from models.device import DeviceModel
    from models.video import VideoModel
    from models.overlay import OverlayConfig
    
    # When running under pytest, skip the actual Base.metadata.create_all(bind=engine) call.
    # The test fixtures will handle creating tables on the temporary test database.
    if "PYTEST_CURRENT_TEST" in os.environ:
        logger.info("Skipping full DB DDL initialization during pytest run. Test fixtures will manage tables.")
        return  # Skip create_all for production engine

    try:
        Base.metadata.create_all(bind=engine) # This uses the production engine
        logger.info("Database initialized for production/development")
    except Exception as e:
        logger.error(f"Error initializing database for production/development: {e}")
        raise
