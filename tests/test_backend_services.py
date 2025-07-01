#!/usr/bin/env python3
"""
Backend service layer tests for improved coverage
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web', 'backend'))


class TestDeviceService:
    """Test DeviceService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def mock_device_manager(self):
        """Mock device manager"""
        manager = Mock()
        manager.get_devices.return_value = []
        manager.get_device.return_value = None
        return manager
    
    @pytest.fixture
    def device_service(self, mock_db, mock_device_manager):
        """Create device service with mocks"""
        from web.backend.services.device_service import DeviceService
        service = DeviceService(mock_db, mock_device_manager)
        return service
    
    def test_get_devices_empty(self, device_service, mock_device_manager, mock_db):
        """Test getting devices when none exist"""
        # Mock the database query
        mock_db.query().offset().limit().all.return_value = []
        
        devices = device_service.get_devices()
        assert devices == []
    
    def test_get_devices_with_data(self, device_service, mock_device_manager):
        """Test getting devices with data"""
        mock_device = Mock()
        mock_device.name = "Test Device"
        mock_device.hostname = "192.168.1.100"
        mock_device.is_playing = False
        mock_device_manager.get_devices.return_value = [mock_device]
        
        devices = device_service.get_devices()
        assert len(devices) == 1
        assert devices[0]["name"] == "Test Device"
    
    def test_play_video(self, device_service, mock_device_manager, mock_db):
        """Test playing video on device"""
        mock_device_manager.play_video_on_device.return_value = True
        
        result = device_service.play_video(1, "test.mp4", loop=True)
        assert result == {"status": "playing", "video": "test.mp4"}
    
    def test_stop_device(self, device_service, mock_device_manager):
        """Test stopping device playback"""
        mock_device_manager.stop_device.return_value = True
        
        result = device_service.stop_device(1)
        assert result == {"status": "stopped"}


class TestVideoService:
    """Test VideoService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def video_service(self, mock_db):
        """Create video service"""
        from web.backend.services.video_service import VideoService
        return VideoService(mock_db)
    
    @patch('os.walk')
    def test_scan_videos_empty(self, mock_walk, video_service):
        """Test scanning videos when none exist"""
        mock_walk.return_value = []
        
        videos = video_service.scan_videos("/videos")
        assert videos == []
    
    @patch('os.walk')
    @patch('os.path.getsize')
    @patch('os.path.getmtime')
    def test_scan_videos_with_files(self, mock_mtime, mock_size, mock_walk, video_service):
        """Test scanning videos with files"""
        mock_walk.return_value = [
            ("/videos", [], ["test.mp4", "test.avi", "not_video.txt"])
        ]
        mock_size.return_value = 1000000  # 1MB
        mock_mtime.return_value = 1234567890
        
        videos = video_service.scan_videos("/videos")
        assert len(videos) == 2  # Only video files
        assert videos[0]["name"] == "test.mp4"
        assert videos[1]["name"] == "test.avi"
    
    def test_get_videos_paginated(self, video_service, mock_db):
        """Test getting videos with pagination"""
        mock_db.query().filter().count.return_value = 0
        mock_db.query().filter().offset().limit().all.return_value = []
        
        result = video_service.get_videos(page=1, per_page=20)
        assert result["items"] == []
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["per_page"] == 20


class TestStreamingService:
    """Test StreamingService"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        config = Mock()
        config.stream_base_url = "http://localhost:8888"
        config.stream_protocol = "http"
        config.videos_dir = "/videos"
        return config
    
    @pytest.fixture
    def streaming_service(self, mock_config):
        """Create streaming service"""
        with patch('web.backend.core.streaming_service.Config') as mock_config_class:
            mock_config_class.return_value = mock_config
            
            from web.backend.core.streaming_service import StreamingService
            return StreamingService()
    
    def test_get_stream_url(self, streaming_service):
        """Test generating stream URL"""
        url = streaming_service.get_stream_url("/videos/test.mp4")
        assert url == "http://localhost:8888/stream/videos/test.mp4"
    
    @patch('os.path.exists')
    def test_validate_video_path_valid(self, mock_exists, streaming_service):
        """Test validating valid video path"""
        mock_exists.return_value = True
        
        valid = streaming_service.validate_video_path("/videos/test.mp4")
        assert valid is True
    
    @patch('os.path.exists')
    def test_validate_video_path_invalid(self, mock_exists, streaming_service):
        """Test validating invalid video path"""
        mock_exists.return_value = False
        
        valid = streaming_service.validate_video_path("/invalid/test.mp4")
        assert valid is False


class TestBrightnessControlService:
    """Test BrightnessControlService"""
    
    @pytest.fixture
    def mock_device_manager(self):
        """Mock device manager"""
        manager = Mock()
        manager.get_devices.return_value = []
        return manager
    
    @pytest.fixture
    def brightness_service(self, mock_device_manager):
        """Create brightness control service"""
        with patch('web.backend.services.brightness_control_service.DeviceManager') as mock_manager_class:
            mock_manager_class.get_instance.return_value = mock_device_manager
            
            from web.backend.services.brightness_control_service import BrightnessControlService
            service = BrightnessControlService()
            service.device_manager = mock_device_manager
            return service
    
    def test_get_brightness_no_devices(self, brightness_service):
        """Test getting brightness with no devices"""
        brightness = brightness_service.get_brightness()
        assert brightness == 100  # Default
    
    def test_set_brightness(self, brightness_service, mock_device_manager):
        """Test setting brightness"""
        mock_device = Mock()
        mock_device.name = "Test Device"
        mock_device_manager.get_devices.return_value = [mock_device]
        
        result = brightness_service.set_brightness(50)
        assert result["brightness"] == 50
        mock_device.set_brightness.assert_called_once_with(50)
    
    @patch('os.path.exists')
    def test_activate_blackout_no_video(self, mock_exists, brightness_service):
        """Test activating blackout when black video doesn't exist"""
        mock_exists.return_value = False
        
        with pytest.raises(Exception, match="Black video not found"):
            brightness_service.activate_blackout()
    
    def test_deactivate_blackout_not_active(self, brightness_service):
        """Test deactivating blackout when not active"""
        brightness_service.blackout_active = False
        
        result = brightness_service.deactivate_blackout()
        assert result["blackout_active"] is False
        assert result["message"] == "Blackout is not currently active"


class TestStreamingRegistry:
    """Test StreamingRegistry"""
    
    @pytest.fixture
    def streaming_registry(self):
        """Create streaming registry"""
        from web.backend.core.streaming_registry import StreamingRegistry
        return StreamingRegistry()
    
    def test_register_session(self, streaming_registry):
        """Test registering streaming session"""
        session_id = streaming_registry.register_session(
            device_name="Test Device",
            video_path="/videos/test.mp4",
            streaming_url="http://localhost:8888/stream/test.mp4",
            streaming_port=8888
        )
        
        assert session_id is not None
        sessions = streaming_registry.get_active_sessions()
        assert len(sessions) == 1
        assert sessions[0]["device_name"] == "Test Device"
    
    def test_unregister_session(self, streaming_registry):
        """Test unregistering streaming session"""
        session_id = streaming_registry.register_session(
            device_name="Test Device",
            video_path="/videos/test.mp4",
            streaming_url="http://localhost:8888/stream/test.mp4",
            streaming_port=8888
        )
        
        streaming_registry.unregister_session(session_id)
        sessions = streaming_registry.get_active_sessions()
        assert len(sessions) == 0
    
    def test_get_session_by_device(self, streaming_registry):
        """Test getting session by device name"""
        session_id = streaming_registry.register_session(
            device_name="Test Device",
            video_path="/videos/test.mp4",
            streaming_url="http://localhost:8888/stream/test.mp4",
            streaming_port=8888
        )
        
        session = streaming_registry.get_session_by_device("Test Device")
        assert session is not None
        assert session["id"] == session_id
        
        # Non-existent device
        session = streaming_registry.get_session_by_device("Unknown Device")
        assert session is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])