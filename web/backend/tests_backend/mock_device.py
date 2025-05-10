"""
Mock implementation of the Device class for testing.
"""
from typing import Dict, Any, Optional
from core.device import Device


class MockDevice(Device):
    """Mock implementation of the Device class for testing."""

    def __init__(self, device_info: Dict[str, Any]):
        """Initialize the mock device."""
        super().__init__(device_info)
        self._current_position = 0
        self.hostname = device_info.get("hostname", "localhost")
        self.action_url = device_info.get("action_url", "")
        self.control_url = device_info.get("control_url", "")
        self.location = device_info.get("location", "")
        
    def __eq__(self, other):
        """Check if two devices are equal."""
        if not isinstance(other, Device):
            return False
        return self.name == other.name and self.hostname == other.hostname

    def play(self, video_url: str) -> bool:
        """Play a video."""
        self.is_playing = True
        self.current_video = video_url
        self._current_position = 0
        return True

    def stop(self) -> bool:
        """Stop playback."""
        self.is_playing = False
        self.current_video = None
        self._current_position = 0
        return True

    def pause(self) -> bool:
        """Pause playback."""
        if self.is_playing:
            self.is_playing = False
            return True
        return False

    def seek(self, position: int) -> bool:
        """Seek to a position in the video."""
        if self.current_video:
            self._current_position = position
            return True
        return False

    @property
    def current_position(self) -> int:
        """Get the current position."""
        return self._current_position
