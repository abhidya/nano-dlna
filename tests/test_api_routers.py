#!/usr/bin/env python3
"""
API router tests for FastAPI endpoints
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web', 'backend'))


@pytest.fixture
def app():
    """Create FastAPI app for testing"""
    from web.backend.main import create_app
    return create_app()


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


class TestDeviceRouter:
    """Test device API endpoints"""
    
    @patch('web.backend.routers.device_router.DeviceService')
    def test_get_devices(self, mock_service_class, client):
        """Test GET /api/devices/"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_devices.return_value = [
            {"id": 1, "name": "Device 1", "is_playing": False},
            {"id": 2, "name": "Device 2", "is_playing": True}
        ]
        
        response = client.get("/api/devices/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Device 1"
    
    @patch('web.backend.routers.device_router.DeviceService')
    def test_get_device_by_id(self, mock_service_class, client):
        """Test GET /api/devices/{device_id}"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_device.return_value = {
            "id": 1,
            "name": "Test Device",
            "is_playing": False
        }
        
        response = client.get("/api/devices/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Device"
    
    @patch('web.backend.routers.device_router.DeviceService')
    def test_play_video(self, mock_service_class, client):
        """Test POST /api/devices/{device_id}/play/{video_id}"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.play_video.return_value = {"status": "playing"}
        
        response = client.post("/api/devices/1/play/1?loop=true")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "playing"
    
    @patch('web.backend.routers.device_router.DeviceService')
    def test_stop_device(self, mock_service_class, client):
        """Test POST /api/devices/{device_id}/stop"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.stop_device.return_value = {"status": "stopped"}
        
        response = client.post("/api/devices/1/stop")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"
    
    @patch('web.backend.routers.device_router.DeviceService')
    def test_pause_device(self, mock_service_class, client):
        """Test POST /api/devices/{device_id}/pause"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.pause_device.return_value = {"status": "paused"}
        
        response = client.post("/api/devices/1/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"
    
    @patch('web.backend.routers.device_router.DeviceService')
    def test_seek_device(self, mock_service_class, client):
        """Test POST /api/devices/{device_id}/seek"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.seek_device.return_value = {"status": "seeked", "position": 30}
        
        response = client.post("/api/devices/1/seek?position=30")
        assert response.status_code == 200
        data = response.json()
        assert data["position"] == 30


class TestVideoRouter:
    """Test video API endpoints"""
    
    @patch('web.backend.routers.video_router.VideoService')
    def test_get_videos(self, mock_service_class, client):
        """Test GET /api/videos/"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_videos.return_value = {
            "items": [
                {"id": 1, "name": "video1.mp4"},
                {"id": 2, "name": "video2.mp4"}
            ],
            "total": 2,
            "page": 1,
            "per_page": 20
        }
        
        response = client.get("/api/videos/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
    
    @patch('web.backend.routers.video_router.VideoService')
    def test_get_video_by_id(self, mock_service_class, client):
        """Test GET /api/videos/{video_id}"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.get_video.return_value = {
            "id": 1,
            "name": "test.mp4",
            "path": "/videos/test.mp4",
            "duration": 120
        }
        
        response = client.get("/api/videos/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test.mp4"
        assert data["duration"] == 120
    
    @patch('web.backend.routers.video_router.VideoService')
    def test_scan_videos(self, mock_service_class, client):
        """Test POST /api/videos/scan"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.scan_and_sync_videos.return_value = 5
        
        response = client.post("/api/videos/scan")
        assert response.status_code == 200
        data = response.json()
        assert data["videos_added"] == 5


class TestStreamingRouter:
    """Test streaming API endpoints"""
    
    @patch('web.backend.routers.streaming_router.StreamingRegistry')
    def test_get_active_sessions(self, mock_registry_class, client):
        """Test GET /api/streaming/sessions"""
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        mock_registry.get_active_sessions.return_value = [
            {
                "id": "session-1",
                "device_name": "Device 1",
                "video_path": "/videos/test.mp4",
                "is_active": True
            }
        ]
        
        response = client.get("/api/streaming/sessions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["device_name"] == "Device 1"
    
    @patch('web.backend.routers.streaming_router.StreamingRegistry')
    def test_get_session_by_id(self, mock_registry_class, client):
        """Test GET /api/streaming/sessions/{session_id}"""
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        mock_registry.get_session.return_value = {
            "id": "session-1",
            "device_name": "Device 1",
            "video_path": "/videos/test.mp4",
            "is_active": True
        }
        
        response = client.get("/api/streaming/sessions/session-1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "session-1"
    
    @patch('web.backend.routers.streaming_router.StreamingRegistry')
    def test_stop_session(self, mock_registry_class, client):
        """Test POST /api/streaming/sessions/{session_id}/stop"""
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        mock_registry.unregister_session.return_value = None
        
        response = client.post("/api/streaming/sessions/session-1/stop")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test GET /api/health"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @patch('web.backend.routers.device_router.DeviceManager')
    def test_device_discovery_status(self, mock_manager_class, client):
        """Test GET /api/devices/discovery/status"""
        mock_manager = Mock()
        mock_manager_class.get_instance.return_value = mock_manager
        mock_manager.discovery_active = True
        
        response = client.get("/api/devices/discovery/status")
        assert response.status_code == 200
        data = response.json()
        assert data["discovery_active"] is True
    
    @patch('web.backend.routers.device_router.DeviceManager')
    def test_pause_discovery(self, mock_manager_class, client):
        """Test POST /api/devices/discovery/pause"""
        mock_manager = Mock()
        mock_manager_class.get_instance.return_value = mock_manager
        
        response = client.post("/api/devices/discovery/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["discovery_active"] is False
        mock_manager.pause_discovery.assert_called_once()
    
    @patch('web.backend.routers.device_router.DeviceManager')
    def test_resume_discovery(self, mock_manager_class, client):
        """Test POST /api/devices/discovery/resume"""
        mock_manager = Mock()
        mock_manager_class.get_instance.return_value = mock_manager
        
        response = client.post("/api/devices/discovery/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["discovery_active"] is True
        mock_manager.resume_discovery.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])