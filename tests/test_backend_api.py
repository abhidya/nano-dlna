#!/usr/bin/env python3
"""
Backend API tests for better coverage
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def mock_app():
    """Create mock FastAPI app"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    app = FastAPI()
    
    # Mock the main app initialization
    with patch('web.backend.main.create_app') as mock_create:
        mock_create.return_value = app
        
        # Import routers after patching
        from web.backend.routers import device_router, video_router
        
        # Add routers
        app.include_router(device_router.router, prefix="/api")
        app.include_router(video_router.router, prefix="/api")
        
        client = TestClient(app)
        yield client

class TestDeviceAPI:
    """Test device API endpoints"""
    
    @patch('web.backend.services.device_service.DeviceService')
    def test_get_devices(self, mock_service_class, mock_app):
        """Test GET /api/devices/"""
        # Mock service instance
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_devices.return_value = []
        
        response = mock_app.get("/api/devices/")
        assert response.status_code == 200
        assert response.json() == []
    
    @patch('web.backend.services.device_service.DeviceService')
    def test_get_device_by_id(self, mock_service_class, mock_app):
        """Test GET /api/devices/{device_id}"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock device data
        device_data = {
            "id": 1,
            "name": "Test Device",
            "hostname": "192.168.1.100",
            "is_playing": False
        }
        mock_service.get_device.return_value = device_data
        
        response = mock_app.get("/api/devices/1")
        assert response.status_code == 200
        assert response.json() == device_data
    
    @patch('web.backend.services.device_service.DeviceService')
    def test_play_video_on_device(self, mock_service_class, mock_app):
        """Test POST /api/devices/{device_id}/play/{video_id}"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.play_video.return_value = {"status": "playing"}
        
        response = mock_app.post("/api/devices/1/play/1")
        assert response.status_code == 200
        assert response.json() == {"status": "playing"}
    
    @patch('web.backend.services.device_service.DeviceService')
    def test_stop_device(self, mock_service_class, mock_app):
        """Test POST /api/devices/{device_id}/stop"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.stop_device.return_value = {"status": "stopped"}
        
        response = mock_app.post("/api/devices/1/stop")
        assert response.status_code == 200
        assert response.json() == {"status": "stopped"}

class TestVideoAPI:
    """Test video API endpoints"""
    
    @patch('web.backend.services.video_service.VideoService')
    def test_get_videos(self, mock_service_class, mock_app):
        """Test GET /api/videos/"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_videos.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "per_page": 20
        }
        
        response = mock_app.get("/api/videos/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 0
    
    @patch('web.backend.services.video_service.VideoService')
    def test_get_video_by_id(self, mock_service_class, mock_app):
        """Test GET /api/videos/{video_id}"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        video_data = {
            "id": 1,
            "name": "test.mp4",
            "path": "/videos/test.mp4",
            "duration": 120
        }
        mock_service.get_video.return_value = video_data
        
        response = mock_app.get("/api/videos/1")
        assert response.status_code == 200
        assert response.json() == video_data

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, mock_app):
        """Test GET /api/health"""
        response = mock_app.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

class TestStreamingService:
    """Test streaming service"""
    
    @patch('web.backend.core.streaming_service.Config')
    def test_streaming_service_init(self, mock_config_class):
        """Test StreamingService initialization"""
        from web.backend.core.streaming_service import StreamingService
        
        mock_config = Mock()
        mock_config.stream_base_url = "http://localhost:8888"
        mock_config.stream_protocol = "http"
        mock_config_class.return_value = mock_config
        
        service = StreamingService()
        assert service.config == mock_config
    
    @patch('web.backend.core.streaming_service.Config')
    def test_get_stream_url(self, mock_config_class):
        """Test stream URL generation"""
        from web.backend.core.streaming_service import StreamingService
        
        mock_config = Mock()
        mock_config.stream_base_url = "http://localhost:8888"
        mock_config.stream_protocol = "http"
        mock_config_class.return_value = mock_config
        
        service = StreamingService()
        url = service.get_stream_url("/videos/test.mp4")
        assert url == "http://localhost:8888/stream/videos/test.mp4"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])