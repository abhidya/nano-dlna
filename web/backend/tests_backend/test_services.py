"""
Tests for service modules.
"""
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add parent directory for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.device_service import DeviceService
from services.video_service import VideoService
from models.device import DeviceModel
from models.video import VideoModel
from schemas.device import DeviceCreate, DeviceUpdate
from schemas.video import VideoCreate, VideoUpdate
from core.device_manager import DeviceManager
from core.streaming_registry import StreamingSessionRegistry
from database.database import Base


# Fixture for in-memory database session
@pytest.fixture(scope="module")
def setup_test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(engine)

# Fixture for DeviceManager mock
@pytest.fixture
def mock_device_manager():
    return MagicMock(spec=DeviceManager)

# Fixture for StreamingSessionRegistry mock
@pytest.fixture
def mock_streaming_registry():
    return MagicMock(spec=StreamingSessionRegistry)

# Fixture for creating temp files
@pytest.fixture
def tmp_file_factory():
    created_files = []
    def _create_tmp_file(suffix, content):
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.write(content)
        temp_file.close()
        created_files.append(temp_file.name)
        return temp_file.name
    yield _create_tmp_file
    for f_path in created_files:
        if os.path.exists(f_path):
            os.remove(f_path)


class TestDeviceService:
    """Tests for the DeviceService class."""
    
    def test_get_devices(self, setup_test_db, mock_device_manager):
        """Test getting all devices."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create some test devices
            device1 = DeviceModel(
                name="Device 1",
                type="dlna",
                hostname="1.1.1.1",
                action_url="a1",
                friendly_name="f1",
                status="online"
            )
            
            device2 = DeviceModel(
                name="Device 2",
                type="transcreen",
                hostname="2.2.2.2",
                action_url="a2",
                friendly_name="f2",
                status="offline"
            )
            
            db.add_all([device1, device2])
            db.commit()
            db.refresh(device1)
            db.refresh(device2)
            
            # Create a device service
            device_service = DeviceService(db, mock_device_manager)
            
            # Get all devices
            devices = device_service.get_devices()
            
            # Check that both devices are returned
            assert len(devices) == 2
            
            # Check that the devices have the correct properties
            device1_found = False
            device2_found = False
            for device in devices:
                if device.name == "Device 1":
                    device1_found = True
                    assert device.type == "dlna"
                    assert device.hostname == "1.1.1.1"
                    assert device.status == "online"
                elif device.name == "Device 2":
                    device2_found = True
                    assert device.type == "transcreen"
                    assert device.hostname == "2.2.2.2"
                    assert device.status == "offline"
            
            assert device1_found
            assert device2_found
    
    def test_get_device_by_id(self, setup_test_db, mock_device_manager):
        """Test getting a device by ID."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a test device
            device = DeviceModel(
                name="Test Device",
                type="dlna",
                hostname="1.1.1.1",
                action_url="a1",
                friendly_name="f1",
                status="online"
            )
            
            db.add(device)
            db.commit()
            db.refresh(device)
            
            # Create a device service
            device_service = DeviceService(db, mock_device_manager)
            
            # Get the device by ID
            retrieved_device = device_service.get_device_by_id(device.id)
            
            # Check that the device is returned
            assert retrieved_device is not None
            assert retrieved_device.id == device.id
            assert retrieved_device.name == "Test Device"
            assert retrieved_device.type == "dlna"
            assert retrieved_device.hostname == "1.1.1.1"
            assert retrieved_device.status == "online"
    
    def test_create_device(self, setup_test_db, mock_device_manager):
        """Test creating a device."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a device service
            device_service = DeviceService(db, mock_device_manager)
            
            # Create a device
            device_data = DeviceCreate(
                name="New Device",
                type="dlna",
                hostname="3.3.3.3",
                action_url="a3",
                friendly_name="f3",
                status="disconnected",
                config={}
            )
            
            created_device = device_service.create_device(device_data)
            
            # Check that the device is created
            assert created_device is not None
            assert created_device.id is not None
            assert created_device.name == "New Device"
            assert created_device.type == "dlna"
            assert created_device.hostname == "3.3.3.3"
            assert created_device.status == "disconnected"
            
            # Check that the device is in the database
            db_device = db.query(DeviceModel).filter(DeviceModel.id == created_device.id).first()
            assert db_device is not None
            assert db_device.name == "New Device"
            
            mock_device_manager.register_device.assert_called_once()
    
    def test_update_device(self, setup_test_db, mock_device_manager):
        """Test updating a device."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a test device
            device = DeviceModel(
                name="Test Device Update",
                type="dlna",
                hostname="4.4.4.4",
                action_url="a4",
                friendly_name="f4",
                status="online"
            )
            
            db.add(device)
            db.commit()
            db.refresh(device)
            
            # Create a device service
            device_service = DeviceService(db, mock_device_manager)
            
            # Update the device
            update_data = DeviceUpdate(name="Updated Device", status="offline")
            
            updated_device = device_service.update_device(device.id, update_data)
            
            # Check that the device is updated
            assert updated_device is not None
            assert updated_device.id == device.id
            assert updated_device.name == "Updated Device"
            assert updated_device.status == "offline"
            
            # Check that the device is updated in the database
            db_device = db.query(DeviceModel).filter(DeviceModel.id == device.id).first()
            assert db_device is not None
            assert db_device.name == "Updated Device"
            assert db_device.status == "offline"
            
            mock_device_manager.update_device_registration.assert_called_once()
    
    def test_delete_device(self, setup_test_db, mock_device_manager):
        """Test deleting a device."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a test device
            device = DeviceModel(
                name="Test Device Delete",
                type="dlna",
                hostname="5.5.5.5",
                action_url="a5",
                friendly_name="f5",
                status="online"
            )
            
            db.add(device)
            db.commit()
            db.refresh(device)
            
            device_id = device.id
            
            # Create a device service
            device_service = DeviceService(db, mock_device_manager)
            
            # Delete the device
            deleted = device_service.delete_device(device_id)
            
            # Check that the device is deleted from the database
            db_device = db.query(DeviceModel).filter(DeviceModel.id == device_id).first()
            assert db_device is None
            
            mock_device_manager.unregister_device.assert_called_once()
    
    def test_load_devices_from_config(self, setup_test_db, mock_device_manager, tmp_file_factory):
        """Test loading devices from a config file."""
        SessionLocal = setup_test_db
        config_content = b'''
        {
            "devices": [
                {
                    "name": "Config Device",
                    "type": "dlna",
                    "hostname": "6.6.6.6",
                    "friendly_name": "f6",
                    "action_url": "a6",
                    "config": {"autoplay": true}
                }
            ]
        }
        '''
        config_file = tmp_file_factory(".json", config_content)

        with SessionLocal() as db:
            # Create a device service
            device_service = DeviceService(db, mock_device_manager)
            
            # Load devices from the config file
            loaded_devices = device_service.load_devices_from_config(config_file)
            
            # Check that devices are loaded
            assert len(loaded_devices) == 1
            
            # Check that the loaded device has the correct properties
            db_device = loaded_devices[0]
            assert db_device.name == "Config Device"
            assert db_device.type == "dlna"
            assert db_device.hostname == "6.6.6.6"
            assert db_device.friendly_name == "f6"
            assert db_device.action_url == "a6"
            assert db_device.config["autoplay"] is True
            
            mock_device_manager.register_device.assert_called_once()


class TestVideoService:
    """Tests for the VideoService class."""
    
    def test_get_videos(self, setup_test_db, mock_streaming_registry):
        """Test getting all videos."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create some test videos
            video1 = VideoModel(
                name="Video 1",
                path="/p1",
                file_name="f1.mp4",
                file_size=100
            )
            
            video2 = VideoModel(
                name="Video 2",
                path="/p2",
                file_name="f2.mp4",
                file_size=200
            )
            
            db.add_all([video1, video2])
            db.commit()
            
            # Create a video service
            video_service = VideoService(db, mock_streaming_registry)
            
            # Get all videos
            videos = video_service.get_videos()
            
            # Check that both videos are returned
            assert len(videos) == 2
            
            # Check that the videos have the correct properties
            video1_found = False
            video2_found = False
            for video in videos:
                if video.name == "Video 1":
                    video1_found = True
                    assert video.path == "/p1"
                    assert video.file_name == "f1.mp4"
                    assert video.file_size == 100
                elif video.name == "Video 2":
                    video2_found = True
                    assert video.path == "/p2"
                    assert video.file_name == "f2.mp4"
                    assert video.file_size == 200
            
            assert video1_found
            assert video2_found
    
    def test_get_video_by_id(self, setup_test_db, mock_streaming_registry):
        """Test getting a video by ID."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a test video
            video = VideoModel(
                name="Test Video",
                path="/p3",
                file_name="f3.mp4",
                file_size=300
            )
            
            db.add(video)
            db.commit()
            db.refresh(video)
            
            # Create a video service
            video_service = VideoService(db, mock_streaming_registry)
            
            # Get the video by ID
            retrieved_video = video_service.get_video_by_id(video.id)
            
            # Check that the video is returned
            assert retrieved_video is not None
            assert retrieved_video.id == video.id
            assert retrieved_video.name == "Test Video"
            assert retrieved_video.path == "/p3"
            assert retrieved_video.file_name == "f3.mp4"
            assert retrieved_video.file_size == 300
    
    def test_create_video(self, setup_test_db, mock_streaming_registry):
        """Test creating a video."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a video service
            video_service = VideoService(db, mock_streaming_registry)
            
            # Create a video
            video_data = VideoCreate(
                name="New Video",
                path="/p4",
                file_name="f4.mp4",
                file_size=400,
                duration=40.0,
                format="mp4",
                resolution="10x10",
                has_subtitle=False
            )
            
            created_video = video_service.create_video(video_data)
            
            # Check that the video is created
            assert created_video is not None
            assert created_video.id is not None
            assert created_video.name == "New Video"
            assert created_video.path == "/p4"
            assert created_video.file_size == 400
            assert created_video.duration == 40.0
            assert created_video.format == "mp4"
            assert created_video.resolution == "10x10"
            assert created_video.has_subtitle is False
    
    def test_update_video(self, setup_test_db, mock_streaming_registry):
        """Test updating a video."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a test video
            video = VideoModel(
                name="Test Video Update",
                path="/p5",
                file_name="f5.mp4",
                file_size=500
            )
            
            db.add(video)
            db.commit()
            db.refresh(video)
            
            # Create a video service
            video_service = VideoService(db, mock_streaming_registry)
            
            # Update the video
            update_data = VideoUpdate(name="Updated Video", duration=55.5)
            
            updated_video = video_service.update_video(video.id, update_data)
            
            # Check that the video is updated
            assert updated_video is not None
            assert updated_video.id == video.id
            assert updated_video.name == "Updated Video"
            assert updated_video.duration == 55.5
    
    def test_delete_video(self, setup_test_db, mock_streaming_registry):
        """Test deleting a video."""
        SessionLocal = setup_test_db
        with SessionLocal() as db:
            # Create a test video
            video = VideoModel(
                name="Test Video Delete",
                path="/p6",
                file_name="f6.mp4",
                file_size=600
            )
            
            db.add(video)
            db.commit()
            db.refresh(video)
            
            video_id = video.id
            
            # Create a video service
            video_service = VideoService(db, mock_streaming_registry)
            
            # Delete the video
            deleted = video_service.delete_video(video_id)
            
            # Check that the video is deleted from the database
            db_video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
            assert db_video is None
    
    @patch('services.video_service.scan_directory_for_videos')
    def test_scan_and_sync_videos(self, mock_scan, setup_test_db, mock_streaming_registry):
        SessionLocal = setup_test_db
        # Mock scan_directory_for_videos to return some video data
        mock_scan.return_value = [
            VideoCreate(name="Scan Video 1", path="/scan/v1.mp4", file_name="v1.mp4", file_size=100),
            VideoCreate(name="Scan Video 2", path="/scan/v2.mp4", file_name="v2.mp4", file_size=200),
        ]
        
        with SessionLocal() as db:
            # Add an existing video that should be kept
            existing_video = VideoModel(name="Existing Video", path="/scan/v1.mp4", file_name="v1.mp4", file_size=100)
            # Add a video that is no longer found and should be removed
            removed_video = VideoModel(name="Removed Video", path="/removed/v3.mp4", file_name="v3.mp4", file_size=300)
            db.add_all([existing_video, removed_video])
            db.commit()
            db.refresh(removed_video)
            removed_video_id = removed_video.id
            
            video_service = VideoService(db, mock_streaming_registry)
            added_count, removed_count = video_service.scan_and_sync_videos("/scan")

            mock_scan.assert_called_once_with("/scan")
            assert added_count == 1 # "Scan Video 2" should be added
            assert removed_count == 1 # "Removed Video" should be removed
            
            # Verify DB state
            videos_in_db = db.query(VideoModel).all()
            assert len(videos_in_db) == 2
            db_paths = {v.path for v in videos_in_db}
            assert "/scan/v1.mp4" in db_paths
            assert "/scan/v2.mp4" in db_paths
            assert "/removed/v3.mp4" not in db_paths
            assert db.query(VideoModel).filter(VideoModel.id == removed_video_id).first() is None
