"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Location schemas
class LocationCreate(BaseModel):
    """Schema for creating a new location."""
    name: str
    longitude: float
    latitude: float
    description: Optional[str] = None


class LocationResponse(BaseModel):
    """Schema for location response."""
    id: UUID
    name: str
    longitude: float
    latitude: float
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# Image schemas
class ImageUploadResponse(BaseModel):
    """Schema for image upload response."""
    image_id: UUID
    location_id: UUID
    upload_timestamp: datetime
    detections_count: int


class BoundingBoxResponse(BaseModel):
    """Schema for bounding box coordinates."""
    x: int
    y: int
    width: int
    height: int


class DetectionResponse(BaseModel):
    """Schema for animal detection response."""
    species: str
    confidence: float
    bounding_box: BoundingBoxResponse
    classification_model: str
    is_uncertain: bool


class ImageDetailResponse(BaseModel):
    """Schema for detailed image response with detections."""
    image_id: UUID
    location_id: UUID
    raw: str  # base64 encoded image
    upload_timestamp: datetime
    detections: List[DetectionResponse]


# Spotting schemas
class SpottingLocationResponse(BaseModel):
    """Schema for aggregated spotting data by location."""
    pos: Dict[str, float]  # {"longitude": x, "latitude": y}
    animals: List[str]  # unique species names
    ts_last_spotting: datetime
    ts_last_image: datetime
    image_id: UUID
