"""
Tests for database models.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from web.backend.database.database import Base
from web.backend.models.device import DeviceModel
from web.backend.models.video import VideoModel


# Fixture to set up the database
@pytest.fixture(scope="module")
def setup_test_db():
    engine = create_engine("sqlite:///:memory:")  # Use in-memory SQLite database
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal  # Yield the sessionmaker
    Base.metadata.drop_all(engine) # Clean up


class TestDeviceModel:
    """Tests for the Device model."""
    
    def test_device_creation(self, setup_test_db):
        """Test creating a device."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a new device
            device = DeviceModel(
                name="Test Device",
                type="dlna",
                hostname="192.168.1.100",
                action_url="http://example.com/action",
                friendly_name="Test DLNA Device",
                status="online",
            )
            db.add(device)
            db.commit()
            db.refresh(device)
            
            # Check that the device is in the database
            assert device.id is not None
            assert device.name == "Test Device"

    def test_device_update(self, setup_test_db):
        """Test updating a device."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a new device
            device = DeviceModel(
                name="Test Device Update",
                type="dlna",
                hostname="192.168.1.101",
                action_url="http://example.com/action_update",
                friendly_name="Test DLNA Device Update",
                status="offline",
            )
            db.add(device)
            db.commit()
            db.refresh(device)
            
            # Update the device
            device.status = "online"
            device.friendly_name = "Updated Test Device"
            db.commit()
            db.refresh(device)
            
            # Check that the device is updated
            assert device.status == "online"
            assert device.friendly_name == "Updated Test Device"

    def test_device_deletion(self, setup_test_db):
        """Test deleting a device."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a new device
            device = DeviceModel(
                name="Test Device Deletion",
                type="dlna",
                hostname="192.168.1.102",
                action_url="http://example.com/action_deletion",
                friendly_name="Test DLNA Device Deletion",
                status="online",
            )
            db.add(device)
            db.commit()
            db.refresh(device)
            device_id = device.id
            
            # Delete the device
            db.delete(device)
            db.commit()
            
            # Check that the device was deleted
            assert db.query(DeviceModel).filter(DeviceModel.id == device_id).first() is None


class TestVideoModel:
    """Tests for the Video model."""
    
    def test_video_creation(self, setup_test_db):
        """Test creating a video."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a new video
            video = VideoModel(
                name="Test Video",
                path="/path/to/test_video.mp4",
                file_name="test_video.mp4",
                file_size=1024000,
                duration=120.5,
                format="mp4"
            )
            db.add(video)
            db.commit()
            db.refresh(video)
            
            # Check that the video is in the database
            assert video.id is not None
            assert video.name == "Test Video"

    def test_video_update(self, setup_test_db):
        """Test updating a video."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a new video
            video = VideoModel(
                name="Test Video Update",
                path="/path/to/test_video_update.mp4",
                file_name="test_video_update.mp4",
                file_size=2048000,
                duration=180.0,
                format="mp4"
            )
            db.add(video)
            db.commit()
            db.refresh(video)
            
            # Update the video
            video.name = "Updated Test Video"
            video.duration = 185.5
            db.commit()
            db.refresh(video)
            
            # Check that the video is updated
            assert video.name == "Updated Test Video"
            assert video.duration == 185.5

    def test_video_deletion(self, setup_test_db):
        """Test deleting a video."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a new video
            video = VideoModel(
                name="Test Video Deletion",
                path="/path/to/test_video_deletion.mp4",
                file_name="test_video_deletion.mp4",
                file_size=512000,
                duration=60.0,
                format="mp4"
            )
            db.add(video)
            db.commit()
            db.refresh(video)
            video_id = video.id
            
            # Delete the video
            db.delete(video)
            db.commit()
            
            # Check that the video was deleted
            assert db.query(VideoModel).filter(VideoModel.id == video_id).first() is None

        
# Add relationship tests if there are relationships between models
class TestModelRelationships:
    """Tests for model relationships."""
    
    def test_device_video_assignment(self, setup_test_db):
        """Test assigning a video to a device."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a device and a video
            device = DeviceModel(
                name="Test Device Relationship",
                type="dlna",
                hostname="127.0.0.1",
                action_url="http://127.0.0.1:8000/action",
                location="http://127.0.0.1:8000/location",
                friendly_name="Test DLNA Device",
                status="online"
            )
            
            video = VideoModel(
                name="Test Video Relationship",
                path="/path/to/test_video_relationship.mp4",
                file_name="test_video_relationship.mp4",
                file_size=1024,
                duration=60.0,
                format="mp4"
            )
            
            # Add them to the database
            db.add(device)
            db.add(video)
            db.commit()
            db.refresh(device)
            db.refresh(video)
            
            # Add a video assignment if your model supports it
            if hasattr(device, 'videos'):
                device.videos.append(video)
                db.commit()
                db.refresh(device)
                
                # Check that the video was assigned to the device
                assert video in device.videos
            
            # Clean up
            db.delete(video)
            db.delete(device)
            db.commit()
