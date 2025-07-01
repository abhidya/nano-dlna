"""Device factory for creating test device instances."""

import factory
from factory import fuzzy
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import random
import string

from web.backend.models.device import Device, DeviceType, DeviceStatus
from tests.mocks.device_mocks import MockDLNADevice


class DeviceFactory(factory.Factory):
    """Factory for creating Device instances."""
    
    class Meta:
        model = Device
    
    id = factory.Sequence(lambda n: n)
    name = factory.LazyFunction(lambda: f"TestDevice_{random.randint(1000, 9999)}")
    type = fuzzy.FuzzyChoice([t.value for t in DeviceType])
    ip_address = factory.LazyFunction(
        lambda: f"192.168.1.{random.randint(1, 254)}"
    )
    port = fuzzy.FuzzyInteger(8000, 9999)
    status = fuzzy.FuzzyChoice([s.value for s in DeviceStatus])
    last_seen = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    is_playing = False
    current_video_id = None
    playback_started_at = None
    user_control_mode = "auto"
    user_control_reason = None
    
    @factory.post_generation
    def capabilities(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            self.capabilities = extracted
        else:
            # Default capabilities based on device type
            if self.type == DeviceType.DLNA.value:
                self.capabilities = ["play", "pause", "stop", "seek"]
            elif self.type == DeviceType.AIRPLAY.value:
                self.capabilities = ["play", "pause", "stop", "volume"]
            else:
                self.capabilities = ["play", "stop"]


class DLNADeviceFactory(DeviceFactory):
    """Factory specifically for DLNA devices."""
    
    type = DeviceType.DLNA.value
    name = factory.LazyFunction(
        lambda: f"DLNA_{random.choice(['Living Room', 'Bedroom', 'Kitchen'])}_{random.randint(100, 999)}"
    )
    
    @factory.lazy_attribute
    def dlna_metadata(self):
        return {
            "manufacturer": random.choice(["Samsung", "LG", "Sony", "Generic"]),
            "model": f"Model-{random.randint(1000, 9999)}",
            "friendly_name": self.name,
            "udn": f"uuid:{''.join(random.choices(string.ascii_lowercase + string.digits, k=32))}",
            "services": [
                "urn:schemas-upnp-org:service:AVTransport:1",
                "urn:schemas-upnp-org:service:RenderingControl:1"
            ]
        }
    
    @classmethod
    def create_mock_instance(cls, **kwargs) -> MockDLNADevice:
        """Create a mock DLNA device instance for testing."""
        device_data = cls.build(**kwargs)
        
        mock_device = MockDLNADevice(
            name=device_data.name,
            ip=device_data.ip_address,
            port=device_data.port
        )
        
        # Set additional attributes
        for key, value in device_data.__dict__.items():
            if hasattr(mock_device, key):
                setattr(mock_device, key, value)
        
        return mock_device


class AirPlayDeviceFactory(DeviceFactory):
    """Factory specifically for AirPlay devices."""
    
    type = DeviceType.AIRPLAY.value
    name = factory.LazyFunction(
        lambda: f"AppleTV_{random.choice(['Living Room', 'Bedroom', 'Office'])}_{random.randint(100, 999)}"
    )
    
    @factory.lazy_attribute
    def airplay_metadata(self):
        return {
            "device_id": ''.join(random.choices(string.hexdigits.upper(), k=12)),
            "features": random.randint(0x1, 0xFFFF),
            "model": random.choice(["AppleTV3,2", "AppleTV5,3", "AppleTV6,2"]),
            "srcvers": "220.68",
            "vv": random.randint(1, 2)
        }


class DeviceGroupFactory(factory.Factory):
    """Factory for creating device groups."""
    
    class Meta:
        model = dict
    
    name = factory.LazyFunction(
        lambda: f"Group_{random.choice(['Living Room', 'All Devices', 'Projectors'])}_{random.randint(100, 999)}"
    )
    devices = factory.LazyFunction(
        lambda: [DLNADeviceFactory.build() for _ in range(random.randint(2, 5))]
    )
    sync_enabled = True
    master_device_id = factory.LazyAttribute(
        lambda obj: obj.devices[0].id if obj.devices else None
    )


def create_device_network(num_devices: int = 5) -> Dict[str, Any]:
    """Create a network of interconnected test devices."""
    devices = []
    
    # Create a mix of device types
    for i in range(num_devices):
        if i % 3 == 0:
            device = AirPlayDeviceFactory.create()
        else:
            device = DLNADeviceFactory.create()
        
        # Set some devices as playing
        if i % 2 == 0:
            device.is_playing = True
            device.playback_started_at = datetime.now(timezone.utc)
            device.current_video_id = random.randint(1, 100)
        
        devices.append(device)
    
    # Create device groups
    groups = []
    if num_devices >= 3:
        # All devices group
        all_devices_group = DeviceGroupFactory.create(
            name="All Devices",
            devices=devices
        )
        groups.append(all_devices_group)
        
        # Type-specific groups
        dlna_devices = [d for d in devices if d.type == DeviceType.DLNA.value]
        if dlna_devices:
            dlna_group = DeviceGroupFactory.create(
                name="DLNA Devices",
                devices=dlna_devices
            )
            groups.append(dlna_group)
    
    return {
        "devices": devices,
        "groups": groups,
        "network_info": {
            "total_devices": len(devices),
            "active_devices": len([d for d in devices if d.is_playing]),
            "device_types": {
                DeviceType.DLNA.value: len([d for d in devices if d.type == DeviceType.DLNA.value]),
                DeviceType.AIRPLAY.value: len([d for d in devices if d.type == DeviceType.AIRPLAY.value])
            }
        }
    }