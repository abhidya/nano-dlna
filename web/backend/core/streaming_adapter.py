"""
Canonical streaming adapter interface.

Callers use this module's small interface; concrete streaming implementations
absorb their own parameter names and server details behind the seam.
"""

import socket
from typing import Any, Dict, Optional, Tuple


class TwistedStreamingAdapter:
    """Adapter for the Twisted DLNA streaming implementation."""

    def __init__(self, server: Optional[Any] = None):
        if server is None:
            from .twisted_streaming import get_instance

            server = get_instance()
        self.server = server

    def get_serve_ip(self, target_ip: Optional[str] = None) -> str:
        if hasattr(self.server, "get_serve_ip"):
            return self.server.get_serve_ip(target_ip)
        return detect_serve_ip(target_ip)

    def start_server(
        self,
        files: Dict[str, str],
        serve_ip: Optional[str] = None,
        serve_port: Optional[int] = None,
        port_range: Optional[Tuple[int, int]] = None,
        device_name: Optional[str] = None,
    ) -> Tuple[Dict[str, str], Any]:
        _ = device_name  # Twisted updates sessions by serving port, not caller name.
        return self.server.start_server(
            files=files,
            serve_ip=serve_ip,
            port=serve_port,
            port_range=port_range,
        )


def detect_serve_ip(target_ip: Optional[str] = None) -> str:
    """Return the local IP used to reach a target network."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect((target_ip or "8.8.8.8", 80))
        ip = sock.getsockname()[0]
        if ip.startswith("127."):
            raise RuntimeError("Auto-detected localhost, not valid for DLNA streaming")
        return ip
    finally:
        sock.close()


def get_streaming_adapter() -> TwistedStreamingAdapter:
    """Default streaming adapter used by application modules."""
    return TwistedStreamingAdapter()
