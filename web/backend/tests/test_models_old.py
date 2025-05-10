import pytest
from datetime import datetime
from models.device import DeviceModel
from models.video import VideoModel


def test_device_model_create(test_db):
    """Test creating a device model"""
    # Create a device
    device = DeviceModel(
        name="test_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Device",
        status="connected"
    )
    
    # Add to database
    test_db.add(device)
    test_db.commit()
    
    # Retrieve from database
    db_device = test_db.query(DeviceModel).filter_by(name="test_device").first()
    
    # Verify attributes
    assert db_device.name == "test_device"
    assert db_device.type == "dlna"
    assert db_device.hostname == "10.0.0.1"
    assert db_device.action_url == "http://10.0.0.1/action"
    assert db_device.friendly_name == "Test Device"
    assert db_device.status == "connected"


def test_device_model_update(test_db):
    """Test updating a device model"""
    # Create a device
    device = DeviceModel(
        name="test_device_update",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Device",
        status="disconnected"
    )
    
    # Add to database
    test_db.add(device)
    test_db.commit()
    
    # Update the device
    device.status = "connected"
    device.hostname = "10.0.0.2"
    test_db.commit()
    
    # Retrieve from database
    db_device = test_db.query(DeviceModel).filter_by(name="test_device_update").first()
    
    # Verify updated attributes
    assert db_device.status == "connected"
    assert db_device.hostname == "10.0.0.2"


def test_device_model_delete(test_db):
    """Test deleting a device model"""
    # Create a device
    device = DeviceModel(
        name="test_device_delete",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Device",
        status="connected"
    )
    
    # Add to database
    test_db.add(device)
    test_db.commit()
    
    # Delete the device
    test_db.delete(device)
    test_db.commit()
    
    # Try to retrieve from database
    db_device = test_db.query(DeviceModel).filter_by(name="test_device_delete").first()
    
    # Verify it's gone
    assert db_device is None


def test_video_model_create(test_db):
    """Test creating a video model"""
    # Create a video
    video = VideoModel(
        name="test_video.mp4",
        path="/path/to/test_video.mp4",
        file_size=1024,
        duration=60.0
    )
    
    # Add to database
    test_db.add(video)
    test_db.commit()
    
    # Retrieve from database
    db_video = test_db.query(VideoModel).filter_by(name="test_video.mp4").first()
    
    # Verify attributes
    assert db_video.name == "test_video.mp4"
    assert db_video.path == "/path/to/test_video.mp4"
    assert db_video.file_size == 1024
    assert db_video.duration == 60.0
    assert db_video.created_at is not None


def test_video_model_update(test_db):
    """Test updating a video model"""
    # Create a video
    video = VideoModel(
        name="test_video_update.mp4",
        path="/path/to/test_video_update.mp4",
        file_size=1024,
        duration=60.0
    )
    
    # Add to database
    test_db.add(video)
    test_db.commit()
    
    # Update the video
    video.file_size = 2048
    video.duration = 120.0
    test_db.commit()
    
    # Retrieve from database
    db_video = test_db.query(VideoModel).filter_by(name="test_video_update.mp4").first()
    
    # Verify updated attributes
    assert db_video.file_size == 2048
    assert db_video.duration == 120.0


def test_video_model_delete(test_db):
    """Test deleting a video model"""
    # Create a video
    video = VideoModel(
        name="test_video_delete.mp4",
        path="/path/to/test_video_delete.mp4",
        file_size=1024,
        duration=60.0
    )
    
    # Add to database
    test_db.add(video)
    test_db.commit()
    
    # Delete the video
    test_db.delete(video)
    test_db.commit()
    
    # Try to retrieve from database
    db_video = test_db.query(VideoModel).filter_by(name="test_video_delete.mp4").first()
    
    # Verify it's gone
    assert db_video is None 