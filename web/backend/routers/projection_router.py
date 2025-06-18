from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import os
import uuid
import json
from datetime import datetime
from PIL import Image
import numpy as np

from database.database import get_db
from services.mask_analyzer import MaskAnalyzer
from services.projection_service import ProjectionService
from schemas.projection import (
    ProjectionConfigCreate,
    ProjectionConfigUpdate,
    ProjectionConfigResponse,
    Zone,
    ZoneTransform,
    ZoneAssignment,
    MaskData
)

router = APIRouter(prefix="/api/projection", tags=["projection"])

# In-memory storage for masks and temporary sessions
projection_sessions = {}
uploaded_masks = {}

@router.post("/mask")
async def upload_mask(
    masks: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload multiple projection masks - each becomes one zone"""
    try:
        # Ensure masks is a list (handle single file upload)
        if not isinstance(masks, list):
            masks = [masks]
            
        # Validate file types
        for mask in masks:
            if not mask.filename.lower().endswith('.png'):
                raise HTTPException(status_code=400, detail=f"Only PNG files are supported. Invalid file: {mask.filename}")
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "uploads", "masks")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Process all masks
        all_zones = []
        mask_id = str(uuid.uuid4())  # Single ID for this batch of masks
        
        for index, mask in enumerate(masks):
            # Generate unique filename for each mask
            filename = f"{mask_id}_{index}.png"
            filepath = os.path.join(upload_dir, filename)
            
            # Save file
            content = await mask.read()
            with open(filepath, "wb") as f:
                f.write(content)
            
            # Analyze mask to find white regions
            analyzer = MaskAnalyzer()
            detected_zones = analyzer.analyze_mask(filepath)
            
            # Add source mask info to each detected zone
            for zone in detected_zones:
                zone["sourceMask"] = mask.filename
            all_zones.extend(detected_zones)
        
        # Store mask info
        mask_info = {
            "id": mask_id,
            "name": f"{len(masks)} masks uploaded",
            "filepath": upload_dir,  # Directory containing all masks
            "width": max(zone["bounds"]["width"] for zone in all_zones) if all_zones else 0,
            "height": max(zone["bounds"]["height"] for zone in all_zones) if all_zones else 0,
            "zones": all_zones,
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
        uploaded_masks[mask_id] = mask_info
        
        return mask_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/masks/{mask_id}")
async def get_mask(mask_id: str, db: Session = Depends(get_db)):
    """Get mask information by ID"""
    if mask_id not in uploaded_masks:
        raise HTTPException(status_code=404, detail="Mask not found")
    
    return uploaded_masks[mask_id]

@router.get("/masks/{session_id}/image")
async def get_mask_image(session_id: str):
    """Get the mask image file for a session - returns composite of all masks"""
    # First check if this is a session ID
    if session_id in projection_sessions:
        session = projection_sessions[session_id]
        mask_id = session.get("maskId")
        if mask_id and mask_id in uploaded_masks:
            upload_dir = uploaded_masks[mask_id]["filepath"]
            mask_info = uploaded_masks[mask_id]
            
            # Create composite mask with all uploaded mask files
            composite = None
            # Iterate through all possible mask files (not zones)
            mask_index = 0
            while True:
                mask_file = f"{mask_id}_{mask_index}.png"
                filepath = os.path.join(upload_dir, mask_file)
                
                if os.path.exists(filepath):
                    img = Image.open(filepath).convert('RGBA')
                    if composite is None:
                        composite = Image.new('RGBA', img.size, (0, 0, 0, 255))
                    
                    # Paste white areas from this mask onto composite
                    composite.paste(img, (0, 0), img)
                    mask_index += 1
                else:
                    # No more mask files
                    break
            
            if composite:
                # Save composite temporarily
                composite_path = os.path.join(upload_dir, f"{mask_id}_composite.png")
                composite.save(composite_path)
                return FileResponse(composite_path, media_type="image/png")
    
    # Try direct mask ID lookup
    if session_id in uploaded_masks:
        upload_dir = uploaded_masks[session_id]["filepath"]
        mask_file = f"{session_id}_0.png"
        filepath = os.path.join(upload_dir, mask_file)
        
        if os.path.exists(filepath):
            return FileResponse(filepath, media_type="image/png")
    
    raise HTTPException(status_code=404, detail="Mask image not found")

@router.get("/animations")
async def get_animations():
    """Get list of available animations"""
    # For now, return static list. Later this can come from database
    animations = [
        {
            "id": "neural_noise",
            "name": "Neural Noise",
            "description": "Flowing neural network patterns",
            "dataInputs": ["weather"],
            "thumbnail": "🧠"
        },
        {
            "id": "moving_clouds",
            "name": "Moving Clouds", 
            "description": "Drifting cloud layers",
            "dataInputs": ["weather"],
            "thumbnail": "☁️"
        },
        {
            "id": "spectrum_bars",
            "name": "Spectrum Bars",
            "description": "Animated spectrum visualization",
            "dataInputs": ["transit"],
            "thumbnail": "📊"
        },
        {
            "id": "webgl_flowers",
            "name": "WebGL Flowers",
            "description": "Blooming flower patterns",
            "dataInputs": ["weather", "transit"],
            "thumbnail": "🌸"
        },
        {
            "id": "gradient_bubbles",
            "name": "Gradient Bubbles",
            "description": "Floating gradient orbs",
            "dataInputs": ["weather"],
            "thumbnail": "🫧"
        },
        {
            "id": "milk_physics",
            "name": "Milk Physics",
            "description": "Liquid particle simulation",
            "dataInputs": ["weather"],
            "thumbnail": "🥛"
        },
        {
            "id": "rainstorm",
            "name": "Rainstorm",
            "description": "Weather-driven rain effects",
            "dataInputs": ["weather"],
            "thumbnail": "🌧️"
        },
        {
            "id": "segment_clock",
            "name": "7-Segment Clock",
            "description": "Digital time display",
            "dataInputs": ["weather"],
            "thumbnail": "🕐"
        },
        {
            "id": "pride_spectrum",
            "name": "Pride Spectrum",
            "description": "Rainbow spectrum waves",
            "dataInputs": ["weather", "transit"],
            "thumbnail": "🌈"
        },
        {
            "id": "pipes_flow",
            "name": "Pipes Flow",
            "description": "Organic flowing circles",
            "dataInputs": ["weather", "transit"],
            "thumbnail": "🔵"
        },
        {
            "id": "skillet_switch",
            "name": "Skillet Switch",
            "description": "System state indicators",
            "dataInputs": ["weather", "transit"],
            "thumbnail": "🎚️"
        }
    ]
    
    return {"animations": animations}

@router.post("/animations/import")
async def import_codepen(
    data: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Import animation from CodePen URL"""
    url = data.get("url", "")
    
    if not url or "codepen.io" not in url:
        raise HTTPException(status_code=400, detail="Invalid CodePen URL")
    
    # For now, return mock data. Real implementation would:
    # 1. Fetch CodePen data via API
    # 2. Transform code to remove mouse dependencies
    # 3. Save to animations directory
    
    animation_id = f"codepen_{uuid.uuid4().hex[:8]}"
    
    return {
        "id": animation_id,
        "name": "Imported Animation",
        "description": f"Imported from {url}",
        "dataInputs": [],
        "thumbnail": "📦",
        "source": url
    }

@router.post("/sessions/create")
async def create_session(
    session_data: Dict,
    db: Session = Depends(get_db)
):
    """Create a new projection session"""
    try:
        session_id = str(uuid.uuid4())
        
        # Validate mask exists
        mask_id = session_data.get("maskId")
        if mask_id not in uploaded_masks:
            raise HTTPException(status_code=400, detail="Invalid mask ID")
        
        # Store session
        session = {
            "id": session_id,
            "maskId": mask_id,
            "mask": uploaded_masks[mask_id],
            "zones": session_data.get("zones", []),
            "created_at": datetime.utcnow().isoformat()
        }
        
        projection_sessions[session_id] = session
        
        return {"id": session_id, "status": "created"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get projection session data"""
    if session_id not in projection_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return projection_sessions[session_id]

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete a projection session"""
    if session_id not in projection_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del projection_sessions[session_id]
    return {"status": "deleted"}

# Configuration endpoints (database-backed)
@router.post("/configs", response_model=ProjectionConfigResponse)
async def create_projection_config(
    config: ProjectionConfigCreate,
    db: Session = Depends(get_db)
):
    """Create a new projection configuration"""
    try:
        service = ProjectionService(db)
        return service.create_config(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configs", response_model=List[ProjectionConfigResponse])
async def list_projection_configs(
    db: Session = Depends(get_db)
):
    """List all projection configurations"""
    service = ProjectionService(db)
    return service.get_configs()

@router.get("/configs/{config_id}", response_model=ProjectionConfigResponse)
async def get_projection_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific projection configuration"""
    service = ProjectionService(db)
    config = service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config

@router.put("/configs/{config_id}", response_model=ProjectionConfigResponse)
async def update_projection_config(
    config_id: int,
    update_data: ProjectionConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update a projection configuration"""
    service = ProjectionService(db)
    config = service.update_config(config_id, update_data)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config

@router.delete("/configs/{config_id}")
async def delete_projection_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Delete a projection configuration"""
    service = ProjectionService(db)
    if not service.delete_config(config_id):
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"status": "deleted"}

@router.post("/configs/{config_id}/duplicate", response_model=ProjectionConfigResponse)
async def duplicate_projection_config(
    config_id: int,
    new_name: str = Query(..., description="Name for the duplicated configuration"),
    db: Session = Depends(get_db)
):
    """Duplicate a projection configuration"""
    service = ProjectionService(db)
    config = service.duplicate_config(config_id, new_name)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config

@router.post("/configs/{config_id}/launch")
async def launch_from_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Create a session from a saved configuration"""
    service = ProjectionService(db)
    config = service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Create session from config
    session_id = str(uuid.uuid4())
    session = {
        "id": session_id,
        "config_id": config_id,
        "maskId": config.mask_data.get("id"),
        "mask": config.mask_data,
        "zones": config.zones,
        "created_at": datetime.utcnow().isoformat()
    }
    
    projection_sessions[session_id] = session
    return {"id": session_id, "status": "created"}

@router.get("/data/weather")
async def get_weather_data():
    """Get current weather data for animations"""
    # Mock data for now. Real implementation would fetch from weather API
    return {
        "temperature": 22,
        "humidity": 65,
        "windSpeed": 15,
        "windDirection": 180,
        "conditions": "partly_cloudy",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/data/transit")
async def get_transit_data():
    """Get current transit data for animations"""
    # Mock data for now. Real implementation would fetch from transit API
    return {
        "nextArrival": "5 minutes",
        "routeName": "Blue Line",
        "destination": "Downtown",
        "timestamp": datetime.utcnow().isoformat()
    }