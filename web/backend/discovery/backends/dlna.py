"""
DLNA/UPnP discovery backend implementation.
"""

import asyncio
import socket
import struct
import xml.etree.ElementTree as ET
import re
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp

from ..base import DiscoveryBackend, Device, CastingMethod, CastingSession, DeviceCapability

logger = logging.getLogger(__name__)

# SSDP constants for DLNA device discovery
SSDP_BROADCAST_PORT = 1900
SSDP_BROADCAST_ADDR = "239.255.255.250"

SSDP_BROADCAST_PARAMS = [
    "M-SEARCH * HTTP/1.1",
    f"HOST: {SSDP_BROADCAST_ADDR}:{SSDP_BROADCAST_PORT}",
    "MAN: \"ssdp:discover\"", 
    "MX: 10", 
    "ST: ssdp:all", 
    "", 
    ""
]
SSDP_BROADCAST_MSG = "\r\n".join(SSDP_BROADCAST_PARAMS)

UPNP_DEVICE_TYPE = "urn:schemas-upnp-org:device:MediaRenderer:1"
UPNP_SERVICE_TYPE = "urn:schemas-upnp-org:service:AVTransport:1"


class DLNADiscoveryBackend(DiscoveryBackend):
    """
    Discovery backend for DLNA/UPnP devices.
    """
    
    def __init__(self):
        super().__init__("DLNA", CastingMethod.DLNA)
        self.discovery_timeout = 2.0
        
    async def discover_devices(self) -> List[Device]:
        """
        Discover DLNA devices on the network using SSDP.
        """
        logger.debug("Starting DLNA device discovery")
        
        # Create socket for SSDP broadcast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack("B", 4)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        sock.bind(("0.0.0.0", 0))
        sock.settimeout(self.discovery_timeout)
        
        # Send SSDP broadcast
        sock.sendto(SSDP_BROADCAST_MSG.encode("UTF-8"), 
                   (SSDP_BROADCAST_ADDR, SSDP_BROADCAST_PORT))
        
        # Collect responses
        devices = []
        device_locations = set()
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                response = data.decode("UTF-8")
                
                # Parse SSDP response
                headers = {}
                for line in response.split("\r\n")[1:]:
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        headers[key.strip().lower()] = value.strip()
                
                # Check if it's an AVTransport device
                if "st" in headers and "AVTransport" in headers["st"]:
                    location = headers.get("location")
                    if location and location not in device_locations:
                        device_locations.add(location)
                        device = await self._parse_device_description(location)
                        if device:
                            devices.append(device)
                            
            except socket.timeout:
                break
            except Exception as e:
                logger.error(f"Error processing SSDP response: {e}")
                
        sock.close()
        logger.info(f"Discovered {len(devices)} DLNA devices")
        return devices
    
    async def _parse_device_description(self, location_url: str) -> Optional[Device]:
        """
        Parse device description from XML at location URL.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(location_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    xml_content = await response.text()
                    
            # Remove namespace declarations for easier parsing
            xml_content = re.sub(r'\s(xmlns="[^"]+"|xmlns=\'[^\']+\')', '', xml_content, count=1)
            root = ET.fromstring(xml_content)
            
            # Find device element
            device_elem = root.find("./device")
            if not device_elem:
                device_elem = root.find(f"./device/deviceList/device/[deviceType='{UPNP_DEVICE_TYPE}']")
                
            if not device_elem:
                return None
                
            # Extract device information
            friendly_name = self._get_xml_text(device_elem, "./friendlyName", "Unknown Device")
            manufacturer = self._get_xml_text(device_elem, "./manufacturer", "Unknown")
            model = self._get_xml_text(device_elem, "./modelName", "Unknown")
            
            # Find AVTransport service
            service_elem = device_elem.find(f".//service/[serviceType='{UPNP_SERVICE_TYPE}']")
            if not service_elem:
                # Try alternative paths
                service_elem = device_elem.find(".//service/[serviceType='urn:schemas-upnp-org:service:AVTransport:1']")
                
            if not service_elem:
                logger.warning(f"No AVTransport service found for device at {location_url}")
                return None
                
            # Get control URL
            control_url = self._get_xml_text(service_elem, "./controlURL")
            if not control_url:
                return None
                
            # Parse hostname and port from location URL
            from urllib.parse import urlparse
            parsed = urlparse(location_url)
            hostname = parsed.hostname
            port = parsed.port or 80
            
            # Build full control URL
            if not control_url.startswith("http"):
                if control_url.startswith("/"):
                    control_url = f"http://{hostname}:{port}{control_url}"
                else:
                    control_url = f"http://{hostname}:{port}/{control_url}"
                    
            # Create device object
            device = Device(
                id=f"dlna_{hostname}_{port}",
                name=friendly_name,
                friendly_name=friendly_name,
                casting_method=CastingMethod.DLNA,
                hostname=hostname,
                port=port,
                capabilities=[
                    DeviceCapability.VIDEO_PLAYBACK,
                    DeviceCapability.AUDIO_PLAYBACK,
                    DeviceCapability.VOLUME_CONTROL,
                    DeviceCapability.SEEK_CONTROL
                ],
                metadata={
                    "model": model,
                    "service_type": UPNP_SERVICE_TYPE
                },
                action_url=control_url,
                location=location_url,
                manufacturer=manufacturer
            )
            
            logger.info(f"Discovered DLNA device: {friendly_name} at {hostname}:{port}")
            return device
            
        except Exception as e:
            logger.error(f"Error parsing device description from {location_url}: {e}")
            return None
    
    def _get_xml_text(self, parent, path: str, default: str = "") -> str:
        """Extract text from XML element."""
        elem = parent.find(path)
        return elem.text if elem is not None and elem.text else default
    
    async def cast_content(self, device: Device, content_url: str,
                          content_type: str = "video/mp4",
                          metadata: Optional[Dict[str, Any]] = None) -> CastingSession:
        """
        Cast content to a DLNA device.
        """
        if not device.action_url:
            raise ValueError(f"Device {device.name} missing action URL")
            
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Prepare DIDL-Lite metadata
        didl_lite = self._create_didl_lite(content_url, content_type, metadata)
        
        # Send SetAVTransportURI action
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
            <InstanceID>0</InstanceID>
            <CurrentURI>{content_url}</CurrentURI>
            <CurrentURIMetaData>{didl_lite}</CurrentURIMetaData>
        </u:SetAVTransportURI>
    </s:Body>
</s:Envelope>"""
        
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": '"urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI"'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(device.action_url, data=soap_body, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to set URI: {response.status}")
                    
        # Send Play action
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:Play xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
            <InstanceID>0</InstanceID>
            <Speed>1</Speed>
        </u:Play>
    </s:Body>
</s:Envelope>"""
        
        headers["SOAPAction"] = '"urn:schemas-upnp-org:service:AVTransport:1#Play"'
        
        async with aiohttp.ClientSession() as session:
            async with session.post(device.action_url, data=soap_body, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"Failed to play: {response.status}")
                    
        # Create session
        casting_session = CastingSession(
            id=session_id,
            device=device,
            content_url=content_url,
            content_type=content_type,
            metadata=metadata or {}
        )
        
        # Track session
        self.active_sessions[session_id] = casting_session
        
        logger.info(f"Started casting to {device.name}")
        return casting_session
    
    async def stop_casting(self, session: CastingSession) -> bool:
        """Stop casting on DLNA device."""
        try:
            soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:Stop xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
            <InstanceID>0</InstanceID>
        </u:Stop>
    </s:Body>
</s:Envelope>"""
            
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": '"urn:schemas-upnp-org:service:AVTransport:1#Stop"'
            }
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(session.device.action_url, 
                                           data=soap_body, 
                                           headers=headers) as response:
                    success = response.status == 200
                    
            if success:
                session.is_active = False
                self.active_sessions.pop(session.id, None)
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to stop casting: {e}")
            return False
    
    async def pause_casting(self, session: CastingSession) -> bool:
        """Pause casting on DLNA device."""
        try:
            soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:Pause xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
            <InstanceID>0</InstanceID>
        </u:Pause>
    </s:Body>
</s:Envelope>"""
            
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": '"urn:schemas-upnp-org:service:AVTransport:1#Pause"'
            }
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(session.device.action_url,
                                           data=soap_body,
                                           headers=headers) as response:
                    if response.status == 200:
                        session.is_paused = True
                        return True
                        
            return False
            
        except Exception as e:
            logger.error(f"Failed to pause casting: {e}")
            return False
    
    async def resume_casting(self, session: CastingSession) -> bool:
        """Resume casting on DLNA device."""
        return await self.cast_content(session.device, session.content_url, 
                                     session.content_type, session.metadata)
    
    async def seek(self, session: CastingSession, position: float) -> bool:
        """Seek to position on DLNA device."""
        try:
            # Convert position to HH:MM:SS format
            hours = int(position // 3600)
            minutes = int((position % 3600) // 60)
            seconds = int(position % 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:Seek xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
            <InstanceID>0</InstanceID>
            <Unit>REL_TIME</Unit>
            <Target>{time_str}</Target>
        </u:Seek>
    </s:Body>
</s:Envelope>"""
            
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": '"urn:schemas-upnp-org:service:AVTransport:1#Seek"'
            }
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(session.device.action_url,
                                           data=soap_body,
                                           headers=headers) as response:
                    if response.status == 200:
                        session.position = position
                        return True
                        
            return False
            
        except Exception as e:
            logger.error(f"Failed to seek: {e}")
            return False
    
    async def get_status(self, session: CastingSession) -> Dict[str, Any]:
        """Get playback status from DLNA device."""
        try:
            soap_body = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:GetPositionInfo xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
            <InstanceID>0</InstanceID>
        </u:GetPositionInfo>
    </s:Body>
</s:Envelope>"""
            
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": '"urn:schemas-upnp-org:service:AVTransport:1#GetPositionInfo"'
            }
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(session.device.action_url,
                                           data=soap_body,
                                           headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Parse response to extract position and duration
                        # This is simplified - real implementation would parse XML properly
                        return {
                            "is_playing": session.is_active and not session.is_paused,
                            "position": session.position,
                            "duration": session.duration,
                            "content_url": session.content_url
                        }
                        
            return {"error": "Failed to get status"}
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"error": str(e)}
    
    def _create_didl_lite(self, content_url: str, content_type: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create DIDL-Lite metadata for content."""
        title = "Video" if metadata is None else metadata.get("title", "Video")
        
        # Escape XML special characters
        import html
        title = html.escape(title)
        content_url = html.escape(content_url)
        
        return f"""&lt;DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"&gt;&lt;item id="1" parentID="0" restricted="1"&gt;&lt;dc:title&gt;{title}&lt;/dc:title&gt;&lt;res protocolInfo="http-get:*:{content_type}:*"&gt;{content_url}&lt;/res&gt;&lt;upnp:class&gt;object.item.videoItem&lt;/upnp:class&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;"""