"""Pydantic schemas for user detection-related request/response validation."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from pydantic import BaseModel

if TYPE_CHECKING:
    from api.statistics.statistics_schemas import SpeciesCountResponse


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
    user_detections: List["SpeciesCountResponse"]
    total_user_detections: int
    automated_detections: List[str]
