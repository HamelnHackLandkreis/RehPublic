"""Pydantic schemas for image-related request/response validation."""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel


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
    processing_status: str  # uploading, detecting, completed, failed
    processed: bool


class ImageDetailResponse(BaseModel):
    """Schema for detailed image response with detections."""

    image_id: UUID
    location_id: UUID
    raw: str  # base64 encoded image
    upload_timestamp: datetime
    detections: List[DetectionResponse]
    processing_status: str  # uploading, detecting, completed, failed
    processed: bool


class ImageUploadResponse(BaseModel):
    """Schema for image upload response."""

    image_id: UUID
    location_id: UUID
    upload_timestamp: datetime
    detections_count: int
    detected_species: List[str]
    task_id: str | None = None
    processing_status: str  # uploading, detecting, completed, failed


class ImageStatusResponse(BaseModel):
    """Schema for image processing status response."""

    image_id: UUID
    processing_status: str  # uploading, detecting, completed, failed
    processed: bool
    detections_count: int
    detected_species: List[str]
    upload_timestamp: datetime


class ImageBase64Response(BaseModel):
    """Schema for image base64 data response."""

    image_id: UUID
    base64_data: str
