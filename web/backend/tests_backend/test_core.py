"""
Tests for core modules.
"""
import os
import pytest
import tempfile
import time # Added import for time.sleep
import socket # Added import for socket.error
import json # Added import for json.load
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime # Added for status update tests
from web.backend.core.device import Device
from web.backend.models.device import DeviceModel # Added import for DeviceModel
from web.backend.tests_backend.mock_device import MockDevice
from web.backend.tests_backend.mock_streaming_session import MockStreamingSession
from web.backend.core.device_manager import DeviceManager 
# Corrected import for DeviceService:
from web.backend.services.device_service import DeviceService 
from web.backend.core.streaming_registry import StreamingSessionRegistry
from web.backend.core.streaming_session import StreamingSession
from web.backend.core.config_service import ConfigService


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

    def test_update_status_method(self):
        """Test the update_status method."""
        device = MockDevice({"device_name": "Test UpdateStatus"})
        device.update_status("testing_status")
        assert device.status == "testing_status"

    def test_update_playing_method(self):
        """Test the update_playing method."""
        device = MockDevice({"device_name": "Test UpdatePlaying"})
        assert device.is_playing is False # Initial state
        device.update_playing(True)
        assert device.is_playing is True
        device.update_playing(False)
        assert device.is_playing is False

    def test_update_video_method(self):
        """Test the update_video method."""
        device = MockDevice({"device_name": "Test UpdateVideo"})
        assert device.current_video is None # Initial state
        device.update_video("/test/video.mp4")
        assert device.current_video == "/test/video.mp4"
        device.update_video(None)
        assert device.current_video is None
    
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
    
    @patch('web.backend.core.device_manager.threading.Thread')
    @patch('web.backend.core.device_manager.os.environ')
    def test_start_discovery(self, mock_environ, mock_thread):
        """Test starting device discovery."""
        mock_environ.get.return_value = None 
        mock_environ.__contains__.side_effect = lambda item: item != 'PYTEST_CURRENT_TEST'
        manager = DeviceManager()
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        manager.start_discovery()
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        assert manager.discovery_running is True
    
    @patch('web.backend.core.device_manager.threading.Thread')
    def test_stop_discovery(self, mock_thread):
        """Test stopping device discovery."""
        manager = DeviceManager()
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        manager.start_discovery() 
        manager.stop_discovery()
        assert manager.discovery_running is False

    def test_get_device_manager_singleton(self):
        """Test that get_device_manager returns a singleton instance."""
        from web.backend.core.device_manager import get_device_manager
        manager1 = get_device_manager()
        manager2 = get_device_manager()
        assert manager1 is manager2
        from web.backend.core import device_manager as dm_module
        dm_module._device_manager_instance = None


    @patch('socket.socket')
    def test_get_serve_ip_auto_detect(self, mock_socket_constructor):
        """Test get_serve_ip auto-detection."""
        mock_socket_instance = MagicMock()
        mock_socket_instance.getsockname.return_value = ('192.168.1.101', 12345)
        mock_socket_constructor.return_value = mock_socket_instance
        manager = DeviceManager()
        ip = manager.get_serve_ip()
        assert ip == '192.168.1.101'
        mock_socket_instance.connect.assert_called_once_with(('8.8.8.8', 80))
        mock_socket_instance.close.assert_called_once()

    @patch.dict(os.environ, {'STREAMING_SERVE_IP': '10.0.0.5'})
    def test_get_serve_ip_env_variable(self):
        """Test get_serve_ip using environment variable."""
        manager = DeviceManager()
        ip = manager.get_serve_ip()
        assert ip == '10.0.0.5'

    @patch.dict(os.environ, {'STREAMING_SERVE_IP': '127.0.0.1'})
    def test_get_serve_ip_env_variable_localhost_error(self):
        """Test get_serve_ip raises error if env var is localhost."""
        manager = DeviceManager()
        with pytest.raises(RuntimeError, match="STREAMING_SERVE_IP must be a LAN IP, not localhost/127.0.0.1"):
            manager.get_serve_ip()
            
    @patch('socket.socket')
    def test_get_serve_ip_auto_detect_localhost_error(self, mock_socket_constructor):
        """Test get_serve_ip raises error if auto-detected IP is localhost."""
        mock_socket_instance = MagicMock()
        mock_socket_instance.getsockname.return_value = ('127.0.0.1', 12345) 
        mock_socket_constructor.return_value = mock_socket_instance
        manager = DeviceManager()
        with pytest.raises(RuntimeError, match="Could not determine LAN IP for streaming. Set STREAMING_SERVE_IP env variable."): 
            manager.get_serve_ip()

    @patch('socket.socket')
    def test_get_serve_ip_connect_error(self, mock_socket_constructor):
        """Test get_serve_ip raises error if socket.connect fails."""
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect.side_effect = socket.error("Connection failed") 
        mock_socket_constructor.return_value = mock_socket_instance
        manager = DeviceManager()
        with pytest.raises(RuntimeError, match="Could not determine LAN IP for streaming."):
            manager.get_serve_ip()

    @pytest.fixture
    def device_manager_with_config(self, tmp_config_file):
        from web.backend.core import config_service as cs_module
        from web.backend.core import device_manager as dm_module
        cs_module._config_service_instance = None
        dm_module._device_manager_instance = None
        manager = DeviceManager()
        mock_config_service = MagicMock(spec=ConfigService)
        mock_config_service.load_configs_from_file.return_value = ["TestDeviceConfig"]
        mock_config_service.get_device_config.return_value = {
            "device_name": "TestDeviceConfig", "type": "dlna",
            "hostname": "10.0.0.1", "action_url": "http://10.0.0.1/action",
            "video_file": "test.mp4"
        }
        manager.config_service = mock_config_service
        return manager, tmp_config_file, mock_config_service

    def test_load_devices_from_config(self, device_manager_with_config):
        """Test loading devices from a configuration file."""
        manager, config_file_path, mock_config_service = device_manager_with_config
        mock_device_instance = MockDevice({
            "device_name": "TestDeviceConfig", "type": "dlna", 
            "hostname": "10.0.0.1", "action_url": "http://10.0.0.1/action"
        })
        with patch.object(manager, 'register_device', return_value=mock_device_instance) as mock_register:
            loaded_devices = manager.load_devices_from_config(config_file_path)
        mock_config_service.load_configs_from_file.assert_called_once_with(os.path.abspath(config_file_path))
        manager.devices["TestDeviceConfig"] = mock_device_instance
        loaded_devices_after_register = manager.load_devices_from_config(config_file_path)
        assert len(loaded_devices_after_register) == 1
        assert loaded_devices_after_register[0].name == "TestDeviceConfig"

    def test_save_devices_to_config(self, device_manager_with_config, tmp_config_file):
        """Test saving devices to a configuration file."""
        manager, _, _ = device_manager_with_config
        device_info = {
            "device_name": "SaveTestDevice", "type": "dlna",
            "hostname": "10.0.0.2", "action_url": "http://10.0.0.2/action",
            "friendly_name": "Save Test"
        }
        manager.register_device(device_info.copy())
        save_file_path = os.path.join(os.path.dirname(tmp_config_file), "saved_test_config.json")
        result = manager.save_devices_to_config(save_file_path)
        assert result is True
        assert os.path.exists(save_file_path)
        with open(save_file_path, "r") as f:
            saved_data = json.load(f)
        assert len(saved_data) == 1
        assert saved_data[0]["device_name"] == "SaveTestDevice"
        os.remove(save_file_path)

    def test_update_device_status_method(self):
        """Test the DeviceManager's update_device_status method."""
        manager = DeviceManager()
        device_name = "status_test_device"
        manager.update_device_status(device_name, "new_status", is_playing=True, current_video="/vid.mp4", error="test_error")
        assert device_name in manager.device_status
        status_dict = manager.device_status[device_name]
        assert status_dict["status"] == "new_status"
        assert status_dict["is_playing"] is True
        assert status_dict["current_video"] == "/vid.mp4"
        assert status_dict["last_error"] == "test_error"
        assert "last_updated" in status_dict
        assert "last_error_time" in status_dict
        manager.update_device_status(device_name, "another_status", is_playing=False)
        status_dict = manager.device_status[device_name]
        assert status_dict["status"] == "another_status"
        assert status_dict["is_playing"] is False
        assert status_dict["current_video"] == "/vid.mp4" 
        assert status_dict["last_error"] == "test_error"   

    @patch('web.backend.database.database.get_db') # Patch get_db first
    @patch('web.backend.services.device_service.DeviceService') # Then DeviceService
    def test_update_device_playback_progress(self, MockDeviceServiceClass, mock_get_db_func):
        """Test updating device playback progress, mocking DeviceService."""
        manager = DeviceManager()
        device_name = "progress_device"
        
        mock_db_session = MagicMock()
        
        # This is the instance we want to be returned when DeviceService() is called
        configured_mock_service_instance = MagicMock(spec=DeviceService)
        
        mock_db_device = MagicMock(spec=DeviceModel)

        # Configure the get_device_by_name method on our desired instance
        def get_device_by_name_side_effect(name_arg):
            print(f"SIDE EFFECT: configured_mock_service_instance.get_device_by_name called with name: {name_arg}")
            if name_arg == device_name: 
                print(f"SIDE EFFECT: Returning mock_db_device for {name_arg}")
                return mock_db_device
            print(f"SIDE EFFECT: Returning None for {name_arg}")
            return None
        configured_mock_service_instance.get_device_by_name.side_effect = get_device_by_name_side_effect

        # This is the instance we want to be returned when DeviceService() is called
        # And it's the instance on which we'll check calls.
        mock_device_service_instance = MockDeviceServiceClass.return_value 
        
        mock_db_device = MagicMock(spec=DeviceModel)

        # Configure the get_device_by_name method on our desired instance
        def get_device_by_name_side_effect(name_arg):
            print(f"SIDE EFFECT: mock_device_service_instance.get_device_by_name called with name: {name_arg}")
            if name_arg == device_name: 
                print(f"SIDE EFFECT: Returning mock_db_device for {name_arg}")
                return mock_db_device
            print(f"SIDE EFFECT: Returning None for {name_arg}")
            return None
        mock_device_service_instance.get_device_by_name.side_effect = get_device_by_name_side_effect
        
        # Also, explicitly set the device_service on the manager instance for the fallback path
        # manager.device_service = mock_device_service_instance # Keep this commented for now

        # Configure mock_get_db
        mock_db_generator = MagicMock()
        mock_db_generator.__next__.return_value = mock_db_session
        mock_get_db_func.return_value = mock_db_generator # mock_get_db_func is the mock from @patch
            
        mock_core_device = MagicMock(spec=Device)
        manager.devices[device_name] = mock_core_device

        manager.update_device_playback_progress(device_name, "00:10:00", "01:00:00", 16)

        assert device_name in manager.device_status
        status_dict = manager.device_status[device_name]
        assert status_dict["playback_position"] == "00:10:00"
        assert status_dict["playback_duration"] == "01:00:00"
        assert status_dict["playback_progress"] == 16
            
        mock_device_service_instance.get_device_by_name.assert_called_once_with(device_name)
        # If the side_effect returned mock_db_device, then commit should have been called.
        if mock_db_device == configured_mock_service_instance.get_device_by_name.return_value: # Check if it was configured to return mock_db_device
            mock_db_session.commit.assert_called_once()
            
        assert mock_core_device.current_position == "00:10:00"
        assert mock_core_device.duration_formatted == "01:00:00"
        assert mock_core_device.playback_progress == 16

    def test_update_device_playing_state(self):
        """Test updating device playing state."""
        manager = DeviceManager()
        device_name = "playing_state_device"
        mock_core_device = MagicMock(spec=Device)
        mock_core_device.name = device_name 
        
        with patch.object(manager, 'get_device', return_value=mock_core_device):
            manager.update_device_playing_state(device_name, True, "/test/video1.mp4")

        mock_core_device.update_playing.assert_called_once_with(True)
        assert mock_core_device.current_video == "/test/video1.mp4"
        
        assert device_name in manager.device_status
        status_dict = manager.device_status[device_name]
        assert status_dict["is_playing"] is True
        assert status_dict["current_video"] == "/test/video1.mp4"

        with patch.object(manager, 'get_device', return_value=mock_core_device):
            manager.update_device_playing_state(device_name, False, "/test/video2.mp4")
        
        mock_core_device.update_playing.assert_called_with(False) 
        assert mock_core_device.current_video == "/test/video2.mp4"

        status_dict = manager.device_status[device_name]
        assert status_dict["is_playing"] is False
        assert status_dict["current_video"] == "/test/video2.mp4"


class TestStreamingSession:
    """Tests for the StreamingSession class."""

    @pytest.fixture
    def sample_session_params(self):
        return {
            "session_id": "test-session-123",
            "device_name": "Test Device",
            "video_path": "/path/to/video.mp4",
            "server_ip": "127.0.0.1",
            "server_port": 8000
        }

    def test_session_creation(self, sample_session_params):
        """Test creating a streaming session."""
        session = StreamingSession(**sample_session_params)
        
        assert session.session_id == "test-session-123"
        assert session.device_name == "Test Device"
        assert session.video_path == "/path/to/video.mp4"
        assert session.server_ip == "127.0.0.1"
        assert session.server_port == 8000
        assert session.status == "initializing" 
        assert session.active is True
        assert session.bytes_served == 0
        assert session.client_ip is None
        assert session.client_connections == 0
        assert session.connection_errors == 0
        assert len(session.bandwidth_samples) == 0
        assert len(session.connection_history) == 0
        assert session.error_message is None

    def test_update_activity(self, sample_session_params):
        """Test updating session activity."""
        session = StreamingSession(**sample_session_params)
        
        session.update_activity(client_ip="192.168.1.10", bytes_transferred=1024)
        assert session.client_ip == "192.168.1.10"
        assert session.bytes_served == 1024
        assert len(session.bandwidth_samples) == 1
        assert session.bandwidth_samples[0][1] == 1024
        
        time.sleep(0.1) 
        session.update_activity(bytes_transferred=2048)
        assert session.bytes_served == 1024 + 2048
        assert len(session.bandwidth_samples) == 2
        assert session.bandwidth_samples[1][1] == 2048
        assert session.bandwidth_samples[1][2] > 0 

    def test_record_connection(self, sample_session_params):
        """Test recording connection events."""
        session = StreamingSession(**sample_session_params)
        
        session.record_connection(connected=True)
        assert session.client_connections == 1
        assert session.status == "active"
        assert len(session.connection_history) == 1
        assert session.connection_history[0][1] == "connected"
        
        session.record_connection(connected=False)
        assert session.connection_errors == 1
        assert session.status == "stalled" 
        assert len(session.connection_history) == 2
        assert session.connection_history[1][1] == "disconnected"

        for i in range(25):
            session.record_connection(connected=True)
        assert len(session.connection_history) == 20


    def test_set_error(self, sample_session_params):
        """Test setting an error state."""
        session = StreamingSession(**sample_session_params)
        session.set_error("Test error message")
        assert session.status == "error"
        assert session.error_message == "Test error message"
        assert session.active is False

    def test_complete_session(self, sample_session_params):
        """Test completing a session."""
        session = StreamingSession(**sample_session_params)
        session.complete()
        assert session.status == "completed"
        assert session.active is False

    def test_get_bandwidth(self, sample_session_params):
        """Test bandwidth calculation."""
        session = StreamingSession(**sample_session_params)
        assert session.get_bandwidth() == 0 

        session.update_activity(bytes_transferred=1000) 
        time.sleep(0.1)
        session.update_activity(bytes_transferred=1000) 
        
        bandwidth = session.get_bandwidth()
        assert bandwidth > 0

        for _ in range(15):
            time.sleep(0.01)
            session.update_activity(bytes_transferred=100)
        assert len(session.bandwidth_samples) == 10 
        assert session.get_bandwidth() > 0

        session_zero_duration = StreamingSession(**sample_session_params)
        now = time.time()
        session_zero_duration.bandwidth_samples.append((now, 100, 0))
        session_zero_duration.bandwidth_samples.append((now, 200, 0)) 
        assert session_zero_duration.get_bandwidth() == 0


    def test_is_stalled(self, sample_session_params):
        """Test session stalling logic."""
        session = StreamingSession(**sample_session_params)
        assert session.is_stalled(inactivity_threshold=0.1) is False 

        time.sleep(0.2)
        assert session.is_stalled(inactivity_threshold=0.1) is True 

        session.update_activity(bytes_transferred=100)
        assert session.is_stalled(inactivity_threshold=0.1) is False 

        session.set_error("some error")
        assert session.is_stalled() is False 

        session_for_error_status_check = StreamingSession(**sample_session_params)
        session_for_error_status_check.status = "error" 
        assert session_for_error_status_check.is_stalled() is True 

        session.active = False 
        assert session.is_stalled() is False 

    def test_session_to_dict(self, sample_session_params):
        """Test converting a session to a dictionary."""
        session = StreamingSession(**sample_session_params)
        session.update_activity(client_ip="192.168.1.20", bytes_transferred=5000)
        session.record_connection(True)
        
        session_dict = session.to_dict()
        
        assert session_dict["session_id"] == "test-session-123"
        assert session_dict["device_name"] == "Test Device"
        assert session_dict["video_path"] == "/path/to/video.mp4"
        assert session_dict["status"] == "active" 
        assert session_dict["bytes_served"] == 5000
        assert session_dict["client_ip"] == "192.168.1.20"
        assert session_dict["connection_count"] == 1
        assert session_dict["active"] is True
        assert "start_time" in session_dict
        assert "last_activity" in session_dict
        assert "bandwidth_bps" in session_dict
        assert "duration_seconds" in session_dict
        assert session_dict["error_message"] is None


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
        registry.sessions.clear()
        device = MockDevice({
            "device_name": "Test Device", "hostname": "127.0.0.1",
            "type": "test", "action_url": "http://127.0.0.1:8000/action"
        })
        video_path = "/path/to/video.mp4"
        session = MockStreamingSession(device=device, video_path=video_path)
        registry.sessions[session.session_id] = session
        assert session.session_id in registry.sessions
    
    def test_get_sessions(self):
        """Test getting all sessions from the registry."""
        registry = StreamingSessionRegistry.get_instance()
        registry.sessions.clear()
        device = MockDevice({
            "device_name": "Test Device", "hostname": "127.0.0.1",
            "type": "test", "action_url": "http://127.0.0.1:8000/action"
        })
        video_path = "/path/to/video.mp4"
        session = MockStreamingSession(device=device, video_path=video_path)
        registry.sessions[session.session_id] = session
        sessions = registry.get_active_sessions()
        assert len(sessions) == 1
    
    def test_get_session_by_id(self):
        """Test getting a session by ID."""
        registry = StreamingSessionRegistry.get_instance()
        registry.sessions.clear()
        device = MockDevice({
            "device_name": "Test Device", "hostname": "127.0.0.1",
            "type": "test", "action_url": "http://127.0.0.1:8000/action"
        })
        video_path = "/path/to/video.mp4"
        session = MockStreamingSession(device=device, video_path=video_path)
        registry.sessions[session.session_id] = session
        retrieved_session = registry.get_session(session.session_id)
        assert retrieved_session is not None
        assert retrieved_session.device.name == "Test Device"
        assert registry.get_session("nonexistent") is None
    
    def test_remove_session(self):
        """Test removing a session from the registry."""
        registry = StreamingSessionRegistry.get_instance()
        registry.sessions.clear()
        device = MockDevice({
            "device_name": "Test Device", "hostname": "127.0.0.1",
            "type": "test", "action_url": "http://127.0.0.1:8000/action"
        })
        video_path = "/path/to/video.mp4"
        session = MockStreamingSession(device=device, video_path=video_path)
        registry.sessions[session.session_id] = session
        assert session.session_id in registry.sessions
        registry.unregister_session(session.session_id)
        assert session.session_id not in registry.sessions


class TestConfigService:
    """Tests for the ConfigService class."""
    
    def test_load_config(self):
        """Test loading a configuration file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_file.write(b'''
            {
                "devices": [
                    {
                        "name": "Test Device", "type": "dlna", "hostname": "127.0.0.1",
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
            config_service = ConfigService.get_instance()
            config = config_service.load_config(file_path)
            assert "devices" in config
            assert len(config["devices"]) == 1
            assert config["devices"][0]["name"] == "Test Device"
        finally:
            os.remove(file_path)
    
    def test_save_config(self):
        """Test saving a configuration file."""
        config = {
            "devices": [{
                "name": "Test Device", "type": "dlna", "hostname": "127.0.0.1",
                "location": "http://127.0.0.1:8000/location",
                "action_url": "http://127.0.0.1:8000/action",
                "control_url": "http://127.0.0.1:8000/control"
            }]
        }
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            file_path = temp_file.name
        try:
            config_service = ConfigService.get_instance()
            config_service.save_config(config, file_path)
            loaded_config = config_service.load_config(file_path)
            assert "devices" in loaded_config
            assert len(loaded_config["devices"]) == 1
            assert loaded_config["devices"][0]["name"] == "Test Device"
        finally:
            os.remove(file_path)
