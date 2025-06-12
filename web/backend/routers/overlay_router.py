from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import uuid
from datetime import datetime

from database.database import get_db
from schemas.overlay import (
    OverlayConfigCreate,
    OverlayConfigUpdate,
    OverlayConfigResponse,
    OverlayStreamRequest,
    OverlayStreamResponse
)
from services.overlay_service import OverlayService
from models.overlay import OverlayConfig

router = APIRouter(prefix="/api/overlay", tags=["overlay"])

@router.post("/configs", response_model=OverlayConfigResponse)
async def create_overlay_config(
    config: OverlayConfigCreate,
    db: Session = Depends(get_db)
):
    """Create a new overlay configuration"""
    try:
        service = OverlayService(db)
        new_config = service.create_config(config)
        return new_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configs", response_model=List[OverlayConfigResponse])
async def list_overlay_configs(
    video_id: Optional[int] = Query(None, description="Filter by video ID"),
    db: Session = Depends(get_db)
):
    """List overlay configurations, optionally filtered by video ID"""
    try:
        service = OverlayService(db)
        configs = service.list_configs(video_id=video_id)
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configs/{config_id}", response_model=OverlayConfigResponse)
async def get_overlay_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific overlay configuration"""
    try:
        service = OverlayService(db)
        config = service.get_config(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/configs/{config_id}", response_model=OverlayConfigResponse)
async def update_overlay_config(
    config_id: int,
    config_update: OverlayConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update an overlay configuration"""
    try:
        service = OverlayService(db)
        updated_config = service.update_config(config_id, config_update)
        if not updated_config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return updated_config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/configs/{config_id}")
async def delete_overlay_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Delete an overlay configuration"""
    try:
        service = OverlayService(db)
        success = service.delete_config(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return {"message": "Configuration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/configs/{config_id}/duplicate", response_model=OverlayConfigResponse)
async def duplicate_overlay_config(
    config_id: int,
    new_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Duplicate an overlay configuration"""
    try:
        service = OverlayService(db)
        new_config = service.duplicate_config(config_id, new_name)
        if not new_config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return new_config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream", response_model=OverlayStreamResponse)
async def create_overlay_stream(
    stream_request: OverlayStreamRequest,
    db: Session = Depends(get_db)
):
    """Create a streaming URL for overlay projection"""
    try:
        service = OverlayService(db)
        stream_info = service.create_stream(stream_request.video_id, stream_request.config_id)
        return stream_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates", response_model=List[OverlayConfigResponse])
async def list_overlay_templates():
    """Get available overlay configuration templates"""
    templates = [
        {
            "id": -1,
            "name": "Weather & Time Display",
            "video_id": None,
            "video_transform": {"x": 0, "y": 0, "scale": 1, "rotation": 0},
            "widgets": [
                {
                    "id": "weather-1",
                    "type": "weather",
                    "position": {"x": 50, "y": 50},
                    "size": {"width": 400, "height": 200},
                    "config": {"city": "San Francisco", "units": "metric"},
                    "visible": True
                },
                {
                    "id": "time-1",
                    "type": "time",
                    "position": {"x": 1470, "y": 50},
                    "size": {"width": 300, "height": 100},
                    "config": {"format": "24h", "showSeconds": True},
                    "visible": True
                },
                {
                    "id": "lights-1",
                    "type": "lights",
                    "position": {"x": 50, "y": 950},
                    "size": {"width": 120, "height": 60},
                    "config": {},
                    "visible": True
                }
            ],
            "api_configs": {
                "weather_api_key": "",
                "timezone": "America/Los_Angeles"
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": -2,
            "name": "Transit Information Board",
            "video_id": None,
            "video_transform": {"x": 0, "y": 0, "scale": 1, "rotation": 0},
            "widgets": [
                {
                    "id": "time-1",
                    "type": "time",
                    "position": {"x": 760, "y": 50},
                    "size": {"width": 400, "height": 150},
                    "config": {"format": "12h", "showSeconds": False},
                    "visible": True
                },
                {
                    "id": "transit-1",
                    "type": "transit",
                    "position": {"x": 50, "y": 300},
                    "size": {"width": 600, "height": 400},
                    "config": {"stopName": "Main Station", "routeFilter": ""},
                    "visible": True
                },
                {
                    "id": "transit-2",
                    "type": "transit",
                    "position": {"x": 1270, "y": 300},
                    "size": {"width": 600, "height": 400},
                    "config": {"stopName": "Secondary Station", "routeFilter": ""},
                    "visible": True
                }
            ],
            "api_configs": {
                "transit_stop_id": "13915",
                "timezone": "America/Los_Angeles"
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    return templates

@router.post("/configs/from-template/{template_id}", response_model=OverlayConfigResponse)
async def create_config_from_template(
    template_id: int,
    video_id: int,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new overlay configuration from a template"""
    try:
        # Get templates
        templates = await list_overlay_templates()
        template = next((t for t in templates if t["id"] == template_id), None)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Create new config from template
        config_data = OverlayConfigCreate(
            name=name or f"{template['name']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            video_id=video_id,
            video_transform=template["video_transform"],
            widgets=template["widgets"],
            api_configs=template["api_configs"]
        )
        
        service = OverlayService(db)
        new_config = service.create_config(config_data)
        return new_config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))