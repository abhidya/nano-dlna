import os
import sys
import pytest
import tempfile
import json
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import backend modules
from database.database import Base, get_db
from main import app
from core.device_manager import DeviceManager
from core.config_service import ConfigService
from services.device_service import DeviceService
from services.video_service import VideoService

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture
def test_db():
    """Create a test database with tables"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Override the get_db dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Return the session for test use
    db = TestingSessionLocal()
    yield db
    
    # Clean up
    db.close()
    Base.metadata.drop_all(engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture
def client(test_db):
    """Create a test client with the test database"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def device_manager():
    """Create a mocked device manager"""
    with patch('core.device_manager.ConfigService'), \
         patch('core.device_manager.StreamingSessionRegistry'):
        manager = DeviceManager()
        # Mock methods as needed
        manager.get_serve_ip = MagicMock(return_value="127.0.0.1")
        manager.start_discovery = MagicMock()
        manager.stop_discovery = MagicMock()
        yield manager


@pytest.fixture
def config_service():
    """Create a mocked config service"""
    with patch.object(ConfigService, '_instance', None):
        with patch.object(ConfigService, '_config_files', {}):
            service = ConfigService.get_instance()
            yield service


@pytest.fixture
def device_service(test_db, device_manager):
    """Create a device service with test database"""
    service = DeviceService(test_db, device_manager)
    yield service


@pytest.fixture
def video_service(test_db):
    """Create a video service with test database"""
    service = VideoService(test_db)
    yield service


@pytest.fixture
def sample_device_config():
    """Sample device configuration data"""
    return {
        "TestDevice": {
            "device_name": "TestDevice",
            "type": "dlna",
            "hostname": "10.0.0.1",
            "action_url": "http://10.0.0.1/action",
            "friendly_name": "Test Device",
            "video_file": "test_video.mp4"
        }
    }


@pytest.fixture
def temp_config_file(sample_device_config):
    """Create a temporary config file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
        json.dump(sample_device_config, temp)
        temp_name = temp.name
    
    yield temp_name
    
    # Clean up
    if os.path.exists(temp_name):
        os.remove(temp_name)


@pytest.fixture
def mock_dlna_device():
    """Mock DLNA device for testing"""
    device = MagicMock()
    device.name = "TestDevice"
    device.type = "dlna"
    device.hostname = "10.0.0.1"
    device.action_url = "http://10.0.0.1/action"
    device.friendly_name = "Test Device"
    device.is_playing = False
    device.current_video = None
    device.play.return_value = True
    device.stop.return_value = True
    device.pause.return_value = True
    
    return device 