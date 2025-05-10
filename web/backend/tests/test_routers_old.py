import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock

# Device router tests
def test_get_devices(client, test_db):
    """Test the GET /api/devices/ endpoint"""
    response = client.get("/api/devices/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_device(client, test_db):
    """Test the GET /api/devices/{device_name} endpoint"""
    # First test with non-existent device
    response = client.get("/api/devices/non_existent_device")
    assert response.status_code == 404
    
    # Create a device in the DB
    from models.device import DeviceModel
    device = DeviceModel(
        name="test_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Device",
        status="connected"
    )
    test_db.add(device)
    test_db.commit()
    
    # Test with existing device
    response = client.get("/api/devices/test_device")
    assert response.status_code == 200
    assert response.json()["name"] == "test_device"


@patch('services.device_service.DeviceService.discover_devices')
def test_discover_devices(mock_discover, client, test_db):
    """Test the POST /api/devices/discover endpoint"""
    # Mock the discover_devices method
    mock_discover.return_value = [
        {
            "name": "discovered_device",
            "type": "dlna",
            "hostname": "10.0.0.1"
        }
    ]
    
    # Corrected to use client.get for the GET endpoint
    response = client.get("/api/devices/discover") 
    assert response.status_code == 200
    # Assert the structure returned by the GET endpoint
    data = response.json()
    assert "devices" in data
    assert "total" in data
    # Further assertions can be added based on mock_discover return value if needed
    mock_discover.assert_called_once()


@patch('services.device_service.DeviceService.play_video')
def test_play_video(mock_play, client, test_db):
    """Test the POST /api/devices/{device_id}/play endpoint"""
    # Mock the play_video method
    mock_play.return_value = True
    
    # Create a device and video in the DB
    from models.device import DeviceModel
    from models.video import VideoModel
    device = DeviceModel(name="test_play_device")
    video = VideoModel(
        name="test_play_video.mp4",
        path="/path/to/test_play_video.mp4",
        file_size=1024,
        duration=60.0
    )
    test_db.add(device)
    test_db.add(video)
    test_db.commit()
    test_db.refresh(device)
    test_db.refresh(video)
    
    # Test play endpoint
    response = client.post(f"/api/devices/{device.id}/play?video_id={video.id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_play.assert_called_once_with(device.id, video.id, loop=False)
    
    # Test with looping
    response = client.post(f"/api/devices/{device.id}/play?video_id={video.id}&loop=true")
    assert response.status_code == 200
    mock_play.assert_called_with(device.id, video.id, loop=True)


# Video router tests
def test_get_videos(client, test_db):
    """Test the GET /api/videos/ endpoint"""
    response = client.get("/api/videos/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_video(client, test_db):
    """Test the GET /api/videos/{video_id} endpoint"""
    # First test with non-existent video
    response = client.get("/api/videos/999")
    assert response.status_code == 404
    
    # Create a video in the DB
    from models.video import VideoModel
    video = VideoModel(
        name="test_get_video.mp4",
        path="/path/to/test_get_video.mp4",
        file_size=1024,
        duration=60.0
    )
    test_db.add(video)
    test_db.commit()
    test_db.refresh(video)
    
    # Test get endpoint for created video
    response = client.get(f"/api/videos/{video.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == video.id
    assert data["name"] == "test_get_video.mp4"
    assert data["file_size"] == 1024


@patch('services.video_service.VideoService.create_video')
def test_upload_video(mock_create, client, test_db):
    """Test the POST /api/videos/ endpoint"""
    # Mock the create_video method
    mock_create.return_value = {
        "id": 1,
        "name": "test_upload.mp4",
        "path": "/path/to/test_upload.mp4",
        "size": 1024,
        "duration": 60.0
    }
    
    # Create a temporary file for upload
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp:
        temp.write(b"fake video content")
        temp_path = temp.name
    
    try:
        # Test upload endpoint
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/api/videos/",
                files={"file": ("test_upload.mp4", f, "video/mp4")}
            )
        
        assert response.status_code == 200
        assert response.json()["name"] == "test_upload.mp4"
        mock_create.assert_called_once()
    
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)


@patch('services.video_service.VideoService.delete_video')
def test_delete_video(mock_delete, client, test_db):
    """Test the DELETE /api/videos/{video_id} endpoint"""
    # Mock the delete_video method
    mock_delete.return_value = True
    
    # Create a video in the DB
    from models.video import VideoModel
    video = VideoModel(
        name="test_delete_video.mp4",
        path="/path/to/test_delete_video.mp4",
        file_size=1024,
        duration=60.0
    )
    test_db.add(video)
    test_db.commit()
    test_db.refresh(video)
    
    # Test delete endpoint
    response = client.delete(f"/api/videos/{video.id}")
    assert response.status_code == 200
    assert response.json().get("success") is True
    mock_delete.assert_called_once_with(video.id)
    
    # Test deleting non-existent video
    mock_delete.reset_mock()
    mock_delete.return_value = False
    response = client.delete("/api/videos/999")
    assert response.status_code == 404
    mock_delete.assert_called_once_with(999)


# Streaming router tests
@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_get_streaming_stats(mock_registry, client):
    """Test the GET /api/streaming/stats endpoint"""
    # Mock the registry and its methods
    instance = MagicMock()
    instance.get_stats.return_value = {"active_sessions": 1, "total_bytes": 1024}
    mock_registry.return_value = instance
    
    # Test the endpoint
    response = client.get("/api/streaming/stats")
    assert response.status_code == 200
    assert response.json() == {"active_sessions": 1, "total_bytes": 1024}
    instance.get_stats.assert_called_once()


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_get_streaming_health(mock_registry, client):
    """Test the GET /api/streaming/health endpoint"""
    # Mock the registry and its methods
    instance = MagicMock()
    instance.get_health.return_value = {"status": "ok", "errors": 0}
    mock_registry.return_value = instance
    
    # Test the endpoint
    response = client.get("/api/streaming/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "errors": 0}
    instance.get_health.assert_called_once()


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_get_active_sessions(mock_registry, client):
    """Test the GET /api/streaming/sessions endpoint"""
    # Mock the registry and its methods
    instance = MagicMock()
    instance.get_active_sessions.return_value = [
        {"session_id": "1", "device": "dev1", "video": "vid1", "bytes_transferred": 512}
    ]
    mock_registry.return_value = instance
    
    # Test the endpoint
    response = client.get("/api/streaming/sessions")
    assert response.status_code == 200
    assert response.json() == [
        {"session_id": "1", "device": "dev1", "video": "vid1", "bytes_transferred": 512}
    ]
    instance.get_active_sessions.assert_called_once() 