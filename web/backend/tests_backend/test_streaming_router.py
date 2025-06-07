"""
Tests for the streaming router.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from web.backend.main import app
from web.backend.models.device import DeviceModel
from web.backend.models.video import VideoModel
from web.backend.core.streaming_registry import StreamingSessionRegistry
from web.backend.core.streaming_session import StreamingSession


class TestStreamingRouter:
    """Tests for the streaming router."""
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    def test_get_streaming_status(self, mock_registry_class, test_client):
        """Test getting streaming status."""
        # Configure the mock
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_registry.get_active_sessions.return_value = [
            {
                "id": "session1",
                "device_id": 1,
                "video_id": 2,
                "start_time": "2025-05-11T12:00:00",
                "status": "active"
            },
            {
                "id": "session2",
                "device_id": 3,
                "video_id": 4,
                "start_time": "2025-05-11T12:30:00",
                "status": "active"
            }
        ]
        
        # Make the request
        response = test_client.get("/api/streaming/status")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert "active_sessions" in data
        assert len(data["active_sessions"]) == 2
        assert data["active_sessions"][0]["id"] == "session1"
        assert data["active_sessions"][1]["id"] == "session2"
        
        # Verify the mock was called correctly
        mock_registry_class.get_instance.assert_called_once()
        mock_registry.get_active_sessions.assert_called_once()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    @patch("web.backend.routers.streaming_router.DeviceService")
    def test_start_streaming(self, mock_device_service_class, mock_registry_class, test_client, test_db):
        """Test starting a streaming session."""
        # Create test data in the database
        db = test_db
        
        # Create a test device
        device = DeviceModel(
            name="Test Device",
            type="dlna",
            hostname="127.0.0.1",
            action_url="http://127.0.0.1:8000/action",
            location="http://127.0.0.1:8000/location",
            friendly_name="Test Device",
            status="online"
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Create a test video
        video = VideoModel(
            name="Test Video",
            path="/path/to/test_video.mp4",
            file_name="test_video.mp4",
            format="mp4",
            file_size=1024
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        
        # Configure the mocks
        mock_device_service = MagicMock()
        mock_device_service_class.return_value = mock_device_service
        mock_device_service.play_video.return_value = True
        
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_session = MagicMock()
        mock_session.id = "test_session_id"
        mock_session.to_dict.return_value = {
            "id": "test_session_id",
            "device_id": device.id,
            "video_id": video.id,
            "start_time": "2025-05-11T12:00:00",
            "status": "active"
        }
        mock_registry.create_session.return_value = mock_session
        
        # Prepare the request data
        request_data = {
            "device_id": device.id,
            "video_id": video.id
        }
        
        # Make the request
        response = test_client.post("/api/streaming/start", json=request_data)
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Started streaming session" in data["message"]
        assert data["session"]["id"] == "test_session_id"
        assert data["session"]["device_id"] == device.id
        assert data["session"]["video_id"] == video.id
        
        # Verify the mocks were called correctly
        mock_device_service.play_video.assert_called_once_with(device.id, video.id, loop=True)
        mock_registry.create_session.assert_called_once_with(device.id, video.id)
        
        # Clean up
        db.delete(video)
        db.delete(device)
        db.commit()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    @patch("web.backend.routers.streaming_router.DeviceService")
    def test_start_streaming_failure(self, mock_device_service_class, mock_registry_class, test_client, test_db):
        """Test starting a streaming session with failure."""
        # Create test data in the database
        db = test_db
        
        # Create a test device
        device = DeviceModel(
            name="Test Device",
            type="dlna",
            hostname="127.0.0.1",
            action_url="http://127.0.0.1:8000/action",
            location="http://127.0.0.1:8000/location",
            friendly_name="Test Device",
            status="online"
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Create a test video
        video = VideoModel(
            name="Test Video",
            path="/path/to/test_video.mp4",
            file_name="test_video.mp4",
            format="mp4",
            file_size=1024
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        
        # Configure the mocks
        mock_device_service = MagicMock()
        mock_device_service_class.return_value = mock_device_service
        mock_device_service.play_video.return_value = False
        
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        
        # Prepare the request data
        request_data = {
            "device_id": device.id,
            "video_id": video.id
        }
        
        # Make the request
        response = test_client.post("/api/streaming/start", json=request_data)
        
        # Check the response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to start streaming" in data["detail"]
        
        # Verify the mocks were called correctly
        mock_device_service.play_video.assert_called_once_with(device.id, video.id, loop=True)
        mock_registry.create_session.assert_not_called()
        
        # Clean up
        db.delete(video)
        db.delete(device)
        db.commit()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    @patch("web.backend.routers.streaming_router.DeviceService")
    def test_start_streaming_invalid_device(self, mock_device_service_class, mock_registry_class, test_client, test_db):
        """Test starting a streaming session with an invalid device."""
        # Create test data in the database
        db = test_db
        
        # Create a test video
        video = VideoModel(
            name="Test Video",
            path="/path/to/test_video.mp4",
            file_name="test_video.mp4",
            format="mp4",
            file_size=1024
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        
        # Configure the mocks
        mock_device_service = MagicMock()
        mock_device_service_class.return_value = mock_device_service
        
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        
        # Prepare the request data with an invalid device ID
        request_data = {
            "device_id": 9999,  # Non-existent device ID
            "video_id": video.id
        }
        
        # Make the request
        response = test_client.post("/api/streaming/start", json=request_data)
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Device not found" in data["detail"]
        
        # Verify the mocks were not called
        mock_device_service.play_video.assert_not_called()
        mock_registry.create_session.assert_not_called()
        
        # Clean up
        db.delete(video)
        db.commit()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    @patch("web.backend.routers.streaming_router.DeviceService")
    def test_start_streaming_invalid_video(self, mock_device_service_class, mock_registry_class, test_client, test_db):
        """Test starting a streaming session with an invalid video."""
        # Create test data in the database
        db = test_db
        
        # Create a test device
        device = DeviceModel(
            name="Test Device",
            type="dlna",
            hostname="127.0.0.1",
            action_url="http://127.0.0.1:8000/action",
            location="http://127.0.0.1:8000/location",
            friendly_name="Test Device",
            status="online"
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Configure the mocks
        mock_device_service = MagicMock()
        mock_device_service_class.return_value = mock_device_service
        
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        
        # Prepare the request data with an invalid video ID
        request_data = {
            "device_id": device.id,
            "video_id": 9999  # Non-existent video ID
        }
        
        # Make the request
        response = test_client.post("/api/streaming/start", json=request_data)
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Video not found" in data["detail"]
        
        # Verify the mocks were not called
        mock_device_service.play_video.assert_not_called()
        mock_registry.create_session.assert_not_called()
        
        # Clean up
        db.delete(device)
        db.commit()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    @patch("web.backend.routers.streaming_router.DeviceService")
    def test_stop_streaming(self, mock_device_service_class, mock_registry_class, test_client, test_db):
        """Test stopping a streaming session."""
        # Create test data in the database
        db = test_db
        
        # Create a test device
        device = DeviceModel(
            name="Test Device",
            type="dlna",
            hostname="127.0.0.1",
            action_url="http://127.0.0.1:8000/action",
            location="http://127.0.0.1:8000/location",
            friendly_name="Test Device",
            status="online"
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Configure the mocks
        mock_device_service = MagicMock()
        mock_device_service_class.return_value = mock_device_service
        mock_device_service.stop_playback.return_value = True
        
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_registry.get_session.return_value = MagicMock(
            id="test_session_id",
            device_id=device.id,
            video_id=1
        )
        
        # Make the request
        response = test_client.post(f"/api/streaming/stop/{device.id}")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Stopped streaming" in data["message"]
        
        # Verify the mocks were called correctly
        mock_device_service.stop_playback.assert_called_once_with(device.id)
        mock_registry.end_session.assert_called_once_with(device.id)
        
        # Clean up
        db.delete(device)
        db.commit()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    @patch("web.backend.routers.streaming_router.DeviceService")
    def test_stop_streaming_failure(self, mock_device_service_class, mock_registry_class, test_client, test_db):
        """Test stopping a streaming session with failure."""
        # Create test data in the database
        db = test_db
        
        # Create a test device
        device = DeviceModel(
            name="Test Device",
            type="dlna",
            hostname="127.0.0.1",
            action_url="http://127.0.0.1:8000/action",
            location="http://127.0.0.1:8000/location",
            friendly_name="Test Device",
            status="online"
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Configure the mocks
        mock_device_service = MagicMock()
        mock_device_service_class.return_value = mock_device_service
        mock_device_service.stop_playback.return_value = False
        
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_registry.get_session.return_value = MagicMock(
            id="test_session_id",
            device_id=device.id,
            video_id=1
        )
        
        # Make the request
        response = test_client.post(f"/api/streaming/stop/{device.id}")
        
        # Check the response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to stop streaming" in data["detail"]
        
        # Verify the mocks were called correctly
        mock_device_service.stop_playback.assert_called_once_with(device.id)
        mock_registry.end_session.assert_not_called()
        
        # Clean up
        db.delete(device)
        db.commit()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    @patch("web.backend.routers.streaming_router.DeviceService")
    def test_stop_streaming_invalid_device(self, mock_device_service_class, mock_registry_class, test_client):
        """Test stopping a streaming session with an invalid device."""
        # Configure the mocks
        mock_device_service = MagicMock()
        mock_device_service_class.return_value = mock_device_service
        
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        
        # Make the request with an invalid device ID
        response = test_client.post("/api/streaming/stop/9999")
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Device not found" in data["detail"]
        
        # Verify the mocks were not called
        mock_device_service.stop_playback.assert_not_called()
        mock_registry.end_session.assert_not_called()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    @patch("web.backend.routers.streaming_router.DeviceService")
    def test_stop_all_streaming(self, mock_device_service_class, mock_registry_class, test_client):
        """Test stopping all streaming sessions."""
        # Configure the mocks
        mock_device_service = MagicMock()
        mock_device_service_class.return_value = mock_device_service
        mock_device_service.stop_all_playback.return_value = True
        
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        
        # Make the request
        response = test_client.post("/api/streaming/stop/all")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Stopped all streaming sessions" in data["message"]
        
        # Verify the mocks were called correctly
        mock_device_service.stop_all_playback.assert_called_once()
        mock_registry.end_all_sessions.assert_called_once()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    @patch("web.backend.routers.streaming_router.DeviceService")
    def test_stop_all_streaming_failure(self, mock_device_service_class, mock_registry_class, test_client):
        """Test stopping all streaming sessions with failure."""
        # Configure the mocks
        mock_device_service = MagicMock()
        mock_device_service_class.return_value = mock_device_service
        mock_device_service.stop_all_playback.return_value = False
        
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        
        # Make the request
        response = test_client.post("/api/streaming/stop/all")
        
        # Check the response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to stop all streaming sessions" in data["detail"]
        
        # Verify the mocks were called correctly
        mock_device_service.stop_all_playback.assert_called_once()
        mock_registry.end_all_sessions.assert_not_called()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    def test_get_streaming_session(self, mock_registry_class, test_client, test_db):
        """Test getting a streaming session."""
        # Create test data in the database
        db = test_db
        
        # Create a test device
        device = DeviceModel(
            name="Test Device",
            type="dlna",
            hostname="127.0.0.1",
            action_url="http://127.0.0.1:8000/action",
            location="http://127.0.0.1:8000/location",
            friendly_name="Test Device",
            status="online"
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Configure the mocks
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_session = MagicMock()
        mock_session.to_dict.return_value = {
            "id": "test_session_id",
            "device_id": device.id,
            "video_id": 1,
            "start_time": "2025-05-11T12:00:00",
            "status": "active"
        }
        mock_registry.get_session.return_value = mock_session
        
        # Make the request
        response = test_client.get(f"/api/streaming/session/{device.id}")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_session_id"
        assert data["device_id"] == device.id
        assert data["video_id"] == 1
        assert data["status"] == "active"
        
        # Verify the mock was called correctly
        mock_registry.get_session.assert_called_once_with(device.id)
        
        # Clean up
        db.delete(device)
        db.commit()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    def test_get_streaming_session_not_found(self, mock_registry_class, test_client, test_db):
        """Test getting a streaming session that doesn't exist."""
        # Create test data in the database
        db = test_db
        
        # Create a test device
        device = DeviceModel(
            name="Test Device",
            type="dlna",
            hostname="127.0.0.1",
            action_url="http://127.0.0.1:8000/action",
            location="http://127.0.0.1:8000/location",
            friendly_name="Test Device",
            status="online"
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Configure the mocks
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        mock_registry.get_session.return_value = None
        
        # Make the request
        response = test_client.get(f"/api/streaming/session/{device.id}")
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "No active streaming session found" in data["detail"]
        
        # Verify the mock was called correctly
        mock_registry.get_session.assert_called_once_with(device.id)
        
        # Clean up
        db.delete(device)
        db.commit()
    
    @patch("web.backend.routers.streaming_router.StreamingSessionRegistry")
    def test_get_streaming_session_invalid_device(self, mock_registry_class, test_client):
        """Test getting a streaming session for an invalid device."""
        # Configure the mocks
        mock_registry = MagicMock()
        mock_registry_class.get_instance.return_value = mock_registry
        
        # Make the request with an invalid device ID
        response = test_client.get("/api/streaming/session/9999")
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Device not found" in data["detail"]
        
        # Verify the mock was not called
        mock_registry.get_session.assert_not_called()
