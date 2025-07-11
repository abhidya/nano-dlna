"""
Unified discovery manager that orchestrates multiple discovery backends.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime, timedelta
import threading

from .base import DiscoveryBackend, Device, CastingMethod, CastingSession, DeviceCapability

logger = logging.getLogger(__name__)


class DiscoveryManager:
    """
    Central manager for all discovery backends.
    Provides a unified interface for device discovery and casting.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance of DiscoveryManager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize the discovery manager"""
        self.backends: Dict[str, DiscoveryBackend] = {}
        self.all_devices: Dict[str, Device] = {}
        self.device_sessions: Dict[str, List[CastingSession]] = {}
        self._callbacks: List[Callable] = []
        self._device_lock = threading.RLock()
        self._running = False
        
        # Device grouping and zones
        self.device_groups: Dict[str, Set[str]] = {}
        self.device_zones: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.auto_cast_enabled = True
        self.device_timeout = timedelta(minutes=2)
        
    def register_backend(self, backend: DiscoveryBackend):
        """
        Register a discovery backend.
        
        Args:
            backend: Backend to register
        """
        backend_name = backend.name
        if backend_name in self.backends:
            logger.warning(f"Backend {backend_name} already registered, replacing")
            
        self.backends[backend_name] = backend
        
        # Register callback for backend events
        backend.register_callback(self._handle_backend_event)
        
        logger.info(f"Registered discovery backend: {backend_name}")
        
    def unregister_backend(self, backend_name: str):
        """
        Unregister a discovery backend.
        
        Args:
            backend_name: Name of backend to unregister
        """
        if backend_name in self.backends:
            backend = self.backends.pop(backend_name)
            asyncio.create_task(backend.stop_discovery())
            logger.info(f"Unregistered discovery backend: {backend_name}")
            
    async def start_discovery(self, backend_names: Optional[List[str]] = None):
        """
        Start discovery on specified backends or all if none specified.
        
        Args:
            backend_names: List of backend names to start, or None for all
        """
        self._running = True
        
        if backend_names is None:
            backend_names = list(self.backends.keys())
            
        tasks = []
        for name in backend_names:
            if name in self.backends:
                backend = self.backends[name]
                tasks.append(backend.start_discovery())
            else:
                logger.warning(f"Backend {name} not found")
                
        await asyncio.gather(*tasks)
        logger.info(f"Started discovery on backends: {backend_names}")
        
    async def stop_discovery(self, backend_names: Optional[List[str]] = None):
        """
        Stop discovery on specified backends or all if none specified.
        
        Args:
            backend_names: List of backend names to stop, or None for all
        """
        self._running = False
        
        if backend_names is None:
            backend_names = list(self.backends.keys())
            
        tasks = []
        for name in backend_names:
            if name in self.backends:
                backend = self.backends[name]
                tasks.append(backend.stop_discovery())
                
        await asyncio.gather(*tasks)
        logger.info(f"Stopped discovery on backends: {backend_names}")
        
    def get_all_devices(self, online_only: bool = False) -> List[Device]:
        """
        Get all discovered devices across all backends.
        
        Args:
            online_only: Only return online devices
            
        Returns:
            List of devices
        """
        with self._device_lock:
            devices = list(self.all_devices.values())
            
        if online_only:
            devices = [d for d in devices if d.is_online]
            
        return devices
    
    def get_devices_by_method(self, casting_method: CastingMethod, 
                             online_only: bool = False) -> List[Device]:
        """
        Get devices by casting method.
        
        Args:
            casting_method: Casting method to filter by
            online_only: Only return online devices
            
        Returns:
            List of devices
        """
        devices = self.get_all_devices(online_only)
        return [d for d in devices if d.casting_method == casting_method]
    
    def get_device_by_id(self, device_id: str) -> Optional[Device]:
        """
        Get device by ID.
        
        Args:
            device_id: Device ID
            
        Returns:
            Device if found
        """
        with self._device_lock:
            return self.all_devices.get(device_id)
    
    def get_devices_with_capability(self, capability: DeviceCapability,
                                   online_only: bool = True) -> List[Device]:
        """
        Get devices with a specific capability.
        
        Args:
            capability: Capability to filter by
            online_only: Only return online devices
            
        Returns:
            List of devices
        """
        devices = self.get_all_devices(online_only)
        return [d for d in devices if d.has_capability(capability)]
    
    async def cast_content(self, device_id: str, content_url: str,
                          content_type: str = "video/mp4",
                          metadata: Optional[Dict[str, Any]] = None) -> Optional[CastingSession]:
        """
        Cast content to a device using appropriate backend.
        
        Args:
            device_id: Target device ID
            content_url: URL of content to cast
            content_type: MIME type of content
            metadata: Additional metadata
            
        Returns:
            CastingSession if successful
        """
        device = self.get_device_by_id(device_id)
        if not device:
            logger.error(f"Device {device_id} not found")
            return None
            
        # Find appropriate backend
        backend = self._get_backend_for_device(device)
        if not backend:
            logger.error(f"No backend found for device {device_id}")
            return None
            
        try:
            session = await backend.cast_content(device, content_url, content_type, metadata)
            
            # Track session
            with self._device_lock:
                if device_id not in self.device_sessions:
                    self.device_sessions[device_id] = []
                self.device_sessions[device_id].append(session)
                
            # Notify callbacks
            await self._notify_callbacks('content_cast', {
                'device': device,
                'session': session
            })
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to cast to device {device_id}: {e}")
            return None
    
    async def stop_casting(self, session_id: str) -> bool:
        """
        Stop a casting session.
        
        Args:
            session_id: Session ID to stop
            
        Returns:
            True if successful
        """
        session = self._find_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return False
            
        backend = self._get_backend_for_device(session.device)
        if not backend:
            return False
            
        try:
            success = await backend.stop_casting(session)
            
            if success:
                # Remove from active sessions
                with self._device_lock:
                    device_id = session.device.id
                    if device_id in self.device_sessions:
                        self.device_sessions[device_id] = [
                            s for s in self.device_sessions[device_id] 
                            if s.id != session_id
                        ]
                        
                # Notify callbacks
                await self._notify_callbacks('content_stopped', {
                    'device': session.device,
                    'session': session
                })
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to stop session {session_id}: {e}")
            return False
    
    async def pause_casting(self, session_id: str) -> bool:
        """Pause a casting session"""
        session = self._find_session(session_id)
        if not session:
            return False
            
        backend = self._get_backend_for_device(session.device)
        if not backend:
            return False
            
        return await backend.pause_casting(session)
    
    async def resume_casting(self, session_id: str) -> bool:
        """Resume a casting session"""
        session = self._find_session(session_id)
        if not session:
            return False
            
        backend = self._get_backend_for_device(session.device)
        if not backend:
            return False
            
        return await backend.resume_casting(session)
    
    async def seek(self, session_id: str, position: float) -> bool:
        """Seek in a casting session"""
        session = self._find_session(session_id)
        if not session:
            return False
            
        backend = self._get_backend_for_device(session.device)
        if not backend:
            return False
            
        return await backend.seek(session, position)
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a casting session"""
        session = self._find_session(session_id)
        if not session:
            return None
            
        backend = self._get_backend_for_device(session.device)
        if not backend:
            return None
            
        return await backend.get_status(session)
    
    def get_active_sessions(self, device_id: Optional[str] = None) -> List[CastingSession]:
        """
        Get active casting sessions.
        
        Args:
            device_id: Filter by device ID, or None for all
            
        Returns:
            List of active sessions
        """
        with self._device_lock:
            if device_id:
                sessions = self.device_sessions.get(device_id, [])
            else:
                sessions = []
                for device_sessions in self.device_sessions.values():
                    sessions.extend(device_sessions)
                    
        return [s for s in sessions if s.is_active]
    
    def create_device_group(self, group_name: str, device_ids: List[str]):
        """
        Create a device group for synchronized casting.
        
        Args:
            group_name: Name of the group
            device_ids: List of device IDs to include
        """
        with self._device_lock:
            self.device_groups[group_name] = set(device_ids)
        logger.info(f"Created device group {group_name} with {len(device_ids)} devices")
        
    def add_to_group(self, group_name: str, device_id: str):
        """Add device to group"""
        with self._device_lock:
            if group_name not in self.device_groups:
                self.device_groups[group_name] = set()
            self.device_groups[group_name].add(device_id)
            
    def remove_from_group(self, group_name: str, device_id: str):
        """Remove device from group"""
        with self._device_lock:
            if group_name in self.device_groups:
                self.device_groups[group_name].discard(device_id)
                
    async def cast_to_group(self, group_name: str, content_url: str,
                           content_type: str = "video/mp4",
                           metadata: Optional[Dict[str, Any]] = None) -> List[CastingSession]:
        """
        Cast content to all devices in a group.
        
        Args:
            group_name: Name of the group
            content_url: URL of content to cast
            content_type: MIME type of content
            metadata: Additional metadata
            
        Returns:
            List of casting sessions
        """
        with self._device_lock:
            device_ids = list(self.device_groups.get(group_name, []))
            
        tasks = []
        for device_id in device_ids:
            tasks.append(self.cast_content(device_id, content_url, content_type, metadata))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        sessions = []
        for result in results:
            if isinstance(result, CastingSession):
                sessions.append(result)
            else:
                logger.error(f"Failed to cast to device in group: {result}")
                
        return sessions
    
    def register_callback(self, callback: Callable):
        """Register callback for discovery events"""
        self._callbacks.append(callback)
        
    async def _handle_backend_event(self, event_type: str, data: Any):
        """Handle events from backends"""
        if event_type == 'device_discovered':
            device = data
            with self._device_lock:
                self.all_devices[device.id] = device
                
            await self._notify_callbacks('device_discovered', device)
            
        elif event_type == 'device_lost':
            device = data
            await self._notify_callbacks('device_lost', device)
            
    async def _notify_callbacks(self, event_type: str, data: Any):
        """Notify all callbacks of an event"""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in discovery callback: {e}")
                
    def _get_backend_for_device(self, device: Device) -> Optional[DiscoveryBackend]:
        """Get appropriate backend for a device"""
        for backend in self.backends.values():
            if backend.supports_device(device):
                return backend
        return None
    
    def _find_session(self, session_id: str) -> Optional[CastingSession]:
        """Find a session by ID"""
        with self._device_lock:
            for sessions in self.device_sessions.values():
                for session in sessions:
                    if session.id == session_id:
                        return session
        return None
    
    def get_backend_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all backends"""
        status = {}
        for name, backend in self.backends.items():
            status[name] = {
                'name': backend.name,
                'casting_method': backend.casting_method.value,
                'discovery_running': backend.discovery_running,
                'discovered_devices': len(backend.discovered_devices),
                'online_devices': len(backend.get_online_devices()),
                'active_sessions': len(backend.get_active_sessions())
            }
        return status