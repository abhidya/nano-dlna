"""
Tests for the renderer_router module.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from core.renderer_service.service import RendererService


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
def mock_renderer_service():
    """
    Create a mock renderer service.
    """
    with patch('routers.renderer_router.renderer_service') as mock_service:
        # Configure the mock service
        mock_service.config = {
            'projectors': {
                'proj-1': {
                    'id': 'proj-1',
                    'name': 'Test Projector 1',
                    'sender': 'dlna',
                    'target_name': 'Test_Device_DLNA',
                    'scene': 'test-scene'
                },
                'proj-2': {
                    'id': 'proj-2',
                    'name': 'Test Projector 2',
                    'sender': 'direct',
                    'target_name': '0'
                }
            },
            'scenes': {
                'test-scene': {
                    'id': 'test-scene',
                    'name': 'Test Scene',
                    'template': 'test.html',
                    'data': {}
                },
                'blank': {
                    'id': 'blank',
                    'name': 'Blank Scene',
                    'template': 'blank.html',
                    'data': {}
                }
            }
        }
        
        # Configure mock methods
        mock_service.start_renderer.return_value = True
        mock_service.stop_renderer.return_value = True
        mock_service.get_renderer_status.return_value = {
            'type': 'chrome',
            'running': True,
            'scene_id': 'test-scene',
            'projector_id': 'proj-1',
            'sender_type': 'dlna',
            'target_name': 'Test_Device_DLNA'
        }
        mock_service.list_active_renderers.return_value = [
            {
                'type': 'chrome',
                'running': True,
                'scene_id': 'test-scene',
                'projector_id': 'proj-1',
                'sender_type': 'dlna',
                'target_name': 'Test_Device_DLNA'
            }
        ]
        mock_service.get_projector_config.return_value = {
            'id': 'proj-1',
            'name': 'Test Projector 1',
            'sender': 'dlna',
            'target_name': 'Test_Device_DLNA',
            'scene': 'test-scene'
        }
        
        yield mock_service


class TestRendererRouter:
    """
    Tests for the renderer_router module.
    """
    
    def test_start_renderer(self, client, mock_renderer_service):
        """
        Test starting a renderer.
        """
        response = client.post(
            "/api/renderer/start",
            json={
                "scene": "test-scene",
                "projector": "proj-1"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "Started renderer for scene" in response.json()["message"]
        mock_renderer_service.start_renderer.assert_called_once_with("test-scene", "proj-1")
    
    def test_start_renderer_failure(self, client, mock_renderer_service):
        """
        Test starting a renderer with a failure.
        """
        mock_renderer_service.start_renderer.return_value = False
        
        response = client.post(
            "/api/renderer/start",
            json={
                "scene": "test-scene",
                "projector": "proj-1"
            }
        )
        
        assert response.status_code == 500
        assert "Failed to start renderer" in response.json()["detail"]
        mock_renderer_service.start_renderer.assert_called_once_with("test-scene", "proj-1")
    
    def test_stop_renderer(self, client, mock_renderer_service):
        """
        Test stopping a renderer.
        """
        response = client.post(
            "/api/renderer/stop",
            json={
                "projector": "proj-1"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "Stopped renderer on projector" in response.json()["message"]
        mock_renderer_service.stop_renderer.assert_called_once_with("proj-1")
    
    def test_stop_renderer_failure(self, client, mock_renderer_service):
        """
        Test stopping a renderer with a failure.
        """
        mock_renderer_service.stop_renderer.return_value = False
        
        response = client.post(
            "/api/renderer/stop",
            json={
                "projector": "proj-1"
            }
        )
        
        assert response.status_code == 500
        assert "Failed to stop renderer" in response.json()["detail"]
        mock_renderer_service.stop_renderer.assert_called_once_with("proj-1")
    
    def test_get_renderer_status(self, client, mock_renderer_service):
        """
        Test getting renderer status.
        """
        response = client.get("/api/renderer/status/proj-1")
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "Got renderer status for projector" in response.json()["message"]
        assert response.json()["data"]["scene_id"] == "test-scene"
        assert response.json()["data"]["projector_id"] == "proj-1"
        mock_renderer_service.get_renderer_status.assert_called_once_with("proj-1")
    
    def test_get_renderer_status_not_found(self, client, mock_renderer_service):
        """
        Test getting renderer status for a projector that doesn't have an active renderer.
        """
        mock_renderer_service.get_renderer_status.return_value = None
        
        response = client.get("/api/renderer/status/proj-2")
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "No active renderer found" in response.json()["message"]
        assert response.json()["data"] is None
        mock_renderer_service.get_renderer_status.assert_called_once_with("proj-2")
    
    def test_list_renderers(self, client, mock_renderer_service):
        """
        Test listing active renderers.
        """
        response = client.get("/api/renderer/list")
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "Listed 1 active renderers" in response.json()["message"]
        assert len(response.json()["data"]["renderers"]) == 1
        assert response.json()["data"]["renderers"][0]["scene_id"] == "test-scene"
        mock_renderer_service.list_active_renderers.assert_called_once()
    
    def test_list_projectors(self, client, mock_renderer_service):
        """
        Test listing available projectors.
        """
        response = client.get("/api/renderer/projectors")
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "Listed 2 projectors" in response.json()["message"]
        assert len(response.json()["data"]["projectors"]) == 2
        
        # Check that the projectors are in the expected format (list of objects with id field)
        projectors = response.json()["data"]["projectors"]
        assert isinstance(projectors, list)
        for projector in projectors:
            assert "id" in projector
            assert "name" in projector
            assert "sender" in projector
    
    def test_list_scenes(self, client, mock_renderer_service):
        """
        Test listing available scenes.
        """
        response = client.get("/api/renderer/scenes")
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "Listed 2 scenes" in response.json()["message"]
        assert len(response.json()["data"]["scenes"]) == 2
        
        # Check that the scenes are in the expected format (list of objects with id field)
        scenes = response.json()["data"]["scenes"]
        assert isinstance(scenes, list)
        for scene in scenes:
            assert "id" in scene
            assert "name" in scene
    
    def test_start_projector(self, client, mock_renderer_service):
        """
        Test starting a projector with its default scene.
        """
        response = client.post("/api/renderer/start_projector?projector_id=proj-1")
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "Started projector proj-1 with scene test-scene" in response.json()["message"]
        mock_renderer_service.get_projector_config.assert_called_once_with("proj-1")
        mock_renderer_service.start_renderer.assert_called_once_with("test-scene", "proj-1")
    
    def test_start_projector_not_found(self, client, mock_renderer_service):
        """
        Test starting a projector that doesn't exist.
        """
        mock_renderer_service.get_projector_config.return_value = None
        
        response = client.post("/api/renderer/start_projector?projector_id=proj-3")
        
        assert response.status_code == 404
        assert "Projector not found" in response.json()["detail"]
        mock_renderer_service.get_projector_config.assert_called_once_with("proj-3")
    
    def test_start_projector_no_scene(self, client, mock_renderer_service):
        """
        Test starting a projector that doesn't have a default scene.
        """
        mock_renderer_service.get_projector_config.return_value = {
            'id': 'proj-2',
            'name': 'Test Projector 2',
            'sender': 'direct',
            'target_name': '0'
        }
        
        response = client.post("/api/renderer/start_projector?projector_id=proj-2")
        
        assert response.status_code == 400
        assert "No default scene configured" in response.json()["detail"]
        mock_renderer_service.get_projector_config.assert_called_once_with("proj-2")
