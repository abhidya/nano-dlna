#!/usr/bin/env python3
"""
Comprehensive test suite with improved fixtures and test coverage
"""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nanodlna.devices import Config
from web.backend.core.dlna_device import DLNADevice
from web.backend.core.device import Device
from web.backend.core.device_manager import DeviceManager
from web.backend.core.streaming_service import StreamingService

@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    config = Mock(spec=Config)
    config.videos_dir = "/tmp/test_videos"
    config.stream_base_url = "http://localhost:8888"
    config.stream_protocol = "http"
    config.polling_interval = 0.1
    config.web_ui_port = 8000
    config.dashboard_url = "http://localhost:3000"
    return config

@pytest.fixture
def temp_video_dir():
    """Create temporary video directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_device():
    """Create a mock DLNA device"""
    device = Mock(spec=DLNADevice)
    device.uuid = "test-device-123"
    device.name = "Test Device"
    device.url = "http://192.168.1.100:7070"
    device.is_playing = False
    device.current_position = 0
    device.current_duration = 0
    device.current_video = None
    device.set_brightness = Mock()
    device.play = Mock()
    device.stop = Mock()
    device.pause = Mock()
    device.seek = Mock()
    return device

@pytest.fixture
def device_manager(mock_config):
    """Create device manager with mock config"""
    with patch('web.backend.core.device_manager.Config') as mock_config_class:
        mock_config_class.return_value = mock_config
        manager = DeviceManager()
        yield manager

@pytest.fixture
def streaming_service(mock_config):
    """Create streaming service with mock config"""
    with patch('web.backend.core.streaming_service.Config') as mock_config_class:
        mock_config_class.return_value = mock_config
        service = StreamingService()
        yield service

class TestDeviceManager:
    """Test device manager functionality"""
    
    def test_add_device(self, device_manager, mock_device):
        """Test adding a device"""
        device_manager.add_device(mock_device)
        assert mock_device.uuid in device_manager.devices
        assert device_manager.devices[mock_device.uuid] == mock_device
    
    def test_remove_device(self, device_manager, mock_device):
        """Test removing a device"""
        device_manager.add_device(mock_device)
        device_manager.remove_device(mock_device.uuid)
        assert mock_device.uuid not in device_manager.devices
    
    def test_get_device(self, device_manager, mock_device):
        """Test getting a device"""
        device_manager.add_device(mock_device)
        device = device_manager.get_device(mock_device.uuid)
        assert device == mock_device
    
    def test_get_all_devices(self, device_manager, mock_device):
        """Test getting all devices"""
        device_manager.add_device(mock_device)
        devices = device_manager.get_all_devices()
        assert len(devices) == 1
        assert devices[0] == mock_device
    
    def test_play_video_on_device(self, device_manager, mock_device):
        """Test playing video on device with HTTP URL"""
        device_manager.add_device(mock_device)
        video_path = "/videos/test.mp4"
        
        # Expected HTTP streaming URL
        expected_url = f"{mock_config.stream_base_url}/stream{video_path}"
        
        success = device_manager.play_video_on_device(mock_device.uuid, video_path)
        
        assert success is True
        mock_device.play.assert_called_once()
        # Check that play was called with HTTP URL, not local path
        call_args = mock_device.play.call_args[0][0]
        assert call_args.startswith("http://")
        assert "/stream/" in call_args
    
    def test_stop_device(self, device_manager, mock_device):
        """Test stopping device playback"""
        device_manager.add_device(mock_device)
        device_manager.stop_device(mock_device.uuid)
        mock_device.stop.assert_called_once()

class TestStreamingService:
    """Test streaming service functionality"""
    
    def test_get_stream_url(self, streaming_service):
        """Test generating stream URL"""
        video_path = "/videos/test.mp4"
        url = streaming_service.get_stream_url(video_path)
        assert url.startswith("http://")
        assert "/stream/" in url
        assert "test.mp4" in url
    
    def test_validate_video_path(self, streaming_service, temp_video_dir):
        """Test video path validation"""
        streaming_service.config.videos_dir = temp_video_dir
        
        # Create test video file
        video_file = Path(temp_video_dir) / "test.mp4"
        video_file.touch()
        
        # Valid path
        assert streaming_service.validate_video_path(str(video_file)) is True
        
        # Invalid path
        assert streaming_service.validate_video_path("/invalid/path.mp4") is False

class TestDLNADevice:
    """Test DLNA device functionality"""
    
    @pytest.fixture
    def dlna_device(self):
        """Create a DLNA device with mocked service"""
        with patch('nanodlna.dlna_device.DLNAService') as mock_service:
            device = DLNADevice(
                uuid="test-123",
                name="Test Device",
                url="http://192.168.1.100:7070"
            )
            device.service = mock_service.return_value
            yield device
    
    def test_device_initialization(self, dlna_device):
        """Test device initialization"""
        assert dlna_device.uuid == "test-123"
        assert dlna_device.name == "Test Device"
        assert dlna_device.url == "http://192.168.1.100:7070"
        assert dlna_device.is_playing is False
    
    def test_play_video(self, dlna_device):
        """Test playing video"""
        dlna_device.service.SetAVTransportURI = Mock(return_value={'status': 200})
        dlna_device.service.Play = Mock(return_value={'status': 200})
        
        url = "http://localhost:8888/stream/test.mp4"
        dlna_device.play(url)
        
        dlna_device.service.SetAVTransportURI.assert_called_once()
        dlna_device.service.Play.assert_called_once()
        assert dlna_device.is_playing is True
    
    def test_stop_playback(self, dlna_device):
        """Test stopping playback"""
        dlna_device.is_playing = True
        dlna_device.service.Stop = Mock(return_value={'status': 200})
        
        dlna_device.stop()
        
        dlna_device.service.Stop.assert_called_once()
        assert dlna_device.is_playing is False

class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_playback_cycle(self, device_manager, streaming_service, mock_device):
        """Test complete playback cycle"""
        # Add device
        device_manager.add_device(mock_device)
        
        # Generate stream URL
        video_path = "/videos/test.mp4"
        stream_url = streaming_service.get_stream_url(video_path)
        
        # Play video
        success = device_manager.play_video_on_device(mock_device.uuid, video_path)
        assert success is True
        
        # Verify play was called with streaming URL
        mock_device.play.assert_called_once()
        call_args = mock_device.play.call_args[0][0]
        assert "http://" in call_args
        assert "/stream/" in call_args
        
        # Stop playback
        device_manager.stop_device(mock_device.uuid)
        mock_device.stop.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])