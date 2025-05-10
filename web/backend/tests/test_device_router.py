import pytest
import json
from unittest.mock import patch, MagicMock
import os

def test_get_devices(client, test_db):
    """Test the GET /api/devices/ endpoint"""
    response = client.get("/api/devices/")
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert "total" in data
    assert isinstance(data["devices"], list)


def test_get_device_not_found(client, test_db):
    """Test the GET /api/devices/{device_id} endpoint with non-existent device"""
    response = client.get("/api/devices/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_device_found(client, test_db):
    """Test the GET /api/devices/{device_id} endpoint with existing device"""
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
    test_db.refresh(device)
    
    # Test with existing device
    response = client.get(f"/api/devices/{device.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_device"
    assert data["type"] == "dlna"
    assert data["hostname"] == "10.0.0.1"
    assert data["status"] == "connected"


@patch('services.device_service.DeviceService.discover_devices')
def test_discover_devices_get(mock_discover, client, test_db):
    """Test the GET /api/devices/discover endpoint"""
    # Mock the discover_devices method
    mock_discover.return_value = [
        {
            "name": "discovered_device",
            "type": "dlna",
            "hostname": "10.0.0.1"
        }
    ]
    
    response = client.get("/api/devices/discover")
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert "total" in data
    mock_discover.assert_called_once()


@patch('services.device_service.DeviceService.discover_devices')
def test_discover_devices_post(mock_discover, client, test_db):
    """Test the POST /api/devices/discover endpoint"""
    # Mock the discover_devices method
    mock_discover.return_value = [
        {
            "name": "discovered_device",
            "type": "dlna",
            "hostname": "10.0.0.1"
        }
    ]
    
    response = client.post("/api/devices/discover")
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert "total" in data
    mock_discover.assert_called_once()


@patch('services.device_service.DeviceService.create_device')
def test_create_device_success(mock_create, client, test_db):
    """Test the POST /api/devices/ endpoint with valid data"""
    # Mock the create_device method
    mock_create.return_value = {
        "id": 1,
        "name": "new_device",
        "type": "dlna",
        "hostname": "10.0.0.2",
        "action_url": "http://10.0.0.2/action",
        "friendly_name": "New Device",
        "status": "connected"
    }
    
    # Test create endpoint
    device_data = {
        "name": "new_device",
        "type": "dlna",
        "hostname": "10.0.0.2",
        "action_url": "http://10.0.0.2/action",
        "friendly_name": "New Device"
    }
    response = client.post("/api/devices/", json=device_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "new_device"
    assert data["type"] == "dlna"
    mock_create.assert_called_once()


@patch('services.device_service.DeviceService.create_device')
def test_create_device_error(mock_create, client, test_db):
    """Test the POST /api/devices/ endpoint with invalid data"""
    # Mock the create_device method to raise an error
    mock_create.side_effect = ValueError("Invalid device data")
    
    # Test create endpoint with invalid data
    device_data = {
        "name": "invalid_device",
        "type": "invalid_type"  # Missing required fields
    }
    response = client.post("/api/devices/", json=device_data)
    assert response.status_code == 400
    assert "Invalid device data" in response.json()["detail"]
    mock_create.assert_called_once()


@patch('services.device_service.DeviceService.update_device')
def test_update_device_success(mock_update, client, test_db):
    """Test the PUT /api/devices/{device_id} endpoint with valid data"""
    # Mock the update_device method
    mock_update.return_value = {
        "id": 1,
        "name": "updated_device",
        "type": "dlna",
        "hostname": "10.0.0.3",
        "action_url": "http://10.0.0.3/action",
        "friendly_name": "Updated Device",
        "status": "connected"
    }
    
    # Test update endpoint
    update_data = {
        "hostname": "10.0.0.3",
        "friendly_name": "Updated Device"
    }
    response = client.put("/api/devices/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["hostname"] == "10.0.0.3"
    assert data["friendly_name"] == "Updated Device"
    mock_update.assert_called_once_with(1, update_data)


@patch('services.device_service.DeviceService.update_device')
def test_update_device_not_found(mock_update, client, test_db):
    """Test the PUT /api/devices/{device_id} endpoint with non-existent device"""
    # Mock the update_device method to return None (device not found)
    mock_update.return_value = None
    
    # Test update endpoint with non-existent device
    update_data = {
        "hostname": "10.0.0.3",
        "friendly_name": "Updated Device"
    }
    response = client.put("/api/devices/999", json=update_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    mock_update.assert_called_once_with(999, update_data)


@patch('services.device_service.DeviceService.delete_device')
def test_delete_device_success(mock_delete, client, test_db):
    """Test the DELETE /api/devices/{device_id} endpoint with existing device"""
    # Mock the delete_device method to return True (success)
    mock_delete.return_value = True
    
    # Test delete endpoint
    response = client.delete("/api/devices/1")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "deleted" in data["message"].lower()
    mock_delete.assert_called_once_with(1)


@patch('services.device_service.DeviceService.delete_device')
def test_delete_device_not_found(mock_delete, client, test_db):
    """Test the DELETE /api/devices/{device_id} endpoint with non-existent device"""
    # Mock the delete_device method to return False (device not found)
    mock_delete.return_value = False
    
    # Test delete endpoint with non-existent device
    response = client.delete("/api/devices/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    mock_delete.assert_called_once_with(999)


@patch('services.device_service.DeviceService.play_video')
@patch('services.video_service.VideoService.get_video_by_id')
def test_play_video_success(mock_get_video, mock_play, client, test_db):
    """Test the POST /api/devices/{device_id}/play endpoint with valid data"""
    # Create a device in the DB
    from models.device import DeviceModel
    device = DeviceModel(
        name="test_play_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Play Device",
        status="connected"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    
    # Mock the get_video_by_id method
    mock_video = MagicMock()
    mock_video.id = 1
    mock_video.path = "/path/to/test_video.mp4"
    mock_get_video.return_value = mock_video
    
    # Mock the play_video method to return True (success)
    mock_play.return_value = True
    
    # Create a temporary file to simulate the video file
    with open("/tmp/test_video.mp4", "w") as f:
        f.write("test video content")
    
    # Patch os.path.exists to return True for the video path
    with patch('os.path.exists', return_value=True):
        # Test play endpoint
        response = client.post(f"/api/devices/{device.id}/play", json={"video_id": 1, "loop": True})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "playing" in data["message"].lower()
        mock_get_video.assert_called_once_with(1)
        mock_play.assert_called_once_with(device.id, mock_video.path, True)
    
    # Clean up
    if os.path.exists("/tmp/test_video.mp4"):
        os.remove("/tmp/test_video.mp4")


@patch('services.device_service.DeviceService.play_video')
@patch('services.video_service.VideoService.get_video_by_id')
def test_play_video_device_not_found(mock_get_video, mock_play, client, test_db):
    """Test the POST /api/devices/{device_id}/play endpoint with non-existent device"""
    # Mock the get_video_by_id method
    mock_video = MagicMock()
    mock_video.id = 1
    mock_video.path = "/path/to/test_video.mp4"
    mock_get_video.return_value = mock_video
    
    # Test play endpoint with non-existent device
    response = client.post("/api/devices/999/play", json={"video_id": 1, "loop": False})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    mock_get_video.assert_called_once_with(1)
    mock_play.assert_not_called()


@patch('services.device_service.DeviceService.play_video')
@patch('services.video_service.VideoService.get_video_by_id')
def test_play_video_video_not_found(mock_get_video, mock_play, client, test_db):
    """Test the POST /api/devices/{device_id}/play endpoint with non-existent video"""
    # Create a device in the DB
    from models.device import DeviceModel
    device = DeviceModel(
        name="test_play_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Play Device",
        status="connected"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    
    # Mock the get_video_by_id method to return None (video not found)
    mock_get_video.return_value = None
    
    # Test play endpoint with non-existent video
    response = client.post(f"/api/devices/{device.id}/play", json={"video_id": 999, "loop": False})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    mock_get_video.assert_called_once_with(999)
    mock_play.assert_not_called()


@patch('services.device_service.DeviceService.play_video')
@patch('services.video_service.VideoService.get_video_by_id')
def test_play_video_file_not_found(mock_get_video, mock_play, client, test_db):
    """Test the POST /api/devices/{device_id}/play endpoint with non-existent video file"""
    # Create a device in the DB
    from models.device import DeviceModel
    device = DeviceModel(
        name="test_play_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Play Device",
        status="connected"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    
    # Mock the get_video_by_id method
    mock_video = MagicMock()
    mock_video.id = 1
    mock_video.path = "/path/to/nonexistent_video.mp4"
    mock_get_video.return_value = mock_video
    
    # Patch os.path.exists to return False for the video path
    with patch('os.path.exists', return_value=False):
        # Test play endpoint with non-existent video file
        response = client.post(f"/api/devices/{device.id}/play", json={"video_id": 1, "loop": False})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        mock_get_video.assert_called_once_with(1)
        mock_play.assert_not_called()


@patch('services.device_service.DeviceService.play_video')
@patch('services.video_service.VideoService.get_video_by_id')
def test_play_video_play_failed(mock_get_video, mock_play, client, test_db):
    """Test the POST /api/devices/{device_id}/play endpoint with play failure"""
    # Create a device in the DB
    from models.device import DeviceModel
    device = DeviceModel(
        name="test_play_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Play Device",
        status="connected"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    
    # Mock the get_video_by_id method
    mock_video = MagicMock()
    mock_video.id = 1
    mock_video.path = "/path/to/test_video.mp4"
    mock_get_video.return_value = mock_video
    
    # Mock the play_video method to return False (failure)
    mock_play.return_value = False
    
    # Patch os.path.exists to return True for the video path
    with patch('os.path.exists', return_value=True):
        # Test play endpoint with play failure
        response = client.post(f"/api/devices/{device.id}/play", json={"video_id": 1, "loop": False})
        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()
        mock_get_video.assert_called_once_with(1)
        mock_play.assert_called_once_with(device.id, mock_video.path, False)


@patch('services.device_service.DeviceService.stop_video')
def test_stop_video_success(mock_stop, client, test_db):
    """Test the POST /api/devices/{device_id}/stop endpoint with success"""
    # Create a device in the DB
    from models.device import DeviceModel
    device = DeviceModel(
        name="test_stop_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Stop Device",
        status="connected"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    
    # Mock the stop_video method to return True (success)
    mock_stop.return_value = True
    
    # Test stop endpoint
    response = client.post(f"/api/devices/{device.id}/stop")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "stopped" in data["message"].lower()
    mock_stop.assert_called_once_with(device.id)


@patch('services.device_service.DeviceService.stop_video')
def test_stop_video_failure(mock_stop, client, test_db):
    """Test the POST /api/devices/{device_id}/stop endpoint with failure"""
    # Create a device in the DB
    from models.device import DeviceModel
    device = DeviceModel(
        name="test_stop_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Stop Device",
        status="connected"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    
    # Mock the stop_video method to return False (failure)
    mock_stop.return_value = False
    
    # Test stop endpoint with failure
    response = client.post(f"/api/devices/{device.id}/stop")
    assert response.status_code == 500
    assert "failed" in response.json()["detail"].lower()
    mock_stop.assert_called_once_with(device.id)


@patch('services.device_service.DeviceService.pause_video')
def test_pause_video_success(mock_pause, client, test_db):
    """Test the POST /api/devices/{device_id}/pause endpoint with success"""
    # Create a device in the DB
    from models.device import DeviceModel
    device = DeviceModel(
        name="test_pause_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Pause Device",
        status="connected"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    
    # Mock the pause_video method to return True (success)
    mock_pause.return_value = True
    
    # Test pause endpoint
    response = client.post(f"/api/devices/{device.id}/pause")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "paused" in data["message"].lower()
    mock_pause.assert_called_once_with(device.id)


@patch('services.device_service.DeviceService.pause_video')
def test_pause_video_failure(mock_pause, client, test_db):
    """Test the POST /api/devices/{device_id}/pause endpoint with failure"""
    # Create a device in the DB
    from models.device import DeviceModel
    device = DeviceModel(
        name="test_pause_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Pause Device",
        status="connected"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    
    # Mock the pause_video method to return False (failure)
    mock_pause.return_value = False
    
    # Test pause endpoint with failure
    response = client.post(f"/api/devices/{device.id}/pause")
    assert response.status_code == 500
    assert "failed" in response.json()["detail"].lower()
    mock_pause.assert_called_once_with(device.id)


@patch('services.device_service.DeviceService.seek_video')
def test_seek_video_success(mock_seek, client, test_db):
    """Test the POST /api/devices/{device_id}/seek endpoint with success"""
    # Create a device in the DB
    from models.device import DeviceModel
    device = DeviceModel(
        name="test_seek_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Seek Device",
        status="connected"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    
    # Mock the seek_video method to return True (success)
    mock_seek.return_value = True
    
    # Test seek endpoint
    response = client.post(f"/api/devices/{device.id}/seek?position=00:01:30")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "seeked" in data["message"].lower()
    mock_seek.assert_called_once_with(device.id, "00:01:30")


@patch('services.device_service.DeviceService.seek_video')
def test_seek_video_failure(mock_seek, client, test_db):
    """Test the POST /api/devices/{device_id}/seek endpoint with failure"""
    # Create a device in the DB
    from models.device import DeviceModel
    device = DeviceModel(
        name="test_seek_device",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Seek Device",
        status="connected"
    )
    test_db.add(device)
    test_db.commit()
    test_db.refresh(device)
    
    # Mock the seek_video method to return False (failure)
    mock_seek.return_value = False
    
    # Test seek endpoint with failure
    response = client.post(f"/api/devices/{device.id}/seek?position=00:01:30")
    assert response.status_code == 500
    assert "failed" in response.json()["detail"].lower()
    mock_seek.assert_called_once_with(device.id, "00:01:30")


@patch('services.device_service.DeviceService.load_devices_from_config')
def test_load_devices_from_config_success(mock_load, client, test_db):
    """Test the POST /api/devices/load-config endpoint with success"""
    # Mock the load_devices_from_config method
    mock_load.return_value = [
        {
            "id": 1,
            "name": "config_device",
            "type": "dlna",
            "hostname": "10.0.0.1",
            "action_url": "http://10.0.0.1/action",
            "friendly_name": "Config Device",
            "status": "connected"
        }
    ]
    
    # Patch os.path.exists and os.path.isabs to return True
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isabs', return_value=True):
        # Test load-config endpoint
        response = client.post("/api/devices/load-config?config_file=/path/to/config.json")
        assert response.status_code == 200
        data = response.json()
        assert "devices" in data
        assert "total" in data
        assert len(data["devices"]) == 1
        assert data["devices"][0]["name"] == "config_device"
        mock_load.assert_called_once_with("/path/to/config.json")


@patch('services.device_service.DeviceService.load_devices_from_config')
def test_load_devices_from_config_file_not_found(mock_load, client, test_db):
    """Test the POST /api/devices/load-config endpoint with non-existent config file"""
    # Patch os.path.exists to return False
    with patch('os.path.exists', return_value=False), \
         patch('os.path.isabs', return_value=True):
        # Test load-config endpoint with non-existent config file
        response = client.post("/api/devices/load-config?config_file=/path/to/nonexistent.json")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        mock_load.assert_not_called()


@patch('services.device_service.DeviceService.save_devices_to_config')
def test_save_devices_to_config_success(mock_save, client, test_db):
    """Test the POST /api/devices/save-config endpoint with success"""
    # Mock the save_devices_to_config method to return True (success)
    mock_save.return_value = True
    
    # Test save-config endpoint
    response = client.post("/api/devices/save-config?config_file=/path/to/config.json")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "saved" in data["message"].lower()
    mock_save.assert_called_once_with("/path/to/config.json")


@patch('services.device_service.DeviceService.save_devices_to_config')
def test_save_devices_to_config_failure(mock_save, client, test_db):
    """Test the POST /api/devices/save-config endpoint with failure"""
    # Mock the save_devices_to_config method to return False (failure)
    mock_save.return_value = False
    
    # Test save-config endpoint with failure
    response = client.post("/api/devices/save-config?config_file=/path/to/config.json")
    assert response.status_code == 500
    assert "failed" in response.json()["detail"].lower()
    mock_save.assert_called_once_with("/path/to/config.json")
