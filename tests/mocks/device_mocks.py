"""
Mock device classes for testing
"""
import threading
from typing import Dict, Any, Optional, List
from unittest.mock import MagicMock


class MockDevice:
    """Base mock device class"""
    
    def __init__(self, device_info: Dict[str, Any]):
        self.name = device_info.get("name", "Unknown")
        self.id = device_info.get("id", "unknown-id")
        self.hostname = device_info.get("hostname", "127.0.0.1")
        self.status = "disconnected"
        self.video = None
        self.playing = False
        self.device_info = device_info
        
    def update_status(self, status: str):
        """Update device status"""
        self.status = status
        
    def update_video(self, video: Optional[str]):
        """Update current video"""
        self.video = video
        
    def update_playing(self, playing: bool):
        """Update playing state"""
        self.playing = playing
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "id": self.id,
            "hostname": self.hostname,
            "status": self.status,
            "video": self.video,
            "playing": self.playing,
            **self.device_info
        }


class MockDLNADevice(MockDevice):
    """Mock DLNA device for testing"""
    
    def __init__(self, device_info: Dict[str, Any]):
        super().__init__(device_info)
        self.location = device_info.get("location", f"http://{self.hostname}:8000/device")
        self.action_url = device_info.get("action_url", f"http://{self.hostname}:8000/AVTransport/Control")
        self.friendly_name = device_info.get("friendly_name", self.name)
        
        # Thread management
        self._thread_lock = threading.Lock()
        self._loop_enabled = False
        self._loop_thread = None
        
        # Mock methods
        self._send_dlna_action = MagicMock()
        self._send_dlna_action_with_response = MagicMock()
        self._get_transport_info = MagicMock(return_value={"CurrentTransportState": "PLAYING"})
        self._get_position_info = MagicMock(return_value={"RelTime": "00:00:01", "TrackDuration": "00:01:00"})
        self.device_manager = MagicMock()
        self._try_restart_video = MagicMock(return_value=True)
        
    def _setup_loop_monitoring(self, video_url: str):
        """Mock setup loop monitoring"""
        with self._thread_lock:
            self._loop_enabled = True
            self._loop_thread = threading.Thread(target=lambda: None)
            self._loop_thread.daemon = True
            self._loop_thread.start()
            
    def _setup_loop_monitoring_v2(self, video_url: str):
        """Mock setup loop monitoring v2"""
        self._setup_loop_monitoring(video_url)
        
    def stop_video(self):
        """Mock stop video"""
        with self._thread_lock:
            self._loop_enabled = False
        self.update_playing(False)
        self.update_video(None)
        
    def _handle_streaming_health_check(self, session_id: str, reason: str):
        """Mock streaming health check handler"""
        pass


class MockDeviceManager:
    """Mock device manager for testing"""
    
    def __init__(self):
        self.devices: Dict[str, MockDevice] = {}
        self.device_status: Dict[str, str] = {}
        # UPDATED: Use consolidated lock architecture matching DeviceManager
        self.device_state_lock = threading.RLock()
        self.assignment_lock = threading.Lock()
        self.monitoring_lock = threading.Lock()
        self.statistics_lock = threading.Lock()
        self.discovery_running = False
        
    def add_device(self, device: MockDevice):
        """Add a device to the manager"""
        with self.device_state_lock:
            self.devices[device.name] = device
        with self.device_state_lock:
            self.device_status[device.name] = device.status
            
    def get_device(self, device_name: str) -> Optional[MockDevice]:
        """Get a device by name"""
        with self.device_state_lock:
            return self.devices.get(device_name)
            
    def get_all_devices(self) -> List[MockDevice]:
        """Get all devices"""
        with self.device_state_lock:
            return list(self.devices.values())
            
    def update_device_status(self, device_name: str, status: str):
        """Update device status"""
        with self.device_state_lock:
            self.device_status[device_name] = status
            
    def update_device_playback_progress(self, device_name: str, progress: Dict[str, Any]):
        """Mock update playback progress"""
        pass
        
    def start_discovery(self):
        """Mock start discovery"""
        self.discovery_running = True
        
    def stop_discovery(self):
        """Mock stop discovery"""
        self.discovery_running = False