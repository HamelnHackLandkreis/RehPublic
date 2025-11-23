"""User model for Auth0 authentication."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from src.api.models import Base


class User(Base):
    """User model representing an authenticated user."""

    __tablename__ = "users"

    id = Column(String, primary_key=True)  # Auth0 user ID (sub claim)
    email = Column(String, nullable=True, index=True)
    name = Column(String, nullable=True)
    privacy_public = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    images = relationship("Image", back_populates="user")
