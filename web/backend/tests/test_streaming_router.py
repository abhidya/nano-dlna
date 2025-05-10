import pytest
import os
import json
from unittest.mock import patch, MagicMock

@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_get_streaming_stats(mock_get_instance, client):
    """Test the GET /api/streaming/ endpoint"""
    # Mock the registry instance
    mock_registry = MagicMock()
    mock_registry.get_streaming_stats.return_value = {
        "active_sessions": 2,
        "total_bytes": 1024000,
        "average_bitrate": 512000,
        "active_devices": 1
    }
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint
    response = client.get("/api/streaming/")
    assert response.status_code == 200
    data = response.json()
    assert data["active_sessions"] == 2
    assert data["total_bytes"] == 1024000
    assert data["average_bitrate"] == 512000
    assert data["active_devices"] == 1
    mock_registry.get_streaming_stats.assert_called_once()


@patch('services.device_service.DeviceService.play_video')
def test_start_streaming_success(mock_play_video, client, test_db):
    """Test the POST /api/streaming/start endpoint with success"""
    # Mock the play_video method to return True (success)
    mock_play_video.return_value = True
    
    # Create a temporary video file
    with open("/tmp/test_streaming.mp4", "w") as f:
        f.write("test video content")
    
    # Patch os.path.exists to return True for the video path
    with patch('os.path.exists', return_value=True):
        # Test the endpoint
        response = client.post(
            "/api/streaming/start",
            params={"device_id": 1, "video_path": "/tmp/test_streaming.mp4"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "streaming started" in data["message"].lower()
        mock_play_video.assert_called_once_with(1, "/tmp/test_streaming.mp4", loop=True)
    
    # Clean up
    if os.path.exists("/tmp/test_streaming.mp4"):
        os.remove("/tmp/test_streaming.mp4")


def test_start_streaming_video_not_found(client, test_db):
    """Test the POST /api/streaming/start endpoint with non-existent video file"""
    # Patch os.path.exists to return False for the video path
    with patch('os.path.exists', return_value=False):
        # Test the endpoint with non-existent video file
        response = client.post(
            "/api/streaming/start",
            params={"device_id": 1, "video_path": "/path/to/nonexistent.mp4"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@patch('services.device_service.DeviceService.play_video')
def test_start_streaming_play_failed(mock_play_video, client, test_db):
    """Test the POST /api/streaming/start endpoint with play failure"""
    # Mock the play_video method to return False (failure)
    mock_play_video.return_value = False
    
    # Patch os.path.exists to return True for the video path
    with patch('os.path.exists', return_value=True):
        # Test the endpoint with play failure
        response = client.post(
            "/api/streaming/start",
            params={"device_id": 1, "video_path": "/path/to/test.mp4"}
        )
        assert response.status_code == 500
        assert "failed to start streaming" in response.json()["detail"].lower()
        mock_play_video.assert_called_once_with(1, "/path/to/test.mp4", loop=True)


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_get_all_sessions(mock_get_instance, client):
    """Test the GET /api/streaming/sessions endpoint"""
    # Mock the registry instance
    mock_registry = MagicMock()
    mock_session1 = MagicMock()
    mock_session1.to_dict.return_value = {
        "id": "session1",
        "device_name": "device1",
        "video_path": "/path/to/video1.mp4",
        "status": "active",
        "start_time": "2025-05-05T10:00:00",
        "last_activity_time": "2025-05-05T10:05:00"
    }
    mock_session2 = MagicMock()
    mock_session2.to_dict.return_value = {
        "id": "session2",
        "device_name": "device2",
        "video_path": "/path/to/video2.mp4",
        "status": "completed",
        "start_time": "2025-05-05T09:00:00",
        "last_activity_time": "2025-05-05T09:30:00"
    }
    mock_registry.get_active_sessions.return_value = [mock_session1, mock_session2]
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint
    response = client.get("/api/streaming/sessions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "session1"
    assert data[0]["device_name"] == "device1"
    assert data[0]["status"] == "active"
    assert data[1]["id"] == "session2"
    assert data[1]["device_name"] == "device2"
    assert data[1]["status"] == "completed"
    mock_registry.get_active_sessions.assert_called_once()


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_get_session_found(mock_get_instance, client):
    """Test the GET /api/streaming/sessions/{session_id} endpoint with existing session"""
    # Mock the registry instance
    mock_registry = MagicMock()
    mock_session = MagicMock()
    mock_session.to_dict.return_value = {
        "id": "session1",
        "device_name": "device1",
        "video_path": "/path/to/video1.mp4",
        "status": "active",
        "start_time": "2025-05-05T10:00:00",
        "last_activity_time": "2025-05-05T10:05:00"
    }
    mock_registry.get_session.return_value = mock_session
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint
    response = client.get("/api/streaming/sessions/session1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "session1"
    assert data["device_name"] == "device1"
    assert data["status"] == "active"
    mock_registry.get_session.assert_called_once_with("session1")


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_get_session_not_found(mock_get_instance, client):
    """Test the GET /api/streaming/sessions/{session_id} endpoint with non-existent session"""
    # Mock the registry instance
    mock_registry = MagicMock()
    mock_registry.get_session.return_value = None
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint with non-existent session
    response = client.get("/api/streaming/sessions/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    mock_registry.get_session.assert_called_once_with("nonexistent")


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_get_sessions_for_device(mock_get_instance, client):
    """Test the GET /api/streaming/device/{device_name} endpoint"""
    # Mock the registry instance
    mock_registry = MagicMock()
    mock_session1 = MagicMock()
    mock_session1.to_dict.return_value = {
        "id": "session1",
        "device_name": "device1",
        "video_path": "/path/to/video1.mp4",
        "status": "active",
        "start_time": "2025-05-05T10:00:00",
        "last_activity_time": "2025-05-05T10:05:00"
    }
    mock_session2 = MagicMock()
    mock_session2.to_dict.return_value = {
        "id": "session2",
        "device_name": "device1",
        "video_path": "/path/to/video2.mp4",
        "status": "completed",
        "start_time": "2025-05-05T09:00:00",
        "last_activity_time": "2025-05-05T09:30:00"
    }
    mock_registry.get_sessions_for_device.return_value = [mock_session1, mock_session2]
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint
    response = client.get("/api/streaming/device/device1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "session1"
    assert data[0]["device_name"] == "device1"
    assert data[0]["status"] == "active"
    assert data[1]["id"] == "session2"
    assert data[1]["device_name"] == "device1"
    assert data[1]["status"] == "completed"
    mock_registry.get_sessions_for_device.assert_called_once_with("device1")


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_complete_session_success(mock_get_instance, client):
    """Test the POST /api/streaming/sessions/{session_id}/complete endpoint with success"""
    # Mock the registry instance
    mock_registry = MagicMock()
    mock_session = MagicMock()
    mock_registry.get_session.return_value = mock_session
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint
    response = client.post("/api/streaming/sessions/session1/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "marked as completed" in data["message"].lower()
    mock_registry.get_session.assert_called_once_with("session1")
    mock_session.complete.assert_called_once()


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_complete_session_not_found(mock_get_instance, client):
    """Test the POST /api/streaming/sessions/{session_id}/complete endpoint with non-existent session"""
    # Mock the registry instance
    mock_registry = MagicMock()
    mock_registry.get_session.return_value = None
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint with non-existent session
    response = client.post("/api/streaming/sessions/nonexistent/complete")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    mock_registry.get_session.assert_called_once_with("nonexistent")


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_reset_session_success(mock_get_instance, client):
    """Test the POST /api/streaming/sessions/{session_id}/reset endpoint with success"""
    # Mock the registry instance
    mock_registry = MagicMock()
    mock_session = MagicMock()
    mock_registry.get_session.return_value = mock_session
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint
    response = client.post("/api/streaming/sessions/session1/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "reset to active status" in data["message"].lower()
    mock_registry.get_session.assert_called_once_with("session1")
    assert mock_session.status == "active"
    mock_session.update_activity.assert_called_once()


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_reset_session_not_found(mock_get_instance, client):
    """Test the POST /api/streaming/sessions/{session_id}/reset endpoint with non-existent session"""
    # Mock the registry instance
    mock_registry = MagicMock()
    mock_registry.get_session.return_value = None
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint with non-existent session
    response = client.post("/api/streaming/sessions/nonexistent/reset")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    mock_registry.get_session.assert_called_once_with("nonexistent")


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_get_streaming_analytics(mock_get_instance, client):
    """Test the GET /api/streaming/analytics endpoint"""
    # Mock the registry instance
    mock_registry = MagicMock()
    mock_registry.get_streaming_stats.return_value = {
        "active_sessions": 2,
        "total_bytes": 1024000,
        "average_bitrate": 512000,
        "active_devices": 1
    }
    
    # Mock active sessions
    mock_session1 = MagicMock()
    mock_session1.get_bandwidth.return_value = 256000
    mock_session1.connection_history = ["conn1", "conn2"]
    mock_session1.last_activity_time.timestamp.return_value = 1620200700
    mock_session1.start_time.timestamp.return_value = 1620200400
    
    mock_session2 = MagicMock()
    mock_session2.get_bandwidth.return_value = 128000
    mock_session2.connection_history = ["conn3"]
    mock_session2.last_activity_time.timestamp.return_value = 1620200600
    mock_session2.start_time.timestamp.return_value = 1620200400
    
    mock_registry.get_active_sessions.return_value = [mock_session1, mock_session2]
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint
    response = client.get("/api/streaming/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["active_sessions"] == 2
    assert data["total_bytes"] == 1024000
    assert data["average_bitrate"] == 512000
    assert data["active_devices"] == 1
    assert data["total_bandwidth_bps"] == 384000  # 256000 + 128000
    assert data["connection_events"] == 3  # 2 + 1
    mock_registry.get_streaming_stats.assert_called_once()
    mock_registry.get_active_sessions.assert_called_once()


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_get_streaming_health(mock_get_instance, client):
    """Test the GET /api/streaming/health endpoint"""
    # Mock the registry instance
    mock_registry = MagicMock()
    
    # Mock active sessions
    mock_session1 = MagicMock()
    mock_session1.is_stalled.return_value = False
    mock_session1.connection_errors = 0
    
    mock_session2 = MagicMock()
    mock_session2.is_stalled.return_value = True
    mock_session2.connection_errors = 2
    
    mock_registry.get_active_sessions.return_value = [mock_session1, mock_session2]
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint
    response = client.get("/api/streaming/health")
    assert response.status_code == 200
    data = response.json()
    assert data["stalled_sessions"] == 1
    assert data["error_sessions"] == 1
    assert data["total_active_sessions"] == 2
    assert "health_score" in data
    assert "status" in data
    mock_registry.get_active_sessions.assert_called_once()


@patch('core.streaming_registry.StreamingSessionRegistry.get_instance')
def test_get_streaming_health_no_sessions(mock_get_instance, client):
    """Test the GET /api/streaming/health endpoint with no active sessions"""
    # Mock the registry instance
    mock_registry = MagicMock()
    mock_registry.get_active_sessions.return_value = []
    mock_get_instance.return_value = mock_registry
    
    # Test the endpoint with no active sessions
    response = client.get("/api/streaming/health")
    assert response.status_code == 200
    data = response.json()
    assert data["stalled_sessions"] == 0
    assert data["error_sessions"] == 0
    assert data["total_active_sessions"] == 0
    assert data["health_score"] == 100
    assert data["status"] == "healthy"
    mock_registry.get_active_sessions.assert_called_once()
