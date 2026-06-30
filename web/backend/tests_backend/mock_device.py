from typing import Any, Dict, Optional


class MockDevice:
    def __init__(self, device_info: Dict[str, Any]):
        self.device_info = dict(device_info)
        self.name = device_info.get("device_name") or device_info.get("name", "Unknown Device")
        self.hostname = device_info.get("hostname", "127.0.0.1")
        self.type = device_info.get("type", "unknown")
        self.action_url = device_info.get("action_url")
        self.location = device_info.get("location")
        self.control_url = device_info.get("control_url")
        self.status = "disconnected"
        self.current_video: Optional[str] = None
        self.is_playing = False

    def update_status(self, status: str) -> None:
        self.status = status

    def update_playing(self, is_playing: bool) -> None:
        self.is_playing = is_playing

    def update_video(self, video_path: Optional[str]) -> None:
        self.current_video = video_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.device_info,
            "name": self.name,
            "hostname": self.hostname,
            "type": self.type,
            "action_url": self.action_url,
            "location": self.location,
            "control_url": self.control_url,
            "status": self.status,
            "current_video": self.current_video,
            "is_playing": self.is_playing,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MockDevice):
            return NotImplemented
        return (
            self.name,
            self.hostname,
            self.type,
            self.action_url,
        ) == (
            other.name,
            other.hostname,
            other.type,
            other.action_url,
        )
