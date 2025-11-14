"""Location model for wildlife camera API."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.orm import relationship

from api.models import Base


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
