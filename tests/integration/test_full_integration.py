"""Full integration tests for complete workflows."""

import asyncio
import time
from typing import Dict, List
import pytest
from unittest.mock import Mock, patch

from web.backend.core.device_manager import DeviceManager
from web.backend.core.streaming_service import StreamingService
from web.backend.services.device_service import DeviceService
from web.backend.services.video_service import VideoService
from tests.factories import DeviceFactory, VideoFactory, create_device_network
from tests.utils.test_helpers import (
    AsyncTestHelper, DatabaseTestHelper, wait_for, assert_eventually
)
from tests.mocks.dlna_mocks import MockDLNADevice


class TestDeviceDiscoveryIntegration:
    """Test device discovery integration workflow."""
    
    @pytest.fixture
    def device_manager(self):
        """Create device manager instance."""
        manager = DeviceManager()
        yield manager
        manager.stop_discovery()
    
    def test_device_discovery_lifecycle(self, device_manager):
        """Test complete device discovery lifecycle."""
        # Create mock devices
        mock_devices = [
            MockDLNADevice(name=f"Device_{i}", ip=f"192.168.1.{100+i}")
            for i in range(3)
        ]
        
        with patch('web.backend.core.device_manager.discover_dlna_devices', 
                  return_value=mock_devices):
            # Start discovery
            device_manager.start_discovery()
            
            # Wait for devices to be discovered
            assert_eventually(
                lambda: len(device_manager.devices) == 3,
                timeout=10,
                message="Devices were not discovered"
            )
            
            # Verify device states
            for device_name, device in device_manager.devices.items():
                assert device.status == "connected"
                assert device_name in [d.name for d in mock_devices]
            
            # Simulate device going offline
            mock_devices.pop()  # Remove last device
            
            # Wait for device to be marked as disconnected
            time.sleep(device_manager.device_timeout + 5)
            
            disconnected_devices = [
                d for d in device_manager.devices.values() 
                if d.status == "disconnected"
            ]
            assert len(disconnected_devices) == 1
    
    def test_device_rediscovery(self, device_manager):
        """Test device rediscovery after disconnect."""
        mock_device = MockDLNADevice(name="TestDevice", ip="192.168.1.100")
        
        # Initial discovery
        with patch('web.backend.core.device_manager.discover_dlna_devices', 
                  return_value=[mock_device]):
            device_manager.start_discovery()
            
            wait_for(lambda: "TestDevice" in device_manager.devices)
            assert device_manager.devices["TestDevice"].status == "connected"
        
        # Simulate device disconnect
        with patch('web.backend.core.device_manager.discover_dlna_devices', 
                  return_value=[]):
            time.sleep(device_manager.device_timeout + 5)
            assert device_manager.devices["TestDevice"].status == "disconnected"
        
        # Simulate device coming back online
        with patch('web.backend.core.device_manager.discover_dlna_devices', 
                  return_value=[mock_device]):
            time.sleep(device_manager.discovery_interval + 1)
            
            assert_eventually(
                lambda: device_manager.devices["TestDevice"].status == "connected",
                timeout=10
            )


class TestStreamingIntegration:
    """Test video streaming integration."""
    
    @pytest.fixture
    def streaming_service(self):
        """Create streaming service instance."""
        service = StreamingService()
        yield service
        service.stop_all_streams()
    
    def test_streaming_lifecycle(self, streaming_service, tmp_path):
        """Test complete streaming lifecycle."""
        # Create test video file
        video_file = tmp_path / "test_video.mp4"
        video_file.write_bytes(b"FAKE_VIDEO_DATA" * 10000)
        
        # Start streaming
        stream_info = streaming_service.create_stream(str(video_file))
        
        assert stream_info is not None
        assert "url" in stream_info
        assert "port" in stream_info
        
        # Verify stream is accessible
        import requests
        response = requests.head(stream_info["url"], timeout=5)
        assert response.status_code == 200
        
        # Stop streaming
        streaming_service.stop_stream(str(video_file))
        
        # Verify stream is no longer accessible
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.head(stream_info["url"], timeout=1)
    
    def test_multiple_streams(self, streaming_service, tmp_path):
        """Test multiple concurrent streams."""
        # Create multiple video files
        video_files = []
        for i in range(3):
            video_file = tmp_path / f"video_{i}.mp4"
            video_file.write_bytes(b"VIDEO_DATA" * 1000)
            video_files.append(video_file)
        
        # Start multiple streams
        streams = []
        for video_file in video_files:
            stream_info = streaming_service.create_stream(str(video_file))
            streams.append(stream_info)
        
        # Verify all streams are on different ports
        ports = [s["port"] for s in streams]
        assert len(set(ports)) == len(ports)
        
        # Verify all streams are active
        assert len(streaming_service.active_streams) == 3
        
        # Stop all streams
        streaming_service.stop_all_streams()
        assert len(streaming_service.active_streams) == 0


class TestPlaybackIntegration:
    """Test complete playback integration."""
    
    @pytest.fixture
    def setup_services(self, tmp_path):
        """Setup all required services."""
        device_manager = DeviceManager()
        streaming_service = StreamingService()
        
        with DatabaseTestHelper.temp_database() as db:
            device_service = DeviceService(db)
            video_service = VideoService(db)
            
            # Create test data
            test_video = tmp_path / "test.mp4"
            test_video.write_bytes(b"VIDEO" * 10000)
            
            yield {
                "device_manager": device_manager,
                "streaming_service": streaming_service,
                "device_service": device_service,
                "video_service": video_service,
                "test_video": test_video,
                "db": db
            }
        
        device_manager.stop_discovery()
        streaming_service.stop_all_streams()
    
    def test_complete_playback_workflow(self, setup_services):
        """Test complete playback workflow from discovery to playing."""
        services = setup_services
        
        # 1. Discover device
        mock_device = MockDLNADevice(name="TestTV", ip="192.168.1.100")
        
        with patch('web.backend.core.device_manager.discover_dlna_devices', 
                  return_value=[mock_device]):
            services["device_manager"].start_discovery()
            
            wait_for(lambda: "TestTV" in services["device_manager"].devices)
        
        # 2. Register device in database
        device = services["device_service"].create_device({
            "name": "TestTV",
            "type": "dlna",
            "ip_address": "192.168.1.100",
            "port": 8080
        })
        
        # 3. Upload video
        video = services["video_service"].create_video({
            "name": "Test Video",
            "file_path": str(services["test_video"]),
            "file_size": services["test_video"].stat().st_size,
            "duration": "00:10:00"
        })
        
        # 4. Play video on device
        with patch.object(mock_device, 'play') as mock_play:
            result = services["device_service"].play_video_on_device(
                device.id, 
                str(services["test_video"]),
                loop=True
            )
            
            assert result["status"] == "success"
            mock_play.assert_called_once()
            
            # Verify streaming started
            assert len(services["streaming_service"].active_streams) > 0
            
            # Verify device status updated
            updated_device = services["device_service"].get_device(device.id)
            assert updated_device.is_playing
            assert updated_device.current_video_id == video.id
        
        # 5. Stop playback
        with patch.object(mock_device, 'stop') as mock_stop:
            services["device_service"].stop_playback(device.id)
            
            mock_stop.assert_called_once()
            
            # Verify device status
            updated_device = services["device_service"].get_device(device.id)
            assert not updated_device.is_playing
            assert updated_device.current_video_id is None


class TestMultiDeviceSynchronization:
    """Test multi-device synchronization."""
    
    def test_synchronized_playback(self, setup_services):
        """Test synchronized playback across multiple devices."""
        services = setup_services
        
        # Create multiple mock devices
        mock_devices = [
            MockDLNADevice(name=f"Device_{i}", ip=f"192.168.1.{100+i}")
            for i in range(3)
        ]
        
        # Register devices
        db_devices = []
        for mock_device in mock_devices:
            device = services["device_service"].create_device({
                "name": mock_device.name,
                "type": "dlna",
                "ip_address": mock_device.ip,
                "port": 8080
            })
            db_devices.append(device)
        
        # Create device group
        group = services["device_service"].create_device_group({
            "name": "Living Room",
            "device_ids": [d.id for d in db_devices]
        })
        
        # Play video on group
        with patch('web.backend.core.device_manager.get_device_instance') as mock_get:
            mock_get.side_effect = lambda name: next(
                d for d in mock_devices if d.name == name
            )
            
            # Mock play method for all devices
            for mock_device in mock_devices:
                mock_device.play = Mock()
                mock_device.seek = Mock()
            
            # Start synchronized playback
            services["device_service"].play_on_group(
                group.id,
                str(services["test_video"])
            )
            
            # Verify all devices started playing
            for mock_device in mock_devices:
                mock_device.play.assert_called_once()
            
            # Simulate playback drift
            time.sleep(2)
            
            # Trigger synchronization
            services["device_service"].synchronize_group(group.id)
            
            # Verify seek was called to synchronize
            for mock_device in mock_devices[1:]:  # Skip master device
                mock_device.seek.assert_called()


class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    def test_streaming_failure_recovery(self, setup_services):
        """Test recovery from streaming failures."""
        services = setup_services
        mock_device = MockDLNADevice(name="TestDevice", ip="192.168.1.100")
        
        # Register device
        device = services["device_service"].create_device({
            "name": "TestDevice",
            "type": "dlna",
            "ip_address": "192.168.1.100",
            "port": 8080
        })
        
        # Simulate streaming failure
        with patch.object(services["streaming_service"], 'create_stream') as mock_stream:
            mock_stream.side_effect = Exception("Network error")
            
            result = services["device_service"].play_video_on_device(
                device.id,
                str(services["test_video"])
            )
            
            assert result["status"] == "error"
            assert "Network error" in result["message"]
            
            # Verify device state is consistent
            updated_device = services["device_service"].get_device(device.id)
            assert not updated_device.is_playing
    
    def test_device_disconnect_during_playback(self, setup_services):
        """Test handling device disconnect during playback."""
        services = setup_services
        mock_device = MockDLNADevice(name="TestDevice", ip="192.168.1.100")
        
        # Setup device and start playback
        device = services["device_service"].create_device({
            "name": "TestDevice",
            "type": "dlna",
            "ip_address": "192.168.1.100",
            "port": 8080
        })
        
        with patch.object(mock_device, 'play'):
            services["device_service"].play_video_on_device(
                device.id,
                str(services["test_video"])
            )
        
        # Simulate device disconnect
        services["device_manager"].devices["TestDevice"].status = "disconnected"
        
        # Trigger health check
        services["device_manager"].check_device_health()
        
        # Verify playback was stopped
        updated_device = services["device_service"].get_device(device.id)
        assert not updated_device.is_playing
        assert updated_device.status == "disconnected"


class TestPerformanceIntegration:
    """Test performance under load."""
    
    def test_concurrent_device_operations(self, setup_services):
        """Test system performance with concurrent device operations."""
        services = setup_services
        
        # Create multiple devices
        devices = []
        for i in range(10):
            device = services["device_service"].create_device({
                "name": f"Device_{i}",
                "type": "dlna",
                "ip_address": f"192.168.1.{100+i}",
                "port": 8080 + i
            })
            devices.append(device)
        
        # Perform concurrent operations
        import concurrent.futures
        
        def play_on_device(device_id):
            return services["device_service"].play_video_on_device(
                device_id,
                str(services["test_video"])
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            
            futures = [
                executor.submit(play_on_device, device.id)
                for device in devices
            ]
            
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            elapsed_time = time.time() - start_time
        
        # Verify all operations completed
        assert len(results) == 10
        
        # Verify performance (should complete within reasonable time)
        assert elapsed_time < 5.0  # 5 seconds for 10 devices
        
        print(f"\nConcurrent operations completed in {elapsed_time:.2f} seconds")