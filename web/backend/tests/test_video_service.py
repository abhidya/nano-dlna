import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO

from services.video_service import VideoService
from models.video import VideoModel


@pytest.fixture
def video_service(test_db):
    """Create a VideoService instance for testing"""
    return VideoService(db=test_db)


def test_get_all_videos(video_service, test_db):
    """Test the get_all_videos method"""
    # Create test videos
    video1 = VideoModel(
        name="test_video1.mp4",
        path="/path/to/test_video1.mp4",
        file_size=1024,
        duration=60.0
    )
    video2 = VideoModel(
        name="test_video2.mp4",
        path="/path/to/test_video2.mp4",
        file_size=2048,
        duration=120.0
    )
    test_db.add(video1)
    test_db.add(video2)
    test_db.commit()
    
    # Test the method
    videos, total = video_service.get_all_videos()
    
    assert total == 2
    assert len(videos) == 2
    assert videos[0].name == "test_video1.mp4"
    assert videos[1].name == "test_video2.mp4"


def test_get_video_by_id_found(video_service, test_db):
    """Test the get_video_by_id method with existing video"""
    # Create a test video
    video = VideoModel(
        name="test_video.mp4",
        path="/path/to/test_video.mp4",
        file_size=1024,
        duration=60.0
    )
    test_db.add(video)
    test_db.commit()
    test_db.refresh(video)
    
    # Test the method
    result = video_service.get_video_by_id(video.id)
    
    assert result is not None
    assert result.id == video.id
    assert result.name == "test_video.mp4"
    assert result.path == "/path/to/test_video.mp4"
    assert result.file_size == 1024
    assert result.duration == 60.0


def test_get_video_by_id_not_found(video_service, test_db):
    """Test the get_video_by_id method with non-existent video"""
    # Test the method with non-existent video
    result = video_service.get_video_by_id(999)
    
    assert result is None


def test_create_video_success(video_service, test_db):
    """Test the create_video method with valid data"""
    # Test data
    video_data = {
        "name": "new_video.mp4",
        "path": "/path/to/new_video.mp4",
        "file_size": 2048,
        "duration": 120.0
    }
    
    # Test the method
    result = video_service.create_video(video_data)
    
    assert result is not None
    assert result.name == "new_video.mp4"
    assert result.path == "/path/to/new_video.mp4"
    assert result.file_size == 2048
    assert result.duration == 120.0
    
    # Verify the video was added to the database
    video = test_db.query(VideoModel).filter(VideoModel.name == "new_video.mp4").first()
    assert video is not None
    assert video.name == "new_video.mp4"


def test_create_video_invalid_data(video_service, test_db):
    """Test the create_video method with invalid data"""
    # Test with invalid data (missing required fields)
    video_data = {
        "name": "invalid_video.mp4"
        # Missing required fields
    }
    
    # Test the method
    with pytest.raises(ValueError):
        video_service.create_video(video_data)
    
    # Verify no video was added to the database
    video = test_db.query(VideoModel).filter(VideoModel.name == "invalid_video.mp4").first()
    assert video is None


def test_update_video_success(video_service, test_db):
    """Test the update_video method with valid data"""
    # Create a test video
    video = VideoModel(
        name="test_video.mp4",
        path="/path/to/test_video.mp4",
        file_size=1024,
        duration=60.0
    )
    test_db.add(video)
    test_db.commit()
    test_db.refresh(video)
    
    # Test data
    update_data = {
        "name": "updated_video.mp4",
        "duration": 90.0
    }
    
    # Test the method
    result = video_service.update_video(video.id, update_data)
    
    assert result is not None
    assert result.id == video.id
    assert result.name == "updated_video.mp4"  # Updated
    assert result.path == "/path/to/test_video.mp4"  # Unchanged
    assert result.file_size == 1024  # Unchanged
    assert result.duration == 90.0  # Updated
    
    # Verify the video was updated in the database
    updated_video = test_db.query(VideoModel).filter(VideoModel.id == video.id).first()
    assert updated_video is not None
    assert updated_video.name == "updated_video.mp4"
    assert updated_video.duration == 90.0


def test_update_video_not_found(video_service, test_db):
    """Test the update_video method with non-existent video"""
    # Test data
    update_data = {
        "name": "updated_video.mp4",
        "duration": 90.0
    }
    
    # Test the method with non-existent video
    result = video_service.update_video(999, update_data)
    
    assert result is None


def test_delete_video_success(video_service, test_db):
    """Test the delete_video method with existing video"""
    # Create a test video
    video = VideoModel(
        name="test_video.mp4",
        path="/path/to/test_video.mp4",
        file_size=1024,
        duration=60.0
    )
    test_db.add(video)
    test_db.commit()
    test_db.refresh(video)
    
    # Test the method
    result = video_service.delete_video(video.id)
    
    assert result is True
    
    # Verify the video was deleted from the database
    deleted_video = test_db.query(VideoModel).filter(VideoModel.id == video.id).first()
    assert deleted_video is None


def test_delete_video_not_found(video_service, test_db):
    """Test the delete_video method with non-existent video"""
    # Test the method with non-existent video
    result = video_service.delete_video(999)
    
    assert result is False


@patch('os.path.getsize')
@patch('services.video_service.get_video_duration')
def test_upload_video_success(mock_get_duration, mock_getsize, video_service, test_db):
    """Test the upload_video method with success"""
    # Mock the get_video_duration function
    mock_get_duration.return_value = 60.0
    
    # Mock os.path.getsize
    mock_getsize.return_value = 1024
    
    # Create a temporary directory for uploads
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the save_upload_file method
        with patch.object(video_service, 'save_upload_file', return_value=os.path.join(temp_dir, "uploaded_video.mp4")):
            # Test the method
            result = video_service.upload_video(
                file=MagicMock(),
                filename="uploaded_video.mp4",
                upload_dir=temp_dir
            )
            
            assert result is not None
            assert result.name == "uploaded_video.mp4"
            assert result.path == os.path.join(temp_dir, "uploaded_video.mp4")
            assert result.file_size == 1024
            assert result.duration == 60.0
            
            # Verify the video was added to the database
            video = test_db.query(VideoModel).filter(VideoModel.name == "uploaded_video.mp4").first()
            assert video is not None
            assert video.name == "uploaded_video.mp4"


@patch('os.path.getsize')
@patch('services.video_service.get_video_duration')
def test_upload_video_with_custom_name(mock_get_duration, mock_getsize, video_service, test_db):
    """Test the upload_video method with custom name"""
    # Mock the get_video_duration function
    mock_get_duration.return_value = 60.0
    
    # Mock os.path.getsize
    mock_getsize.return_value = 1024
    
    # Create a temporary directory for uploads
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the save_upload_file method
        with patch.object(video_service, 'save_upload_file', return_value=os.path.join(temp_dir, "uploaded_video.mp4")):
            # Test the method with custom name
            result = video_service.upload_video(
                file=MagicMock(),
                filename="uploaded_video.mp4",
                upload_dir=temp_dir,
                custom_name="Custom Video Name"
            )
            
            assert result is not None
            assert result.name == "Custom Video Name"
            assert result.path == os.path.join(temp_dir, "uploaded_video.mp4")
            assert result.file_size == 1024
            assert result.duration == 60.0
            
            # Verify the video was added to the database
            video = test_db.query(VideoModel).filter(VideoModel.name == "Custom Video Name").first()
            assert video is not None
            assert video.name == "Custom Video Name"


@patch('os.makedirs')
@patch('shutil.copyfileobj')
def test_save_upload_file(mock_copyfileobj, mock_makedirs, video_service):
    """Test the save_upload_file method"""
    # Create a mock file
    mock_file = MagicMock()
    mock_file.file = BytesIO(b"test video content")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test the method
        result = video_service.save_upload_file(
            file=mock_file,
            upload_dir=temp_dir,
            filename="test_video.mp4"
        )
        
        assert result == os.path.join(temp_dir, "test_video.mp4")
        mock_makedirs.assert_called_once_with(temp_dir, exist_ok=True)
        mock_copyfileobj.assert_called_once()


@patch('core.streaming_service.StreamingService')
def test_stream_video_success(mock_streaming_service, video_service, test_db):
    """Test the stream_video method with success"""
    # Create a test video
    video = VideoModel(
        name="test_video.mp4",
        path="/path/to/test_video.mp4",
        file_size=1024,
        duration=60.0
    )
    test_db.add(video)
    test_db.commit()
    test_db.refresh(video)
    
    # Mock the StreamingService
    mock_service = MagicMock()
    mock_streaming_service.get_instance.return_value = mock_service
    
    # Mock the start_streaming method
    mock_service.start_streaming.return_value = "http://localhost:8000/stream/test_video.mp4"
    
    # Test the method
    result = video_service.stream_video(video.id)
    
    assert result == "http://localhost:8000/stream/test_video.mp4"
    mock_service.start_streaming.assert_called_once_with(video.path, None)


@patch('core.streaming_service.StreamingService')
def test_stream_video_with_serve_ip(mock_streaming_service, video_service, test_db):
    """Test the stream_video method with serve_ip"""
    # Create a test video
    video = VideoModel(
        name="test_video.mp4",
        path="/path/to/test_video.mp4",
        file_size=1024,
        duration=60.0
    )
    test_db.add(video)
    test_db.commit()
    test_db.refresh(video)
    
    # Mock the StreamingService
    mock_service = MagicMock()
    mock_streaming_service.get_instance.return_value = mock_service
    
    # Mock the start_streaming method
    mock_service.start_streaming.return_value = "http://192.168.1.100:8000/stream/test_video.mp4"
    
    # Test the method with serve_ip
    result = video_service.stream_video(video.id, serve_ip="192.168.1.100")
    
    assert result == "http://192.168.1.100:8000/stream/test_video.mp4"
    mock_service.start_streaming.assert_called_once_with(video.path, "192.168.1.100")


@patch('core.streaming_service.StreamingService')
def test_stream_video_not_found(mock_streaming_service, video_service, test_db):
    """Test the stream_video method with non-existent video"""
    # Mock the StreamingService
    mock_service = MagicMock()
    mock_streaming_service.get_instance.return_value = mock_service
    
    # Test the method with non-existent video
    result = video_service.stream_video(999)
    
    assert result is None
    mock_service.start_streaming.assert_not_called()


@patch('os.walk')
@patch('os.path.getsize')
@patch('services.video_service.get_video_duration')
def test_scan_directory_success(mock_get_duration, mock_getsize, mock_walk, video_service, test_db):
    """Test the scan_directory method with success"""
    # Mock os.walk to return video files
    mock_walk.return_value = [
        ("/path/to/videos", [], ["video1.mp4", "video2.mp4", "not_a_video.txt"])
    ]
    
    # Mock os.path.getsize
    mock_getsize.return_value = 1024
    
    # Mock get_video_duration
    mock_get_duration.return_value = 60.0
    
    # Mock is_video_file to return True for video files
    with patch.object(video_service, 'is_video_file', side_effect=lambda f: f.endswith(('.mp4', '.avi', '.mkv'))):
        # Test the method
        result = video_service.scan_directory("/path/to/videos")
        
        assert len(result) == 2
        assert result[0]["name"] == "video1.mp4"
        assert result[0]["path"] == "/path/to/videos/video1.mp4"
        assert result[0]["file_size"] == 1024
        assert result[0]["duration"] == 60.0
        assert result[1]["name"] == "video2.mp4"
        
        # Verify the videos were added to the database
        videos = test_db.query(VideoModel).all()
        assert len(videos) == 2
        assert videos[0].name == "video1.mp4"
        assert videos[1].name == "video2.mp4"


def test_is_video_file(video_service):
    """Test the is_video_file method"""
    # Test with video files
    assert video_service.is_video_file("test.mp4") is True
    assert video_service.is_video_file("test.avi") is True
    assert video_service.is_video_file("test.mkv") is True
    assert video_service.is_video_file("test.mov") is True
    assert video_service.is_video_file("test.wmv") is True
    
    # Test with non-video files
    assert video_service.is_video_file("test.txt") is False
    assert video_service.is_video_file("test.jpg") is False
    assert video_service.is_video_file("test.pdf") is False
    
    # Test with uppercase extensions
    assert video_service.is_video_file("test.MP4") is True
    assert video_service.is_video_file("test.AVI") is True
    
    # Test with no extension
    assert video_service.is_video_file("test") is False


@patch('services.video_service.get_video_duration')
def test_get_video_info(mock_get_duration, video_service):
    """Test the get_video_info method"""
    # Mock get_video_duration
    mock_get_duration.return_value = 60.0
    
    # Mock os.path.getsize
    with patch('os.path.getsize', return_value=1024):
        # Test the method
        result = video_service.get_video_info("/path/to/test_video.mp4")
        
        assert result["name"] == "test_video.mp4"
        assert result["path"] == "/path/to/test_video.mp4"
        assert result["file_size"] == 1024
        assert result["duration"] == 60.0
        mock_get_duration.assert_called_once_with("/path/to/test_video.mp4")
