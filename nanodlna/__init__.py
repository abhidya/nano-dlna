# -*- coding: utf-8 -*-

__title__ = 'nanodlna'
__version__ = '0.2.1'
__short_version__ = '.'.join(__version__.split('.')[:2])
__author__ = 'Gabriel Magno'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016, Gabriel Magno'

# Import modules
from . import devices, dlna, streaming

# Export functions needed by tests
def discover_devices(timeout=5.0, host=None):
    """
    Discover DLNA devices on the network.
    
    Args:
        timeout (float): Timeout in seconds for device discovery
        host (str): Host IP to bind to for discovery
        
    Returns:
        list: List of discovered devices
    """
    return dlna._discover_upnp_devices(timeout, host)

def send_video(device_info, video_path, loop=False):
    """
    Send a video to a DLNA device.
    
    Args:
        device_info (dict): Device information dictionary
        video_path (str): Path to the video file
        loop (bool): Whether to loop the video
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Configure streaming server
        files = {"file_video": video_path}
        
        # Get serve_ip from device's hostname
        target_ip = device_info.get("hostname")
        serve_ip = streaming.get_serve_ip(target_ip)
        
        # Start streaming
        url_dict, _ = streaming.start_server(files, serve_ip)
        
        # Create args object with loop attribute
        class Args:
            pass
        args = Args()
        args.loop = loop
        
        # Play the video
        dlna.play(url_dict, device_info, args)
        return True
    except Exception as e:
        print(f"Error sending video: {e}")
        return False
