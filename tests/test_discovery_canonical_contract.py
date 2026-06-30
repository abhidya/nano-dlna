from web.backend.discovery.base import CastingMethod, Device, DeviceCapability
from web.backend.discovery.dlna_compat import canonical_device_to_legacy_dict
from web.backend.discovery.discovery_manager import DiscoveryManager
from web.backend.core.device_manager import DeviceManager


def make_device():
    return Device(
        id="dlna_10.0.0.5_80",
        name="Living Room TV",
        friendly_name="Living Room TV",
        casting_method=CastingMethod.DLNA,
        hostname="10.0.0.5",
        port=80,
        capabilities=[DeviceCapability.VIDEO_PLAYBACK],
        action_url="http://10.0.0.5:80/AVTransport/Control",
        location="http://10.0.0.5/device.xml",
        manufacturer="Example",
    )


def test_canonical_dlna_device_translates_to_legacy_shape():
    legacy = canonical_device_to_legacy_dict(make_device())

    assert legacy == {
        "device_name": "Living Room TV",
        "type": "dlna",
        "location": "http://10.0.0.5/device.xml",
        "hostname": "10.0.0.5",
        "manufacturer": "Example",
        "friendly_name": "Living Room TV",
        "action_url": "http://10.0.0.5:80/AVTransport/Control",
        "st": "urn:schemas-upnp-org:service:AVTransport:1",
    }


def test_discovery_manager_adds_devices_through_public_interface():
    manager = DiscoveryManager()
    device = make_device()

    manager.add_discovered_device(device)

    assert manager.get_device_by_id(device.id) == device


def test_device_manager_registers_dlna_description_through_canonical_module(monkeypatch):
    expected = canonical_device_to_legacy_dict(make_device())

    monkeypatch.setattr(
        "web.backend.discovery.dlna_compat.parse_dlna_device_dict",
        lambda location_url: expected,
    )

    manager = DeviceManager()

    assert manager._register_dlna_device("http://10.0.0.5/device.xml") == expected
