"""
Pytest configuration file with fixtures for testing.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database.database import Base, get_db
from models.device import DeviceModel
from models.video import VideoModel
from core.device_manager import DeviceManager
from core.streaming_registry import StreamingSessionRegistry
from core.twisted_streaming import get_instance as get_twisted_streaming


# Database setup
@pytest.fixture(scope="function")
def test_db():
    """Create a test database."""
    # Create a temporary file for the test database
    temp_db = tempfile.NamedTemporaryFile(suffix=".db")
    
    # Create the engine and session
    engine = create_engine(f"sqlite:///{temp_db.name}")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create the tables
    Base.metadata.create_all(bind=engine)
    
    # Override the get_db dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create a session and yield it
    db = TestingSessionLocal()
    yield db
    
    # Clean up
    db.close()
    temp_db.close()
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_client(test_db):
    """Create a test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def device_manager():
    """Create a device manager."""
    return DeviceManager()


@pytest.fixture(scope="function")
def streaming_registry():
    """Create a streaming registry."""
    return StreamingSessionRegistry.get_instance()


@pytest.fixture(scope="function")
def twisted_streaming():
    """Get twisted streaming instance."""
    return get_twisted_streaming()


@pytest.fixture(scope="function")
def sample_device():
    """Create a sample device."""
    return DeviceModel(
        name="Test Device",
        type="dlna",
        hostname="127.0.0.1",
        action_url="http://127.0.0.1:8000/action",
        location="http://127.0.0.1:8000/location",
        friendly_name="Test Device",
        status="online"
    )


@pytest.fixture(scope="function")
def sample_video():
    """Create a sample video."""
    return VideoModel(
        name="Test Video",
        path="/path/to/test_video.mp4",
        file_name="test_video.mp4",
        file_size=1024,
        format="mp4",
        duration=60.0,
        resolution="1920x1080",
        has_subtitle=False
    )


@pytest.fixture(scope="function")
def tmp_video_file():
    """Create a temporary video file."""
    # Create a temporary file to simulate a video
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp4")
    # Write some dummy content to the file
    temp_file.write(b"test video content")
    temp_file.flush()
    
    yield temp_file.name
    
    # Clean up
    temp_file.close()


@pytest.fixture(scope="function")
def tmp_config_file():
    """Create a temporary config file."""
    # Create a temporary file to simulate a config file
    temp_file = tempfile.NamedTemporaryFile(suffix=".json")
    # Write a sample configuration
    temp_file.write(b'''
    {
        "devices": [
            {
                "name": "Test Device",
                "type": "dlna",
                "hostname": "127.0.0.1",
                "location": "http://127.0.0.1:8000/location",
                "action_url": "http://127.0.0.1:8000/action",
                "control_url": "http://127.0.0.1:8000/control"
            }
        ]
    }
    ''')
    temp_file.flush()
    
    yield temp_file.name
    
    # Clean up
    temp_file.close()
