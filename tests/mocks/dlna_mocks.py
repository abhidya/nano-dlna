"""
Mock DLNA functions for testing
"""
from typing import List, Dict, Any, Optional


def mock_discover_devices(timeout: int = 5) -> List[Dict[str, Any]]:
    """Mock device discovery"""
    return [
        {
            "location": "http://10.0.0.45:3500/",
            "friendly_name": "Test_Projector-45[DLNA]",
            "hostname": "10.0.0.45",
            "action_url": "http://10.0.0.45:3500/AVTransport/control.xml",
            "name": "Test_Projector-45[DLNA]",
            "type": "dlna"
        },
        {
            "location": "http://10.0.0.122:49595/description.xml",
            "friendly_name": "Test_SideProjector_dlna",
            "hostname": "10.0.0.122",
            "action_url": "http://10.0.0.122:49595/upnp/control/rendertransport1",
            "name": "Test_SideProjector_dlna",
            "type": "dlna"
        }
    ]


def mock_play(device_info: Dict[str, Any], video_url: str, instance: int = 0, 
              set_next: bool = False, title: Optional[str] = None,
              metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Mock DLNA play function"""
    return True


def mock_stop(device_info: Dict[str, Any], instance: int = 0) -> bool:
    """Mock DLNA stop function"""
    return True


class MockDLNAException(Exception):
    """Mock DLNA exception for testing error handling"""
    pass