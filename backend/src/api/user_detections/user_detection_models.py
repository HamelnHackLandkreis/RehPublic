"""UserDetection model for wildlife camera API."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, String

from api.models import Base


class UserDetection(Base):  # type: ignore[valid-type,misc]
    """UserDetection model representing manual user identifications of animals in images."""

    __tablename__ = "user_detections"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    image_id = Column(
        String, ForeignKey("images.id", ondelete="CASCADE"), nullable=False
    )
    species = Column(String, nullable=False, index=True)
    user_session_id = Column(String, nullable=True, index=True)
    detection_timestamp = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_user_detections_image_id", "image_id"),
        Index("idx_user_detections_species", "species"),
    )
