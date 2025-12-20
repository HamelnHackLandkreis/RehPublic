"""Schemas for image pull source API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ImagePullSourceBase(BaseModel):
    """Base schema for image pull source."""

    name: str = Field(..., description="Unique name for this image source")
    location_id: UUID = Field(
        ..., description="UUID of the location to associate images with"
    )
    base_url: str = Field(..., description="Base URL to pull images from")
    auth_type: str = Field(
        default="basic", description="Authentication type: basic, header, or none"
    )
    auth_username: str | None = Field(
        None, description="Username for basic authentication"
    )
    auth_password: str | None = Field(
        None, description="Password for basic authentication"
    )
    auth_header: str | None = Field(
        None, description="Pre-encoded Authorization header value"
    )
    is_active: bool = Field(default=True, description="Whether this source is active")


class ImagePullSourceCreate(ImagePullSourceBase):
    """Schema for creating an image pull source.

    Note: user_id is NOT included here - it's extracted from the authenticated
    user in the controller, similar to image uploads.
    """

    pass


class ImagePullSourceResponse(ImagePullSourceBase):
    """Schema for image pull source response."""

    id: UUID
    user_id: UUID
    last_pulled_filename: str | None
    last_pull_timestamp: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PullSourceProcessResult(BaseModel):
    """Result of processing a single image pull source."""

    source_id: str
    source_name: str
    processed_count: int
    status: str
    processed_images: list[dict] | None = None
    error: str | None = None
