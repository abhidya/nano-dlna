"""Load testing for the Nano-DLNA system."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional
import statistics

import pytest
from locust import HttpUser, task, between, events
import requests

from tests.utils.test_helpers import TestTimer, PerformanceTestHelper


@dataclass
class PerformanceMetrics:
    """Container for performance test metrics."""
    operation: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    min_time: float
    max_time: float
    avg_time: float
    median_time: float
    p95_time: float
    p99_time: float
    requests_per_second: float
    
    def __str__(self):
        return f"""
Performance Metrics for {self.operation}:
  Total Requests: {self.total_requests}
  Successful: {self.successful_requests}
  Failed: {self.failed_requests}
  Min Time: {self.min_time:.3f}s
  Max Time: {self.max_time:.3f}s
  Average Time: {self.avg_time:.3f}s
  Median Time: {self.median_time:.3f}s
  95th Percentile: {self.p95_time:.3f}s
  99th Percentile: {self.p99_time:.3f}s
  Requests/Second: {self.requests_per_second:.2f}
"""


class LoadTester:
    """Base class for load testing operations."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def measure_operation(
        self,
        operation_name: str,
        operation_func,
        num_requests: int = 100,
        num_workers: int = 10
    ) -> PerformanceMetrics:
        """Measure performance of an operation."""
        times = []
        errors = 0
        
        with TestTimer(f"Load test: {operation_name}") as timer:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [
                    executor.submit(self._timed_operation, operation_func)
                    for _ in range(num_requests)
                ]
                
                for future in as_completed(futures):
                    result = future.result()
                    if result is not None:
                        times.append(result)
                    else:
                        errors += 1
        
        if not times:
            raise ValueError("No successful operations")
        
        times.sort()
        
        return PerformanceMetrics(
            operation=operation_name,
            total_requests=num_requests,
            successful_requests=len(times),
            failed_requests=errors,
            min_time=min(times),
            max_time=max(times),
            avg_time=statistics.mean(times),
            median_time=statistics.median(times),
            p95_time=times[int(len(times) * 0.95)],
            p99_time=times[int(len(times) * 0.99)],
            requests_per_second=num_requests / timer.duration
        )
    
    def _timed_operation(self, operation_func) -> Optional[float]:
        """Execute operation and return execution time."""
        start_time = time.time()
        try:
            operation_func()
            return time.time() - start_time
        except Exception as e:
            print(f"Operation failed: {e}")
            return None


class APILoadTester(LoadTester):
    """Load tester for API endpoints."""
    
    def test_device_list_endpoint(self) -> PerformanceMetrics:
        """Test /api/devices endpoint performance."""
        def operation():
            response = self.session.get(f"{self.base_url}/api/devices/")
            response.raise_for_status()
        
        return self.measure_operation("GET /api/devices", operation)
    
    def test_video_list_endpoint(self) -> PerformanceMetrics:
        """Test /api/videos endpoint performance."""
        def operation():
            response = self.session.get(f"{self.base_url}/api/videos/")
            response.raise_for_status()
        
        return self.measure_operation("GET /api/videos", operation)
    
    def test_device_creation(self) -> PerformanceMetrics:
        """Test device creation performance."""
        counter = 0
        
        def operation():
            nonlocal counter
            counter += 1
            device_data = {
                "name": f"LoadTest_Device_{counter}",
                "type": "dlna",
                "ip_address": f"192.168.1.{(counter % 254) + 1}",
                "port": 8000 + (counter % 1000)
            }
            response = self.session.post(
                f"{self.base_url}/api/devices/",
                json=device_data
            )
            response.raise_for_status()
        
        return self.measure_operation("POST /api/devices", operation, num_requests=50)
    
    def test_playback_operation(self) -> PerformanceMetrics:
        """Test playback initiation performance."""
        # First create a device and video
        device_response = self.session.post(
            f"{self.base_url}/api/devices/",
            json={
                "name": "LoadTest_Player",
                "type": "dlna",
                "ip_address": "192.168.1.200",
                "port": 8080
            }
        )
        device_id = device_response.json()["id"]
        
        def operation():
            response = self.session.post(
                f"{self.base_url}/api/devices/{device_id}/play",
                json={"video_id": 1, "loop": True}
            )
            response.raise_for_status()
        
        return self.measure_operation("POST /api/devices/{id}/play", operation, num_requests=20)


class StreamingLoadTester(LoadTester):
    """Load tester for streaming operations."""
    
    def test_concurrent_streams(self, num_streams: int = 10) -> Dict[str, any]:
        """Test concurrent streaming performance."""
        metrics = {
            "streams_requested": num_streams,
            "streams_established": 0,
            "average_setup_time": 0,
            "total_bandwidth_mbps": 0,
            "errors": []
        }
        
        stream_urls = []
        setup_times = []
        
        with TestTimer(f"Establishing {num_streams} concurrent streams") as timer:
            with ThreadPoolExecutor(max_workers=num_streams) as executor:
                futures = []
                
                for i in range(num_streams):
                    future = executor.submit(
                        self._establish_stream,
                        f"test_video_{i}.mp4"
                    )
                    futures.append(future)
                
                for future in as_completed(futures):
                    try:
                        url, setup_time = future.result()
                        stream_urls.append(url)
                        setup_times.append(setup_time)
                        metrics["streams_established"] += 1
                    except Exception as e:
                        metrics["errors"].append(str(e))
        
        if setup_times:
            metrics["average_setup_time"] = statistics.mean(setup_times)
        
        # Test bandwidth by downloading from all streams
        if stream_urls:
            bandwidth_results = self._test_bandwidth(stream_urls)
            metrics["total_bandwidth_mbps"] = bandwidth_results["total_mbps"]
        
        return metrics
    
    def _establish_stream(self, video_name: str) -> tuple:
        """Establish a single stream and return URL and setup time."""
        start_time = time.time()
        
        response = self.session.post(
            f"{self.base_url}/api/streaming/create",
            json={"video_name": video_name}
        )
        response.raise_for_status()
        
        stream_url = response.json()["url"]
        setup_time = time.time() - start_time
        
        return stream_url, setup_time
    
    def _test_bandwidth(self, stream_urls: List[str]) -> Dict[str, float]:
        """Test bandwidth for multiple streams."""
        total_bytes = 0
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=len(stream_urls)) as executor:
            futures = [
                executor.submit(self._download_stream_sample, url)
                for url in stream_urls
            ]
            
            for future in as_completed(futures):
                try:
                    bytes_downloaded = future.result()
                    total_bytes += bytes_downloaded
                except Exception:
                    pass
        
        duration = time.time() - start_time
        total_mbps = (total_bytes * 8) / (duration * 1_000_000)
        
        return {
            "total_bytes": total_bytes,
            "duration_seconds": duration,
            "total_mbps": total_mbps
        }
    
    def _download_stream_sample(self, url: str, sample_size: int = 1_000_000) -> int:
        """Download sample from stream."""
        response = self.session.get(url, stream=True)
        bytes_downloaded = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            bytes_downloaded += len(chunk)
            if bytes_downloaded >= sample_size:
                break
        
        return bytes_downloaded


class WebSocketLoadTester:
    """Load tester for WebSocket connections."""
    
    def __init__(self, ws_url: str = "ws://localhost:8000/ws"):
        self.ws_url = ws_url
    
    async def test_concurrent_connections(self, num_connections: int = 100) -> Dict[str, any]:
        """Test concurrent WebSocket connections."""
        import websockets
        
        metrics = {
            "connections_requested": num_connections,
            "connections_established": 0,
            "average_latency_ms": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": []
        }
        
        latencies = []
        
        async def establish_connection(conn_id: int):
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    metrics["connections_established"] += 1
                    
                    # Test latency
                    for _ in range(10):
                        start_time = time.time()
                        await websocket.send(f"ping_{conn_id}")
                        response = await websocket.recv()
                        latency = (time.time() - start_time) * 1000
                        latencies.append(latency)
                        
                        metrics["messages_sent"] += 1
                        if response:
                            metrics["messages_received"] += 1
                    
            except Exception as e:
                metrics["errors"].append(f"Connection {conn_id}: {str(e)}")
        
        # Run concurrent connections
        tasks = [establish_connection(i) for i in range(num_connections)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        if latencies:
            metrics["average_latency_ms"] = statistics.mean(latencies)
        
        return metrics


# Locust test scenarios
class NanoDLNAUser(HttpUser):
    """Locust user for load testing Nano-DLNA."""
    
    wait_time = between(1, 3)
    
    @task(3)
    def view_devices(self):
        """View device list."""
        self.client.get("/api/devices/")
    
    @task(2)
    def view_videos(self):
        """View video list."""
        self.client.get("/api/videos/")
    
    @task(1)
    def play_video(self):
        """Simulate playing a video."""
        # Get a device
        devices_response = self.client.get("/api/devices/")
        if devices_response.status_code == 200:
            devices = devices_response.json()
            if devices:
                device_id = devices[0]["id"]
                
                # Play video
                self.client.post(
                    f"/api/devices/{device_id}/play",
                    json={"video_id": 1, "loop": True}
                )
    
    @task(1)
    def check_device_status(self):
        """Check device status."""
        devices_response = self.client.get("/api/devices/")
        if devices_response.status_code == 200:
            devices = devices_response.json()
            if devices:
                device_id = devices[0]["id"]
                self.client.get(f"/api/devices/{device_id}")
    
    def on_start(self):
        """Setup before testing."""
        # Create a test device
        self.client.post(
            "/api/devices/",
            json={
                "name": f"LoadTest_User_{self.environment.runner.user_count}",
                "type": "dlna",
                "ip_address": "192.168.1.100",
                "port": 8080
            }
        )


# Performance test scenarios
class TestPerformanceScenarios:
    """Test various performance scenarios."""
    
    @pytest.mark.performance
    def test_api_load(self):
        """Test API performance under load."""
        tester = APILoadTester()
        
        # Test various endpoints
        results = {
            "device_list": tester.test_device_list_endpoint(),
            "video_list": tester.test_video_list_endpoint(),
            "device_creation": tester.test_device_creation(),
        }
        
        # Print results
        for endpoint, metrics in results.items():
            print(metrics)
        
        # Assert performance requirements
        assert results["device_list"].avg_time < 0.2  # 200ms
        assert results["video_list"].avg_time < 0.2
        assert results["device_creation"].avg_time < 0.5  # 500ms
    
    @pytest.mark.performance
    def test_streaming_load(self):
        """Test streaming performance under load."""
        tester = StreamingLoadTester()
        
        # Test concurrent streams
        results = tester.test_concurrent_streams(num_streams=5)
        
        print(f"\nStreaming Load Test Results:")
        print(f"  Streams Established: {results['streams_established']}/{results['streams_requested']}")
        print(f"  Average Setup Time: {results['average_setup_time']:.3f}s")
        print(f"  Total Bandwidth: {results['total_bandwidth_mbps']:.2f} Mbps")
        
        # Assert performance requirements
        assert results["streams_established"] >= results["streams_requested"] * 0.9
        assert results["average_setup_time"] < 2.0  # 2 seconds
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_websocket_load(self):
        """Test WebSocket performance under load."""
        tester = WebSocketLoadTester()
        
        # Test concurrent connections
        results = await tester.test_concurrent_connections(num_connections=50)
        
        print(f"\nWebSocket Load Test Results:")
        print(f"  Connections: {results['connections_established']}/{results['connections_requested']}")
        print(f"  Average Latency: {results['average_latency_ms']:.2f}ms")
        print(f"  Messages: {results['messages_sent']} sent, {results['messages_received']} received")
        
        # Assert performance requirements
        assert results["connections_established"] >= results["connections_requested"] * 0.9
        assert results["average_latency_ms"] < 50  # 50ms
    
    @pytest.mark.performance
    @PerformanceTestHelper.measure_memory_usage
    def test_memory_usage_under_load(self):
        """Test memory usage under load."""
        tester = APILoadTester()
        
        # Generate load
        for _ in range(5):
            tester.test_device_list_endpoint()
            tester.test_video_list_endpoint()
        
        # Memory usage is printed by decorator
    
    @pytest.mark.performance
    @PerformanceTestHelper.benchmark(iterations=10)
    def test_critical_path_performance(self):
        """Benchmark critical path operations."""
        tester = APILoadTester()
        
        # Test device discovery to playback path
        device_response = tester.session.post(
            f"{tester.base_url}/api/devices/",
            json={
                "name": "Benchmark_Device",
                "type": "dlna",
                "ip_address": "192.168.1.250",
                "port": 9999
            }
        )
        device_id = device_response.json()["id"]
        
        # Play video
        tester.session.post(
            f"{tester.base_url}/api/devices/{device_id}/play",
            json={"video_id": 1, "loop": True}
        )
        
        # Stop playback
        tester.session.post(f"{tester.base_url}/api/devices/{device_id}/stop")