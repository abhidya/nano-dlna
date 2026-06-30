"""
Playback-session orchestration.

DeviceManager and DLNA adapters keep their public methods, but progress,
streaming-session ownership, and registry bookkeeping live here.
"""

import logging
import time
import traceback
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PlaybackSessionCoordinator:
    """Deep module for playback-session state and registry coordination."""

    def __init__(self, device_manager: Any, registry: Any):
        self.device_manager = device_manager
        self.registry = registry

    def register_streaming_session(
        self,
        device_name: str,
        video_path: str,
        server_ip: str,
        server_port: Optional[int],
    ) -> Optional[Any]:
        if server_port is None:
            logger.warning("Cannot register streaming session without server port for %s", device_name)
            return None
        session = self.registry.register_session(
            device_name=device_name,
            video_path=video_path,
            server_ip=server_ip,
            server_port=server_port,
        )
        logger.debug("Registered streaming session %s for device %s", session.session_id, device_name)
        return session

    def complete_sessions(self, device_name: str) -> None:
        for session in self.registry.get_sessions_for_device(device_name):
            logger.info("Completing streaming session %s on device stop", session.session_id)
            session.complete()

    def owns_session(self, device_name: str, session_id: str) -> bool:
        session = self.registry.get_session(session_id)
        return bool(session and session.device_name == device_name)

    def refresh_active_sessions(self, device_name: str) -> None:
        for session in self.registry.get_sessions_for_device(device_name):
            if session.active:
                session.update_activity()

    def has_recent_activity(self, device_name: str, seconds: float = 30.0) -> bool:
        for session in self.registry.get_sessions_for_device(device_name):
            elapsed = (datetime.now() - session.last_activity_time).total_seconds()
            if elapsed < seconds:
                return True
        return False

    def update_progress(self, device_name: str, position: str, duration: str, progress: int) -> None:
        position, duration, progress = self._normalize_progress(device_name, position, duration, progress)
        self._update_in_memory_progress(device_name, position, duration, progress)
        self._update_database_progress(device_name, position, duration, progress)
        self._update_device_object_progress(device_name, position, duration, progress)

    def _normalize_progress(self, device_name: str, position: str, duration: str, progress: int):
        if not device_name:
            logger.error("Device name is required for updating playback progress")
        if not position or not isinstance(position, str):
            logger.error("Invalid position format for %s: %s", device_name, position)
            position = "00:00:00"
        if not duration or not isinstance(duration, str):
            logger.error("Invalid duration format for %s: %s", device_name, duration)
            duration = "00:00:00"
        if not isinstance(progress, int) or progress < 0 or progress > 100:
            logger.error("Invalid progress value for %s: %s", device_name, progress)
            progress = 0
        return position, duration, progress

    def _update_in_memory_progress(self, device_name: str, position: str, duration: str, progress: int) -> None:
        with self.device_manager.device_state_lock:
            status_dict = self.device_manager.device_status.setdefault(device_name, {})
            status_dict["playback_position"] = position
            status_dict["playback_duration"] = duration
            status_dict["playback_progress"] = progress
            status_dict["last_updated"] = time.time()
        logger.info("Updated in-memory playback progress for %s: %s/%s (%s%%)", device_name, position, duration, progress)

    def _update_database_progress(self, device_name: str, position: str, duration: str, progress: int) -> None:
        try:
            try:
                from ..database.database import get_db
                from ..services.device_service import DeviceService
            except ImportError:
                from database.database import get_db
                from services.device_service import DeviceService

            try:
                db_generator = get_db()
                db = next(db_generator)
                device_service = DeviceService(db, self.device_manager)
                db_device = device_service.get_device_by_name(device_name)
                if db_device:
                    db_device.playback_position = position
                    db_device.playback_duration = duration
                    db_device.playback_progress = progress
                    db.commit()
                else:
                    logger.warning("Device %s not found in database, cannot update playback progress", device_name)
                try:
                    db_generator.close()
                except Exception:
                    pass
            except Exception as db_error:
                logger.error("Error creating database session: %s", db_error)
                logger.debug(traceback.format_exc())
                self._update_existing_device_service(device_name, position, duration, progress)
        except ImportError as import_error:
            logger.error("Import error when updating playback progress: %s", import_error)
            logger.debug(traceback.format_exc())
        except Exception as exc:
            logger.error("Error updating device playback progress in database: %s", exc)
            logger.debug(traceback.format_exc())

    def _update_existing_device_service(self, device_name: str, position: str, duration: str, progress: int) -> None:
        device_service = getattr(self.device_manager, "device_service", None)
        if not device_service:
            return
        try:
            db_device = device_service.get_device_by_name(device_name)
            if db_device:
                db_device.playback_position = position
                db_device.playback_duration = duration
                db_device.playback_progress = progress
                device_service.db.commit()
            else:
                logger.warning("Device %s not found in database via device_service", device_name)
        except Exception as service_error:
            logger.error("Error updating via device_service: %s", service_error)

    def _update_device_object_progress(self, device_name: str, position: str, duration: str, progress: int) -> None:
        try:
            device = self.device_manager.get_device(device_name)
            if device:
                device.current_position = position
                device.duration_formatted = duration
                device.playback_progress = progress
        except Exception as exc:
            logger.error("Error updating core device object playback progress: %s", exc)
