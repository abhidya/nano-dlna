#!/usr/bin/env python3
"""
Comprehensive smoke tests for current backend core contracts.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.backend.core.device_manager import DeviceManager
from web.backend.core.dlna_device import DLNADevice
from web.backend.core.streaming_service import StreamingService


@pytest.fixture
def temp_video_file():
    temp_dir = tempfile.mkdtemp()
    video_file = Path(temp_dir) / "test.mp4"
    video_file.write_bytes(b"")
    yield str(video_file)
    shutil.rmtree(temp_dir)


@pytest.fixture
def device_info():
    return {
        "device_name": "Test Device",
        "type": "dlna",
        "hostname": "192.168.1.100",
        "location": "http://192.168.1.100:8000/device.xml",
        "action_url": "http://192.168.1.100:8000/AVTransport/Control",
    }


@pytest.fixture
def device_manager():
    manager = DeviceManager()
    yield manager
    manager.stop_discovery()


@pytest.fixture
def streaming_service():
    return StreamingService()


class TestDeviceManager:
    def test_register_device(self, device_manager, device_info):
        device = device_manager.register_device(device_info)

        assert device is not None
        assert device.name == "Test Device"
        assert device_manager.get_device("Test Device") is device

    def test_unregister_device(self, device_manager, device_info):
        device_manager.register_device(device_info)

        assert device_manager.unregister_device("Test Device") is True
        assert device_manager.get_device("Test Device") is None

    @patch("web.backend.core.device_manager.DeviceManager.get_serve_ip")
    @patch("web.backend.core.twisted_streaming.TwistedStreamingServer.get_instance")
    def test_auto_play_video(self, mock_get_streaming_server, mock_get_serve_ip, device_manager, device_info, temp_video_file):
        mock_get_serve_ip.return_value = "192.168.1.10"
        streaming_server = Mock()
        streaming_server.start_server.return_value = (
            {"test.mp4": "http://192.168.1.10:9000/test.mp4"},
            Mock(),
        )
        mock_get_streaming_server.return_value = streaming_server

        device = device_manager.register_device(device_info)
        device.play = Mock(return_value=True)

        assert device_manager.auto_play_video(device, temp_video_file) is True
        device.play.assert_called_once_with("http://192.168.1.10:9000/test.mp4", True)


class TestStreamingService:
    def test_get_stream_url(self, streaming_service):
        assert streaming_service.get_stream_url("/videos/test.mp4") == "http://localhost:8888/stream/videos/test.mp4"

    def test_validate_video_path(self, streaming_service, temp_video_file):
        assert streaming_service.validate_video_path(temp_video_file) is True
        assert streaming_service.validate_video_path("/invalid/path.mp4") is False


class TestDLNADevice:
    @pytest.fixture
    def dlna_device(self, device_info):
        return DLNADevice(device_info)

    def test_device_initialization(self, dlna_device):
        assert dlna_device.name == "Test Device"
        assert dlna_device.hostname == "192.168.1.100"
        assert dlna_device.action_url == "http://192.168.1.100:8000/AVTransport/Control"
        assert dlna_device.is_playing is False

    @patch("web.backend.core.dlna_device.DLNADevice._send_dlna_action")
    def test_play_video(self, mock_send_action, dlna_device):
        mock_send_action.return_value = True

        assert dlna_device.play("http://localhost:8888/stream/test.mp4") is True
        assert dlna_device.is_playing is True
        assert dlna_device.current_video == "http://localhost:8888/stream/test.mp4"

    @patch("web.backend.core.dlna_device.DLNADevice._send_dlna_action")
    def test_stop_playback(self, mock_send_action, dlna_device):
        mock_send_action.return_value = True
        dlna_device.is_playing = True

        assert dlna_device.stop() is True
        assert dlna_device.is_playing is False


class TestIntegration:
    @pytest.mark.asyncio
    @patch("web.backend.core.device_manager.DeviceManager.get_serve_ip")
    @patch("web.backend.core.twisted_streaming.TwistedStreamingServer.get_instance")
    async def test_full_playback_cycle(
        self,
        mock_get_streaming_server,
        mock_get_serve_ip,
        device_manager,
        streaming_service,
        device_info,
        temp_video_file,
    ):
        mock_get_serve_ip.return_value = "192.168.1.10"
        streaming_server = Mock()
        streaming_server.start_server.return_value = (
            {"test.mp4": "http://192.168.1.10:9000/test.mp4"},
            Mock(),
        )
        mock_get_streaming_server.return_value = streaming_server

        device = device_manager.register_device(device_info)
        device.play = Mock(return_value=True)
        device.stop = Mock(return_value=True)

        assert streaming_service.get_stream_url(temp_video_file).startswith("http://localhost:8888/stream/")
        assert device_manager.auto_play_video(device, temp_video_file) is True

        device.stop()
        device.stop.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
