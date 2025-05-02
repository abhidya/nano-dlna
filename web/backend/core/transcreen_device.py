import logging
import traceback
import requests
from typing import Dict, List, Optional, Any

from .device import Device

logger = logging.getLogger(__name__)

class TranscreenDevice(Device):
    """
    Implementation of a Transcreen device
    """
    def __init__(self, device_info: Dict[str, Any]):
        super().__init__(device_info)
        self.type = "transcreen"
        self.hostname = device_info.get("hostname")
        
        if not self.hostname:
            logger.error(f"Transcreen device {self.name} missing hostname")
            raise ValueError(f"Transcreen device {self.name} missing hostname")
    
    def play(self, video_url: str, loop: bool = False) -> bool:
        """
        Play a video on the Transcreen device
        
        Args:
            video_url: URL of the video to play
            loop: Whether to loop the video
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Playing video {video_url} on Transcreen device {self.name}")
            
            # Assuming Transcreen uses a specific API endpoint to play videos
            transcreen_play_url = f"http://{self.hostname}/play"
            payload = {
                'url': video_url,
                'loop': loop
            }
            
            response = requests.post(transcreen_play_url, json=payload, timeout=5)
            response.raise_for_status()
            
            # Update device status
            self.update_status("connected")
            self.update_video(video_url)
            self.update_playing(True)
            
            # Store the current streaming URL
            self._current_streaming_url = video_url
            
            # Reset error counters
            self._consecutive_errors = 0
            
            logger.info(f"Successfully started playing video on {self.name}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Transcreen play command to '{self.name}': {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def stop(self) -> bool:
        """
        Stop playback on the Transcreen device
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Stopping playback on Transcreen device {self.name}")
            
            # Example: Send a request to the Transcreen device to stop the video
            transcreen_stop_url = f"http://{self.hostname}/stop"
            
            response = requests.post(transcreen_stop_url, timeout=5)
            response.raise_for_status()
            
            # Update device status
            self.update_playing(False)
            
            logger.debug(f"Sent Transcreen stop command to {self.name}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Transcreen stop command to '{self.name}': {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def pause(self) -> bool:
        """
        Pause playback on the Transcreen device
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Pausing playback on Transcreen device {self.name}")
            
            # Example: Send a request to the Transcreen device to pause the video
            transcreen_pause_url = f"http://{self.hostname}/pause"
            
            response = requests.post(transcreen_pause_url, timeout=5)
            response.raise_for_status()
            
            # Update device status
            self.update_playing(False)
            
            logger.debug(f"Sent Transcreen pause command to {self.name}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Transcreen pause command to '{self.name}': {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def seek(self, position: str) -> bool:
        """
        Seek to a position in the current video
        
        Args:
            position: Position to seek to (format: HH:MM:SS)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Seeking to position {position} on Transcreen device {self.name}")
            
            # Example: Send a request to the Transcreen device to seek to a position
            transcreen_seek_url = f"http://{self.hostname}/seek"
            payload = {
                'position': position
            }
            
            response = requests.post(transcreen_seek_url, json=payload, timeout=5)
            response.raise_for_status()
            
            logger.debug(f"Sent Transcreen seek command to {self.name} with position {position}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Transcreen seek command to '{self.name}': {e}")
            logger.debug(traceback.format_exc())
            return False
