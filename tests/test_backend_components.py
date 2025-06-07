import unittest
import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
import asyncio

# Project root should be on PYTHONPATH via run_tests.sh
from web.backend.database.database import Base # Import Base for use in tests
from web.backend.models.device import DeviceModel
from web.backend.models.video import VideoModel


class TestBackendComponents(unittest.TestCase):
    """Test cases for backend components"""

    @classmethod
    def setUpClass(cls):
        """Clear SQLAlchemy metadata and mappers once before tests in this class run."""
        # The root conftest.py now handles session-wide metadata clearing.
        # Specific clearing here might be redundant or interfere.
        # try:
        #     from web.backend.database.database import Base
        #     from sqlalchemy.orm import clear_mappers
        #     Base.metadata.clear()
        #     clear_mappers()
        # except ImportError:
        #     print("Warning: Could not import Base/clear_mappers in TestBackendComponents.setUpClass.")
        # except Exception as e:
        #     print(f"Warning: Error clearing metadata/mappers in TestBackendComponents.setUpClass: {e}")
        pass # setUpClass is kept for structure, but actual clearing is deferred or handled globally.
    
    def test_device_manager_singleton(self):
        """Test that DeviceManager uses singleton pattern"""
        from web.backend.core.device_manager import get_device_manager
        
        # Get two instances
        manager1 = get_device_manager()
        manager2 = get_device_manager()
        
        # Verify they're the same instance
        self.assertIs(manager1, manager2)
    
    def test_config_service_singleton(self):
        """Test that ConfigService uses singleton pattern"""
        from web.backend.core.config_service import ConfigService
        
        # Get two instances
        config1 = ConfigService.get_instance()
        config2 = ConfigService.get_instance()
        
        # Verify they're the same instance
        self.assertIs(config1, config2)
    
    def test_streaming_registry_singleton(self):
        """Test that StreamingSessionRegistry uses singleton pattern"""
        from web.backend.core.streaming_registry import StreamingSessionRegistry
        
        # Get two instances
        registry1 = StreamingSessionRegistry.get_instance()
        registry2 = StreamingSessionRegistry.get_instance()
        
        # Verify they're the same instance
        self.assertIs(registry1, registry2)
    
    # Removed test_get_device_service_function as the targeted function
    # in web.backend.services.device_service was removed due to being problematic.
    # Service instantiation is now handled by local dependency providers in routers.
    
    @patch('web.backend.core.device_manager.DeviceManager.register_device')
    def test_device_registration(self, mock_register):
        """Test device registration"""
        from web.backend.core.device_manager import get_device_manager
        
        # Setup mock return value
        mock_device = MagicMock()
        mock_register.return_value = mock_device
        
        # Get device manager instance
        manager = get_device_manager()
        
        # Create test device info
        device_info = {
            "device_name": "Test Device",
            "type": "dlna",
            "hostname": "10.0.0.1",
            "action_url": "http://10.0.0.1/action",
            "friendly_name": "Test Device"
        }
        
        # Call register device
        device = manager.register_device(device_info)
        
        # Verify device was registered
        self.assertEqual(device, mock_device)
        mock_register.assert_called_once_with(device_info)
    
    @patch('web.backend.core.config_service.open', new_callable=unittest.mock.mock_open)
    @patch('web.backend.core.config_service.json.load')
    def test_config_loading(self, mock_json_load, mock_file_open):
        """Test configuration loading by mocking file operations"""
        from web.backend.core.config_service import ConfigService
        
        # Define the mock data that json.load should return (a list of device configs)
        mock_device_data = [{
            "device_name": "Smart_Projector-45[DLNA]",
            "type": "dlna", # Required by add_device_config
            "hostname": "1.2.3.4", # Required
            "action_url": "http://example.com/action", # Required
            "video_file": "/tmp/test_video_mock.mp4" # Required and must exist
        }]
        mock_json_load.return_value = mock_device_data
        
        # Ensure the dummy video file exists for validation within add_device_config
        dummy_video_path = "/tmp/test_video_mock.mp4"
        with open(dummy_video_path, "w") as f:
            f.write("dummy")

        config_service = ConfigService.get_instance()
        config_service.clear_configurations() # Ensure clean state

        # Call load_configs_from_file with a dummy path, as open is mocked
        dummy_file_path = "dummy_config.json"
        device_names = config_service.load_configs_from_file(dummy_file_path)
        
        mock_file_open.assert_called_once_with(dummy_file_path, 'r')
        mock_json_load.assert_called_once()

        self.assertEqual(len(device_names), 1)
        self.assertEqual(device_names[0], "Smart_Projector-45[DLNA]")
        
        device_config = config_service.get_device_config("Smart_Projector-45[DLNA]")
        self.assertIsNotNone(device_config)
        self.assertEqual(device_config["video_file"], dummy_video_path)

        # Clean up dummy video file
        if os.path.exists(dummy_video_path):
            os.remove(dummy_video_path)
    
    def test_database_models(self):
        """Test database models"""
        # Models (DeviceModel, VideoModel) are now imported at the module level.
        # Base is also imported at module level.
        # The setUpClass method attempts to clear Base.metadata.
        
        # Verify tables are registered in metadata
        # This implicitly tests that models are defined and associated with Base
        # after setUpClass and module-level imports.
        
        # Explicitly touch the __table__ attribute to ensure models are processed by SQLAlchemy
        # and their tables are registered with the Base.metadata object.
        # This can help if metadata was cleared or if models weren't fully processed earlier.
        try:
            _ = DeviceModel.__table__
            _ = VideoModel.__table__
        except Exception as e:
            # This might fail if Base.metadata is in a really bad state or models can't be processed
            print(f"Error accessing model.__table__: {e}")

        self.assertIn("devices", Base.metadata.tables)
        self.assertIn("videos", Base.metadata.tables)
        
        # Test model instantiation
        device = DeviceModel(
            name="Test Device",
            type="dlna",
            hostname="10.0.0.1",
            action_url="http://10.0.0.1/action",
            friendly_name="Test Device",
            status="connected"
        )
        
        # Verify attributes
        self.assertEqual(device.name, "Test Device")
        self.assertEqual(device.type, "dlna")
        self.assertEqual(device.status, "connected")
        
        # Test video model
        video = VideoModel(
            name="Test Video",
            path="/path/to/video.mp4",
            size=1000,
            duration=60.0
        )
        
        # Verify attributes
        self.assertEqual(video.name, "Test Video")
        self.assertEqual(video.path, "/path/to/video.mp4")
        self.assertEqual(video.size, 1000)
        self.assertEqual(video.duration, 60.0)
    
    @patch('web.backend.core.device_manager.DeviceManager')
    @patch('web.backend.core.device_manager.DLNADevice')
    def test_device_playback(self, mock_dlna_device, mock_manager):
        """Test device playback functionality"""
        from web.backend.core.device_manager import get_device_manager
        
        # Setup mock device
        mock_device = MagicMock()
        mock_device.play.return_value = True
        mock_device.name = "Test Device"
        mock_dlna_device.return_value = mock_device
        
        # Setup manager
        manager = get_device_manager()
        manager.devices = {"Test Device": mock_device}
        
        # Get device
        device = manager.get_device("Test Device")
        
        # Verify correct device returned
        self.assertEqual(device, mock_device)
        
        # Create a temporary video file for the test
        temp_video_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_video_file.write(b"dummy video data")
        temp_video_file.close()
        video_path = temp_video_file.name

        # Mock the streaming service to control the URL generated
        # This assumes DeviceManager uses a streaming service to get the URL
        # If DeviceManager constructs it directly, this part might need adjustment
        # For now, let's assume the play mock needs to handle the URL.
        # The actual auto_play_video calls device.play with a URL.
        # The mock_device.play should be asserted with a URL.

        # Test auto play video
        result = manager.auto_play_video(device, video_path, loop=True)
        
        # Verify video was played
        self.assertTrue(result, "auto_play_video should return True on success")
        
        # The actual call to device.play will be with a URL.
        # We need to assert that it was called, but the exact URL might be tricky
        # if it involves dynamic port numbers from a streaming server.
        # For now, let's check it was called. If specific URL matching is needed,
        # the streaming service interaction within auto_play_video would need mocking.
        mock_device.play.assert_called_once()
        args, kwargs = mock_device.play.call_args
        self.assertTrue(args[0].startswith("http://")) # Check it's a URL
        self.assertTrue(os.path.basename(video_path) in args[0]) # Check filename is in URL
        self.assertEqual(args[1], True) # loop=True

        # Clean up the temporary file
        os.remove(video_path)
    
    async def async_test_streaming_router(self):
        """Test streaming router endpoints"""
        from fastapi.testclient import TestClient
        from web.backend.main import app
        from web.backend.core.streaming_registry import StreamingSessionRegistry # Import for spec
        
        # Create test client
        client = TestClient(app) # app is imported from web.backend.main
        
        # Mock necessary services
        # Patch where StreamingSessionRegistry is *used* by the router, which is web.backend.routers.streaming_router
        with patch('web.backend.routers.streaming_router.StreamingSessionRegistry.get_instance') as mock_registry_get_instance:
            # Setup mock registry instance
            registry_instance_mock = MagicMock(spec=StreamingSessionRegistry)
            registry_instance_mock.get_streaming_stats.return_value = {"active_sessions": 0, "total_bytes": 0}
            registry_instance_mock.get_active_sessions.return_value = [] # For other potential calls if any
            mock_registry_get_instance.return_value = registry_instance_mock
            
            # Test streaming stats endpoint
            response = client.get("/api/streaming/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"active_sessions": 0, "total_bytes": 0})
            
            # Test health endpoint
            response = client.get("/api/streaming/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "healthy")
    
    def test_streaming_router(self):
        """Test streaming router endpoints synchronously"""
        asyncio.run(self.async_test_streaming_router())


if __name__ == "__main__":
    unittest.main()
