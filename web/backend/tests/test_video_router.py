import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from io import BytesIO

def test_get_videos(client, test_db):
    """Test the GET /api/videos/ endpoint"""
    response = client.get("/api/videos/")
    assert response.status_code == 200
    data = response.json()
    assert "videos" in data
    assert "total" in data
    assert isinstance(data["videos"], list)


def test_get_video_not_found(client, test_db):
    """Test the GET /api/videos/{video_id} endpoint with non-existent video"""
    response = client.get("/api/videos/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_video_found(client, test_db):
    """Test the GET /api/videos/{video_id} endpoint with existing video"""
    # Create a video in the DB
    from models.video import VideoModel
    video = VideoModel(
        name="test_video.mp4",
        path="/path/to/test_video.mp4",
        file_size=1024,
        duration=60.0
    )
    test_db.add(video)
    test_db.commit()
    test_db.refresh(video)
    
    # Test with existing video
    response = client.get(f"/api/videos/{video.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_video.mp4"
    assert data["path"] == "/path/to/test_video.mp4"
    assert data["file_size"] == 1024
    assert data["duration"] == 60.0


@patch('services.video_service.VideoService.create_video')
def test_create_video_success(mock_create, client, test_db):
    """Test the POST /api/videos/ endpoint with valid data"""
    # Mock the create_video method
    mock_create.return_value = MagicMock(
        to_dict=lambda: {
            "id": 1,
            "name": "new_video.mp4",
            "path": "/path/to/new_video.mp4",
            "file_size": 2048,
            "duration": 120.0,
            "created_at": "2025-05-05T10:00:00"
        }
    )
    
    # Test create endpoint
    video_data = {
        "name": "new_video.mp4",
        "path": "/path/to/new_video.mp4",
        "file_size": 2048,
        "duration": 120.0
    }
    response = client.post("/api/videos/", json=video_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "new_video.mp4"
    assert data["path"] == "/path/to/new_video.mp4"
    assert data["file_size"] == 2048
    assert data["duration"] == 120.0
    mock_create.assert_called_once()


@patch('services.video_service.VideoService.create_video')
def test_create_video_error(mock_create, client, test_db):
    """Test the POST /api/videos/ endpoint with invalid data"""
    # Mock the create_video method to raise an error
    mock_create.side_effect = ValueError("Invalid video data")
    
    # Test create endpoint with invalid data
    video_data = {
        "name": "invalid_video"  # Missing required fields
    }
    response = client.post("/api/videos/", json=video_data)
    assert response.status_code == 400
    assert "Invalid video data" in response.json()["detail"]
    mock_create.assert_called_once()


@patch('services.video_service.VideoService.update_video')
def test_update_video_success(mock_update, client, test_db):
    """Test the PUT /api/videos/{video_id} endpoint with valid data"""
    # Mock the update_video method
    mock_update.return_value = MagicMock(
        to_dict=lambda: {
            "id": 1,
            "name": "updated_video.mp4",
            "path": "/path/to/updated_video.mp4",
            "file_size": 3072,
            "duration": 180.0,
            "created_at": "2025-05-05T10:00:00"
        }
    )
    
    # Test update endpoint
    update_data = {
        "name": "updated_video.mp4",
        "duration": 180.0
    }
    response = client.put("/api/videos/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated_video.mp4"
    assert data["duration"] == 180.0
    mock_update.assert_called_once_with(1, update_data)


@patch('services.video_service.VideoService.update_video')
def test_update_video_not_found(mock_update, client, test_db):
    """Test the PUT /api/videos/{video_id} endpoint with non-existent video"""
    # Mock the update_video method to return None (video not found)
    mock_update.return_value = None
    
    # Test update endpoint with non-existent video
    update_data = {
        "name": "updated_video.mp4",
        "duration": 180.0
    }
    response = client.put("/api/videos/999", json=update_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    mock_update.assert_called_once_with(999, update_data)


@patch('services.video_service.VideoService.delete_video')
def test_delete_video_success(mock_delete, client, test_db):
    """Test the DELETE /api/videos/{video_id} endpoint with existing video"""
    # Mock the delete_video method to return True (success)
    mock_delete.return_value = True
    
    # Test delete endpoint
    response = client.delete("/api/videos/1")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "deleted" in data["message"].lower()
    mock_delete.assert_called_once_with(1)


@patch('services.video_service.VideoService.delete_video')
def test_delete_video_not_found(mock_delete, client, test_db):
    """Test the DELETE /api/videos/{video_id} endpoint with non-existent video"""
    # Mock the delete_video method to return False (video not found)
    mock_delete.return_value = False
    
    # Test delete endpoint with non-existent video
    response = client.delete("/api/videos/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    mock_delete.assert_called_once_with(999)


@patch('services.video_service.VideoService.upload_video')
def test_upload_video_success(mock_upload, client, test_db):
    """Test the POST /api/videos/upload endpoint with valid file"""
    # Mock the upload_video method
    mock_upload.return_value = MagicMock(
        to_dict=lambda: {
            "id": 1,
            "name": "uploaded_video.mp4",
            "path": "/path/to/uploads/uploaded_video.mp4",
            "file_size": 4096,
            "duration": 240.0,
            "created_at": "2025-05-05T10:00:00"
        }
    )
    
    # Create a test video file
    video_content = b"test video content"
    
    # Test upload endpoint
    response = client.post(
        "/api/videos/upload",
        files={"file": ("uploaded_video.mp4", BytesIO(video_content), "video/mp4")},
        data={"name": "Custom Video Name", "upload_dir": "uploads"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "uploaded successfully" in data["message"].lower()
    assert data["video"]["name"] == "uploaded_video.mp4"
    mock_upload.assert_called_once()


def test_upload_video_invalid_content_type(client, test_db):
    """Test the POST /api/videos/upload endpoint with invalid content type"""
    # Create a test file with non-video content type
    file_content = b"test text content"
    
    # Test upload endpoint with invalid content type
    response = client.post(
        "/api/videos/upload",
        files={"file": ("test.txt", BytesIO(file_content), "text/plain")},
        data={"upload_dir": "uploads"}
    )
    
    assert response.status_code == 400
    assert "not a video" in response.json()["detail"].lower()


@patch('services.video_service.VideoService.upload_video')
def test_upload_video_no_filename(mock_upload, client, test_db):
    """Test the POST /api/videos/upload endpoint with no filename"""
    # Test upload endpoint with no filename
    response = client.post(
        "/api/videos/upload",
        files={"file": ("", BytesIO(b""), "video/mp4")},
        data={"upload_dir": "uploads"}
    )
    
    assert response.status_code == 400
    assert "no name" in response.json()["detail"].lower()
    mock_upload.assert_not_called()


@patch('services.video_service.VideoService.upload_video')
def test_upload_video_upload_failed(mock_upload, client, test_db):
    """Test the POST /api/videos/upload endpoint with upload failure"""
    # Mock the upload_video method to return None (upload failed)
    mock_upload.return_value = None
    
    # Create a test video file
    video_content = b"test video content"
    
    # Test upload endpoint with upload failure
    response = client.post(
        "/api/videos/upload",
        files={"file": ("failed_upload.mp4", BytesIO(video_content), "video/mp4")},
        data={"upload_dir": "uploads"}
    )
    
    assert response.status_code == 500
    assert "failed to upload" in response.json()["detail"].lower()
    mock_upload.assert_called_once()


@patch('services.video_service.VideoService.stream_video')
def test_stream_video_success(mock_stream, client, test_db):
    """Test the POST /api/videos/{video_id}/stream endpoint with success"""
    # Mock the stream_video method
    mock_stream.return_value = "http://localhost:8000/stream/test_video.mp4"
    
    # Test stream endpoint
    response = client.post("/api/videos/1/stream")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["url"] == "http://localhost:8000/stream/test_video.mp4"
    mock_stream.assert_called_once_with(1, None)


@patch('services.video_service.VideoService.stream_video')
def test_stream_video_with_serve_ip(mock_stream, client, test_db):
    """Test the POST /api/videos/{video_id}/stream endpoint with serve_ip"""
    # Mock the stream_video method
    mock_stream.return_value = "http://192.168.1.100:8000/stream/test_video.mp4"
    
    # Test stream endpoint with serve_ip
    response = client.post("/api/videos/1/stream?serve_ip=192.168.1.100")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["url"] == "http://192.168.1.100:8000/stream/test_video.mp4"
    mock_stream.assert_called_once_with(1, "192.168.1.100")


@patch('services.video_service.VideoService.stream_video')
def test_stream_video_failure(mock_stream, client, test_db):
    """Test the POST /api/videos/{video_id}/stream endpoint with failure"""
    # Mock the stream_video method to return None (failure)
    mock_stream.return_value = None
    
    # Test stream endpoint with failure
    response = client.post("/api/videos/999/stream")
    assert response.status_code == 500
    assert "failed to stream" in response.json()["detail"].lower()
    mock_stream.assert_called_once_with(999, None)


@patch('services.video_service.VideoService.scan_directory')
def test_scan_directory_success_query_param(mock_scan, client, test_db):
    """Test the POST /api/videos/scan-directory endpoint with query parameter"""
    # Mock the scan_directory method
    mock_scan.return_value = [
        {
            "id": 1,
            "name": "video1.mp4",
            "path": "/path/to/videos/video1.mp4",
            "file_size": 1024,
            "duration": 60.0
        },
        {
            "id": 2,
            "name": "video2.mp4",
            "path": "/path/to/videos/video2.mp4",
            "file_size": 2048,
            "duration": 120.0
        }
    ]
    
    # Patch os.path.exists and os.path.isdir to return True
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isdir', return_value=True):
        # Test scan-directory endpoint with query parameter
        response = client.post("/api/videos/scan-directory?directory=/path/to/videos")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "found 2 videos" in data["message"].lower()
        assert len(data["videos"]) == 2
        assert data["videos"][0]["name"] == "video1.mp4"
        assert data["videos"][1]["name"] == "video2.mp4"
        mock_scan.assert_called_once_with("/path/to/videos")


@patch('services.video_service.VideoService.scan_directory')
def test_scan_directory_success_body(mock_scan, client, test_db):
    """Test the POST /api/videos/scan-directory endpoint with request body"""
    # Mock the scan_directory method
    mock_scan.return_value = [
        {
            "id": 1,
            "name": "video1.mp4",
            "path": "/path/to/videos/video1.mp4",
            "file_size": 1024,
            "duration": 60.0
        },
        {
            "id": 2,
            "name": "video2.mp4",
            "path": "/path/to/videos/video2.mp4",
            "file_size": 2048,
            "duration": 120.0
        }
    ]
    
    # Patch os.path.exists and os.path.isdir to return True
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isdir', return_value=True):
        # Test scan-directory endpoint with request body
        response = client.post(
            "/api/videos/scan-directory",
            json={"directory": "/path/to/videos"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "found 2 videos" in data["message"].lower()
        assert len(data["videos"]) == 2
        assert data["videos"][0]["name"] == "video1.mp4"
        assert data["videos"][1]["name"] == "video2.mp4"
        mock_scan.assert_called_once_with("/path/to/videos")


def test_scan_directory_no_directory(client, test_db):
    """Test the POST /api/videos/scan-directory endpoint with no directory"""
    # Test scan-directory endpoint with no directory
    response = client.post("/api/videos/scan-directory")
    assert response.status_code == 400
    assert "directory parameter is required" in response.json()["detail"].lower()


def test_scan_directory_directory_not_found(client, test_db):
    """Test the POST /api/videos/scan-directory endpoint with non-existent directory"""
    # Patch os.path.exists to return False
    with patch('os.path.exists', return_value=False):
        # Test scan-directory endpoint with non-existent directory
        response = client.post("/api/videos/scan-directory?directory=/path/to/nonexistent")
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"].lower()


def test_scan_directory_not_a_directory(client, test_db):
    """Test the POST /api/videos/scan-directory endpoint with a file instead of a directory"""
    # Patch os.path.exists to return True and os.path.isdir to return False
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isdir', return_value=False):
        # Test scan-directory endpoint with a file instead of a directory
        response = client.post("/api/videos/scan-directory?directory=/path/to/file.txt")
        assert response.status_code == 400
        assert "is not a directory" in response.json()["detail"].lower()


@patch('services.video_service.VideoService.scan_directory')
def test_scan_videos_alias(mock_scan, client, test_db):
    """Test the POST /api/videos/scan endpoint (alias for scan-directory)"""
    # Mock the scan_directory method
    mock_scan.return_value = [
        {
            "id": 1,
            "name": "video1.mp4",
            "path": "/path/to/videos/video1.mp4",
            "file_size": 1024,
            "duration": 60.0
        }
    ]
    
    # Patch os.path.exists and os.path.isdir to return True
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isdir', return_value=True):
        # Test scan endpoint (alias for scan-directory)
        response = client.post("/api/videos/scan?directory=/path/to/videos")
        assert response.status_code == 200
        data = response.json()
        assert "found 1 videos" in data["message"].lower()
        assert len(data["videos"]) == 1
        assert data["videos"][0]["name"] == "video1.mp4"
        mock_scan.assert_called_once_with("/path/to/videos")
