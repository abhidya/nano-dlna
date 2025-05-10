"""
Tests for the database module.
"""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import tempfile
from sqlalchemy.orm import Session

from database.database import Base, get_db
from services.device_service import DeviceService
from models.device import DeviceModel
from models.video import VideoModel
from schemas.device import DeviceCreate
from schemas.video import VideoCreate


class TestDatabase:
    """Tests for the database module."""
    
    def test_connection(self):
        """Test database connection."""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix=".db") as temp_file:
            # Create engine
            engine = create_engine(f"sqlite:///{temp_file.name}")
            
            # Create the tables
            Base.metadata.create_all(bind=engine)
            
            # Create a session
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Check that the session is active
            assert session.is_active
            
            # Close the session
            session.close()
    
    def test_tables_created(self):
        """Test that tables are created."""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix=".db") as temp_file:
            # Create engine
            engine = create_engine(f"sqlite:///{temp_file.name}")
            
            # Create the tables
            Base.metadata.create_all(bind=engine)
            
            # Check that the tables are created
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            assert "devices" in table_names
            assert "videos" in table_names
    
    def test_device_table(self):
        """Test the device table."""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix=".db") as temp_file:
            # Create engine
            engine = create_engine(f"sqlite:///{temp_file.name}")
            
            # Create the tables
            Base.metadata.create_all(bind=engine)
            
            # Create a session
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Create a device
            device = DeviceModel(
                name="Test Device",
                type="dlna",
                hostname="127.0.0.1",
                action_url="http://127.0.0.1:8000/action",
                location="http://127.0.0.1:8000/location",
                friendly_name="Test Device",
                status="online"
            )
            
            # Add the device to the database
            session.add(device)
            session.commit()
            
            # Get the device from the database
            db_device = session.query(DeviceModel).filter(DeviceModel.name == "Test Device").first()
            
            # Check that the device is retrieved
            assert db_device is not None
            assert db_device.name == "Test Device"
            assert db_device.type == "dlna"
            assert db_device.hostname == "127.0.0.1"
            assert db_device.action_url == "http://127.0.0.1:8000/action"
            assert db_device.location == "http://127.0.0.1:8000/location"
            assert db_device.friendly_name == "Test Device"
            assert db_device.status == "online"
            
            # Close the session
            session.close()
    
    def test_video_table(self):
        """Test the video table."""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix=".db") as temp_file:
            # Create engine
            engine = create_engine(f"sqlite:///{temp_file.name}")
            
            # Create the tables
            Base.metadata.create_all(bind=engine)
            
            # Create a session
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Create a video
            video = VideoModel(
                name="Test Video",
                path="/path/to/test_video.mp4",
                file_name="test_video.mp4",
                file_size=1024,
                format="mp4",
                resolution="1920x1080"
            )
            
            # Add the video to the database
            session.add(video)
            session.commit()
            
            # Get the video from the database
            db_video = session.query(VideoModel).filter(VideoModel.name == "Test Video").first()
            
            # Check that the video is retrieved
            assert db_video is not None
            assert db_video.name == "Test Video"
            assert db_video.path == "/path/to/test_video.mp4"
            assert db_video.file_name == "test_video.mp4"
            assert db_video.file_size == 1024
            assert db_video.format == "mp4"
            assert db_video.resolution == "1920x1080"
            
            # Close the session
            session.close()
    
    def test_get_db(self, monkeypatch):
        """Test the get_db function."""
        # Mock the database URL
        monkeypatch.setattr("database.database.DATABASE_URL", "sqlite:///:memory:")
        
        # Create a generator from get_db
        db_generator = get_db()
        
        # Get the session
        db = next(db_generator)
        
        # Check that the session is active
        assert db.is_active
        
        # Close the session
        try:
            next(db_generator)
        except StopIteration:
            pass
