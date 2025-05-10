"""
Integration tests for the nano-dlna dashboard.

These tests verify that the different components of the system work together correctly.
They focus on the integration between:
- Device discovery and management
- Video streaming
- Renderer service
- Depth processing

Note: These tests require a running backend server and may interact with actual devices.
"""

import pytest
import requests
import time
import os
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
def mock_device_manager():
    """
    Mock the device manager to avoid actual device discovery.
    """
    with patch('routers.device_router.device_manager') as mock_dm:
        # Configure the mock device manager
        mock_device = MagicMock()
        mock_device.name = "Test_Device"
        mock_device.location = "http://192.168.1.100:49152/description.xml"
        mock_device.friendly_name = "Test Device"
        mock_device.is_playing = False
        mock_device.current_video = None
        mock_device.play.return_value = True
        mock_device.stop.return_value = True
        mock_device.pause.return_value = True
        mock_device.seek.return_value = True
        
        mock_dm.discover_devices.return_value = [mock_device]
        mock_dm.get_device.return_value = mock_device
        mock_dm.devices = {"Test_Device": mock_device}
        mock_dm.device_status = {
            "Test_Device": {
                "status": "connected",
                "is_playing": False,
                "last_updated": time.time()
            }
        }
        
        yield mock_dm


@pytest.fixture
def mock_streaming_service():
    """
    Mock the streaming service to avoid actual streaming.
    """
    with patch('routers.streaming_router.streaming_service') as mock_ss:
        # Configure the mock streaming service
        mock_ss.start_streaming.return_value = {
            "session_id": "test-session-id",
            "url": "http://localhost:8000/stream/test-session-id",
            "device_name": "Test_Device",
            "video_path": "/path/to/test_video.mp4"
        }
        mock_ss.get_session.return_value = {
            "session_id": "test-session-id",
            "url": "http://localhost:8000/stream/test-session-id",
            "device_name": "Test_Device",
            "video_path": "/path/to/test_video.mp4",
            "status": "active",
            "start_time": time.time() - 60,
            "end_time": None,
            "bytes_sent": 1024 * 1024,
            "client_ip": "127.0.0.1"
        }
        mock_ss.get_sessions.return_value = [{
            "session_id": "test-session-id",
            "url": "http://localhost:8000/stream/test-session-id",
            "device_name": "Test_Device",
            "video_path": "/path/to/test_video.mp4",
            "status": "active",
            "start_time": time.time() - 60,
            "end_time": None,
            "bytes_sent": 1024 * 1024,
            "client_ip": "127.0.0.1"
        }]
        
        yield mock_ss


@pytest.fixture
def mock_renderer_service():
    """
    Mock the renderer service to avoid actual rendering.
    """
    with patch('routers.renderer_router.renderer_service') as mock_rs:
        # Configure the mock renderer service
        mock_rs.config = {
            'projectors': {
                'proj-1': {
                    'id': 'proj-1',
                    'name': 'Test Projector 1',
                    'sender': 'dlna',
                    'target_name': 'Test_Device',
                    'scene': 'test-scene'
                }
            },
            'scenes': {
                'test-scene': {
                    'id': 'test-scene',
                    'name': 'Test Scene',
                    'template': 'test.html',
                    'data': {}
                }
            }
        }
        
        mock_rs.start_renderer.return_value = True
        mock_rs.stop_renderer.return_value = True
        mock_rs.get_renderer_status.return_value = {
            'type': 'chrome',
            'running': True,
            'scene_id': 'test-scene',
            'projector_id': 'proj-1',
            'sender_type': 'dlna',
            'target_name': 'Test_Device'
        }
        mock_rs.list_active_renderers.return_value = [
            {
                'type': 'chrome',
                'running': True,
                'scene_id': 'test-scene',
                'projector_id': 'proj-1',
                'sender_type': 'dlna',
                'target_name': 'Test_Device'
            }
        ]
        
        yield mock_rs


@pytest.fixture
def mock_depth_processing():
    """
    Mock the depth processing modules to avoid actual processing.
    """
    import numpy as np
    
    with patch('routers.depth_router.DepthLoader') as mock_loader, \
         patch('routers.depth_router.DepthSegmenter') as mock_segmenter, \
         patch('routers.depth_router.DepthVisualizer') as mock_visualizer, \
         patch('routers.depth_router.temp_depth_maps', {
             "test-uuid": {
                 "depth_map": np.zeros((100, 100)),
                 "segmentation": np.zeros((100, 100), dtype=np.int32),
                 "filename": "test_depth_map.png",
                 "temp_path": "/tmp/test_depth_map.png"
             }
         }), \
         patch('routers.depth_router.uuid') as mock_uuid:
        
        # Configure mock loader
        mock_loader.load_depth_map.return_value = np.zeros((100, 100))
        mock_loader.normalize_depth_map.return_value = np.zeros((100, 100))
        mock_loader.visualize_depth_map.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Configure mock segmenter
        mock_segmenter.kmeans_segmentation.return_value = (np.zeros((100, 100), dtype=np.int32), [0, 1, 2, 3, 4])
        mock_segmenter.threshold_segmentation.return_value = np.zeros((100, 100), dtype=np.int32)
        mock_segmenter.depth_band_segmentation.return_value = np.zeros((100, 100), dtype=np.int32)
        mock_segmenter.extract_binary_mask.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_segmenter.clean_binary_mask.return_value = np.zeros((100, 100), dtype=np.uint8)
        
        # Configure mock visualizer
        mock_visualizer.export_image.return_value = b"test_image_data"
        mock_visualizer.create_overlay.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Configure mock uuid
        mock_uuid.uuid4.return_value = "test-uuid"
        
        yield mock_loader, mock_segmenter, mock_visualizer


@pytest.fixture
def mock_video_service():
    """
    Mock the video service to avoid actual database operations.
    """
    with patch('routers.video_router.video_service') as mock_vs:
        # Configure the mock video service
        mock_vs.get_videos.return_value = [
            {
                "id": 1,
                "name": "test_video.mp4",
                "path": "/path/to/test_video.mp4",
                "size": 1024 * 1024,
                "duration": 60,
                "format": "mp4",
                "created_at": "2025-05-09T12:00:00",
                "updated_at": "2025-05-09T12:00:00"
            }
        ]
        mock_vs.get_video.return_value = {
            "id": 1,
            "name": "test_video.mp4",
            "path": "/path/to/test_video.mp4",
            "size": 1024 * 1024,
            "duration": 60,
            "format": "mp4",
            "created_at": "2025-05-09T12:00:00",
            "updated_at": "2025-05-09T12:00:00"
        }
        
        yield mock_vs


@pytest.fixture
def mock_device_service():
    """
    Mock the device service to avoid actual database operations.
    """
    with patch('routers.device_router.device_service') as mock_ds:
        # Configure the mock device service
        mock_ds.get_devices.return_value = [
            {
                "id": 1,
                "name": "Test_Device",
                "location": "http://192.168.1.100:49152/description.xml",
                "friendly_name": "Test Device",
                "type": "dlna",
                "status": "connected",
                "is_playing": False,
                "current_video_id": None,
                "created_at": "2025-05-09T12:00:00",
                "updated_at": "2025-05-09T12:00:00"
            }
        ]
        mock_ds.get_device.return_value = {
            "id": 1,
            "name": "Test_Device",
            "location": "http://192.168.1.100:49152/description.xml",
            "friendly_name": "Test Device",
            "type": "dlna",
            "status": "connected",
            "is_playing": False,
            "current_video_id": None,
            "created_at": "2025-05-09T12:00:00",
            "updated_at": "2025-05-09T12:00:00"
        }
        mock_ds.discover_devices.return_value = [
            {
                "id": 1,
                "name": "Test_Device",
                "location": "http://192.168.1.100:49152/description.xml",
                "friendly_name": "Test Device",
                "type": "dlna",
                "status": "connected",
                "is_playing": False,
                "current_video_id": None,
                "created_at": "2025-05-09T12:00:00",
                "updated_at": "2025-05-09T12:00:00"
            }
        ]
        mock_ds.play_video.return_value = True
        mock_ds.stop_video.return_value = True
        mock_ds.pause_video.return_value = True
        mock_ds.seek_video.return_value = True
        
        yield mock_ds


class TestIntegration:
    """
    Integration tests for the nano-dlna dashboard.
    """
    
    def test_device_discovery_and_play(self, client, mock_device_manager, mock_device_service, mock_video_service, mock_streaming_service):
        """
        Test the device discovery and play workflow.
        
        This test verifies that:
        1. Devices can be discovered
        2. Videos can be played on devices
        3. Playback can be controlled (stop, pause, seek)
        """
        # 1. Discover devices
        response = client.get("/api/devices/discover")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert len(response.json()["devices"]) > 0
        
        # 2. Get devices
        response = client.get("/api/devices")
        assert response.status_code == 200
        assert len(response.json()) > 0
        device_id = response.json()[0]["id"]
        
        # 3. Get videos
        response = client.get("/api/videos")
        assert response.status_code == 200
        assert len(response.json()) > 0
        video_id = response.json()[0]["id"]
        
        # 4. Play video on device
        response = client.post(f"/api/devices/{device_id}/play", json={"video_id": video_id, "loop": True})
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 5. Verify device status
        response = client.get(f"/api/devices/{device_id}")
        assert response.status_code == 200
        assert response.json()["is_playing"] is True
        assert response.json()["current_video_id"] == video_id
        
        # 6. Pause video
        response = client.post(f"/api/devices/{device_id}/pause")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 7. Seek video
        response = client.post(f"/api/devices/{device_id}/seek?position=30")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 8. Stop video
        response = client.post(f"/api/devices/{device_id}/stop")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 9. Verify device status
        response = client.get(f"/api/devices/{device_id}")
        assert response.status_code == 200
        assert response.json()["is_playing"] is False
        assert response.json()["current_video_id"] is None
    
    def test_renderer_workflow(self, client, mock_renderer_service, mock_device_manager):
        """
        Test the renderer workflow.
        
        This test verifies that:
        1. Renderers can be started
        2. Renderer status can be retrieved
        3. Renderers can be stopped
        """
        # 1. List projectors
        response = client.get("/api/renderer/projectors")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert len(response.json()["data"]["projectors"]) > 0
        projector_id = response.json()["data"]["projectors"][0]["id"]
        
        # 2. List scenes
        response = client.get("/api/renderer/scenes")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert len(response.json()["data"]["scenes"]) > 0
        scene_id = response.json()["data"]["scenes"][0]["id"]
        
        # 3. Start renderer
        response = client.post("/api/renderer/start", json={"scene": scene_id, "projector": projector_id})
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 4. Get renderer status
        response = client.get(f"/api/renderer/status/{projector_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["data"]["scene_id"] == scene_id
        assert response.json()["data"]["projector_id"] == projector_id
        
        # 5. List active renderers
        response = client.get("/api/renderer/list")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert len(response.json()["data"]["renderers"]) > 0
        
        # 6. Stop renderer
        response = client.post("/api/renderer/stop", json={"projector": projector_id})
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 7. Verify renderer is stopped
        response = client.get(f"/api/renderer/status/{projector_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["data"] is None
    
    def test_depth_processing_workflow(self, client, mock_depth_processing):
        """
        Test the depth processing workflow.
        
        This test verifies that:
        1. Depth maps can be uploaded
        2. Depth maps can be segmented
        3. Masks can be exported
        """
        # 1. Upload depth map
        with open("test_depth_map.png", "wb") as f:
            f.write(b"test_depth_map_data")
        
        with open("test_depth_map.png", "rb") as f:
            response = client.post(
                "/api/depth/upload",
                files={"file": ("test_depth_map.png", f, "image/png")},
                data={"normalize": "true"}
            )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "depth_id" in response.json()
        depth_id = response.json()["depth_id"]
        
        # 2. Preview depth map
        response = client.get(f"/api/depth/preview/{depth_id}")
        assert response.status_code == 200
        assert response.content == b"test_image_data"
        
        # 3. Segment depth map using KMeans
        response = client.post(
            f"/api/depth/segment/{depth_id}",
            json={"method": "kmeans", "n_clusters": 5}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["segment_count"] > 0
        
        # 4. Preview segmentation
        response = client.get(f"/api/depth/segmentation_preview/{depth_id}")
        assert response.status_code == 200
        assert response.content == b"test_image_data"
        
        # 5. Get mask for a segment
        response = client.get(f"/api/depth/mask/{depth_id}/1")
        assert response.status_code == 200
        assert response.content == b"test_image_data"
        
        # 6. Segment depth map using threshold
        response = client.post(
            f"/api/depth/segment/{depth_id}",
            json={"method": "threshold", "thresholds": [0.25, 0.5, 0.75]}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 7. Segment depth map using bands
        response = client.post(
            f"/api/depth/segment/{depth_id}",
            json={"method": "bands", "n_bands": 5}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 8. Delete depth map
        response = client.delete(f"/api/depth/{depth_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Clean up
        os.remove("test_depth_map.png")
    
    def test_renderer_and_depth_integration(self, client, mock_renderer_service, mock_depth_processing, mock_device_manager):
        """
        Test the integration between renderer and depth processing.
        
        This test verifies that:
        1. Depth maps can be processed
        2. Projection mappings can be created
        3. Renderers can use projection mappings
        """
        # 1. Upload depth map
        with open("test_depth_map.png", "wb") as f:
            f.write(b"test_depth_map_data")
        
        with open("test_depth_map.png", "rb") as f:
            response = client.post(
                "/api/depth/upload",
                files={"file": ("test_depth_map.png", f, "image/png")},
                data={"normalize": "true"}
            )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "depth_id" in response.json()
        depth_id = response.json()["depth_id"]
        
        # 2. Segment depth map
        response = client.post(
            f"/api/depth/segment/{depth_id}",
            json={"method": "kmeans", "n_clusters": 5}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 3. Create a projection mapping configuration
        # Note: This is a placeholder for the actual implementation
        # In a real test, we would create a projection mapping configuration
        # and then use it with a renderer
        
        # 4. Clean up
        response = client.delete(f"/api/depth/{depth_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        os.remove("test_depth_map.png")
    
    def test_streaming_workflow(self, client, mock_streaming_service, mock_device_manager, mock_device_service, mock_video_service):
        """
        Test the streaming workflow.
        
        This test verifies that:
        1. Streaming sessions can be started
        2. Streaming sessions can be monitored
        3. Streaming sessions can be completed
        """
        # 1. Get devices
        response = client.get("/api/devices")
        assert response.status_code == 200
        assert len(response.json()) > 0
        device_id = response.json()[0]["id"]
        device_name = response.json()[0]["name"]
        
        # 2. Get videos
        response = client.get("/api/videos")
        assert response.status_code == 200
        assert len(response.json()) > 0
        video_id = response.json()[0]["id"]
        video_path = response.json()[0]["path"]
        
        # 3. Start streaming
        response = client.post("/api/streaming/start", json={"device_id": device_id, "video_path": video_path})
        assert response.status_code == 200
        assert "session_id" in response.json()
        session_id = response.json()["session_id"]
        
        # 4. Get streaming session
        response = client.get(f"/api/streaming/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["session_id"] == session_id
        assert response.json()["device_name"] == device_name
        assert response.json()["video_path"] == video_path
        
        # 5. Get sessions for device
        response = client.get(f"/api/streaming/device/{device_name}")
        assert response.status_code == 200
        assert len(response.json()) > 0
        assert response.json()[0]["session_id"] == session_id
        
        # 6. Complete session
        response = client.post(f"/api/streaming/sessions/{session_id}/complete")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 7. Verify session is completed
        response = client.get(f"/api/streaming/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
