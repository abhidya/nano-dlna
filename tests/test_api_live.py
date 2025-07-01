#!/usr/bin/env python3
"""
Live API testing framework that handles service restarts gracefully
"""
import pytest
import httpx
import asyncio
import time
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class APITestClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client: Optional[httpx.AsyncClient] = None
        self.retry_count = 5
        self.retry_delay = 1.0
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        await self.wait_for_service()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def wait_for_service(self):
        """Wait for service to be available"""
        for i in range(self.retry_count):
            try:
                response = await self.client.get("/api/health")
                if response.status_code == 200:
                    logger.info("Service is ready")
                    return
            except (httpx.ConnectError, httpx.ReadTimeout):
                logger.info(f"Service not ready, attempt {i+1}/{self.retry_count}")
                await asyncio.sleep(self.retry_delay)
        raise RuntimeError("Service failed to start")
    
    async def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make request with automatic retry on connection errors"""
        for i in range(self.retry_count):
            try:
                response = await self.client.request(method, path, **kwargs)
                return response
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                if i == self.retry_count - 1:
                    raise
                logger.warning(f"Request failed, retrying: {e}")
                await asyncio.sleep(self.retry_delay)
                await self.wait_for_service()
    
    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("GET", path, **kwargs)
    
    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("POST", path, **kwargs)

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def api_client():
    """Fixture providing API client with automatic retry"""
    async with APITestClient() as client:
        yield client

@pytest.fixture
async def clean_devices(api_client):
    """Ensure clean device state before/after tests"""
    # Clean before test
    devices = await api_client.get("/api/devices/")
    device_list = devices.json()
    
    for device in device_list:
        if device.get("is_playing"):
            await api_client.post(f"/api/devices/{device['id']}/stop")
    
    yield
    
    # Clean after test
    devices = await api_client.get("/api/devices/")
    device_list = devices.json()
    
    for device in device_list:
        if device.get("is_playing"):
            await api_client.post(f"/api/devices/{device['id']}/stop")

@pytest.mark.asyncio
async def test_api_health(api_client):
    """Test API health endpoint"""
    response = await api_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_device_listing(api_client):
    """Test device listing API"""
    response = await api_client.get("/api/devices/")
    assert response.status_code == 200
    devices = response.json()
    assert isinstance(devices, list)

@pytest.mark.asyncio
async def test_video_listing(api_client):
    """Test video listing API"""
    response = await api_client.get("/api/videos/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)

@pytest.mark.asyncio
async def test_device_playback_cycle(api_client, clean_devices):
    """Test complete playback cycle"""
    # Get devices
    devices_response = await api_client.get("/api/devices/")
    devices = devices_response.json()
    
    if not devices:
        pytest.skip("No devices available for testing")
    
    device = devices[0]
    device_id = device["id"]
    
    # Get videos
    videos_response = await api_client.get("/api/videos/")
    videos = videos_response.json()["items"]
    
    if not videos:
        pytest.skip("No videos available for testing")
    
    video = videos[0]
    video_id = video["id"]
    
    # Start playback
    play_response = await api_client.post(
        f"/api/devices/{device_id}/play/{video_id}"
    )
    assert play_response.status_code == 200
    
    # Wait for playback to establish
    await asyncio.sleep(2)
    
    # Check device status
    status_response = await api_client.get(f"/api/devices/{device_id}")
    device_info = status_response.json()
    assert device_info.get("is_playing") is True
    assert device_info.get("current_video") == video_id
    
    # Stop playback
    stop_response = await api_client.post(f"/api/devices/{device_id}/stop")
    assert stop_response.status_code == 200
    
    # Verify stopped
    await asyncio.sleep(1)
    status_response = await api_client.get(f"/api/devices/{device_id}")
    device_info = status_response.json()
    assert device_info.get("is_playing") is False

@pytest.mark.asyncio
async def test_discovery_toggle(api_client):
    """Test discovery pause/resume"""
    # Pause discovery
    pause_response = await api_client.post("/api/devices/discovery/pause")
    assert pause_response.status_code == 200
    
    await asyncio.sleep(1)
    
    # Resume discovery
    resume_response = await api_client.post("/api/devices/discovery/resume")
    assert resume_response.status_code == 200

@pytest.mark.asyncio
async def test_concurrent_requests(api_client):
    """Test handling of concurrent API requests"""
    tasks = []
    
    # Create multiple concurrent requests
    for _ in range(10):
        tasks.append(api_client.get("/api/devices/"))
        tasks.append(api_client.get("/api/videos/"))
    
    # Execute all requests concurrently
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify all succeeded
    for response in responses:
        assert not isinstance(response, Exception)
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])