"""
Tests for core modules.
"""
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from core.device import Device
from tests_backend.mock_device import MockDevice
from tests_backend.mock_streaming_session import MockStreamingSession
from core.device_manager import DeviceManager
from core.streaming_registry import StreamingSessionRegistry
from core.streaming_session import StreamingSession
from core.config_service import ConfigService


class TestDeviceClass:
    """Tests for the Device base class."""
    
    def test_device_creation(self):
        """Test creating a device."""
        device = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action",
            "location": "http://127.0.0.1:8000/location",
            "control_url": "http://127.0.0.1:8000/control"
        })
        
        assert device.name == "Test Device"
        assert device.hostname == "127.0.0.1"
        assert device.type == "test"
        assert device.action_url == "http://127.0.0.1:8000/action"
        assert device.control_url == "http://127.0.0.1:8000/control"
    
    def test_device_properties(self):
        """Test device properties."""
        device = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        
        # Test default properties
        assert device.status == "disconnected"
        
        # Set and test status
        device.status = "online"
        assert device.status == "online"
    
    def test_device_to_dict(self):
        """Test converting a device to a dictionary."""
        device = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        
        device_dict = device.to_dict()
        assert device_dict["name"] == "Test Device"
        assert device_dict["hostname"] == "127.0.0.1"
        assert device_dict["type"] == "test"
        assert device_dict["action_url"] == "http://127.0.0.1:8000/action"
    
    def test_device_equality(self):
        """Test device equality."""
        device1 = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        
        device2 = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        
        device3 = MockDevice({
            "device_name": "Another Device",
            "hostname": "192.168.1.100",
            "type": "test",
            "action_url": "http://192.168.1.100:8000/action"
        })
        
        assert device1 == device2
        assert device1 != device3


class TestDeviceManager:
    """Tests for the DeviceManager class."""
    
    def test_device_manager_init(self):
        """Test initializing the device manager."""
        manager = DeviceManager()
        assert isinstance(manager.devices, dict)
        assert len(manager.devices) == 0
    
    def test_add_device(self):
        """Test adding a device."""
        manager = DeviceManager()
        
        device = MockDevice({
            "name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        
        # Use register_device instead of add_device
        manager.register_device({"device_name": "Test Device", "type": "dlna", "hostname": "127.0.0.1", "action_url": "http://127.0.0.1:8000/action"})
        assert "Test Device" in manager.devices
    
    def test_get_device(self):
        """Test getting a device."""
        manager = DeviceManager()
        
        # Register a device
        manager.register_device({"device_name": "Test Device", "type": "dlna", "hostname": "127.0.0.1", "action_url": "http://127.0.0.1:8000/action"})
        
        # Test get_device
        device = manager.get_device("Test Device")
        assert device is not None
        assert device.name == "Test Device"
        assert manager.get_device("Nonexistent Device") is None
    
    def test_remove_device(self):
        """Test removing a device."""
        manager = DeviceManager()
        
        # Register a device
        manager.register_device({"device_name": "Test Device", "type": "dlna", "hostname": "127.0.0.1", "action_url": "http://127.0.0.1:8000/action"})
        assert "Test Device" in manager.devices
        
        # Test unregister_device
        manager.unregister_device("Test Device")
        assert "Test Device" not in manager.devices
    
    @patch('core.device_manager.threading.Thread')
    def test_start_discovery(self, mock_thread):
        """Test starting device discovery."""
        manager = DeviceManager()
        
        # Mock the thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Start discovery
        manager.start_discovery()
        
        # Check that the thread was started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        
        # Check that discovery is running
        assert manager.discovery_running is True
    
    @patch('core.device_manager.threading.Thread')
    def test_stop_discovery(self, mock_thread):
        """Test stopping device discovery."""
        manager = DeviceManager()
        
        # Mock the thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Start discovery
        manager.start_discovery()
        
        # Stop discovery
        manager.stop_discovery()
        
        # Check that discovery is not running
        assert manager.discovery_running is False


class TestStreamingSession:
    """Tests for the StreamingSession class."""
    
    def test_session_creation(self):
        """Test creating a streaming session."""
        device = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        video_path = "/path/to/video.mp4"
        
        session = MockStreamingSession(
            device=device,
            video_path=video_path
        )
        
        assert session.device.name == "Test Device"
        assert session.video_path == video_path
        assert session.status == "playing"
        assert session.session_id is not None
    
    def test_session_update_status(self):
        """Test updating the session status."""
        device = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        video_path = "/path/to/video.mp4"
        
        session = MockStreamingSession(
            device=device,
            video_path=video_path
        )
        
        # Initial status is "playing"
        assert session.status == "playing"
        
        # Update the status
        session.update_status("paused")
        assert session.status == "paused"
        
        # Update again
        session.update_status("stopped")
        assert session.status == "stopped"
    
    def test_session_to_dict(self):
        """Test converting a session to a dictionary."""
        device = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        video_path = "/path/to/video.mp4"
        
        session = MockStreamingSession(
            device=device,
            video_path=video_path
        )
        
        session_dict = session.to_dict()
        assert session_dict["device_name"] == "Test Device"
        assert session_dict["video_path"] == video_path
        assert session_dict["status"] == "playing"
        assert "session_id" in session_dict


class TestStreamingRegistry:
    """Tests for the StreamingSessionRegistry class."""
    
    def test_registry_singleton(self):
        """Test that the registry is a singleton."""
        registry1 = StreamingSessionRegistry.get_instance()
        registry2 = StreamingSessionRegistry.get_instance()
        assert registry1 is registry2
    
    def test_add_session(self):
        """Test adding a session to the registry."""
        registry = StreamingSessionRegistry.get_instance()
        
        # Clear any existing sessions
        registry.sessions.clear()
        
        # Create a mock device
        device = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        
        video_path = "/path/to/video.mp4"
        
        # Create a mock session
        session = MockStreamingSession(
            device=device,
            video_path=video_path
        )
        
        # Add the session to the registry
        registry.sessions[session.session_id] = session
        
        # Verify the session was added
        assert session.session_id in registry.sessions
    
    def test_get_sessions(self):
        """Test getting all sessions from the registry."""
        registry = StreamingSessionRegistry.get_instance()
        
        # Clear any existing sessions
        registry.sessions.clear()
        
        # Create a mock device
        device = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        
        video_path = "/path/to/video.mp4"
        
        # Create a mock session
        session = MockStreamingSession(
            device=device,
            video_path=video_path
        )
        
        # Add the session to the registry
        registry.sessions[session.session_id] = session
        
        # Get all sessions
        sessions = registry.get_active_sessions()
        assert len(sessions) == 1
    
    def test_get_session_by_id(self):
        """Test getting a session by ID."""
        registry = StreamingSessionRegistry.get_instance()
        
        # Clear any existing sessions
        registry.sessions.clear()
        
        # Create a mock device
        device = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        
        video_path = "/path/to/video.mp4"
        
        # Create a mock session
        session = MockStreamingSession(
            device=device,
            video_path=video_path
        )
        
        # Add the session to the registry
        registry.sessions[session.session_id] = session
        
        # Get the session by ID
        retrieved_session = registry.get_session(session.session_id)
        assert retrieved_session is not None
        assert retrieved_session.device.name == "Test Device"
        assert registry.get_session("nonexistent") is None
    
    def test_remove_session(self):
        """Test removing a session from the registry."""
        registry = StreamingSessionRegistry.get_instance()
        
        # Clear any existing sessions
        registry.sessions.clear()
        
        # Create a mock device
        device = MockDevice({
            "device_name": "Test Device",
            "hostname": "127.0.0.1",
            "type": "test",
            "action_url": "http://127.0.0.1:8000/action"
        })
        
        video_path = "/path/to/video.mp4"
        
        # Create a mock session
        session = MockStreamingSession(
            device=device,
            video_path=video_path
        )
        
        # Add the session to the registry
        registry.sessions[session.session_id] = session
        
        # Verify the session was added
        assert session.session_id in registry.sessions
        
        # Remove the session
        registry.unregister_session(session.session_id)
        
        # Verify the session was removed
        assert session.session_id not in registry.sessions


class TestConfigService:
    """Tests for the ConfigService class."""
    
    def test_load_config(self):
        """Test loading a configuration file."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_file.write(b'''
            {
                "devices": [
                    {
                        "name": "Test Device",
                        "type": "dlna",
                        "hostname": "127.0.0.1",
                        "location": "http://127.0.0.1:8000/location",
                        "action_url": "http://127.0.0.1:8000/action",
                        "control_url": "http://127.0.0.1:8000/control"
                    }
                ]
            }
            ''')
            temp_file.flush()
            file_path = temp_file.name
        
        try:
            # Get the config service instance
            config_service = ConfigService.get_instance()
            
            # Load the config
            config = config_service.load_config(file_path)
            
            # Check the config
            assert "devices" in config
            assert len(config["devices"]) == 1
            assert config["devices"][0]["name"] == "Test Device"
            assert config["devices"][0]["type"] == "dlna"
            assert config["devices"][0]["hostname"] == "127.0.0.1"
        finally:
            # Clean up
            os.remove(file_path)
    
    def test_save_config(self):
        """Test saving a configuration file."""
        # Create a config
        config = {
            "devices": [
                {
                    "name": "Test Device",
                    "type": "dlna",
                    "hostname": "127.0.0.1",
                    "location": "http://127.0.0.1:8000/location",
                    "action_url": "http://127.0.0.1:8000/action",
                    "control_url": "http://127.0.0.1:8000/control"
                }
            ]
        }
        
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            file_path = temp_file.name
        
        try:
            # Get the config service instance
            config_service = ConfigService.get_instance()
            
            # Save the config
            config_service.save_config(config, file_path)
            
            # Load the config back and check it
            loaded_config = config_service.load_config(file_path)
            assert "devices" in loaded_config
            assert len(loaded_config["devices"]) == 1
            assert loaded_config["devices"][0]["name"] == "Test Device"
            assert loaded_config["devices"][0]["type"] == "dlna"
            assert loaded_config["devices"][0]["hostname"] == "127.0.0.1"
        finally:
            # Clean up
            os.remove(file_path)
