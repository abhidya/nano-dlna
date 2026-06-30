import uuid
from typing import Any


class MockStreamingSession:
    def __init__(self, device: Any, video_path: str):
        self.session_id = str(uuid.uuid4())
        self.device = device
        self.device_name = device.name
        self.video_path = video_path
        self.active = True
        self.status = "active"
