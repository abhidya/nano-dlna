import threading
from datetime import datetime, timedelta
from types import SimpleNamespace

from web.backend.core.playback_session import PlaybackSessionCoordinator


class FakeRegistry:
    def __init__(self):
        self.sessions = {}

    def register_session(self, device_name, video_path, server_ip, server_port):
        session = SimpleNamespace(
            session_id="session-1",
            device_name=device_name,
            video_path=video_path,
            server_ip=server_ip,
            server_port=server_port,
            active=True,
            last_activity_time=datetime.now(),
            complete_called=False,
            update_activity=lambda: setattr(session, "last_activity_time", datetime.now()),
            complete=lambda: setattr(session, "complete_called", True),
        )
        self.sessions[session.session_id] = session
        return session

    def get_sessions_for_device(self, device_name):
        return [session for session in self.sessions.values() if session.device_name == device_name]

    def get_session(self, session_id):
        return self.sessions.get(session_id)


class FakeManager:
    def __init__(self):
        self.device_state_lock = threading.RLock()
        self.device_status = {}
        self.device = SimpleNamespace(
            current_position=None,
            duration_formatted=None,
            playback_progress=None,
        )

    def get_device(self, device_name):
        return self.device


def test_playback_session_coordinator_owns_session_lifecycle():
    manager = FakeManager()
    registry = FakeRegistry()
    coordinator = PlaybackSessionCoordinator(manager, registry)

    session = coordinator.register_streaming_session("TV", "movie.mp4", "10.0.0.2", 9000)

    assert coordinator.owns_session("TV", session.session_id) is True
    assert coordinator.has_recent_activity("TV") is True

    session.last_activity_time = datetime.now() - timedelta(seconds=60)
    assert coordinator.has_recent_activity("TV", seconds=30) is False

    coordinator.complete_sessions("TV")
    assert session.complete_called is True


def test_playback_session_coordinator_updates_progress_locality(monkeypatch):
    manager = FakeManager()
    registry = FakeRegistry()
    coordinator = PlaybackSessionCoordinator(manager, registry)
    monkeypatch.setattr(coordinator, "_update_database_progress", lambda *args, **kwargs: None)

    coordinator.update_progress("TV", "00:00:05", "00:00:10", 50)

    assert manager.device_status["TV"]["playback_progress"] == 50
    assert manager.device.current_position == "00:00:05"
    assert manager.device.duration_formatted == "00:00:10"
    assert manager.device.playback_progress == 50
