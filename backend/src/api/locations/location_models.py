"""Location and Spotting models for wildlife camera API."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from src.api.models import Base


class Location(Base):
    """Location model representing a wildlife camera location."""

    __tablename__ = "locations"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(
        String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_public = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    images = relationship(
        "Image", back_populates="location", cascade="all, delete-orphan"
    )
    image_pull_sources = relationship(
        "ImagePullSource", back_populates="location", cascade="all, delete-orphan"
    )
    owner = relationship("User", foreign_keys=[owner_id])


class Spotting(Base):
    """Spotting model representing a detected animal in an image."""

    __tablename__ = "spottings"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    image_id = Column(
        String, ForeignKey("images.id", ondelete="CASCADE"), nullable=False
    )
    species = Column(String, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    bbox_x = Column(Integer, nullable=False)
    bbox_y = Column(Integer, nullable=False)
    bbox_width = Column(Integer, nullable=False)
    bbox_height = Column(Integer, nullable=False)
    detection_timestamp = Column(DateTime, default=datetime.utcnow)
    classification_model = Column(String, nullable=False)
    is_uncertain = Column(Boolean, default=False)

    # Relationships
    image = relationship("Image", back_populates="spottings")

    # Indexes
    __table_args__ = (Index("idx_spottings_image_id", "image_id"),)
