"""Controller for spotting endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas import AnimalSpottingsResponse, SpottingsResponse
from api.spottings.spotting_service import SpottingService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=SpottingsResponse,
    status_code=status.HTTP_200_OK,
    tags=["spottings"],
)
def get_spottings(
    latitude: float = Query(
        ...,
        description="Center latitude for location search (decimal degrees, e.g., 50.123)",
    ),
    longitude: float = Query(
        ...,
        description="Center longitude for location search (decimal degrees, e.g., 10.456)",
    ),
    distance_range: float = Query(
        ...,
        description="Maximum distance from center location in kilometers (km). Example: 5.0 for 5 km radius",
        gt=0,
    ),
    species: Optional[str] = Query(
        None,
        description="Filter by species name (case-insensitive). If provided, only returns spottings of this species.",
    ),
    time_start: Optional[datetime] = Query(
        None,
        description="Start timestamp for time range filter (ISO 8601 format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD). Inclusive. Example: 2024-01-01T00:00:00",
    ),
    time_end: Optional[datetime] = Query(
        None,
        description="End timestamp for time range filter (ISO 8601 format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD). Inclusive. Example: 2024-12-31T23:59:59",
    ),
    db: Session = Depends(get_db),
    spotting_service: SpottingService = Depends(SpottingService.factory),
):
    """Get images within a location and time range, grouped by location.

    Returns up to 5 most recent images per location that are:
    - Within the specified distance range from the center location (distance_range in kilometers)
    - Within the optional time range (if provided, using ISO 8601 datetime format)
    - Matching the optional species filter (if provided)

    Response is grouped by location, where each location contains:
    - Location data (id, name, coordinates, description)
    - List of images with detections (species, confidence, bounding boxes)
    - Note: Base64 image data is NOT included. Use /images/{image_id}/base64 to fetch it.

    Response also includes:
    - total_unique_species: Total number of unique species detected across all locations
    - total_spottings: Total number of animal detections across all locations

    Query Parameters:
        latitude: Center latitude in decimal degrees (e.g., 50.123)
        longitude: Center longitude in decimal degrees (e.g., 10.456)
        distance_range: Maximum distance in kilometers (km) from center location. Must be > 0.
        species: Optional species name filter (case-insensitive). If provided, only returns spottings of this species.
        time_start: Optional start timestamp in ISO 8601 format (inclusive).
                   Examples: "2024-01-01T00:00:00", "2024-01-01"
        time_end: Optional end timestamp in ISO 8601 format (inclusive).
                 Examples: "2024-12-31T23:59:59", "2024-12-31"

    Returns:
        Response with locations array, each containing location data and images (max 5 per location),
        plus total_unique_species and total_spottings counts

    Example:
        GET /spottings?latitude=50.0&longitude=10.0&distance_range=5.0&species=Red%20deer
        GET /spottings?latitude=50.0&longitude=10.0&distance_range=5.0&time_start=2024-01-01T00:00:00&time_end=2024-12-31T23:59:59&species=Wild%20boar
    """
    try:
        return spotting_service.get_spottings_by_location(
            db=db,
            latitude=latitude,
            longitude=longitude,
            distance_range=distance_range,
            species_filter=species,
            time_start=time_start,
            time_end=time_end,
        )
    except Exception as e:
        logger.error(f"Failed to get spottings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get spottings: {str(e)}",
        )


@router.get(
    "/animal",
    response_model=AnimalSpottingsResponse,
    status_code=status.HTTP_200_OK,
    tags=["spottings"],
)
def get_animal_spottings(
    limit: Optional[int] = Query(
        None,
        description="Maximum number of spottings to return. If not provided, returns all.",
        gt=0,
    ),
    offset: Optional[int] = Query(
        0,
        description="Number of spottings to skip for pagination.",
        ge=0,
    ),
    db: Session = Depends(get_db),
    spotting_service: SpottingService = Depends(SpottingService.factory),
):
    """Get all spottings with species "animal".

    Returns all animal detections that were classified as generic "animal" species.
    This is useful for finding detections that need further classification or review.

    Query Parameters:
        limit: Maximum number of spottings to return (optional, for pagination)
        offset: Number of spottings to skip (optional, for pagination)

    Returns:
        AnimalSpottingsResponse containing:
        - spottings: List of animal spottings with image and location information
        - total_count: Total number of animal spottings found

    Example:
        GET /spottings/animal
        GET /spottings/animal?limit=100&offset=0
    """
    try:
        return spotting_service.get_animal_spottings(db=db, limit=limit, offset=offset)
    except Exception as e:
        logger.error(f"Failed to get animal spottings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get animal spottings: {str(e)}",
        )
