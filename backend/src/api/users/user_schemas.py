"""Pydantic schemas for user API endpoints."""

from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Response schema for user data."""

    id: str
    email: str | None = None
    name: str | None = None
    privacy_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PrivacyUpdateRequest(BaseModel):
    """Request schema for updating privacy settings."""

    privacy_public: bool
