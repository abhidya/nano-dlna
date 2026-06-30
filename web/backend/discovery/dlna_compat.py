"""
Compatibility helpers for the canonical DLNA discovery module.

Legacy callers still expect dictionaries shaped like DeviceManager used to
produce. This module keeps that translation in one place.
"""

import asyncio
import threading
from typing import Any, Coroutine, Dict, List, Optional

from .backends.dlna import DLNADiscoveryBackend
from .base import Device


def canonical_device_to_legacy_dict(device: Device) -> Dict[str, Any]:
    return {
        "device_name": device.name,
        "type": "dlna",
        "location": device.location,
        "hostname": device.hostname,
        "manufacturer": device.manufacturer,
        "friendly_name": device.friendly_name,
        "action_url": device.action_url,
        "st": "urn:schemas-upnp-org:service:AVTransport:1",
    }


def discover_dlna_device_dicts(timeout: float = 2.0, host: Optional[str] = None) -> List[Dict[str, Any]]:
    backend = DLNADiscoveryBackend(discovery_timeout=timeout, bind_host=host or "0.0.0.0")
    devices = _run_async(backend.discover_devices())
    return [canonical_device_to_legacy_dict(device) for device in devices]


def parse_dlna_device_dict(location_url: str) -> Optional[Dict[str, Any]]:
    backend = DLNADiscoveryBackend()
    device = _run_async(backend.parse_device_description(location_url))
    return canonical_device_to_legacy_dict(device) if device else None


def _run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result = {}

    def runner() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result["value"] = loop.run_until_complete(coro)
        except BaseException as exc:
            result["error"] = exc
        finally:
            loop.close()

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()
    if "error" in result:
        raise result["error"]
    return result.get("value")
