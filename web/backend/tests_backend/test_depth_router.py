"""
Tests for the depth router.
"""
import pytest
import io
import json
import uuid
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
from fastapi.testclient import TestClient
from web.backend.main import app


class TestDepthRouter:
    """Tests for the depth router."""
    
    @patch("web.backend.routers.depth_router.DepthLoader")
    @patch("web.backend.routers.depth_router.uuid.uuid4")
    def test_upload_depth_map(self, mock_uuid4, mock_depth_loader, test_client):
        """Test uploading a depth map."""
        # Configure the mocks
        mock_uuid4.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        mock_depth_loader.load_depth_map.return_value = mock_depth_map
        mock_depth_loader.normalize_depth_map.return_value = mock_depth_map
        
        # Create a test file
        test_file_content = b"test file content"
        
        # Make the request
        response = test_client.post(
            "/api/depth/upload",
            files={"file": ("test_depth.png", test_file_content, "image/png")},
            data={"normalize": "true"}
        )
        
        # Check the response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Depth map uploaded successfully" in data["message"]
        assert data["depth_id"] == "12345678-1234-5678-1234-567812345678"
        
        # Verify the mocks were called correctly
        mock_depth_loader.load_depth_map.assert_called_once()
        mock_depth_loader.normalize_depth_map.assert_called_once_with(mock_depth_map)
    
    @patch("web.backend.routers.depth_router.DepthLoader")
    def test_upload_depth_map_invalid_extension(self, mock_depth_loader, test_client):
        """Test uploading a depth map with an invalid extension."""
        # Create a test file
        test_file_content = b"test file content"
        
        # Make the request
        response = test_client.post(
            "/api/depth/upload",
            files={"file": ("test_depth.txt", test_file_content, "text/plain")},
            data={"normalize": "true"}
        )
        
        # Check the response
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Unsupported file format" in data["detail"]
        
        # Verify the mock was not called
        mock_depth_loader.load_depth_map.assert_not_called()
    
    @patch("web.backend.routers.depth_router.DepthLoader")
    @patch("web.backend.routers.depth_router.uuid.uuid4")
    def test_upload_depth_map_load_failure(self, mock_uuid4, mock_depth_loader, test_client):
        """Test uploading a depth map with a loading failure."""
        # Configure the mocks
        mock_uuid4.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mock_depth_loader.load_depth_map.return_value = None
        
        # Create a test file
        test_file_content = b"test file content"
        
        # Make the request
        response = test_client.post(
            "/api/depth/upload",
            files={"file": ("test_depth.png", test_file_content, "image/png")},
            data={"normalize": "true"}
        )
        
        # Check the response
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Failed to load depth map" in data["detail"]
        
        # Verify the mock was called correctly
        mock_depth_loader.load_depth_map.assert_called_once()
        mock_depth_loader.normalize_depth_map.assert_not_called()
    
    @patch("web.backend.routers.depth_router.DepthLoader")
    def test_preview_depth_map(self, mock_depth_loader, test_client):
        """Test previewing a depth map."""
        # Configure the mocks
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        mock_visualization = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_depth_loader.visualize_depth_map.return_value = mock_visualization
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": mock_depth_map,
                "segmentation": None,
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }):
            # Configure the mock for export_image
            with patch("web.backend.routers.depth_router.DepthVisualizer") as mock_visualizer:
                mock_visualizer.export_image.return_value = b"test image bytes"
                
                # Make the request
                response = test_client.get(f"/api/depth/preview/{depth_id}")
                
                # Check the response
                assert response.status_code == 200
                assert response.headers["content-type"] == "image/png"
                assert response.content == b"test image bytes"
                
                # Verify the mocks were called correctly
                mock_depth_loader.visualize_depth_map.assert_called_once_with(mock_depth_map)
                mock_visualizer.export_image.assert_called_once_with(mock_visualization)
    
    def test_preview_depth_map_not_found(self, test_client):
        """Test previewing a depth map that doesn't exist."""
        # Make the request
        response = test_client.get("/api/depth/preview/nonexistent")
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Depth map not found" in data["detail"]
    
    @patch("web.backend.routers.depth_router.DepthSegmenter")
    def test_segment_depth_map_kmeans(self, mock_segmenter, test_client):
        """Test segmenting a depth map using KMeans."""
        # Configure the mocks
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        mock_segmentation = np.zeros((100, 100), dtype=np.int32)
        mock_centers = np.array([0.1, 0.5, 0.9])
        mock_segmenter.kmeans_segmentation.return_value = (mock_segmentation, mock_centers)
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": mock_depth_map,
                "segmentation": None,
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }):
            # Prepare the request data
            request_data = {
                "method": "kmeans",
                "n_clusters": 3
            }
            
            # Make the request
            response = test_client.post(f"/api/depth/segment/{depth_id}", json=request_data)
            
            # Check the response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Depth map segmented using kmeans" in data["message"]
            assert data["segment_count"] == 1  # Only one unique value (0) in the mock segmentation
            assert data["segments"] == [0]
            assert data["centers"] == [0.1, 0.5, 0.9]
            assert data["depth_id"] == depth_id
            
            # Verify the mock was called correctly
            mock_segmenter.kmeans_segmentation.assert_called_once_with(
                mock_depth_map, n_clusters=3
            )
    
    @patch("web.backend.routers.depth_router.DepthSegmenter")
    def test_segment_depth_map_threshold(self, mock_segmenter, test_client):
        """Test segmenting a depth map using threshold segmentation."""
        # Configure the mocks
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        mock_segmentation = np.zeros((100, 100), dtype=np.int32)
        mock_segmenter.threshold_segmentation.return_value = mock_segmentation
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": mock_depth_map,
                "segmentation": None,
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }):
            # Prepare the request data
            request_data = {
                "method": "threshold",
                "thresholds": [0.2, 0.5, 0.8]
            }
            
            # Make the request
            response = test_client.post(f"/api/depth/segment/{depth_id}", json=request_data)
            
            # Check the response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Depth map segmented using threshold" in data["message"]
            assert data["segment_count"] == 1  # Only one unique value (0) in the mock segmentation
            assert data["segments"] == [0]
            assert data["depth_id"] == depth_id
            
            # Verify the mock was called correctly
            mock_segmenter.threshold_segmentation.assert_called_once_with(
                mock_depth_map, thresholds=[0.2, 0.5, 0.8]
            )
    
    @patch("web.backend.routers.depth_router.DepthSegmenter")
    def test_segment_depth_map_bands(self, mock_segmenter, test_client):
        """Test segmenting a depth map using depth bands."""
        # Configure the mocks
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        mock_segmentation = np.zeros((100, 100), dtype=np.int32)
        mock_segmenter.depth_band_segmentation.return_value = mock_segmentation
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": mock_depth_map,
                "segmentation": None,
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }):
            # Prepare the request data
            request_data = {
                "method": "bands",
                "n_bands": 5
            }
            
            # Make the request
            response = test_client.post(f"/api/depth/segment/{depth_id}", json=request_data)
            
            # Check the response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Depth map segmented using bands" in data["message"]
            assert data["segment_count"] == 1  # Only one unique value (0) in the mock segmentation
            assert data["segments"] == [0]
            assert data["depth_id"] == depth_id
            
            # Verify the mock was called correctly
            mock_segmenter.depth_band_segmentation.assert_called_once_with(
                mock_depth_map, n_bands=5
            )
    
    def test_segment_depth_map_not_found(self, test_client):
        """Test segmenting a depth map that doesn't exist."""
        # Prepare the request data
        request_data = {
            "method": "kmeans",
            "n_clusters": 3
        }
        
        # Make the request
        response = test_client.post("/api/depth/segment/nonexistent", json=request_data)
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Depth map not found" in data["detail"]
    
    def test_segment_depth_map_invalid_method(self, test_client):
        """Test segmenting a depth map with an invalid method."""
        # Configure the mocks
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": mock_depth_map,
                "segmentation": None,
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }):
            # Prepare the request data
            request_data = {
                "method": "invalid_method",
                "n_clusters": 3
            }
            
            # Make the request
            response = test_client.post(f"/api/depth/segment/{depth_id}", json=request_data)
            
            # Check the response
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Unsupported segmentation method" in data["detail"]
    
    @patch("web.backend.routers.depth_router.DepthLoader")
    @patch("web.backend.routers.depth_router.DepthVisualizer")
    def test_segmentation_preview(self, mock_visualizer, mock_depth_loader, test_client):
        """Test previewing a segmentation."""
        # Configure the mocks
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        mock_segmentation = np.zeros((100, 100), dtype=np.int32)
        mock_visualization = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_overlay = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_depth_loader.visualize_depth_map.return_value = mock_visualization
        mock_visualizer.create_overlay.return_value = mock_overlay
        mock_visualizer.export_image.return_value = b"test image bytes"
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": mock_depth_map,
                "segmentation": mock_segmentation,
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }):
            # Make the request
            response = test_client.get(f"/api/depth/segmentation_preview/{depth_id}?alpha=0.7")
            
            # Check the response
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.content == b"test image bytes"
            
            # Verify the mocks were called correctly
            mock_depth_loader.visualize_depth_map.assert_called_once_with(mock_depth_map)
            mock_visualizer.create_overlay.assert_called_once_with(
                mock_visualization, mock_segmentation, alpha=0.7
            )
            mock_visualizer.export_image.assert_called_once_with(mock_overlay)
    
    def test_segmentation_preview_not_found(self, test_client):
        """Test previewing a segmentation for a depth map that doesn't exist."""
        # Make the request
        response = test_client.get("/api/depth/segmentation_preview/nonexistent")
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Depth map not found" in data["detail"]
    
    def test_segmentation_preview_not_segmented(self, test_client):
        """Test previewing a segmentation for a depth map that hasn't been segmented."""
        # Configure the mocks
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": mock_depth_map,
                "segmentation": None,  # Not segmented
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }):
            # Make the request
            response = test_client.get(f"/api/depth/segmentation_preview/{depth_id}")
            
            # Check the response
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Depth map not segmented yet" in data["detail"]
    
    @patch("web.backend.routers.depth_router.DepthSegmenter")
    @patch("web.backend.routers.depth_router.DepthVisualizer")
    @patch("web.backend.routers.depth_router.zipfile.ZipFile")
    @patch("web.backend.routers.depth_router.BytesIO")
    def test_export_masks(self, mock_bytesio_class, mock_zipfile_class, mock_visualizer, mock_segmenter, test_client):
        """Test exporting masks."""
        # Configure the mocks
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        mock_segmentation = np.zeros((100, 100), dtype=np.int32)
        mock_binary_mask = np.zeros((100, 100), dtype=np.uint8)
        mock_segmenter.extract_binary_mask.return_value = mock_binary_mask
        mock_segmenter.clean_binary_mask.return_value = mock_binary_mask
        mock_visualizer.export_image.return_value = b"test mask bytes"
        
        # Mock BytesIO
        mock_bytesio = MagicMock()
        mock_bytesio_class.return_value = mock_bytesio
        
        # Mock ZipFile
        mock_zipfile = MagicMock()
        mock_zipfile_class.return_value.__enter__.return_value = mock_zipfile
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": mock_depth_map,
                "segmentation": mock_segmentation,
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }):
            # Prepare the request data
            request_data = {
                "segment_ids": [0, 1, 2],
                "clean_mask": True,
                "min_area": 100,
                "kernel_size": 3
            }
            
            # Make the request
            response = test_client.post(f"/api/depth/export_masks/{depth_id}", json=request_data)
            
            # Check the response
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/zip"
            assert "attachment; filename=" in response.headers["content-disposition"]
            
            # Verify the mocks were called correctly
            assert mock_segmenter.extract_binary_mask.call_count == 3
            assert mock_segmenter.clean_binary_mask.call_count == 3
            assert mock_visualizer.export_image.call_count == 3
            assert mock_zipfile.writestr.call_count == 4  # 3 masks + 1 metadata file
    
    def test_export_masks_not_found(self, test_client):
        """Test exporting masks for a depth map that doesn't exist."""
        # Prepare the request data
        request_data = {
            "segment_ids": [0, 1, 2],
            "clean_mask": True,
            "min_area": 100,
            "kernel_size": 3
        }
        
        # Make the request
        response = test_client.post("/api/depth/export_masks/nonexistent", json=request_data)
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Depth map not found" in data["detail"]
    
    def test_export_masks_not_segmented(self, test_client):
        """Test exporting masks for a depth map that hasn't been segmented."""
        # Configure the mocks
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": mock_depth_map,
                "segmentation": None,  # Not segmented
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }):
            # Prepare the request data
            request_data = {
                "segment_ids": [0, 1, 2],
                "clean_mask": True,
                "min_area": 100,
                "kernel_size": 3
            }
            
            # Make the request
            response = test_client.post(f"/api/depth/export_masks/{depth_id}", json=request_data)
            
            # Check the response
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Depth map not segmented yet" in data["detail"]
    
    @patch("web.backend.routers.depth_router.os.path.exists")
    @patch("web.backend.routers.depth_router.os.unlink")
    def test_delete_depth_map(self, mock_unlink, mock_exists, test_client):
        """Test deleting a depth map."""
        # Configure the mocks
        mock_exists.return_value = True
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": np.zeros((100, 100), dtype=np.float32),
                "segmentation": None,
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }, clear=True):
            # Make the request
            response = test_client.delete(f"/api/depth/{depth_id}")
            
            # Check the response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Depth map deleted" in data["message"]
            
            # Verify the mocks were called correctly
            mock_exists.assert_called_once_with("/tmp/test_depth.png")
            mock_unlink.assert_called_once_with("/tmp/test_depth.png")
            
            # Verify the depth map was removed from memory
            assert depth_id not in web.backend.routers.depth_router.temp_depth_maps
    
    def test_delete_depth_map_not_found(self, test_client):
        """Test deleting a depth map that doesn't exist."""
        # Make the request
        response = test_client.delete("/api/depth/nonexistent")
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Depth map not found" in data["detail"]
    
    @patch("web.backend.routers.depth_router.DepthSegmenter")
    @patch("web.backend.routers.depth_router.DepthVisualizer")
    def test_get_mask(self, mock_visualizer, mock_segmenter, test_client):
        """Test getting a mask for a specific segment."""
        # Configure the mocks
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        mock_segmentation = np.zeros((100, 100), dtype=np.int32)
        mock_binary_mask = np.zeros((100, 100), dtype=np.uint8)
        mock_segmenter.extract_binary_mask.return_value = mock_binary_mask
        mock_segmenter.clean_binary_mask.return_value = mock_binary_mask
        mock_visualizer.export_image.return_value = b"test mask bytes"
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": mock_depth_map,
                "segmentation": mock_segmentation,
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }):
            # Make the request
            response = test_client.get(f"/api/depth/mask/{depth_id}/0?clean=true&min_area=200&kernel_size=5")
            
            # Check the response
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.content == b"test mask bytes"
            
            # Verify the mocks were called correctly
            mock_segmenter.extract_binary_mask.assert_called_once_with(mock_segmentation, 0)
            mock_segmenter.clean_binary_mask.assert_called_once_with(
                mock_binary_mask, min_area=200, kernel_size=5
            )
            mock_visualizer.export_image.assert_called_once_with(mock_binary_mask)
    
    def test_get_mask_not_found(self, test_client):
        """Test getting a mask for a depth map that doesn't exist."""
        # Make the request
        response = test_client.get("/api/depth/mask/nonexistent/0")
        
        # Check the response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Depth map not found" in data["detail"]
    
    def test_get_mask_not_segmented(self, test_client):
        """Test getting a mask for a depth map that hasn't been segmented."""
        # Configure the mocks
        mock_depth_map = np.zeros((100, 100), dtype=np.float32)
        
        # Create a test depth map in memory
        depth_id = "test_depth_id"
        with patch.dict("web.backend.routers.depth_router.temp_depth_maps", {
            depth_id: {
                "depth_map": mock_depth_map,
                "segmentation": None,  # Not segmented
                "filename": "test_depth.png",
                "temp_path": "/tmp/test_depth.png"
            }
        }):
            # Make the request
            response = test_client.get(f"/api/depth/mask/{depth_id}/0")
            
            # Check the response
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "Depth map not segmented yet" in data["detail"]
