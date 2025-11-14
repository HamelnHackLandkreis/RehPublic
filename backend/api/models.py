"""SQLAlchemy ORM models for wildlife camera API."""

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
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()  # type: ignore[valid-type,misc]


class Location(Base):  # type: ignore[valid-type,misc]
    """Location model representing a wildlife camera location."""

    __tablename__ = "locations"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    images = relationship(
        "Image", back_populates="location", cascade="all, delete-orphan"
    )


class Image(Base):  # type: ignore[valid-type,misc]
    """Image model representing an uploaded wildlife camera image."""

    __tablename__ = "images"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    location_id = Column(
        String, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    base64_data = Column(Text, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

    # Relationships
    location = relationship("Location", back_populates="images")
    spottings = relationship(
        "Spotting", back_populates="image", cascade="all, delete-orphan"
    )


class Spotting(Base):  # type: ignore[valid-type,misc]
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
