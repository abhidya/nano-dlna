"""
Tests for the renderer router.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from web.backend.main import app
from web.backend.core.renderer_service.service import RendererService


class TestRendererRouter:
    """Tests for the renderer router."""
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_start_renderer(self, mock_renderer_service, test_client):
        """Test starting a renderer."""
        # Configure the mock
        mock_renderer_service.start_renderer.return_value = True
        mock_renderer_service.get_renderer_status.return_value = {
            "status": "running",
            "scene": "test_scene",
            "projector": "test_projector"
        }
        
        # Prepare the request data
        request_data = {
            "scene": "test_scene",
            "projector": "test_projector",
            "options": {"loop": True}
        }
        
        # Make the request
        response = test_client.post("/api/renderer/start", json=request_data)
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Started renderer for scene test_scene on projector test_projector" in data["message"]
        assert data["data"]["status"] == "running"
        assert data["data"]["scene"] == "test_scene"
        assert data["data"]["projector"] == "test_projector"
        
        # Verify the mock was called correctly
        mock_renderer_service.start_renderer.assert_called_once_with(
            "test_scene", "test_projector"
        )
        mock_renderer_service.get_renderer_status.assert_called_once_with("test_projector")
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_start_renderer_failure(self, mock_renderer_service, test_client):
        """Test starting a renderer with failure."""
        # Configure the mock
        mock_renderer_service.start_renderer.return_value = False
        
        # Prepare the request data
        request_data = {
            "scene": "test_scene",
            "projector": "test_projector"
        }
        
        # Make the request
        response = test_client.post("/api/renderer/start", json=request_data)
        
        # Check the response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to start renderer" in data["detail"]
        
        # Verify the mock was called correctly
        mock_renderer_service.start_renderer.assert_called_once_with(
            "test_scene", "test_projector"
        )
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_start_renderer_exception(self, mock_renderer_service, test_client):
        """Test starting a renderer with an exception."""
        # Configure the mock
        mock_renderer_service.start_renderer.side_effect = Exception("Test exception")
        
        # Prepare the request data
        request_data = {
            "scene": "test_scene",
            "projector": "test_projector"
        }
        
        # Make the request
        response = test_client.post("/api/renderer/start", json=request_data)
        
        # Check the response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error starting renderer" in data["detail"]
        assert "Test exception" in data["detail"]
        
        # Verify the mock was called correctly
        mock_renderer_service.start_renderer.assert_called_once_with(
            "test_scene", "test_projector"
        )
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_stop_renderer(self, mock_renderer_service, test_client):
        """Test stopping a renderer."""
        # Configure the mock
        mock_renderer_service.stop_renderer.return_value = True
        
        # Prepare the request data
        request_data = {
            "projector": "test_projector"
        }
        
        # Make the request
        response = test_client.post("/api/renderer/stop", json=request_data)
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Stopped renderer on projector test_projector" in data["message"]
        
        # Verify the mock was called correctly
        mock_renderer_service.stop_renderer.assert_called_once_with("test_projector")
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_stop_renderer_failure(self, mock_renderer_service, test_client):
        """Test stopping a renderer with failure."""
        # Configure the mock
        mock_renderer_service.stop_renderer.return_value = False
        
        # Prepare the request data
        request_data = {
            "projector": "test_projector"
        }
        
        # Make the request
        response = test_client.post("/api/renderer/stop", json=request_data)
        
        # Check the response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to stop renderer" in data["detail"]
        
        # Verify the mock was called correctly
        mock_renderer_service.stop_renderer.assert_called_once_with("test_projector")
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_get_renderer_status(self, mock_renderer_service, test_client):
        """Test getting renderer status."""
        # Configure the mock
        mock_renderer_service.get_renderer_status.return_value = {
            "status": "running",
            "scene": "test_scene",
            "projector": "test_projector"
        }
        
        # Make the request
        response = test_client.get("/api/renderer/status/test_projector")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Got renderer status for projector test_projector" in data["message"]
        assert data["data"]["status"] == "running"
        assert data["data"]["scene"] == "test_scene"
        assert data["data"]["projector"] == "test_projector"
        
        # Verify the mock was called correctly
        mock_renderer_service.get_renderer_status.assert_called_once_with("test_projector")
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_get_renderer_status_not_found(self, mock_renderer_service, test_client):
        """Test getting renderer status when not found."""
        # Configure the mock
        mock_renderer_service.get_renderer_status.return_value = None
        
        # Make the request
        response = test_client.get("/api/renderer/status/test_projector")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "No active renderer found for projector test_projector" in data["message"]
        assert data["data"] is None
        
        # Verify the mock was called correctly
        mock_renderer_service.get_renderer_status.assert_called_once_with("test_projector")
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_list_renderers(self, mock_renderer_service, test_client):
        """Test listing renderers."""
        # Configure the mock
        mock_renderer_service.list_active_renderers.return_value = [
            {
                "projector": "test_projector_1",
                "scene": "test_scene_1",
                "status": "running"
            },
            {
                "projector": "test_projector_2",
                "scene": "test_scene_2",
                "status": "paused"
            }
        ]
        
        # Make the request
        response = test_client.get("/api/renderer/list")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Listed 2 active renderers" in data["message"]
        assert len(data["data"]["renderers"]) == 2
        assert data["data"]["renderers"][0]["projector"] == "test_projector_1"
        assert data["data"]["renderers"][1]["projector"] == "test_projector_2"
        
        # Verify the mock was called correctly
        mock_renderer_service.list_active_renderers.assert_called_once()
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_list_projectors(self, mock_renderer_service, test_client):
        """Test listing projectors."""
        # Configure the mock
        mock_renderer_service.config = {
            "projectors": {
                "proj1": {"name": "Projector 1", "type": "dlna"},
                "proj2": {"name": "Projector 2", "type": "airplay"}
            }
        }
        
        # Make the request
        response = test_client.get("/api/renderer/projectors")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Listed 2 projectors" in data["message"]
        assert len(data["data"]["projectors"]) == 2
        
        # Check that the projectors have the correct structure
        projectors = {p["id"]: p for p in data["data"]["projectors"]}
        assert "proj1" in projectors
        assert projectors["proj1"]["name"] == "Projector 1"
        assert projectors["proj1"]["type"] == "dlna"
        assert "proj2" in projectors
        assert projectors["proj2"]["name"] == "Projector 2"
        assert projectors["proj2"]["type"] == "airplay"
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_list_scenes(self, mock_renderer_service, test_client):
        """Test listing scenes."""
        # Configure the mock
        mock_renderer_service.config = {
            "scenes": {
                "scene1": {"name": "Scene 1", "file": "video1.mp4"},
                "scene2": {"file": "video2.mp4"}  # No name provided
            }
        }
        
        # Make the request
        response = test_client.get("/api/renderer/scenes")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Listed 2 scenes" in data["message"]
        assert len(data["data"]["scenes"]) == 2
        
        # Check that the scenes have the correct structure
        scenes = {s["id"]: s for s in data["data"]["scenes"]}
        assert "scene1" in scenes
        assert scenes["scene1"]["name"] == "Scene 1"
        assert scenes["scene1"]["file"] == "video1.mp4"
        assert "scene2" in scenes
        assert scenes["scene2"]["name"] == "scene2"  # ID used as name
        assert scenes["scene2"]["file"] == "video2.mp4"
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_start_projector(self, mock_renderer_service, test_client):
        """Test starting a projector with its default scene."""
        # Configure the mock
        mock_renderer_service.get_projector_config.return_value = {
            "name": "Test Projector",
            "scene": "default_scene"
        }
        mock_renderer_service.start_renderer.return_value = True
        mock_renderer_service.get_renderer_status.return_value = {
            "status": "running",
            "scene": "default_scene",
            "projector": "test_projector"
        }
        
        # Make the request
        response = test_client.post("/api/renderer/start_projector?projector_id=test_projector")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Started projector test_projector with scene default_scene" in data["message"]
        assert data["data"]["status"] == "running"
        assert data["data"]["scene"] == "default_scene"
        assert data["data"]["projector"] == "test_projector"
        
        # Verify the mocks were called correctly
        mock_renderer_service.get_projector_config.assert_called_once_with("test_projector")
        mock_renderer_service.start_renderer.assert_called_once_with("default_scene", "test_projector")
        mock_renderer_service.get_renderer_status.assert_called_once_with("test_projector")
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_start_projector_with_body(self, mock_renderer_service, test_client):
        """Test starting a projector with its default scene using request body."""
        # Configure the mock
        mock_renderer_service.get_projector_config.return_value = {
            "name": "Test Projector",
            "scene": "default_scene"
        }
        mock_renderer_service.start_renderer.return_value = True
        mock_renderer_service.get_renderer_status.return_value = {
            "status": "running",
            "scene": "default_scene",
            "projector": "test_projector"
        }
        
        # Prepare the request data
        request_data = {
            "projector_id": "test_projector"
        }
        
        # Make the request
        response = test_client.post("/api/renderer/start_projector", json=request_data)
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Started projector test_projector with scene default_scene" in data["message"]
        
        # Verify the mocks were called correctly
        mock_renderer_service.get_projector_config.assert_called_once_with("test_projector")
        mock_renderer_service.start_renderer.assert_called_once_with("default_scene", "test_projector")
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_start_projector_no_id(self, mock_renderer_service, test_client):
        """Test starting a projector without providing an ID."""
        # Make the request
        response = test_client.post("/api/renderer/start_projector")
        
        # Check the response
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "projector_id is required" in data["detail"]
        
        # Verify the mock was not called
        mock_renderer_service.get_projector_config.assert_not_called()
        mock_renderer_service.start_renderer.assert_not_called()
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_start_projector_not_found(self, mock_renderer_service, test_client):
        """Test starting a projector that doesn't exist."""
        # Configure the mock
        mock_renderer_service.get_projector_config.return_value = None
        
        # Make the request
        response = test_client.post("/api/renderer/start_projector?projector_id=nonexistent")
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Projector not found" in data["detail"]
        
        # Verify the mock was called correctly
        mock_renderer_service.get_projector_config.assert_called_once_with("nonexistent")
        mock_renderer_service.start_renderer.assert_not_called()
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_start_projector_no_scene(self, mock_renderer_service, test_client):
        """Test starting a projector with no default scene configured."""
        # Configure the mock
        mock_renderer_service.get_projector_config.return_value = {
            "name": "Test Projector"
            # No scene configured
        }
        
        # Make the request
        response = test_client.post("/api/renderer/start_projector?projector_id=test_projector")
        
        # Check the response
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "No default scene configured" in data["detail"]
        
        # Verify the mock was called correctly
        mock_renderer_service.get_projector_config.assert_called_once_with("test_projector")
        mock_renderer_service.start_renderer.assert_not_called()
    
    @patch("web.backend.routers.renderer_router.AirPlayDiscovery")
    def test_discover_airplay_devices(self, mock_airplay_discovery_class, test_client):
        """Test discovering AirPlay devices."""
        # Configure the mock
        mock_airplay_discovery = MagicMock()
        mock_airplay_discovery_class.return_value = mock_airplay_discovery
        mock_airplay_discovery.discover_devices.return_value = [
            {"name": "Device 1", "address": "192.168.1.100"},
            {"name": "Device 2", "address": "192.168.1.101"}
        ]
        
        # Make the request
        response = test_client.get("/api/renderer/airplay/discover")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Discovered 2 AirPlay devices" in data["message"]
        assert len(data["data"]["devices"]) == 2
        assert data["data"]["devices"][0]["name"] == "Device 1"
        assert data["data"]["devices"][1]["name"] == "Device 2"
        
        # Verify the mock was called correctly
        mock_airplay_discovery.discover_devices.assert_called_once()
    
    @patch("web.backend.routers.renderer_router.AirPlayDiscovery")
    def test_list_airplay_devices(self, mock_airplay_discovery_class, test_client):
        """Test listing AirPlay devices from System Preferences."""
        # Configure the mock
        mock_airplay_discovery = MagicMock()
        mock_airplay_discovery_class.return_value = mock_airplay_discovery
        mock_airplay_discovery.list_devices_from_system_prefs.return_value = [
            {"name": "Device 1", "id": "device1"},
            {"name": "Device 2", "id": "device2"}
        ]
        
        # Make the request
        response = test_client.get("/api/renderer/airplay/list")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Found 2 AirPlay devices in System Preferences" in data["message"]
        assert len(data["data"]["devices"]) == 2
        assert data["data"]["devices"][0]["name"] == "Device 1"
        assert data["data"]["devices"][1]["name"] == "Device 2"
        
        # Verify the mock was called correctly
        mock_airplay_discovery.list_devices_from_system_prefs.assert_called_once()
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_pause_renderer(self, mock_renderer_service, test_client):
        """Test pausing a renderer."""
        # Configure the mock
        mock_renderer_service.pause_renderer.return_value = True
        mock_renderer_service.get_renderer_status.return_value = {
            "status": "paused",
            "scene": "test_scene",
            "projector": "test_projector"
        }
        
        # Make the request
        response = test_client.post("/api/renderer/pause/test_projector")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Paused renderer on projector test_projector" in data["message"]
        assert data["data"]["status"] == "paused"
        
        # Verify the mock was called correctly
        mock_renderer_service.pause_renderer.assert_called_once_with("test_projector")
        mock_renderer_service.get_renderer_status.assert_called_once_with("test_projector")
    
    @patch("web.backend.routers.renderer_router.renderer_service")
    def test_resume_renderer(self, mock_renderer_service, test_client):
        """Test resuming a renderer."""
        # Configure the mock
        mock_renderer_service.resume_renderer.return_value = True
        mock_renderer_service.get_renderer_status.return_value = {
            "status": "running",
            "scene": "test_scene",
            "projector": "test_projector"
        }
        
        # Make the request
        response = test_client.post("/api/renderer/resume/test_projector")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Resumed renderer on projector test_projector" in data["message"]
        assert data["data"]["status"] == "running"
        
        # Verify the mock was called correctly
        mock_renderer_service.resume_renderer.assert_called_once_with("test_projector")
        mock_renderer_service.get_renderer_status.assert_called_once_with("test_projector")
    
    @patch("web.backend.routers.renderer_router.AirPlayDiscovery")
    def test_get_airplay_devices(self, mock_airplay_discovery_class, test_client):
        """Test getting all AirPlay devices."""
        # Configure the mock
        mock_airplay_discovery = MagicMock()
        mock_airplay_discovery_class.return_value = mock_airplay_discovery
        mock_airplay_discovery.get_devices.return_value = [
            {"name": "Device 1", "address": "192.168.1.100", "source": "discovery"},
            {"name": "Device 2", "address": "192.168.1.101", "source": "system_prefs"}
        ]
        
        # Make the request
        response = test_client.get("/api/renderer/airplay/devices")
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Found 2 AirPlay devices" in data["message"]
        assert len(data["data"]["devices"]) == 2
        assert data["data"]["devices"][0]["name"] == "Device 1"
        assert data["data"]["devices"][0]["source"] == "discovery"
        assert data["data"]["devices"][1]["name"] == "Device 2"
        assert data["data"]["devices"][1]["source"] == "system_prefs"
        
        # Verify the mock was called correctly
        mock_airplay_discovery.get_devices.assert_called_once()
