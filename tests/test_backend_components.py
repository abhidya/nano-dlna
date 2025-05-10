import unittest
import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
import asyncio

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestBackendComponents(unittest.TestCase):
    """Test cases for backend components"""
    
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
    
    @patch('web.backend.services.device_service.DeviceService')
    def test_get_device_service_function(self, mock_service):
        """Test the get_device_service function"""
        from web.backend.services.device_service import get_device_service
        
        # Mock session
        mock_session = MagicMock()
        
        # Call function with session
        service = get_device_service(mock_session)
        
        # Verify service returned
        self.assertIsNotNone(service)
        
        # Test dependency function
        async_service = get_device_service(None)
        self.assertTrue(callable(async_service))
    
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
    
    @patch('web.backend.core.config_service.ConfigService._load_config_file')
    def test_config_loading(self, mock_load):
        """Test configuration loading"""
        from web.backend.core.config_service import ConfigService
        
        # Setup mock
        mock_load.return_value = {
            "Smart_Projector-45[DLNA]": {
                "device_name": "Smart_Projector-45[DLNA]",
                "video_file": "test_video.mp4"
            }
        }
        
        # Get config service instance
        config_service = ConfigService.get_instance()
        
        # Create temp config file
        with tempfile.NamedTemporaryFile(suffix='.json') as temp_file:
            # Load config
            device_names = config_service.load_configs_from_file(temp_file.name)
            
            # Verify device names returned
            self.assertEqual(len(device_names), 1)
            self.assertEqual(device_names[0], "Smart_Projector-45[DLNA]")
            
            # Verify config was stored
            device_config = config_service.get_device_config("Smart_Projector-45[DLNA]")
            self.assertIsNotNone(device_config)
            self.assertEqual(device_config["video_file"], "test_video.mp4")
    
    def test_database_models(self):
        """Test database models"""
        from web.backend.models.device import DeviceModel
        from web.backend.models.video import VideoModel
        from sqlalchemy.orm import declarative_base
        
        # Verify models inherit from Base
        self.assertTrue(issubclass(DeviceModel, declarative_base().__class__))
        self.assertTrue(issubclass(VideoModel, declarative_base().__class__))
        
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
        
        # Test auto play video
        result = manager.auto_play_video(device, "test_video.mp4", loop=True)
        
        # Verify video was played
        self.assertTrue(result)
        mock_device.play.assert_called_with("test_video.mp4", True)
    
    async def async_test_streaming_router(self):
        """Test streaming router endpoints"""
        from fastapi.testclient import TestClient
        from web.backend.main import app
        
        # Create test client
        client = TestClient(app)
        
        # Mock necessary services
        with patch('web.backend.core.streaming_registry.StreamingSessionRegistry.get_instance') as mock_registry:
            # Setup mock registry
            registry = MagicMock()
            registry.get_streaming_stats.return_value = {"active_sessions": 0, "total_bytes": 0}
            registry.get_active_sessions.return_value = []
            mock_registry.return_value = registry
            
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