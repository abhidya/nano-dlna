#!/usr/bin/env python3
"""
Backend core module tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web', 'backend'))


class TestConfigService:
    """Test ConfigService"""
    
    @pytest.fixture
    def config_service(self):
        """Create config service"""
        from web.backend.core.config_service import ConfigService
        # Reset singleton
        ConfigService._instance = None
        return ConfigService.get_instance()
    
    def test_singleton(self, config_service):
        """Test singleton pattern"""
        from web.backend.core.config_service import ConfigService
        service2 = ConfigService.get_instance()
        assert config_service is service2
    
    def test_add_device_config(self, config_service):
        """Test adding device configuration"""
        config = {
            "name": "Test Device",
            "hostname": "192.168.1.100",
            "video_file": "/videos/test.mp4"
        }
        
        config_service.add_device_config("Test Device", config, source="test")
        retrieved = config_service.get_device_config("Test Device")
        assert retrieved == config
    
    def test_remove_device_config(self, config_service):
        """Test removing device configuration"""
        config = {"name": "Test Device"}
        config_service.add_device_config("Test Device", config, source="test")
        
        config_service.remove_device_config("Test Device")
        retrieved = config_service.get_device_config("Test Device")
        assert retrieved is None
    
    @patch('builtins.open', create=True)
    @patch('json.load')
    def test_load_configs_from_file(self, mock_json_load, mock_open, config_service):
        """Test loading configurations from file"""
        mock_json_load.return_value = [
            {"name": "Device1", "hostname": "192.168.1.100"},
            {"name": "Device2", "hostname": "192.168.1.101"}
        ]
        
        loaded = config_service.load_configs_from_file("test.json")
        assert len(loaded) == 2
        assert "Device1" in loaded
        assert "Device2" in loaded


class TestDevice:
    """Test Device class"""
    
    @pytest.fixture
    def device(self):
        """Create test device"""
        from web.backend.core.device import Device
        return Device(
            name="Test Device",
            hostname="192.168.1.100",
            device_type="dlna"
        )
    
    def test_device_initialization(self, device):
        """Test device initialization"""
        assert device.name == "Test Device"
        assert device.hostname == "192.168.1.100"
        assert device.device_type == "dlna"
        assert device.status == "disconnected"
        assert device.is_playing is False
    
    def test_update_streaming_info(self, device):
        """Test updating streaming info"""
        device.update_streaming_info(
            streaming_url="http://localhost:8888/stream/test.mp4",
            streaming_port=8888
        )
        
        assert device.streaming_url == "http://localhost:8888/stream/test.mp4"
        assert device.streaming_port == 8888
    
    def test_to_dict(self, device):
        """Test converting device to dictionary"""
        device_dict = device.to_dict()
        
        assert device_dict["name"] == "Test Device"
        assert device_dict["hostname"] == "192.168.1.100"
        assert device_dict["device_type"] == "dlna"
        assert device_dict["status"] == "disconnected"
        assert "is_playing" in device_dict


class TestDLNADevice:
    """Test DLNADevice class"""
    
    @pytest.fixture
    def mock_device_info(self):
        """Create mock device info"""
        return {
            "name": "Test DLNA Device",
            "hostname": "192.168.1.100",
            "port": 8000,
            "location": "http://192.168.1.100:8000/device.xml",
            "action_url": "http://192.168.1.100:8000/control"
        }
    
    @pytest.fixture
    def dlna_device(self, mock_device_info):
        """Create DLNA device"""
        from web.backend.core.dlna_device import DLNADevice
        with patch('web.backend.core.dlna_device.DLNADevice._send_dlna_action'):
            return DLNADevice(mock_device_info)
    
    def test_dlna_device_initialization(self, dlna_device):
        """Test DLNA device initialization"""
        assert dlna_device.name == "Test DLNA Device"
        assert dlna_device.hostname == "192.168.1.100"
        assert dlna_device.action_url == "http://192.168.1.100:8000/control"
    
    @patch('web.backend.core.dlna_device.DLNADevice._send_dlna_action')
    def test_play(self, mock_send_action, dlna_device):
        """Test playing video"""
        mock_send_action.return_value = (200, "OK")
        
        result = dlna_device.play("http://localhost:8888/stream/test.mp4", loop=True)
        assert result is True
        assert dlna_device.is_playing is True
        assert dlna_device.current_video == "http://localhost:8888/stream/test.mp4"
    
    @patch('web.backend.core.dlna_device.DLNADevice._send_dlna_action')
    def test_stop(self, mock_send_action, dlna_device):
        """Test stopping playback"""
        dlna_device.is_playing = True
        mock_send_action.return_value = (200, "OK")
        
        result = dlna_device.stop()
        assert result is True
        assert dlna_device.is_playing is False
        assert dlna_device.current_video is None
    
    @patch('web.backend.core.dlna_device.DLNADevice._send_dlna_action')
    def test_pause(self, mock_send_action, dlna_device):
        """Test pausing playback"""
        dlna_device.is_playing = True
        mock_send_action.return_value = (200, "OK")
        
        result = dlna_device.pause()
        assert result is True
    
    @patch('web.backend.core.dlna_device.DLNADevice._send_dlna_action')
    def test_set_brightness(self, mock_send_action, dlna_device):
        """Test setting brightness"""
        mock_send_action.return_value = (200, "OK")
        
        result = dlna_device.set_brightness(50)
        assert result is True


class TestTwistedStreaming:
    """Test TwistedStreamingServer"""
    
    @pytest.fixture
    def streaming_server(self):
        """Create streaming server"""
        from web.backend.core.twisted_streaming import TwistedStreamingServer
        # Reset singleton
        TwistedStreamingServer._instance = None
        return TwistedStreamingServer.get_instance()
    
    def test_singleton(self, streaming_server):
        """Test singleton pattern"""
        from web.backend.core.twisted_streaming import TwistedStreamingServer
        server2 = TwistedStreamingServer.get_instance()
        assert streaming_server is server2
    
    @patch('web.backend.core.twisted_streaming.reactor')
    @patch('web.backend.core.twisted_streaming.endpoints')
    def test_start_server(self, mock_endpoints, mock_reactor, streaming_server):
        """Test starting streaming server"""
        mock_endpoint = Mock()
        mock_endpoints.TCP4ServerEndpoint.return_value = mock_endpoint
        mock_endpoint.listen.return_value = Mock()
        
        files = {"test.mp4": "/videos/test.mp4"}
        urls, server = streaming_server.start_server(
            files=files,
            serve_ip="192.168.1.10",
            port=9000
        )
        
        assert "test.mp4" in urls
        assert urls["test.mp4"] == "http://192.168.1.10:9000/test.mp4"
    
    def test_stop_all_servers(self, streaming_server):
        """Test stopping all servers"""
        streaming_server.active_servers = {"test": Mock()}
        
        streaming_server.stop_all_servers()
        assert len(streaming_server.active_servers) == 0


class TestStreamingSession:
    """Test StreamingSession"""
    
    @pytest.fixture
    def streaming_session(self):
        """Create streaming session"""
        from web.backend.core.streaming_session import StreamingSession
        return StreamingSession(
            device_name="Test Device",
            video_path="/videos/test.mp4",
            streaming_url="http://localhost:8888/stream/test.mp4",
            streaming_port=8888
        )
    
    def test_session_initialization(self, streaming_session):
        """Test session initialization"""
        assert streaming_session.device_name == "Test Device"
        assert streaming_session.video_path == "/videos/test.mp4"
        assert streaming_session.streaming_url == "http://localhost:8888/stream/test.mp4"
        assert streaming_session.streaming_port == 8888
        assert streaming_session.is_active is True
    
    def test_update_activity(self, streaming_session):
        """Test updating activity"""
        initial_time = streaming_session.last_activity
        streaming_session.update_activity()
        assert streaming_session.last_activity > initial_time
    
    def test_stop_session(self, streaming_session):
        """Test stopping session"""
        streaming_session.stop()
        assert streaming_session.is_active is False
        assert streaming_session.end_time is not None
    
    def test_to_dict(self, streaming_session):
        """Test converting session to dictionary"""
        session_dict = streaming_session.to_dict()
        
        assert session_dict["device_name"] == "Test Device"
        assert session_dict["video_path"] == "/videos/test.mp4"
        assert session_dict["streaming_url"] == "http://localhost:8888/stream/test.mp4"
        assert session_dict["is_active"] is True
        assert "id" in session_dict
        assert "start_time" in session_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])