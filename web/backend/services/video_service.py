import os
import logging
import shutil
import socket
from typing import List, Optional, Dict, Any, BinaryIO
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import subprocess
import json
from fastapi import Depends

from models.video import VideoModel
from schemas.video import VideoCreate, VideoUpdate
from core.twisted_streaming import get_instance as get_twisted_streaming
from database.database import get_db

logger = logging.getLogger(__name__)

def get_video_service(db: Session = Depends(get_db)) -> 'VideoService':
    """
    Dependency for getting the VideoService
    
    Args:
        db: Database session
        
    Returns:
        VideoService: Video service instance
    """
    from core.twisted_streaming import get_instance as get_twisted_streaming
    streaming_service = get_twisted_streaming()
    return VideoService(db, streaming_service)

class VideoService:
    """
    Service for managing videos
    """
    def __init__(self, db: Session, streaming_service: Any):
        self.db = db
        self.streaming_service = streaming_service
    
    def get_videos(self, skip: int = 0, limit: int = 100) -> List[VideoModel]:
        """
        Get all videos
        
        Args:
            skip: Number of videos to skip
            limit: Maximum number of videos to return
            
        Returns:
            List[VideoModel]: List of videos
        """
        return self.db.query(VideoModel).offset(skip).limit(limit).all()
    
    def get_video_by_id(self, video_id: int) -> Optional[VideoModel]:
        """
        Get a video by ID
        
        Args:
            video_id: ID of the video to get
            
        Returns:
            Optional[VideoModel]: The video if found, None otherwise
        """
        return self.db.query(VideoModel).filter(VideoModel.id == video_id).first()
    
    def get_video_by_path(self, path: str) -> Optional[VideoModel]:
        """
        Get a video by path
        
        Args:
            path: Path of the video to get
            
        Returns:
            Optional[VideoModel]: The video if found, None otherwise
        """
        return self.db.query(VideoModel).filter(VideoModel.path == path).first()
    
    def create_video(self, video: VideoCreate) -> VideoModel:
        """
        Create a new video
        
        Args:
            video: Video to create
            
        Returns:
            VideoModel: The created video
        """
        try:
            # Check if the video file exists
            if not os.path.exists(video.path):
                raise ValueError(f"Video file not found: {video.path}")
            
            # Get video file information
            file_name = video.file_name if video.file_name else os.path.basename(video.path)
            file_size = video.file_size if video.file_size is not None else os.path.getsize(video.path)
            
            # Get video metadata
            _duration, _format_name, _resolution = self._get_video_metadata(video.path)

            duration = video.duration if video.duration is not None else _duration
            format_name = video.format if video.format else _format_name
            resolution = video.resolution if video.resolution else _resolution
            
            # Check for subtitle file
            subtitle_path = self._find_subtitle_file(video.path)
            has_subtitle = subtitle_path is not None
            
            # Create the video in the database
            db_video = VideoModel(
                name=video.name,
                path=video.path,
                file_name=file_name,
                file_size=file_size,
                duration=duration,
                format=format_name,
                resolution=resolution,
                has_subtitle=bool(has_subtitle),  # Ensure it's a boolean
                subtitle_path=subtitle_path,
            )
            self.db.add(db_video)
            self.db.commit()
            self.db.refresh(db_video)
            
            return db_video
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating video: {e}")
            raise
    
    def update_video(self, video_id: int, video: VideoUpdate) -> Optional[VideoModel]:
        """
        Update a video
        
        Args:
            video_id: ID of the video to update
            video: Video data to update
            
        Returns:
            Optional[VideoModel]: The updated video if found, None otherwise
        """
        try:
            db_video = self.get_video_by_id(video_id)
            if not db_video:
                return None
            
            # Update the video in the database
            update_data = video.dict(exclude_unset=True)
            
            # If the path is updated, update file information
            if "path" in update_data and update_data["path"] != db_video.path:
                path = update_data["path"]
                
                # Check if the video file exists
                if not os.path.exists(path):
                    raise ValueError(f"Video file not found: {path}")
                
                # Get video file information
                update_data["file_name"] = os.path.basename(path)
                update_data["file_size"] = os.path.getsize(path)
                
                # Get video metadata
                duration, format_name, resolution = self._get_video_metadata(path)
                update_data["duration"] = duration
                update_data["format"] = format_name
                update_data["resolution"] = resolution
                
                # Check for subtitle file
                subtitle_path = self._find_subtitle_file(path)
                update_data["has_subtitle"] = subtitle_path is not None
                update_data["subtitle_path"] = subtitle_path
            
            # Update the video
            for key, value in update_data.items():
                setattr(db_video, key, value)
            
            self.db.commit()
            self.db.refresh(db_video)
            
            return db_video
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating video: {e}")
            raise
    
    def delete_video(self, video_id: int) -> bool:
        """
        Delete a video
        
        Args:
            video_id: ID of the video to delete
            
        Returns:
            bool: True if the video was deleted, False otherwise
        """
        try:
            db_video = self.get_video_by_id(video_id)
            if not db_video:
                return False
            
            # Delete the video from the database
            self.db.delete(db_video)
            self.db.commit()
            
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting video: {e}")
            raise
    
    def upload_video(self, file: BinaryIO, filename: str, upload_dir: str, name: Optional[str] = None) -> Optional[VideoModel]:
        """
        Upload a video file
        
        Args:
            file: Video file to upload
            filename: Name of the file
            upload_dir: Directory to upload the file to
            name: Name of the video (defaults to filename without extension)
            
        Returns:
            Optional[VideoModel]: The uploaded video if successful, None otherwise
        """
        try:
            # Create the upload directory if it doesn't exist
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate a path for the uploaded file
            file_path = os.path.join(upload_dir, filename)
            
            # Save the file
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file, f)
            
            # Create the video
            video_name = name or os.path.splitext(filename)[0]
            video = VideoCreate(name=video_name, path=file_path)
            
            return self.create_video(video)
        except Exception as e:
            logger.error(f"Error uploading video: {e}")
            return None
    
    def stream_video(self, video_id: int, serve_ip: Optional[str] = None) -> Optional[str]:
        """
        Stream a video
        
        Args:
            video_id: ID of the video to stream
            serve_ip: IP address to serve the video on
            
        Returns:
            Optional[str]: URL of the video stream if successful, None otherwise
        """
        try:
            db_video = self.get_video_by_id(video_id)
            if not db_video:
                logger.error(f"Video with ID {video_id} not found")
                return None
            
            # Check if the video file exists
            if not os.path.exists(db_video.path):
                logger.error(f"Video file not found: {db_video.path}")
                return None
            
            # Get the serve IP
            if not serve_ip:
                try:
                    serve_ip = self.streaming_service.get_serve_ip()
                    logger.info(f"Using auto-detected serve IP: {serve_ip}")
                except Exception as e:
                    logger.error(f"Error getting serve IP: {e}")
                    # Default to localhost if we can't get the serve IP
                    serve_ip = "127.0.0.1"
                    logger.warning(f"Defaulting to serve IP: {serve_ip}")
            else:
                logger.info(f"Using provided serve IP: {serve_ip}")
            
            # Try to determine a better serve IP based on the device's hostname
            if serve_ip and serve_ip.startswith("10.0.0."):
                # We're on the same network, use our local IP
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect((serve_ip, 80))
                    local_ip = s.getsockname()[0]
                    s.close()
                    
                    if local_ip.startswith("10.0.0."):
                        serve_ip = local_ip
                        logger.info(f"Using local network IP: {serve_ip}")
                except Exception as e:
                    logger.error(f"Error determining local IP: {e}")
            
            # Start the streaming server using the Twisted implementation
            files = {"file_video": db_video.path}
            if db_video.has_subtitle and db_video.subtitle_path:
                files["file_subtitle"] = db_video.subtitle_path
            
            # Make sure we have absolute paths
            for key, path in files.items():
                files[key] = os.path.abspath(path)
                if not os.path.exists(files[key]):
                    logger.error(f"File not found: {files[key]}")
                    files.pop(key)
            
            logger.info(f"Starting twisted streaming server for {db_video.path} on {serve_ip}")
            
            # Explicitly use port 8001 to avoid conflicts
            files_urls, server = self.streaming_service.start_server(files, serve_ip, serve_port=8001)
            
            # Return the video URL
            video_url = files_urls.get("file_video")
            logger.info(f"Streaming URL: {video_url}")
            return video_url
        except Exception as e:
            logger.error(f"Error streaming video: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _get_video_metadata(self, video_path: str) -> tuple:
        """
        Get metadata for a video file
        
        Args:
            video_path: Path to the video file
            
        Returns:
            tuple: (duration, format_name, resolution)
        """
        try:
            # Use ffprobe to get video metadata
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration : stream=width,height",
                "-of", "json",
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error getting video metadata: {result.stderr}")
                return None, None, None
            
            # Parse the JSON output
            metadata = json.loads(result.stdout)
            
            # Get duration
            duration = float(metadata["format"]["duration"]) if "format" in metadata and "duration" in metadata["format"] else None
            
            # Get resolution
            width = height = None
            if "streams" in metadata:
                for stream in metadata["streams"]:
                    if "width" in stream and "height" in stream:
                        width = stream["width"]
                        height = stream["height"]
                        break
            
            resolution = f"{width}x{height}" if width and height else None
            
            # Get format
            format_name = os.path.splitext(video_path)[1][1:] if "." in os.path.basename(video_path) else None
            
            return duration, format_name, resolution
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return None, None, None
    
    def _find_subtitle_file(self, video_path: str) -> Optional[str]:
        """
        Find a subtitle file for a video
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Optional[str]: Path to the subtitle file if found, None otherwise
        """
        try:
            # Get the video file name without extension
            video_name = os.path.splitext(video_path)[0]
            
            # Check for common subtitle extensions
            subtitle_extensions = [".srt", ".sub", ".sbv", ".ass", ".ssa", ".vtt"]
            for ext in subtitle_extensions:
                subtitle_path = f"{video_name}{ext}"
                if os.path.exists(subtitle_path):
                    return subtitle_path
            
            return None
        except Exception as e:
            logger.error(f"Error finding subtitle file: {e}")
            return None

    def scan_directory(self, directory_path: str) -> List[VideoModel]:
        """
        Scan a directory for videos and add new ones to the database.
        Skips videos that already exist based on their path.

        Args:
            directory_path: The path to the directory to scan.

        Returns:
            List[VideoModel]: A list of all video models found or created from the directory.
        """
        logger.info(f"Scanning directory for videos: {directory_path}")
        video_extensions = [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"]
        found_videos: List[VideoModel] = []

        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return found_videos
        
        if not os.path.isdir(directory_path):
            logger.error(f"Path is not a directory: {directory_path}")
            return found_videos

        for root, _, files in os.walk(directory_path):
            for file_name in files:
                if any(file_name.lower().endswith(ext) for ext in video_extensions):
                    file_path = os.path.join(root, file_name)
                    video_name = os.path.splitext(file_name)[0]
                    
                    try:
                        existing_video = self.get_video_by_path(file_path)
                        if existing_video:
                            logger.debug(f"Video already exists in DB: {file_path}")
                            found_videos.append(existing_video)
                            continue
                        
                        logger.info(f"Found new video: {file_path}, adding to DB.")
                        video_create_schema = VideoCreate(name=video_name, path=file_path)
                        # create_video will handle ffprobe and other metadata
                        db_video = self.create_video(video_create_schema)
                        if db_video:
                            found_videos.append(db_video)
                    except ValueError as ve: # Raised by create_video if path doesn't exist (should not happen here)
                        logger.error(f"Validation error adding video {file_path}: {ve}")
                    except SQLAlchemyError as sqla_e:
                        logger.error(f"Database error adding video {file_path}: {sqla_e}")
                        self.db.rollback() # Ensure rollback on DB error during loop
                    except Exception as e:
                        logger.error(f"Unexpected error adding video {file_path}: {e}")
                        logger.exception("Detailed error during video scan processing:") # Added for more detail
        
        logger.info(f"Finished scanning. Found/created {len(found_videos)} videos in {directory_path}.")
        return found_videos
