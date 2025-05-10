from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import logging

from database.database import get_db
from models.video import VideoModel
from schemas.video import (
    VideoCreate,
    VideoUpdate,
    VideoResponse,
    VideoList,
    VideoUploadResponse,
)
from services.video_service import VideoService, get_video_service
from core.streaming_service import StreamingService

# Add logger
logger = logging.getLogger(__name__)

# Create a streaming service instance
streaming_service = StreamingService()

# Create router
router = APIRouter(
    prefix="/videos",
    tags=["videos"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get the video service
def get_video_service(db: Session = Depends(get_db)) -> VideoService:
    return VideoService(db, streaming_service)

@router.get("/", response_model=VideoList)
def get_videos(
    skip: int = 0,
    limit: int = 100,
    video_service: VideoService = Depends(get_video_service),
):
    """
    Get all videos
    """
    videos = video_service.get_videos(skip=skip, limit=limit)
    # Convert datetime objects to strings
    formatted_videos = []
    for video in videos:
        video_dict = video.to_dict()
        formatted_videos.append(video_dict)
    
    return {
        "videos": formatted_videos,
        "total": len(videos),
    }

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    video_service: VideoService = Depends(get_video_service),
):
    """
    Get a video by ID
    """
    video = video_service.get_video_by_id(video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID {video_id} not found",
        )
    return video.to_dict()

@router.post("/", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
def create_video(
    video: VideoCreate,
    video_service: VideoService = Depends(get_video_service),
):
    """
    Create a new video
    """
    try:
        db_video = video_service.create_video(video)
        return db_video.to_dict()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.put("/{video_id}", response_model=VideoResponse)
def update_video(
    video_id: int,
    video: VideoUpdate,
    video_service: VideoService = Depends(get_video_service),
):
    """
    Update a video
    """
    db_video = video_service.update_video(video_id, video)
    if not db_video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID {video_id} not found",
        )
    return db_video.to_dict()

@router.delete("/{video_id}")
def delete_video(
    video_id: int,
    video_service: VideoService = Depends(get_video_service),
):
    """
    Delete a video
    """
    success = video_service.delete_video(video_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID {video_id} not found",
        )
    return {"success": True, "message": f"Video with ID {video_id} deleted"}

@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    upload_dir: str = Form("uploads"),
    video_service: VideoService = Depends(get_video_service),
):
    """
    Upload a video file
    """
    # Check if the file is a video
    content_type = file.content_type
    if not content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not a video",
        )
    
    # Get the file extension
    filename = file.filename
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no name",
        )
    
    # Upload the video
    video = video_service.upload_video(
        file.file,
        filename,
        upload_dir,
        name,
    )
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload video",
        )
    
    return {
        "success": True,
        "message": f"Video {filename} uploaded successfully",
        "video": video.to_dict() if video else None,
    }

@router.post("/{video_id}/stream")
def stream_video(
    video_id: int,
    serve_ip: Optional[str] = None,
    video_service: VideoService = Depends(get_video_service),
):
    """
    Stream a video
    """
    video_url = video_service.stream_video(video_id, serve_ip)
    if not video_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream video with ID {video_id}",
        )
    
    return {"success": True, "url": video_url}

@router.post("/scan-directory")
def scan_directory(
    directory: str = Query(None, description="Directory to scan for videos"),
    body: dict = Body(None, description="Request body for directory parameter"),
    video_service: VideoService = Depends(get_video_service),
):
    """
    Scan a directory for videos and add them to the database
    Accepts directory from either query parameter or JSON body
    """
    # Get directory from query parameter or body
    scan_directory = directory
    if scan_directory is None and body:
        scan_directory = body.get("directory")
    
    if not scan_directory:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Directory parameter is required (either in query or body)",
        )
    
    # Check if directory exists
    if not os.path.exists(scan_directory):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Directory {scan_directory} does not exist",
        )
    
    if not os.path.isdir(scan_directory):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{scan_directory} is not a directory",
        )
    
    # Scan the directory for video files
    video_extensions = [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"]
    videos = []
    
    for root, _, files in os.walk(scan_directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                file_path = os.path.join(root, file)
                name = os.path.splitext(file)[0]
                
                try:
                    # Check if the video already exists
                    existing_video = video_service.get_video_by_path(file_path)
                    if existing_video:
                        videos.append(existing_video)
                        continue
                    
                    # Create the video
                    video = VideoCreate(name=name, path=file_path)
                    db_video = video_service.create_video(video)
                    videos.append(db_video)
                except Exception as e:
                    # Log the error and continue
                    logger.error(f"Error adding video {file_path}: {e}")
    
    # Convert videos to dictionaries
    formatted_videos = []
    for video in videos:
        video_dict = video.to_dict()
        formatted_videos.append(video_dict)
    
    return {
        "success": True,
        "message": f"Found {len(videos)} videos in {scan_directory}",
        "videos": formatted_videos,
    }

@router.post("/scan")
def scan_videos(
    directory: str = Query(None, description="Directory to scan for videos"),
    body: dict = Body(None, description="Request body for directory parameter"),
    video_service: VideoService = Depends(get_video_service),
):
    """
    Scan a directory for videos and add them to the database
    This is an alias for the scan-directory endpoint for better API compatibility
    Accepts directory from either query parameter or JSON body
    """
    # Get directory from query parameter or body
    scan_directory = directory
    if scan_directory is None and body:
        scan_directory = body.get("directory")
    
    if not scan_directory:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Directory parameter is required (either as query parameter or in JSON body)"
        )
    
    videos = video_service.scan_directory(scan_directory)
    return {"message": f"Found {len(videos)} videos in {scan_directory}", "videos": videos}
