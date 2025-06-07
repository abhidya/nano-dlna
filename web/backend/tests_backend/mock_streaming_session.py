"""
Mock implementation of the StreamingSession class for testing.
"""
import uuid
from typing import Dict, Any, Optional
from web.backend.core.streaming_session import StreamingSession
from web.backend.core.device import Device


class MockStreamingSession(StreamingSession):
    """Mock implementation of the StreamingSession class for testing."""

    def __init__(self, device: Device, video_path: str, session_id: Optional[str] = None):
        """Initialize the mock streaming session."""
        self.device = device
        self.device_name = device.name
        self.video_path = video_path
        self.status = "playing"
        self.session_id = session_id or str(uuid.uuid4())
        self.start_time = None
        self.end_time = None
        self.duration = 0
        self.loop = False
        self.streaming_url = f"http://localhost:8000/{self.session_id}"
        self.active = True

    def update_status(self, status: str) -> None:
        """Update the session status."""
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            "session_id": self.session_id,
            "device_name": self.device.name,
            "video_path": self.video_path,
            "status": self.status,
            "streaming_url": self.streaming_url,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "loop": self.loop
        }
