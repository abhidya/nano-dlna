"""
Shared test utilities and helpers
"""
import os
import tempfile
import json
from typing import Dict, Any, Optional
from unittest.mock import MagicMock


def create_test_video_file(suffix: str = ".mp4", content: bytes = b"test video content") -> str:
    """
    Create a temporary video file for testing
    
    Args:
        suffix: File suffix (default: .mp4)
        content: File content (default: test video content)
        
    Returns:
        str: Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(content)
        return f.name


def create_test_config(devices: Optional[list] = None) -> str:
    """
    Create a temporary config file for testing
    
    Args:
        devices: List of device configurations
        
    Returns:
        str: Path to the temporary config file
    """
    if devices is None:
        devices = [
            {
                "name": "Test Device",
                "type": "dlna",
                "hostname": "127.0.0.1",
                "location": "http://127.0.0.1:8000/location",
                "action_url": "http://127.0.0.1:8000/action",
                "control_url": "http://127.0.0.1:8000/control"
            }
        ]
    
    config = {"devices": devices}
    
    with tempfile.NamedTemporaryFile(suffix=".json", mode='w', delete=False) as f:
        json.dump(config, f)
        return f.name


def create_mock_sqlalchemy_session():
    """Create a mock SQLAlchemy session for testing"""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.filter_by.return_value = session
    session.first.return_value = None
    session.all.return_value = []
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    session.add.return_value = None
    session.delete.return_value = None
    session.flush.return_value = None
    
    return session


def cleanup_test_files(*file_paths):
    """
    Clean up temporary test files
    
    Args:
        *file_paths: Variable number of file paths to clean up
    """
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except Exception:
                pass


class MockWebSocketConnection:
    """Mock WebSocket connection for testing"""
    
    def __init__(self):
        self.messages = []
        self.closed = False
        
    async def send_text(self, message: str):
        """Mock send text message"""
        self.messages.append(message)
        
    async def send_json(self, data: Dict[str, Any]):
        """Mock send JSON message"""
        self.messages.append(json.dumps(data))
        
    async def close(self):
        """Mock close connection"""
        self.closed = True
        
    def get_messages(self) -> list:
        """Get all sent messages"""
        return self.messages
        
    def clear_messages(self):
        """Clear sent messages"""
        self.messages = []