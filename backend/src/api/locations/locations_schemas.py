"""Pydantic schemas for location-related request/response validation."""

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from api.images.images_schemas import BoundingBoxResponse, SpottingImageResponse

if TYPE_CHECKING:
    pass


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
    total_unique_species: int
    total_spottings: int
    images: List[SpottingImageResponse]
    total_images_with_animals: int

    model_config = ConfigDict(from_attributes=True)


class LocationsResponse(BaseModel):
    """Schema for locations list response with totals."""

    locations: List[LocationResponse]
    total_unique_species: int
    total_spottings: int


class SpottingLocationResponse(BaseModel):
    """Schema for aggregated spotting data by location."""

    pos: Dict[str, float]  # {"longitude": x, "latitude": y}
    animals: List[str]  # unique species names
    ts_last_spotting: datetime
    ts_last_image: datetime
    image_id: UUID


class LocationWithImagesResponse(BaseModel):
    """Schema for location with its images."""

    id: UUID
    name: str
    longitude: float
    latitude: float
    description: Optional[str]
    images: List[SpottingImageResponse]
    total_images: int
    total_unique_species: int
    total_spottings: int
    total_images_with_animals: int


class SpottingsResponse(BaseModel):
    """Schema for spottings endpoint response grouped by location."""

    locations: List[LocationWithImagesResponse]
    total_unique_species: int
    total_spottings: int


class AnimalSpottingResponse(BaseModel):
    """Schema for individual animal spotting response."""

    spotting_id: UUID
    image_id: UUID
    location_id: UUID
    location_name: str
    species: str
    confidence: float
    bounding_box: "BoundingBoxResponse"
    classification_model: str
    is_uncertain: bool
    detection_timestamp: datetime
    upload_timestamp: datetime


class AnimalSpottingsResponse(BaseModel):
    """Schema for list of animal spottings response."""

    spottings: List[AnimalSpottingResponse]
    total_count: int
