import pytest
import os
from unittest.mock import patch, MagicMock, mock_open
import json

from services.device_service import DeviceService
from models.device import DeviceModel


@pytest.fixture
def device_service(test_db):
    """Create a DeviceService instance for testing"""
    return DeviceService(db=test_db)


def test_get_all_devices(device_service, test_db):
    """Test the get_all_devices method"""
    # Create test devices
    device1 = DeviceModel(
        name="test_device1",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Device 1",
        status="connected"
    )
    device2 = DeviceModel(
        name="test_device2",
        type="dlna",
        hostname="10.0.0.2",
        action_url="http://10.0.0.2/action",
        friendly_name="Test Device 2",
        status="disconnected"
    )
    test_db.add(device1)
    test_db.add(device2)
    test_db.commit()
    
    # Test the method
    devices, total = device_service.get_all_devices()
    
    assert total == 2
    assert len(devices) == 2
    assert devices[0].name == "test_device1"
    assert devices[1].name == "test_device2"


def test_get_device_by_id_found(device_service, test_db):
    """Test the get_device_by_id method with existing device"""
    # Create a test device
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
    
    # Test the method
    result = device_service.get_device_by_id(device.id)
    
    assert result is not None
    assert result.id == device.id
    assert result.name == "test_device"
    assert result.type == "dlna"
    assert result.hostname == "10.0.0.1"


def test_get_device_by_id_not_found(device_service, test_db):
    """Test the get_device_by_id method with non-existent device"""
    # Test the method with non-existent device
    result = device_service.get_device_by_id(999)
    
    assert result is None


def test_create_device_success(device_service, test_db):
    """Test the create_device method with valid data"""
    # Test data
    device_data = {
        "name": "new_device",
        "type": "dlna",
        "hostname": "10.0.0.3",
        "action_url": "http://10.0.0.3/action",
        "friendly_name": "New Device"
    }
    
    # Test the method
    result = device_service.create_device(device_data)
    
    assert result is not None
    assert result.name == "new_device"
    assert result.type == "dlna"
    assert result.hostname == "10.0.0.3"
    assert result.action_url == "http://10.0.0.3/action"
    assert result.friendly_name == "New Device"
    assert result.status == "disconnected"  # Default status
    
    # Verify the device was added to the database
    device = test_db.query(DeviceModel).filter(DeviceModel.name == "new_device").first()
    assert device is not None
    assert device.name == "new_device"


def test_create_device_invalid_data(device_service, test_db):
    """Test the create_device method with invalid data"""
    # Test with invalid data (missing required fields)
    device_data = {
        "name": "invalid_device"
        # Missing required fields
    }
    
    # Test the method
    with pytest.raises(ValueError):
        device_service.create_device(device_data)
    
    # Verify no device was added to the database
    device = test_db.query(DeviceModel).filter(DeviceModel.name == "invalid_device").first()
    assert device is None


def test_update_device_success(device_service, test_db):
    """Test the update_device method with valid data"""
    # Create a test device
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
    
    # Test data
    update_data = {
        "hostname": "10.0.0.5",
        "friendly_name": "Updated Device"
    }
    
    # Test the method
    result = device_service.update_device(device.id, update_data)
    
    assert result is not None
    assert result.id == device.id
    assert result.name == "test_device"  # Unchanged
    assert result.hostname == "10.0.0.5"  # Updated
    assert result.friendly_name == "Updated Device"  # Updated
    
    # Verify the device was updated in the database
    updated_device = test_db.query(DeviceModel).filter(DeviceModel.id == device.id).first()
    assert updated_device is not None
    assert updated_device.hostname == "10.0.0.5"
    assert updated_device.friendly_name == "Updated Device"


def test_update_device_not_found(device_service, test_db):
    """Test the update_device method with non-existent device"""
    # Test data
    update_data = {
        "hostname": "10.0.0.5",
        "friendly_name": "Updated Device"
    }
    
    # Test the method with non-existent device
    result = device_service.update_device(999, update_data)
    
    assert result is None


def test_delete_device_success(device_service, test_db):
    """Test the delete_device method with existing device"""
    # Create a test device
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
    
    # Test the method
    result = device_service.delete_device(device.id)
    
    assert result is True
    
    # Verify the device was deleted from the database
    deleted_device = test_db.query(DeviceModel).filter(DeviceModel.id == device.id).first()
    assert deleted_device is None


def test_delete_device_not_found(device_service, test_db):
    """Test the delete_device method with non-existent device"""
    # Test the method with non-existent device
    result = device_service.delete_device(999)
    
    assert result is False


@patch('core.device_manager.DeviceManager')
def test_discover_devices(mock_device_manager, device_service, test_db):
    """Test the discover_devices method"""
    # Mock the DeviceManager
    mock_manager = MagicMock()
    mock_device_manager.get_instance.return_value = mock_manager
    
    # Mock the discover method
    mock_manager.discover.return_value = [
        {
            "name": "discovered_device",
            "type": "dlna",
            "hostname": "10.0.0.10",
            "action_url": "http://10.0.0.10/action",
            "friendly_name": "Discovered Device"
        }
    ]
    
    # Test the method
    result = device_service.discover_devices()
    
    assert len(result) == 1
    assert result[0]["name"] == "discovered_device"
    assert result[0]["type"] == "dlna"
    assert result[0]["hostname"] == "10.0.0.10"
    mock_manager.discover.assert_called_once()


@patch('core.device_manager.DeviceManager')
def test_play_video_success(mock_device_manager, device_service, test_db):
    """Test the play_video method with success"""
    # Create a test device
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
    
    # Mock the DeviceManager
    mock_manager = MagicMock()
    mock_device_manager.get_instance.return_value = mock_manager
    
    # Mock the get_device method
    mock_device = MagicMock()
    mock_manager.get_device.return_value = mock_device
    
    # Mock the play_video method
    mock_device.play_video.return_value = True
    
    # Test the method
    result = device_service.play_video(device.id, "/path/to/video.mp4", loop=True)
    
    assert result is True
    mock_manager.get_device.assert_called_once_with(device.name)
    mock_device.play_video.assert_called_once_with("/path/to/video.mp4", loop=True)


@patch('core.device_manager.DeviceManager')
def test_play_video_device_not_found(mock_device_manager, device_service, test_db):
    """Test the play_video method with non-existent device"""
    # Mock the DeviceManager
    mock_manager = MagicMock()
    mock_device_manager.get_instance.return_value = mock_manager
    
    # Test the method with non-existent device
    result = device_service.play_video(999, "/path/to/video.mp4", loop=True)
    
    assert result is False
    mock_manager.get_device.assert_not_called()


@patch('core.device_manager.DeviceManager')
def test_play_video_device_not_in_manager(mock_device_manager, device_service, test_db):
    """Test the play_video method with device not in DeviceManager"""
    # Create a test device
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
    
    # Mock the DeviceManager
    mock_manager = MagicMock()
    mock_device_manager.get_instance.return_value = mock_manager
    
    # Mock the get_device method to return None
    mock_manager.get_device.return_value = None
    
    # Test the method
    result = device_service.play_video(device.id, "/path/to/video.mp4", loop=True)
    
    assert result is False
    mock_manager.get_device.assert_called_once_with(device.name)


@patch('core.device_manager.DeviceManager')
def test_stop_video_success(mock_device_manager, device_service, test_db):
    """Test the stop_video method with success"""
    # Create a test device
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
    
    # Mock the DeviceManager
    mock_manager = MagicMock()
    mock_device_manager.get_instance.return_value = mock_manager
    
    # Mock the get_device method
    mock_device = MagicMock()
    mock_manager.get_device.return_value = mock_device
    
    # Mock the stop method
    mock_device.stop.return_value = True
    
    # Test the method
    result = device_service.stop_video(device.id)
    
    assert result is True
    mock_manager.get_device.assert_called_once_with(device.name)
    mock_device.stop.assert_called_once()


@patch('core.device_manager.DeviceManager')
def test_pause_video_success(mock_device_manager, device_service, test_db):
    """Test the pause_video method with success"""
    # Create a test device
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
    
    # Mock the DeviceManager
    mock_manager = MagicMock()
    mock_device_manager.get_instance.return_value = mock_manager
    
    # Mock the get_device method
    mock_device = MagicMock()
    mock_manager.get_device.return_value = mock_device
    
    # Mock the pause method
    mock_device.pause.return_value = True
    
    # Test the method
    result = device_service.pause_video(device.id)
    
    assert result is True
    mock_manager.get_device.assert_called_once_with(device.name)
    mock_device.pause.assert_called_once()


@patch('core.device_manager.DeviceManager')
def test_seek_video_success(mock_device_manager, device_service, test_db):
    """Test the seek_video method with success"""
    # Create a test device
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
    
    # Mock the DeviceManager
    mock_manager = MagicMock()
    mock_device_manager.get_instance.return_value = mock_manager
    
    # Mock the get_device method
    mock_device = MagicMock()
    mock_manager.get_device.return_value = mock_device
    
    # Mock the seek method
    mock_device.seek.return_value = True
    
    # Test the method
    result = device_service.seek_video(device.id, "00:01:30")
    
    assert result is True
    mock_manager.get_device.assert_called_once_with(device.name)
    mock_device.seek.assert_called_once_with("00:01:30")


@patch('builtins.open', new_callable=mock_open, read_data='{"devices": [{"name": "config_device", "type": "dlna", "hostname": "10.0.0.100"}]}')
def test_load_devices_from_config_success(mock_file, device_service, test_db):
    """Test the load_devices_from_config method with success"""
    # Mock os.path.exists to return True
    with patch('os.path.exists', return_value=True):
        # Test the method
        result = device_service.load_devices_from_config("/path/to/config.json")
        
        assert len(result) == 1
        assert result[0]["name"] == "config_device"
        assert result[0]["type"] == "dlna"
        assert result[0]["hostname"] == "10.0.0.100"
        mock_file.assert_called_once_with("/path/to/config.json", "r")
        
        # Verify the device was added to the database
        device = test_db.query(DeviceModel).filter(DeviceModel.name == "config_device").first()
        assert device is not None
        assert device.name == "config_device"
        assert device.type == "dlna"
        assert device.hostname == "10.0.0.100"


@patch('builtins.open', new_callable=mock_open)
def test_save_devices_to_config_success(mock_file, device_service, test_db):
    """Test the save_devices_to_config method with success"""
    # Create test devices
    device1 = DeviceModel(
        name="test_device1",
        type="dlna",
        hostname="10.0.0.1",
        action_url="http://10.0.0.1/action",
        friendly_name="Test Device 1",
        status="connected"
    )
    device2 = DeviceModel(
        name="test_device2",
        type="dlna",
        hostname="10.0.0.2",
        action_url="http://10.0.0.2/action",
        friendly_name="Test Device 2",
        status="disconnected"
    )
    test_db.add(device1)
    test_db.add(device2)
    test_db.commit()
    
    # Test the method
    result = device_service.save_devices_to_config("/path/to/config.json")
    
    assert result is True
    mock_file.assert_called_once_with("/path/to/config.json", "w")
    
    # Check that the correct JSON was written
    handle = mock_file()
    handle.write.assert_called_once()
    written_data = handle.write.call_args[0][0]
    config_data = json.loads(written_data)
    
    assert "devices" in config_data
    assert len(config_data["devices"]) == 2
    assert config_data["devices"][0]["name"] == "test_device1"
    assert config_data["devices"][1]["name"] == "test_device2"
