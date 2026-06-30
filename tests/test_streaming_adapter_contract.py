from pathlib import Path

from web.backend.core.streaming_adapter import TwistedStreamingAdapter


class FakeTwistedServer:
    def __init__(self):
        self.start_kwargs = None

    def get_serve_ip(self, target_ip=None):
        return "10.0.0.2"

    def start_server(self, files, serve_ip=None, port=None, port_range=None):
        self.start_kwargs = {
            "files": files,
            "serve_ip": serve_ip,
            "port": port,
            "port_range": port_range,
        }
        return {"file_video": f"http://{serve_ip}:{port}/file_video"}, object()


def test_twisted_adapter_exposes_stable_streaming_interface():
    fake = FakeTwistedServer()
    adapter = TwistedStreamingAdapter(fake)

    urls, server = adapter.start_server(
        {"file_video": "movie.mp4"},
        serve_ip="10.0.0.2",
        serve_port=8001,
        port_range=(8001, 8010),
        device_name="Living Room",
    )

    assert urls["file_video"] == "http://10.0.0.2:8001/file_video"
    assert server is not None
    assert fake.start_kwargs == {
        "files": {"file_video": "movie.mp4"},
        "serve_ip": "10.0.0.2",
        "port": 8001,
        "port_range": (8001, 8010),
    }


def test_twisted_server_accepts_canonical_adapter_keywords():
    source = Path("web/backend/core/twisted_streaming.py").read_text(encoding="utf-8")

    assert "serve_port: Optional[int] = None" in source
    assert "device_name: Optional[str] = None" in source
