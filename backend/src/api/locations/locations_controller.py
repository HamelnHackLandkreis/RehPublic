"""Controller for location endpoints."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.images.image_service import ImageService
from src.api.locations.location_repository import LocationRepository
from src.api.locations.locations_service import SpottingService
from src.api.models import auth0_sub_to_uuid
from src.api.images.images_schemas import (
    BoundingBoxResponse,
    DetectionResponse,
    SpottingImageResponse,
)
from src.api.locations.locations_schemas import (
    LocationCreate,
    LocationResponse,
    LocationUpdate,
    SpottingsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize dependencies
location_repository = LocationRepository()
image_service = ImageService()


@router.get(
    "",
    response_model=SpottingsResponse,
    status_code=status.HTTP_200_OK,
    tags=["locations"],
)
def get_locations(
    request: Request,
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
    species: str | None = Query(
        None,
        description="Filter by species name (case-insensitive). If provided, only returns spottings of this species.",
    ),
    time_start: datetime | None = Query(
        None,
        description="Start timestamp for time range filter (ISO 8601 format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD). Inclusive. Example: 2024-01-01T00:00:00",
    ),
    time_end: datetime | None = Query(
        None,
        description="End timestamp for time range filter (ISO 8601 format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD). Inclusive. Example: 2024-12-31T23:59:59",
    ),
    only_my_images: bool = Query(
        False,
        description="If true, only returns images belonging to the authenticated user. Requires authentication.",
    ),
    db: Session = Depends(get_db),
    spotting_service: SpottingService = Depends(SpottingService.factory),
) -> SpottingsResponse:
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
        GET /locations?latitude=50.0&longitude=10.0&distance_range=5.0&species=Red%20deer
        GET /locations?latitude=50.0&longitude=10.0&distance_range=5.0&time_start=2024-01-01T00:00:00&time_end=2024-12-31T23:59:59&species=Wild%20boar
    """
    # Extract user ID from request state (set by authentication middleware)
    requesting_user_id = None
    if hasattr(request.state, "user"):
        requesting_user_id = auth0_sub_to_uuid(request.state.user.sub)

    try:
        return spotting_service.get_spottings_by_location(
            db=db,
            latitude=latitude,
            longitude=longitude,
            distance_range=distance_range,
            requesting_user_id=requesting_user_id,
            species_filter=species,
            time_start=time_start,
            time_end=time_end,
            only_my_images=only_my_images,
        )
    except Exception as e:
        logger.error(f"Failed to get locations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get locations: {str(e)}",
        )


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["locations"],
)
def create_location(
    location_data: LocationCreate, db: Session = Depends(get_db)
) -> LocationResponse:
    """Create a new camera location.

    Args:
        location_data: Location data including name, coordinates, and description

    Returns:
        Created location with generated ID
    """
    try:
        location = location_repository.create(
            db=db,
            name=location_data.name,
            longitude=location_data.longitude,
            latitude=location_data.latitude,
            description=location_data.description,
        )
        return LocationResponse(
            id=UUID(str(location.id)),
            name=str(location.name),
            longitude=float(location.longitude),
            latitude=float(location.latitude),
            description=str(location.description) if location.description else None,
            total_unique_species=0,
            total_spottings=0,
            images=[],
            total_images_with_animals=0,
        )
    except Exception as e:
        logger.error(f"Failed to create location: {e}")
        error_msg = str(e)

        # Handle duplicate location name
        if (
            "UNIQUE constraint failed: locations.name" in error_msg
            or "duplicate" in error_msg.lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Location with name '{location_data.name}' already exists",
            )

        # Generic error for other cases
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create location. Please check your input data.",
        )


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    tags=["locations"],
)
def get_location(
    request: Request, location_id: UUID, db: Session = Depends(get_db)
) -> LocationResponse:
    """Get specific location by ID with spotting statistics.

    Args:
        location_id: UUID of the location

    Returns:
        Location details with:
        - Location data (id, name, coordinates, description)
        - total_unique_species: Total number of unique species detected at this location
        - total_spottings: Total number of animal detections at this location

    Raises:
        HTTPException: 404 if location not found
    """
    result = location_repository.get_by_id_with_statistics(db, location_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found",
        )

    location, total_unique_species, total_spottings = result

    # Extract user ID from request state for privacy filtering
    requesting_user_id = None
    if hasattr(request.state, "user"):
        requesting_user_id = request.state.user.sub

    # Get up to 3 most recent images with spottings eagerly loaded and privacy filtering
    images = image_service.repository.get_by_location_id(
        db=db,
        location_id=location_id,
        requesting_user_id=requesting_user_id,
        limit=3,
    )

    # Convert images to SpottingImageResponse
    image_responses = []
    for image in images:
        spottings = image.spottings
        detections = []
        for spotting in spottings:
            detection = DetectionResponse(
                species=spotting.species,
                confidence=spotting.confidence,
                bounding_box=BoundingBoxResponse(
                    x=spotting.bbox_x,
                    y=spotting.bbox_y,
                    width=spotting.bbox_width,
                    height=spotting.bbox_height,
                ),
                classification_model=spotting.classification_model,
                is_uncertain=spotting.is_uncertain,
            )
            detections.append(detection)

        image_responses.append(
            SpottingImageResponse(
                image_id=UUID(str(image.id)),
                location_id=UUID(str(image.location_id)),
                upload_timestamp=image.upload_timestamp,  # type: ignore[arg-type]
                detections=detections,
                processing_status=str(image.processing_status),
                processed=bool(image.processed),
            )
        )

    # Count images with animals
    images_with_animals = sum(
        1 for img_resp in image_responses if len(img_resp.detections) > 0
    )

    return LocationResponse(
        id=UUID(str(location.id)),
        name=str(location.name),
        longitude=float(location.longitude),
        latitude=float(location.latitude),
        description=str(location.description) if location.description else None,
        total_unique_species=total_unique_species,
        total_spottings=total_spottings,
        images=image_responses,
        total_images_with_animals=images_with_animals,
    )


@router.patch(
    "/{location_id}",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
    tags=["locations"],
)
def update_location(
    location_id: UUID,
    location_data: LocationUpdate,
    db: Session = Depends(get_db),
) -> LocationResponse:
    """Update an existing camera location.

    Args:
        location_id: UUID of the location to update
        location_data: Location data to update (all fields optional)

    Returns:
        Updated location with statistics

    Raises:
        HTTPException: 404 if location not found, 409 if name conflict
    """
    try:
        location = location_repository.update(
            db=db,
            location_id=location_id,
            name=location_data.name,
            longitude=location_data.longitude,
            latitude=location_data.latitude,
            description=location_data.description,
        )

        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location with id {location_id} not found",
            )

        # Get statistics for the updated location
        result = location_repository.get_by_id_with_statistics(db, location_id)
        if result:
            _, total_unique_species, total_spottings = result
        else:
            total_unique_species = 0
            total_spottings = 0

        return LocationResponse(
            id=UUID(str(location.id)),
            name=str(location.name),
            longitude=float(location.longitude),
            latitude=float(location.latitude),
            description=str(location.description) if location.description else None,
            total_unique_species=total_unique_species,
            total_spottings=total_spottings,
            images=[],
            total_images_with_animals=0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update location: {e}")
        error_msg = str(e)

        # Handle duplicate location name
        if (
            "UNIQUE constraint failed: locations.name" in error_msg
            or "duplicate" in error_msg.lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Location with name '{location_data.name}' already exists",
            )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to update location. Please check your input data.",
        )


@router.get(
    "/{location_id}/image-count",
    status_code=status.HTTP_200_OK,
    tags=["locations"],
)
def get_location_image_count(
    location_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """Get the number of images for a location.

    Args:
        location_id: UUID of the location

    Returns:
        Object with image_count field

    Raises:
        HTTPException: 404 if location not found
    """
    location = location_repository.get_by_id(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found",
        )

    image_count = location_repository.get_image_count(db=db, location_id=location_id)
    return {"image_count": image_count}


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_200_OK,
    tags=["locations"],
)
def delete_location(
    location_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """Delete an existing camera location and all its images.

    Args:
        location_id: UUID of the location to delete

    Returns:
        Object with deleted_images count

    Raises:
        HTTPException: 404 if location not found
    """
    try:
        deleted, image_count = location_repository.delete(db=db, location_id=location_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location with id {location_id} not found",
            )

        return {"deleted_images": image_count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete location: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete location.",
        )
