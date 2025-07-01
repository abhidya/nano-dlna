"""Session and streaming factory for creating test session instances."""

import factory
from factory import fuzzy
from datetime import datetime, timezone, timedelta
import random
import uuid
from typing import Dict, List, Optional

from web.backend.models.device import Device
from web.backend.models.video import Video
from tests.factories.device_factory import DeviceFactory, DLNADeviceFactory
from tests.factories.video_factory import VideoFactory


class StreamingSessionFactory(factory.Factory):
    """Factory for creating streaming session instances."""
    
    class Meta:
        model = dict
    
    session_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    device = factory.SubFactory(DeviceFactory)
    video = factory.SubFactory(VideoFactory)
    
    @factory.lazy_attribute
    def stream_url(self):
        port = random.randint(9000, 9999)
        return f"http://10.0.0.74:{port}/{self.video.name}.mp4"
    
    @factory.lazy_attribute
    def server_info(self):
        return {
            "ip": "10.0.0.74",
            "port": int(self.stream_url.split(':')[2].split('/')[0]),
            "protocol": "http",
            "server_type": "twisted"
        }
    
    started_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    
    @factory.lazy_attribute
    def last_accessed(self):
        # Last accessed within the last 30 seconds
        return self.started_at + timedelta(seconds=random.randint(0, 30))
    
    is_active = True
    bytes_served = fuzzy.FuzzyInteger(0, 100_000_000)
    
    @factory.lazy_attribute
    def playback_info(self):
        return {
            "duration": self.video.duration,
            "current_position": f"0:{random.randint(0, 10):02d}:{random.randint(0, 59):02d}",
            "playback_rate": 1.0,
            "loop_enabled": True,
            "loop_count": random.randint(0, 5)
        }
    
    @factory.lazy_attribute
    def client_info(self):
        return {
            "ip": self.device.ip_address,
            "user_agent": random.choice([
                "DLNA/1.0 UPnP/1.0",
                "AirPlay/380.4",
                "VLC/3.0.16",
                "Chrome/91.0"
            ]),
            "requests_count": random.randint(1, 100)
        }


class SessionFactory(factory.Factory):
    """Factory for creating user session instances."""
    
    class Meta:
        model = dict
    
    session_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = fuzzy.FuzzyInteger(1, 100)
    
    @factory.lazy_attribute
    def user_info(self):
        return {
            "username": f"user_{self.user_id}",
            "role": random.choice(["admin", "user", "viewer"]),
            "preferences": {
                "theme": random.choice(["light", "dark", "auto"]),
                "language": random.choice(["en", "es", "fr", "de"]),
                "autoplay": random.choice([True, False])
            }
        }
    
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    
    @factory.lazy_attribute
    def last_activity(self):
        # Activity within the last hour
        return self.created_at + timedelta(minutes=random.randint(0, 60))
    
    @factory.lazy_attribute
    def activities(self):
        activities = []
        activity_types = ["device_connected", "video_played", "settings_changed", "overlay_configured"]
        
        for _ in range(random.randint(1, 10)):
            activity = {
                "type": random.choice(activity_types),
                "timestamp": self.created_at + timedelta(minutes=random.randint(0, 30)),
                "details": {}
            }
            
            if activity["type"] == "device_connected":
                activity["details"] = {"device_id": random.randint(1, 10)}
            elif activity["type"] == "video_played":
                activity["details"] = {
                    "video_id": random.randint(1, 100),
                    "device_id": random.randint(1, 10)
                }
            
            activities.append(activity)
        
        return sorted(activities, key=lambda x: x["timestamp"])


class WebSocketConnectionFactory(factory.Factory):
    """Factory for creating WebSocket connection instances."""
    
    class Meta:
        model = dict
    
    connection_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    client_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    
    @factory.lazy_attribute
    def connection_info(self):
        return {
            "remote_address": f"192.168.1.{random.randint(100, 200)}",
            "protocol": "ws",
            "headers": {
                "User-Agent": random.choice([
                    "Mozilla/5.0 Chrome/91.0",
                    "Mozilla/5.0 Firefox/89.0",
                    "Mozilla/5.0 Safari/14.1"
                ])
            }
        }
    
    connected_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    is_connected = True
    
    @factory.lazy_attribute
    def subscriptions(self):
        return random.sample([
            "device_status",
            "playback_events",
            "overlay_updates",
            "system_alerts"
        ], k=random.randint(1, 4))
    
    @factory.lazy_attribute
    def message_stats(self):
        return {
            "sent": random.randint(0, 1000),
            "received": random.randint(0, 1000),
            "errors": random.randint(0, 10),
            "last_message_at": self.connected_at + timedelta(seconds=random.randint(0, 60))
        }


def create_active_session_scenario() -> Dict[str, any]:
    """Create a complete active session scenario."""
    # Create devices
    devices = [
        DLNADeviceFactory.create(status="connected")
        for _ in range(3)
    ]
    
    # Create videos
    videos = VideoFactory.create_batch(5)
    
    # Create streaming sessions
    streaming_sessions = []
    for i, device in enumerate(devices[:2]):  # First two devices are streaming
        session = StreamingSessionFactory.create(
            device=device,
            video=videos[i]
        )
        streaming_sessions.append(session)
    
    # Create user session
    user_session = SessionFactory.create()
    
    # Create WebSocket connections
    ws_connections = [
        WebSocketConnectionFactory.create()
        for _ in range(2)
    ]
    
    return {
        "devices": devices,
        "videos": videos,
        "streaming_sessions": streaming_sessions,
        "user_session": user_session,
        "websocket_connections": ws_connections,
        "summary": {
            "total_devices": len(devices),
            "active_streams": len(streaming_sessions),
            "connected_clients": len(ws_connections)
        }
    }


class StreamingMetricsFactory(factory.Factory):
    """Factory for creating streaming metrics."""
    
    class Meta:
        model = dict
    
    session_id = factory.LazyAttribute(lambda obj: obj.session.session_id)
    session = factory.SubFactory(StreamingSessionFactory)
    
    @factory.lazy_attribute
    def bandwidth_usage(self):
        return {
            "current_bps": random.randint(1_000_000, 10_000_000),  # 1-10 Mbps
            "average_bps": random.randint(1_000_000, 8_000_000),
            "peak_bps": random.randint(5_000_000, 15_000_000),
            "total_bytes": self.session.bytes_served
        }
    
    @factory.lazy_attribute
    def playback_quality(self):
        return {
            "buffer_health": round(random.uniform(0.8, 1.0), 2),
            "dropped_frames": random.randint(0, 10),
            "rebuffer_events": random.randint(0, 3),
            "average_bitrate": random.randint(2000, 8000)  # kbps
        }
    
    @factory.lazy_attribute
    def network_stats(self):
        return {
            "latency_ms": random.randint(1, 50),
            "packet_loss": round(random.uniform(0, 0.02), 4),  # 0-2%
            "jitter_ms": random.randint(0, 10),
            "connection_quality": random.choice(["excellent", "good", "fair", "poor"])
        }
    
    timestamp = factory.LazyFunction(lambda: datetime.now(timezone.utc))