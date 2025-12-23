"""Image model for wildlife camera API."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.api.models import Base


class Image(Base):
    """Image model representing an uploaded wildlife camera image."""

    __tablename__ = "images"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    location_id = Column(
        String, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    base64_data = Column(Text, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    processing_status = Column(
        String, default="uploading"
    )  # uploading, detecting, completed, failed
    celery_task_id = Column(String, nullable=True)

    # Relationships
    location = relationship("Location", back_populates="images")
    user = relationship("User", back_populates="images")
    spottings = relationship(
        "Spotting", back_populates="image", cascade="all, delete-orphan"
    )
