from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class WidgetPosition(BaseModel):
    x: int
    y: int

class WidgetSize(BaseModel):
    width: int
    height: int

class Widget(BaseModel):
    id: str
    type: str  # 'weather', 'time', 'transit', 'lights'
    position: WidgetPosition
    size: WidgetSize
    config: Dict[str, Any]
    visible: bool = True
    rotation: float = 0  # Rotation in degrees

class VideoTransform(BaseModel):
    x: float = 0
    y: float = 0
    scale: float = 1.0
    rotation: float = 0

class ApiConfigs(BaseModel):
    weather_api_key: Optional[str] = ""
    transit_stop_id: Optional[str] = ""
    timezone: Optional[str] = "America/Los_Angeles"

class OverlayConfigBase(BaseModel):
    name: str
    video_id: int
    video_transform: VideoTransform
    widgets: List[Widget]
    api_configs: ApiConfigs

class OverlayConfigCreate(OverlayConfigBase):
    pass

class OverlayConfigUpdate(BaseModel):
    name: Optional[str] = None
    video_transform: Optional[VideoTransform] = None
    widgets: Optional[List[Widget]] = None
    api_configs: Optional[ApiConfigs] = None

class OverlayConfigResponse(OverlayConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OverlayStreamRequest(BaseModel):
    video_id: int
    config_id: Optional[int] = None

class OverlayStreamResponse(BaseModel):
    streaming_url: str
    port: int
    video_path: str
    config_id: Optional[int] = None