"""
Brightness control service that manages DLNA devices based on brightness settings
"""
import logging
import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.device_manager import get_device_manager
from services.device_service import DeviceService
from database.database import get_db
from utils.create_black_image import create_black_image

logger = logging.getLogger(__name__)

class BrightnessControlService:
    """
    Service to control DLNA devices based on brightness settings
    When brightness is 0, cast black video to all playing devices
    When brightness is restored, resume original videos
    """
    
    def __init__(self):
        self.device_manager = get_device_manager()
        self.black_image_path = None
        self.device_state_backup = {}  # Store device states before blackout
        self.is_blackout_active = False
        self._ensure_black_image()
    
    def _ensure_black_image(self):
        """Ensure black image file exists"""
        try:
            self.black_image_path = create_black_image()
            logger.info(f"Black image available at: {self.black_image_path}")
        except Exception as e:
            logger.error(f"Failed to create black image: {e}")
            # Fallback to any existing black image
            fallback_paths = [
                "/Users/mannybhidya/PycharmProjects/nano-dlna/web/backend/static/black_image.jpg",
                "/Users/mannybhidya/PycharmProjects/nano-dlna/web/backend/static/black.jpg",
                os.path.join(os.path.dirname(__file__), "..", "static", "black_image.jpg")
            ]
            for path in fallback_paths:
                if os.path.exists(path):
                    self.black_image_path = path
                    logger.info(f"Using existing black image at: {path}")
                    break
    
    def set_brightness(self, brightness: int) -> Dict[str, Any]:
        """
        Set brightness level and control DLNA devices accordingly
        
        Args:
            brightness: Brightness level (0-100)
            
        Returns:
            Dict with status information
        """
        logger.info(f"Setting brightness to {brightness}")
        
        if brightness == 0 and not self.is_blackout_active:
            # Activate blackout mode
            return self._activate_blackout()
        elif brightness > 0 and self.is_blackout_active:
            # Deactivate blackout mode
            return self._deactivate_blackout()
        else:
            # Just update brightness value without changing device states
            return {
                "brightness": brightness,
                "status": "updated",
                "blackout_active": self.is_blackout_active,
                "message": f"Brightness set to {brightness}%"
            }
    
    def _activate_blackout(self) -> Dict[str, Any]:
        """Activate blackout mode - display black image on all playing devices"""
        logger.info("Activating blackout mode")
        
        if not self.black_image_path or not os.path.exists(self.black_image_path):
            logger.error("Black image not available")
            return {
                "brightness": 0,
                "status": "error",
                "error": "Black image file not available"
            }
        
        affected_devices = []
        errors = []
        
        # Get all devices
        devices = self.device_manager.get_devices()
        
        for device in devices:
            try:
                # Only affect devices that are currently playing
                if device.is_playing and device.current_video:
                    # Backup current state
                    self.device_state_backup[device.name] = {
                        "video_path": device.current_video,
                        "video_url": getattr(device, 'streaming_url', None),
                        "is_looping": getattr(device, '_loop_enabled', False),
                        "timestamp": datetime.utcnow()
                    }
                    
                    logger.info(f"Backing up state for {device.name}: {self.device_state_backup[device.name]}")
                    
                    # Stop current playback
                    device.stop()
                    time.sleep(0.5)  # Brief pause
                    
                    # Display black image
                    # We'll use the auto_play_video method but pass the image path
                    # The streaming server will serve it and DLNA devices can display it
                    success = self.device_manager.auto_play_video(
                        device, 
                        self.black_image_path, 
                        loop=False  # No looping for images
                    )
                    
                    if success:
                        affected_devices.append(device.name)
                        logger.info(f"Successfully activated blackout on {device.name}")
                    else:
                        errors.append(f"Failed to display black image on {device.name}")
                        logger.error(f"Failed to activate blackout on {device.name}")
                        
            except Exception as e:
                error_msg = f"Error processing device {device.name}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        self.is_blackout_active = True
        
        return {
            "brightness": 0,
            "status": "blackout_activated",
            "blackout_active": True,
            "affected_devices": affected_devices,
            "device_count": len(affected_devices),
            "errors": errors if errors else None,
            "message": f"Blackout activated on {len(affected_devices)} devices"
        }
    
    def _deactivate_blackout(self) -> Dict[str, Any]:
        """Deactivate blackout mode - restore original videos"""
        logger.info("Deactivating blackout mode")
        
        restored_devices = []
        errors = []
        
        # Get all devices
        devices = self.device_manager.get_devices()
        
        for device in devices:
            try:
                # Check if this device has a backed up state
                if device.name in self.device_state_backup:
                    backup = self.device_state_backup[device.name]
                    logger.info(f"Restoring state for {device.name}: {backup}")
                    
                    # Stop black image display
                    device.stop()
                    time.sleep(0.5)  # Brief pause
                    
                    # Restore original video
                    video_path = backup["video_path"]
                    
                    # Extract actual file path from URL if needed
                    if video_path.startswith("http://"):
                        # Try to find the actual file path
                        with self.device_manager.assigned_videos_lock:
                            assigned_path = self.device_manager.assigned_videos.get(device.name)
                            if assigned_path and os.path.exists(assigned_path):
                                video_path = assigned_path
                            else:
                                # Try to extract from URL
                                import re
                                match = re.search(r'/([^/]+\.mp4)$', video_path)
                                if match:
                                    filename = match.group(1)
                                    # Check common locations
                                    possible_paths = [
                                        os.path.join("/Users/mannybhidya/PycharmProjects/nano-dlna", filename),
                                        os.path.join("/Users/mannybhidya/PycharmProjects/nano-dlna/web/uploads/videos", filename),
                                        os.path.join("/Users/mannybhidya/PycharmProjects/nano-dlna/web/backend/uploads", filename)
                                    ]
                                    for path in possible_paths:
                                        if os.path.exists(path):
                                            video_path = path
                                            break
                    
                    if os.path.exists(video_path):
                        success = self.device_manager.auto_play_video(
                            device,
                            video_path,
                            loop=backup.get("is_looping", True)
                        )
                        
                        if success:
                            restored_devices.append(device.name)
                            logger.info(f"Successfully restored video on {device.name}")
                            # Remove from backup after successful restore
                            del self.device_state_backup[device.name]
                        else:
                            errors.append(f"Failed to restore video on {device.name}")
                            logger.error(f"Failed to restore video on {device.name}")
                    else:
                        errors.append(f"Original video not found for {device.name}: {video_path}")
                        logger.error(f"Original video not found: {video_path}")
                        
            except Exception as e:
                error_msg = f"Error restoring device {device.name}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        self.is_blackout_active = False
        
        return {
            "brightness": 100,  # Default restored brightness
            "status": "blackout_deactivated", 
            "blackout_active": False,
            "restored_devices": restored_devices,
            "device_count": len(restored_devices),
            "errors": errors if errors else None,
            "message": f"Blackout deactivated, restored {len(restored_devices)} devices"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current brightness control status"""
        playing_devices = []
        
        devices = self.device_manager.get_devices()
        for device in devices:
            if device.is_playing:
                playing_devices.append({
                    "name": device.name,
                    "current_video": device.current_video,
                    "is_black_image": device.current_video == self.black_image_path if device.current_video else False
                })
        
        return {
            "blackout_active": self.is_blackout_active,
            "black_image_available": bool(self.black_image_path and os.path.exists(self.black_image_path)),
            "black_image_path": self.black_image_path,
            "playing_devices": playing_devices,
            "backed_up_devices": list(self.device_state_backup.keys()),
            "total_devices": len(devices),
            "playing_count": len(playing_devices)
        }

# Singleton instance
_brightness_control_instance = None

def get_brightness_control_service() -> BrightnessControlService:
    """Get singleton instance of brightness control service"""
    global _brightness_control_instance
    if _brightness_control_instance is None:
        _brightness_control_instance = BrightnessControlService()
    return _brightness_control_instance