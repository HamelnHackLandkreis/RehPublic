"""Image pull source model for automated image polling."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from src.api.models import Base


class ImagePullSource(Base):
    """Model representing an external image source to poll periodically.

    This model stores configuration for automated image pulling from external APIs,
    including authentication credentials and tracking of the last processed file.
    """

    __tablename__ = "image_pull_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location_id = Column(
        String,
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    base_url = Column(String, nullable=False)
    auth_type = Column(String, nullable=False, default="basic")
    auth_username = Column(String, nullable=True)
    auth_password = Column(String, nullable=True)
    auth_header = Column(String, nullable=True)
    last_pulled_filename = Column(String, nullable=True)
    last_pull_timestamp = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="image_pull_sources")
    location = relationship("Location", back_populates="image_pull_sources")
