"""
Tests for the depth_router module.
"""

import pytest
import io
import json
import numpy as np
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, ANY

from main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
def mock_depth_processing():
    """
    Mock the depth processing modules.
    """
    with patch('routers.depth_router.DepthLoader') as mock_loader, \
         patch('routers.depth_router.DepthSegmenter') as mock_segmenter, \
         patch('routers.depth_router.DepthVisualizer') as mock_visualizer:
        
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
        
        yield mock_loader, mock_segmenter, mock_visualizer


@pytest.fixture
def mock_temp_file():
    """
    Mock the tempfile module.
    """
    with patch('routers.depth_router.tempfile') as mock_tempfile:
        mock_tempfile.NamedTemporaryFile.return_value.__enter__.return_value.name = "/tmp/test_depth_map.png"
        yield mock_tempfile


@pytest.fixture
def mock_uuid():
    """
    Mock the uuid module.
    """
    with patch('routers.depth_router.uuid') as mock_uuid:
        mock_uuid.uuid4.return_value = "test-uuid"
        yield mock_uuid


class TestDepthRouter:
    """
    Tests for the depth_router module.
    """
    
    def test_upload_depth_map(self, client, mock_depth_processing, mock_temp_file, mock_uuid):
        """
        Test uploading a depth map.
        """
        mock_loader, _, _ = mock_depth_processing
        
        # Create a test file
        test_file = io.BytesIO(b"test_file_content")
        test_file.name = "test_depth_map.png"
        
        response = client.post(
            "/api/depth/upload",
            files={"file": ("test_depth_map.png", test_file, "image/png")},
            data={"normalize": "true"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "Depth map uploaded successfully" in response.json()["message"]
        assert response.json()["depth_id"] == "test-uuid"
        mock_loader.load_depth_map.assert_called_once()
        mock_loader.normalize_depth_map.assert_called_once()
    
    def test_upload_depth_map_unsupported_format(self, client):
        """
        Test uploading a depth map with an unsupported format.
        """
        # Create a test file
        test_file = io.BytesIO(b"test_file_content")
        test_file.name = "test_depth_map.txt"
        
        response = client.post(
            "/api/depth/upload",
            files={"file": ("test_depth_map.txt", test_file, "text/plain")},
            data={"normalize": "true"}
        )
        
        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]
    
    def test_preview_depth_map(self, client, mock_depth_processing, mock_uuid):
        """
        Test previewing a depth map.
        """
        mock_loader, _, mock_visualizer = mock_depth_processing
        
        # Mock the temp_depth_maps dictionary
        with patch('routers.depth_router.temp_depth_maps', {
            "test-uuid": {
                "depth_map": np.zeros((100, 100)),
                "segmentation": None,
                "filename": "test_depth_map.png",
                "temp_path": "/tmp/test_depth_map.png"
            }
        }):
            response = client.get("/api/depth/preview/test-uuid")
            
            assert response.status_code == 200
            assert response.content == b"test_image_data"
            mock_loader.visualize_depth_map.assert_called_once()
            mock_visualizer.export_image.assert_called_once()
    
    def test_preview_depth_map_not_found(self, client):
        """
        Test previewing a depth map that doesn't exist.
        """
        response = client.get("/api/depth/preview/nonexistent-uuid")
        
        assert response.status_code == 404
        assert "Depth map not found" in response.json()["detail"]
    
    def test_segment_depth_map_kmeans(self, client, mock_depth_processing, mock_uuid):
        """
        Test segmenting a depth map using KMeans.
        """
        _, mock_segmenter, _ = mock_depth_processing
        
        # Mock the temp_depth_maps dictionary
        with patch('routers.depth_router.temp_depth_maps', {
            "test-uuid": {
                "depth_map": np.zeros((100, 100)),
                "segmentation": None,
                "filename": "test_depth_map.png",
                "temp_path": "/tmp/test_depth_map.png"
            }
        }):
            response = client.post(
                "/api/depth/segment/test-uuid",
                json={
                    "method": "kmeans",
                    "n_clusters": 5
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert "Depth map segmented using kmeans" in response.json()["message"]
            assert response.json()["segment_count"] > 0
            assert len(response.json()["segments"]) > 0
            assert response.json()["depth_id"] == "test-uuid"
            mock_segmenter.kmeans_segmentation.assert_called_once_with(ANY, n_clusters=5)
    
    def test_segment_depth_map_threshold(self, client, mock_depth_processing, mock_uuid):
        """
        Test segmenting a depth map using threshold.
        """
        _, mock_segmenter, _ = mock_depth_processing
        
        # Mock the temp_depth_maps dictionary
        with patch('routers.depth_router.temp_depth_maps', {
            "test-uuid": {
                "depth_map": np.zeros((100, 100)),
                "segmentation": None,
                "filename": "test_depth_map.png",
                "temp_path": "/tmp/test_depth_map.png"
            }
        }):
            response = client.post(
                "/api/depth/segment/test-uuid",
                json={
                    "method": "threshold",
                    "thresholds": [0.25, 0.5, 0.75]
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert "Depth map segmented using threshold" in response.json()["message"]
            mock_segmenter.threshold_segmentation.assert_called_once_with(ANY, thresholds=[0.25, 0.5, 0.75])
    
    def test_segment_depth_map_bands(self, client, mock_depth_processing, mock_uuid):
        """
        Test segmenting a depth map using depth bands.
        """
        _, mock_segmenter, _ = mock_depth_processing
        
        # Mock the temp_depth_maps dictionary
        with patch('routers.depth_router.temp_depth_maps', {
            "test-uuid": {
                "depth_map": np.zeros((100, 100)),
                "segmentation": None,
                "filename": "test_depth_map.png",
                "temp_path": "/tmp/test_depth_map.png"
            }
        }):
            response = client.post(
                "/api/depth/segment/test-uuid",
                json={
                    "method": "bands",
                    "n_bands": 5
                }
            )
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert "Depth map segmented using bands" in response.json()["message"]
            mock_segmenter.depth_band_segmentation.assert_called_once_with(ANY, n_bands=5)
    
    def test_segment_depth_map_not_found(self, client):
        """
        Test segmenting a depth map that doesn't exist.
        """
        response = client.post(
            "/api/depth/segment/nonexistent-uuid",
            json={
                "method": "kmeans",
                "n_clusters": 5
            }
        )
        
        assert response.status_code == 404
        assert "Depth map not found" in response.json()["detail"]
    
    def test_segment_depth_map_unsupported_method(self, client, mock_uuid):
        """
        Test segmenting a depth map with an unsupported method.
        """
        # Mock the temp_depth_maps dictionary
        with patch('routers.depth_router.temp_depth_maps', {
            "test-uuid": {
                "depth_map": np.zeros((100, 100)),
                "segmentation": None,
                "filename": "test_depth_map.png",
                "temp_path": "/tmp/test_depth_map.png"
            }
        }):
            response = client.post(
                "/api/depth/segment/test-uuid",
                json={
                    "method": "unsupported",
                    "n_clusters": 5
                }
            )
            
            assert response.status_code == 400
            assert "Unsupported segmentation method" in response.json()["detail"]
    
    def test_preview_segmentation(self, client, mock_depth_processing, mock_uuid):
        """
        Test previewing a segmentation.
        """
        mock_loader, _, mock_visualizer = mock_depth_processing
        
        # Mock the temp_depth_maps dictionary
        with patch('routers.depth_router.temp_depth_maps', {
            "test-uuid": {
                "depth_map": np.zeros((100, 100)),
                "segmentation": np.zeros((100, 100), dtype=np.int32),
                "filename": "test_depth_map.png",
                "temp_path": "/tmp/test_depth_map.png"
            }
        }):
            response = client.get("/api/depth/segmentation_preview/test-uuid?alpha=0.5")
            
            assert response.status_code == 200
            assert response.content == b"test_image_data"
            mock_loader.visualize_depth_map.assert_called_once()
            mock_visualizer.create_overlay.assert_called_once()
            mock_visualizer.export_image.assert_called_once()
    
    def test_preview_segmentation_not_found(self, client):
        """
        Test previewing a segmentation for a depth map that doesn't exist.
        """
        response = client.get("/api/depth/segmentation_preview/nonexistent-uuid")
        
        assert response.status_code == 404
        assert "Depth map not found" in response.json()["detail"]
    
    def test_preview_segmentation_not_segmented(self, client, mock_uuid):
        """
        Test previewing a segmentation for a depth map that hasn't been segmented.
        """
        # Mock the temp_depth_maps dictionary
        with patch('routers.depth_router.temp_depth_maps', {
            "test-uuid": {
                "depth_map": np.zeros((100, 100)),
                "segmentation": None,
                "filename": "test_depth_map.png",
                "temp_path": "/tmp/test_depth_map.png"
            }
        }):
            response = client.get("/api/depth/segmentation_preview/test-uuid")
            
            assert response.status_code == 400
            assert "Depth map not segmented yet" in response.json()["detail"]
    
    def test_get_mask(self, client, mock_depth_processing, mock_uuid):
        """
        Test getting a mask for a specific segment.
        """
        _, mock_segmenter, mock_visualizer = mock_depth_processing
        
        # Mock the temp_depth_maps dictionary
        with patch('routers.depth_router.temp_depth_maps', {
            "test-uuid": {
                "depth_map": np.zeros((100, 100)),
                "segmentation": np.zeros((100, 100), dtype=np.int32),
                "filename": "test_depth_map.png",
                "temp_path": "/tmp/test_depth_map.png"
            }
        }):
            response = client.get("/api/depth/mask/test-uuid/1?clean=true&min_area=100&kernel_size=3")
            
            assert response.status_code == 200
            assert response.content == b"test_image_data"
            mock_segmenter.extract_binary_mask.assert_called_once_with(ANY, 1)
            mock_segmenter.clean_binary_mask.assert_called_once_with(ANY, min_area=100, kernel_size=3)
            mock_visualizer.export_image.assert_called_once()
    
    def test_get_mask_not_found(self, client):
        """
        Test getting a mask for a depth map that doesn't exist.
        """
        response = client.get("/api/depth/mask/nonexistent-uuid/1")
        
        assert response.status_code == 404
        assert "Depth map not found" in response.json()["detail"]
    
    def test_get_mask_not_segmented(self, client, mock_uuid):
        """
        Test getting a mask for a depth map that hasn't been segmented.
        """
        # Mock the temp_depth_maps dictionary
        with patch('routers.depth_router.temp_depth_maps', {
            "test-uuid": {
                "depth_map": np.zeros((100, 100)),
                "segmentation": None,
                "filename": "test_depth_map.png",
                "temp_path": "/tmp/test_depth_map.png"
            }
        }):
            response = client.get("/api/depth/mask/test-uuid/1")
            
            assert response.status_code == 400
            assert "Depth map not segmented yet" in response.json()["detail"]
    
    def test_delete_depth_map(self, client, mock_uuid):
        """
        Test deleting a depth map.
        """
        # Mock the temp_depth_maps dictionary and os.path.exists
        with patch('routers.depth_router.temp_depth_maps', {
            "test-uuid": {
                "depth_map": np.zeros((100, 100)),
                "segmentation": None,
                "filename": "test_depth_map.png",
                "temp_path": "/tmp/test_depth_map.png"
            }
        }), patch('routers.depth_router.os.path.exists', return_value=True), \
             patch('routers.depth_router.os.unlink') as mock_unlink:
            
            response = client.delete("/api/depth/test-uuid")
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            assert "Depth map deleted" in response.json()["message"]
            mock_unlink.assert_called_once_with("/tmp/test_depth_map.png")
    
    def test_delete_depth_map_not_found(self, client):
        """
        Test deleting a depth map that doesn't exist.
        """
        response = client.delete("/api/depth/nonexistent-uuid")
        
        assert response.status_code == 404
        assert "Depth map not found" in response.json()["detail"]
