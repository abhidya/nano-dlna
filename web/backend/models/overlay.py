from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.database import Base

class OverlayConfig(Base):
    __tablename__ = "overlay_configs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    video_transform = Column(JSON, nullable=False)
    widgets = Column(JSON, nullable=False)
    api_configs = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship - using string reference to avoid circular imports
    video = relationship("VideoModel", back_populates="overlay_configs")
