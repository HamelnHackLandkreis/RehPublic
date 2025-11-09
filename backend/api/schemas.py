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


# Image schemas (defined before LocationResponse to avoid forward reference)
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


class SpottingImageResponse(BaseModel):
    """Schema for spotting image response without base64 data."""

    image_id: UUID
    location_id: UUID
    upload_timestamp: datetime
    detections: List[DetectionResponse]


class ImageDetailResponse(BaseModel):
    """Schema for detailed image response with detections."""

    image_id: UUID
    location_id: UUID
    raw: str  # base64 encoded image
    upload_timestamp: datetime
    detections: List[DetectionResponse]


class ImageUploadResponse(BaseModel):
    """Schema for image upload response."""

    image_id: UUID
    location_id: UUID
    upload_timestamp: datetime
    detections_count: int
    detected_species: List[str]


class ImageBase64Response(BaseModel):
    """Schema for image base64 data response."""

    image_id: UUID
    base64_data: str


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


# Spotting schemas
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
    total_images_with_animals: int


class SpottingsResponse(BaseModel):
    """Schema for spottings endpoint response grouped by location."""

    locations: List[LocationWithImagesResponse]
    total_unique_species: int
    total_spottings: int


# Wikipedia schemas
class WikipediaArticleResponse(BaseModel):
    """Schema for Wikipedia article response."""

    title: str
    description: Optional[str]
    image_url: Optional[str]
    article_url: str


class WikipediaArticlesRequest(BaseModel):
    """Schema for Wikipedia articles request."""

    titles: List[str]  # List of article titles to fetch


# Statistics schemas
class SpeciesCountResponse(BaseModel):
    """Schema for species count in statistics."""

    name: str
    count: int


class TimePeriodStatisticsResponse(BaseModel):
    """Schema for statistics for a time period."""

    start_time: datetime
    end_time: datetime
    species: List[SpeciesCountResponse]
    total_spottings: int


class StatisticsResponse(BaseModel):
    """Schema for statistics endpoint response."""

    statistics: List[TimePeriodStatisticsResponse]


# User Detection schemas
class UserDetectionCreate(BaseModel):
    """Schema for creating a user detection."""

    image_id: UUID
    species: str
    user_session_id: Optional[str] = None


class UserDetectionResponse(BaseModel):
    """Schema for user detection response."""

    id: UUID
    image_id: UUID
    species: str
    user_session_id: Optional[str]
    detection_timestamp: datetime


class UserDetectionStatsResponse(BaseModel):
    """Schema for user detection statistics response."""

    image_id: UUID
    user_detections: List[SpeciesCountResponse]
    total_user_detections: int
    automated_detections: List[str]


# Animal Spotting schemas
class AnimalSpottingResponse(BaseModel):
    """Schema for individual animal spotting response."""

    spotting_id: UUID
    image_id: UUID
    location_id: UUID
    location_name: str
    species: str
    confidence: float
    bounding_box: BoundingBoxResponse
    classification_model: str
    is_uncertain: bool
    detection_timestamp: datetime
    upload_timestamp: datetime


class AnimalSpottingsResponse(BaseModel):
    """Schema for list of animal spottings response."""

    spottings: List[AnimalSpottingResponse]
    total_count: int
