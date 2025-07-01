"""
Central mock module for nano-dlna tests
"""
from .device_mocks import MockDevice, MockDLNADevice, MockDeviceManager
from .dlna_mocks import mock_discover_devices, mock_play, mock_stop
from .streaming_mocks import MockStreamingService, MockHTTPServer

__all__ = [
    'MockDevice',
    'MockDLNADevice',
    'MockDeviceManager',
    'mock_discover_devices',
    'mock_play',
    'mock_stop',
    'MockStreamingService',
    'MockHTTPServer',
]