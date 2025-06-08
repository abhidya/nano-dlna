from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from models.overlay import OverlayConfig
from models.video import VideoModel
from schemas.overlay import (
    OverlayConfigCreate,
    OverlayConfigUpdate,
    OverlayConfigResponse,
    OverlayStreamResponse
)
from core.streaming_service import StreamingService

class OverlayService:
    def __init__(self, db: Session):
        self.db = db
        self.streaming_service = StreamingService()

    def create_config(self, config_data: OverlayConfigCreate) -> OverlayConfigResponse:
        """Create a new overlay configuration"""
        # Verify video exists
        video = self.db.query(VideoModel).filter(VideoModel.id == config_data.video_id).first()
        if not video:
            raise ValueError(f"Video with id {config_data.video_id} not found")
        
        # Create new config
        new_config = OverlayConfig(
            name=config_data.name,
            video_id=config_data.video_id,
            video_transform=config_data.video_transform.dict(),
            widgets=[w.dict() for w in config_data.widgets],
            api_configs=config_data.api_configs.dict()
        )
        
        self.db.add(new_config)
        self.db.commit()
        self.db.refresh(new_config)
        
        return self._to_response(new_config)

    def list_configs(self, video_id: Optional[int] = None) -> List[OverlayConfigResponse]:
        """List overlay configurations, optionally filtered by video ID"""
        query = self.db.query(OverlayConfig)
        
        if video_id:
            query = query.filter(OverlayConfig.video_id == video_id)
        
        configs = query.order_by(OverlayConfig.updated_at.desc()).all()
        return [self._to_response(config) for config in configs]

    def get_config(self, config_id: int) -> Optional[OverlayConfigResponse]:
        """Get a specific overlay configuration"""
        config = self.db.query(OverlayConfig).filter(OverlayConfig.id == config_id).first()
        if config:
            return self._to_response(config)
        return None

    def update_config(self, config_id: int, config_update: OverlayConfigUpdate) -> Optional[OverlayConfigResponse]:
        """Update an overlay configuration"""
        config = self.db.query(OverlayConfig).filter(OverlayConfig.id == config_id).first()
        if not config:
            return None
        
        # Update fields if provided
        if config_update.name is not None:
            config.name = config_update.name
        
        if config_update.video_transform is not None:
            config.video_transform = config_update.video_transform.dict()
        
        if config_update.widgets is not None:
            config.widgets = [w.dict() for w in config_update.widgets]
        
        if config_update.api_configs is not None:
            config.api_configs = config_update.api_configs.dict()
        
        config.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(config)
        
        return self._to_response(config)

    def delete_config(self, config_id: int) -> bool:
        """Delete an overlay configuration"""
        config = self.db.query(OverlayConfig).filter(OverlayConfig.id == config_id).first()
        if not config:
            return False
        
        self.db.delete(config)
        self.db.commit()
        return True

    def duplicate_config(self, config_id: int, new_name: Optional[str] = None) -> Optional[OverlayConfigResponse]:
        """Duplicate an overlay configuration"""
        original = self.db.query(OverlayConfig).filter(OverlayConfig.id == config_id).first()
        if not original:
            return None
        
        # Create duplicate
        duplicate = OverlayConfig(
            name=new_name or f"{original.name} (Copy)",
            video_id=original.video_id,
            video_transform=original.video_transform,
            widgets=original.widgets,
            api_configs=original.api_configs
        )
        
        self.db.add(duplicate)
        self.db.commit()
        self.db.refresh(duplicate)
        
        return self._to_response(duplicate)

    def create_stream(self, video_id: int, config_id: Optional[int] = None) -> OverlayStreamResponse:
        """Create a streaming URL for overlay projection"""
        # Get video
        video = self.db.query(VideoModel).filter(VideoModel.id == video_id).first()
        if not video:
            raise ValueError(f"Video with id {video_id} not found")
        
        # Log video details
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Creating overlay stream for video: {video.path}, filename: {video.file_name}")
        
        # Start streaming if not already active
        stream_info = self.streaming_service.get_or_create_stream(video.path)
        logger.info(f"Stream info returned: {stream_info}")
        
        # Get the actual port and URL from the stream info
        port = stream_info.get('port', 9000)
        streaming_url = stream_info.get('url', '')
        
        # If no URL returned, build one (fallback)
        if not streaming_url:
            logger.warning(f"No URL returned from streaming service, using fallback")
            streaming_url = f"http://localhost:{port}/{video.file_name}"
        
        # Add /uploads/ path if not already present
        if streaming_url and '/uploads/' not in streaming_url:
            # Insert /uploads/ before the filename
            parts = streaming_url.rsplit('/', 1)
            if len(parts) == 2:
                streaming_url = f"{parts[0]}/uploads/{parts[1]}"
        
        logger.info(f"Returning streaming URL: {streaming_url}")
        
        return OverlayStreamResponse(
            streaming_url=streaming_url,
            port=port,
            video_path=video.path,
            config_id=config_id
        )

    def _to_response(self, config: OverlayConfig) -> OverlayConfigResponse:
        """Convert database model to response schema"""
        return OverlayConfigResponse(
            id=config.id,
            name=config.name,
            video_id=config.video_id,
            video_transform=config.video_transform,
            widgets=config.widgets,
            api_configs=config.api_configs,
            created_at=config.created_at,
            updated_at=config.updated_at
        )