"""API contract tests to ensure API stability and correctness."""

import json
from typing import Any, Dict
from jsonschema import validate, ValidationError
import pytest
from fastapi.testclient import TestClient

from web.backend.main import app
from tests.factories import DeviceFactory, VideoFactory
from tests.utils.test_helpers import DatabaseTestHelper


class APIContract:
    """API contract schemas for validation."""
    
    DEVICE_SCHEMA = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "type": {"type": "string", "enum": ["dlna", "airplay", "chromecast"]},
            "ip_address": {"type": "string", "format": "ipv4"},
            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
            "status": {"type": "string", "enum": ["connected", "disconnected", "playing", "error"]},
            "last_seen": {"type": "string", "format": "date-time"},
            "is_playing": {"type": "boolean"},
            "current_video_id": {"type": ["integer", "null"]},
            "playback_started_at": {"type": ["string", "null"], "format": "date-time"},
            "user_control_mode": {"type": "string", "enum": ["auto", "manual"]},
            "user_control_reason": {"type": ["string", "null"]}
        },
        "required": ["id", "name", "type", "ip_address", "port", "status", "is_playing"],
        "additionalProperties": False
    }
    
    VIDEO_SCHEMA = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "file_path": {"type": "string"},
            "file_size": {"type": "integer", "minimum": 0},
            "duration": {"type": "string"},
            "resolution": {"type": "string", "pattern": "^\\d+x\\d+$"},
            "codec": {"type": "string"},
            "bitrate": {"type": "integer", "minimum": 0},
            "uploaded_at": {"type": "string", "format": "date-time"},
            "last_played": {"type": ["string", "null"], "format": "date-time"},
            "play_count": {"type": "integer", "minimum": 0}
        },
        "required": ["id", "name", "file_path", "file_size", "duration"],
        "additionalProperties": False
    }
    
    PLAYBACK_RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["success", "error"]},
            "message": {"type": "string"},
            "device_id": {"type": "integer"},
            "video_id": {"type": "integer"},
            "stream_url": {"type": "string", "format": "uri"}
        },
        "required": ["status", "message"],
        "additionalProperties": False
    }
    
    ERROR_RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "detail": {
                "oneOf": [
                    {"type": "string"},
                    {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "loc": {"type": "array"},
                                "msg": {"type": "string"},
                                "type": {"type": "string"}
                            }
                        }
                    }
                ]
            }
        },
        "required": ["detail"]
    }


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_db():
    """Create test database with data."""
    with DatabaseTestHelper.temp_database() as db:
        DatabaseTestHelper.seed_test_data(db)
        yield db


class TestDeviceAPIContract:
    """Test device API endpoints for contract compliance."""
    
    def test_get_devices_contract(self, client, test_db):
        """Test GET /api/devices returns correct schema."""
        response = client.get("/api/devices/")
        assert response.status_code == 200
        
        devices = response.json()
        assert isinstance(devices, list)
        
        for device in devices:
            validate(device, APIContract.DEVICE_SCHEMA)
    
    def test_get_device_by_id_contract(self, client, test_db):
        """Test GET /api/devices/{id} returns correct schema."""
        # First create a device
        device_data = DeviceFactory.build().__dict__
        response = client.post("/api/devices/", json=device_data)
        device_id = response.json()["id"]
        
        # Get the device
        response = client.get(f"/api/devices/{device_id}")
        assert response.status_code == 200
        
        validate(response.json(), APIContract.DEVICE_SCHEMA)
    
    def test_create_device_contract(self, client):
        """Test POST /api/devices creates device with correct schema."""
        device_data = {
            "name": "Test Device",
            "type": "dlna",
            "ip_address": "192.168.1.100",
            "port": 8080
        }
        
        response = client.post("/api/devices/", json=device_data)
        assert response.status_code == 201
        
        validate(response.json(), APIContract.DEVICE_SCHEMA)
    
    def test_update_device_contract(self, client, test_db):
        """Test PUT /api/devices/{id} updates device correctly."""
        # Create a device first
        device_data = DeviceFactory.build().__dict__
        response = client.post("/api/devices/", json=device_data)
        device_id = response.json()["id"]
        
        # Update the device
        update_data = {"name": "Updated Device Name"}
        response = client.put(f"/api/devices/{device_id}", json=update_data)
        assert response.status_code == 200
        
        validate(response.json(), APIContract.DEVICE_SCHEMA)
        assert response.json()["name"] == "Updated Device Name"
    
    def test_device_not_found_contract(self, client):
        """Test device not found returns correct error schema."""
        response = client.get("/api/devices/99999")
        assert response.status_code == 404
        
        validate(response.json(), APIContract.ERROR_RESPONSE_SCHEMA)


class TestVideoAPIContract:
    """Test video API endpoints for contract compliance."""
    
    def test_get_videos_contract(self, client, test_db):
        """Test GET /api/videos returns correct schema."""
        response = client.get("/api/videos/")
        assert response.status_code == 200
        
        videos = response.json()
        assert isinstance(videos, list)
        
        for video in videos:
            validate(video, APIContract.VIDEO_SCHEMA)
    
    def test_upload_video_contract(self, client, tmp_path):
        """Test POST /api/videos/upload handles file upload correctly."""
        # Create a test video file
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video content")
        
        with open(video_file, "rb") as f:
            files = {"file": ("test.mp4", f, "video/mp4")}
            response = client.post("/api/videos/upload", files=files)
        
        assert response.status_code == 201
        validate(response.json(), APIContract.VIDEO_SCHEMA)
    
    def test_delete_video_contract(self, client, test_db):
        """Test DELETE /api/videos/{id} returns correct response."""
        # Create a video first
        video_data = VideoFactory.build().__dict__
        response = client.post("/api/videos/", json=video_data)
        video_id = response.json()["id"]
        
        # Delete the video
        response = client.delete(f"/api/videos/{video_id}")
        assert response.status_code == 204


class TestPlaybackAPIContract:
    """Test playback API endpoints for contract compliance."""
    
    def test_play_video_contract(self, client, test_db):
        """Test POST /api/devices/{id}/play returns correct schema."""
        # Create device and video
        device_data = DeviceFactory.build().__dict__
        device_response = client.post("/api/devices/", json=device_data)
        device_id = device_response.json()["id"]
        
        video_data = VideoFactory.build().__dict__
        video_response = client.post("/api/videos/", json=video_data)
        video_id = video_response.json()["id"]
        
        # Play video
        play_data = {"video_id": video_id, "loop": True}
        response = client.post(f"/api/devices/{device_id}/play", json=play_data)
        
        assert response.status_code == 200
        validate(response.json(), APIContract.PLAYBACK_RESPONSE_SCHEMA)
    
    def test_stop_playback_contract(self, client, test_db):
        """Test POST /api/devices/{id}/stop returns correct response."""
        # Create and setup device
        device_data = DeviceFactory.build().__dict__
        response = client.post("/api/devices/", json=device_data)
        device_id = response.json()["id"]
        
        # Stop playback
        response = client.post(f"/api/devices/{device_id}/stop")
        assert response.status_code == 200
        
        result = response.json()
        assert "status" in result
        assert result["status"] in ["success", "error"]
    
    def test_seek_contract(self, client, test_db):
        """Test POST /api/devices/{id}/seek handles seek correctly."""
        # Create device
        device_data = DeviceFactory.build().__dict__
        response = client.post("/api/devices/", json=device_data)
        device_id = response.json()["id"]
        
        # Seek
        seek_data = {"position": "00:05:30"}
        response = client.post(f"/api/devices/{device_id}/seek", json=seek_data)
        
        assert response.status_code in [200, 400]  # 400 if device not playing
        if response.status_code == 400:
            validate(response.json(), APIContract.ERROR_RESPONSE_SCHEMA)


class TestOverlayAPIContract:
    """Test overlay API endpoints for contract compliance."""
    
    OVERLAY_CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "video_id": {"type": "integer"},
            "type": {"type": "string", "enum": ["text", "image", "video", "shape", "effect"]},
            "config": {"type": "object"},
            "enabled": {"type": "boolean"},
            "created_at": {"type": "string", "format": "date-time"}
        },
        "required": ["id", "video_id", "type", "config", "enabled"]
    }
    
    def test_create_overlay_contract(self, client, test_db):
        """Test POST /api/overlay/configs creates overlay correctly."""
        # Create video first
        video_data = VideoFactory.build().__dict__
        video_response = client.post("/api/videos/", json=video_data)
        video_id = video_response.json()["id"]
        
        # Create overlay
        overlay_data = {
            "video_id": video_id,
            "type": "text",
            "config": {
                "text": "Test Overlay",
                "position": {"x": 10, "y": 10}
            },
            "enabled": True
        }
        
        response = client.post("/api/overlay/configs", json=overlay_data)
        assert response.status_code == 201
        
        validate(response.json(), self.OVERLAY_CONFIG_SCHEMA)
    
    def test_get_overlays_for_video_contract(self, client, test_db):
        """Test GET /api/overlay/configs returns overlays for video."""
        # Create video and overlay
        video_data = VideoFactory.build().__dict__
        video_response = client.post("/api/videos/", json=video_data)
        video_id = video_response.json()["id"]
        
        overlay_data = {
            "video_id": video_id,
            "type": "image",
            "config": {"url": "http://example.com/image.png"},
            "enabled": True
        }
        client.post("/api/overlay/configs", json=overlay_data)
        
        # Get overlays
        response = client.get(f"/api/overlay/configs?video_id={video_id}")
        assert response.status_code == 200
        
        overlays = response.json()
        assert isinstance(overlays, list)
        for overlay in overlays:
            validate(overlay, self.OVERLAY_CONFIG_SCHEMA)


class TestWebSocketContract:
    """Test WebSocket endpoint contracts."""
    
    def test_websocket_connection(self, client):
        """Test WebSocket connection and message format."""
        with client.websocket_connect("/ws") as websocket:
            # Send a subscription message
            websocket.send_json({
                "type": "subscribe",
                "channels": ["device_status", "playback_events"]
            })
            
            # Receive confirmation
            data = websocket.receive_json()
            assert "type" in data
            assert data["type"] == "subscription_confirmed"
            
            # Test device status update format
            websocket.send_json({
                "type": "get_device_status",
                "device_id": 1
            })
            
            response = websocket.receive_json()
            assert "type" in response
            assert "data" in response


def test_api_versioning(client):
    """Test API versioning headers."""
    response = client.get("/api/devices/")
    
    # Check for API version header
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "1.0"


def test_rate_limiting_headers(client):
    """Test rate limiting headers are present."""
    response = client.get("/api/devices/")
    
    # Check for rate limit headers
    expected_headers = [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset"
    ]
    
    for header in expected_headers:
        assert header in response.headers


def test_cors_headers(client):
    """Test CORS headers are correctly set."""
    response = client.options("/api/devices/")
    
    assert "Access-Control-Allow-Origin" in response.headers
    assert "Access-Control-Allow-Methods" in response.headers
    assert "Access-Control-Allow-Headers" in response.headers