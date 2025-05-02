from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class DeviceBase(BaseModel):
    """
    Base schema for a device
    """
    name: str = Field(..., description="Device name")
    type: str = Field(..., description="Device type (dlna or transcreen)")
    hostname: str = Field(..., description="Device hostname or IP address")
    friendly_name: str = Field(..., description="User-friendly device name")

class DeviceCreate(DeviceBase):
    """
    Schema for creating a device
    """
    action_url: Optional[str] = Field(None, description="Action URL for DLNA devices")
    manufacturer: Optional[str] = Field(None, description="Device manufacturer")
    location: Optional[str] = Field(None, description="Device location URL")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional device configuration")

class DeviceUpdate(BaseModel):
    """
    Schema for updating a device
    """
    name: Optional[str] = Field(None, description="Device name")
    type: Optional[str] = Field(None, description="Device type (dlna or transcreen)")
    hostname: Optional[str] = Field(None, description="Device hostname or IP address")
    friendly_name: Optional[str] = Field(None, description="User-friendly device name")
    action_url: Optional[str] = Field(None, description="Action URL for DLNA devices")
    manufacturer: Optional[str] = Field(None, description="Device manufacturer")
    location: Optional[str] = Field(None, description="Device location URL")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional device configuration")

class DeviceResponse(DeviceBase):
    """
    Schema for device response
    """
    id: int = Field(..., description="Device ID")
    action_url: Optional[str] = Field(None, description="Action URL for DLNA devices")
    manufacturer: Optional[str] = Field(None, description="Device manufacturer")
    location: Optional[str] = Field(None, description="Device location URL")
    status: str = Field(..., description="Device status")
    is_playing: bool = Field(..., description="Whether the device is playing")
    current_video: Optional[str] = Field(None, description="Path to the current video")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional device configuration")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    
    class Config:
        orm_mode = True

class DeviceList(BaseModel):
    """
    Schema for a list of devices
    """
    devices: List[DeviceResponse] = Field(..., description="List of devices")
    total: int = Field(..., description="Total number of devices")

class DevicePlayRequest(BaseModel):
    """
    Schema for playing a video on a device
    """
    video_id: int = Field(..., description="ID of the video to play")
    loop: bool = Field(False, description="Whether to loop the video")

class DeviceActionResponse(BaseModel):
    """
    Schema for device action response
    """
    success: bool = Field(..., description="Whether the action was successful")
    message: str = Field(..., description="Response message")
