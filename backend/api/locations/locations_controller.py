"""Controller for location endpoints."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from api.database import get_db
from api.images.image_service import ImageService
from api.locations.location_repository import LocationRepository
from api.images.image_models import Image
from api.locations.location_models import Location
from api.spottings.spotting_models import Spotting
from api.schemas import (
    BoundingBoxResponse,
    DetectionResponse,
    LocationCreate,
    LocationResponse,
    LocationsResponse,
    SpottingImageResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize dependencies
location_repository = LocationRepository()
image_service = ImageService()


@router.get(
    "",
    response_model=LocationsResponse,
    status_code=status.HTTP_200_OK,
    tags=["locations"],
)
def get_locations(
    latitude: Optional[float] = Query(
        None,
        description="Center latitude for location filter (decimal degrees, e.g., 50.123). If provided, longitude and distance_range are required.",
    ),
    longitude: Optional[float] = Query(
        None,
        description="Center longitude for location filter (decimal degrees, e.g., 10.456). If provided, latitude and distance_range are required.",
    ),
    distance_range: Optional[float] = Query(
        None,
        description="Maximum distance from center location in kilometers (km). Required if latitude/longitude are provided. Example: 5.0 for 5 km radius",
        gt=0,
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
) -> LocationsResponse:
    """Get camera locations with spotting statistics and images.

    Returns locations with:
    - Location data (id, name, coordinates, description)
    - Spotting statistics (total_unique_species, total_spottings)
    - Up to 3 most recent images per location with detections
    - total_images_with_animals count per location

    Optional filters:
    - latitude/longitude/distance_range: Filter locations within distance range
    - time_start/time_end: Filter images by upload timestamp

    Returns:
        LocationsResponse containing:
        - locations: List of locations with images and statistics
        - total_unique_species: Total number of unique species detected across all locations
        - total_spottings: Total number of animal detections across all locations
    """
    # Validate filter parameters
    if (
        latitude is not None or longitude is not None or distance_range is not None
    ) and (latitude is None or longitude is None or distance_range is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If filtering by location, latitude, longitude, and distance_range must all be provided",
        )

    # Get locations (filtered by distance if parameters provided)
    if latitude is not None and longitude is not None and distance_range is not None:
        # Filter locations by distance
        all_locations = db.query(Location).all()
        locations_in_range = []
        for loc in all_locations:
            distance = image_service.haversine_distance(
                latitude,
                longitude,
                loc.latitude,
                loc.longitude,  # type: ignore[arg-type]
            )
            if distance <= distance_range:
                locations_in_range.append(loc.id)  # type: ignore[arg-type]

        if not locations_in_range:
            return LocationsResponse(
                locations=[],
                total_unique_species=0,
                total_spottings=0,
            )

        # Get locations with statistics for filtered locations using SQL aggregations
        locations_data = []
        location_ids_for_global = []

        for loc_id in locations_in_range:
            location = location_repository.get_by_id(db, UUID(loc_id))  # type: ignore[arg-type]
            if not location:
                continue

            location_ids_for_global.append(loc_id)

            # Use SQL aggregations for per-location statistics
            base_query = (
                db.query(Spotting)
                .join(Image, Spotting.image_id == Image.id)
                .filter(Image.location_id == loc_id)
            )

            # Apply time range filters if provided
            if time_start is not None:
                base_query = base_query.filter(Image.upload_timestamp >= time_start)
            if time_end is not None:
                base_query = base_query.filter(Image.upload_timestamp <= time_end)

            # Get unique species count using SQL DISTINCT COUNT aggregation
            unique_species_count = (
                base_query.with_entities(Spotting.species).distinct().count()
            )

            # Get total spottings count using SQL COUNT aggregation
            spottings_count = base_query.count()

            locations_data.append((location, unique_species_count, spottings_count))

        # Calculate global totals using SQL aggregations
        if location_ids_for_global:
            global_base_query = (
                db.query(Spotting)
                .join(Image, Spotting.image_id == Image.id)
                .filter(Image.location_id.in_(location_ids_for_global))
            )

            # Apply time range filters if provided
            if time_start is not None:
                global_base_query = global_base_query.filter(
                    Image.upload_timestamp >= time_start
                )
            if time_end is not None:
                global_base_query = global_base_query.filter(
                    Image.upload_timestamp <= time_end
                )

            # Get global unique species count using SQL DISTINCT COUNT aggregation
            total_unique_species = (
                global_base_query.with_entities(Spotting.species).distinct().count()
            )

            # Get global total spottings count using SQL COUNT aggregation
            total_spottings = global_base_query.count()
        else:
            total_unique_species = 0
            total_spottings = 0
    else:
        # Get all locations with statistics
        # If time filters are applied, recalculate using SQL aggregations
        if time_start is not None or time_end is not None:
            locations_data = []
            all_location_ids = []

            # Get all locations
            all_locations = db.query(Location).all()

            for location in all_locations:
                all_location_ids.append(location.id)

                # Use SQL aggregations for per-location statistics with time filters
                base_query = (
                    db.query(Spotting)
                    .join(Image, Spotting.image_id == Image.id)
                    .filter(Image.location_id == location.id)
                )

                # Apply time range filters
                if time_start is not None:
                    base_query = base_query.filter(Image.upload_timestamp >= time_start)
                if time_end is not None:
                    base_query = base_query.filter(Image.upload_timestamp <= time_end)

                # Get unique species count using SQL DISTINCT COUNT aggregation
                unique_species_count = (
                    base_query.with_entities(Spotting.species).distinct().count()
                )

                # Get total spottings count using SQL COUNT aggregation
                spottings_count = base_query.count()

                locations_data.append((location, unique_species_count, spottings_count))

            # Calculate global totals using SQL aggregations
            if all_location_ids:
                global_base_query = (
                    db.query(Spotting)
                    .join(Image, Spotting.image_id == Image.id)
                    .filter(Image.location_id.in_(all_location_ids))
                )

                # Apply time range filters
                if time_start is not None:
                    global_base_query = global_base_query.filter(
                        Image.upload_timestamp >= time_start
                    )
                if time_end is not None:
                    global_base_query = global_base_query.filter(
                        Image.upload_timestamp <= time_end
                    )

                # Get global unique species count using SQL DISTINCT COUNT aggregation
                total_unique_species = (
                    global_base_query.with_entities(Spotting.species).distinct().count()
                )

                # Get global total spottings count using SQL COUNT aggregation
                total_spottings = global_base_query.count()
            else:
                total_unique_species = 0
                total_spottings = 0
        else:
            # No time filters - use pre-calculated totals
            locations_data, total_unique_species, total_spottings = (
                location_repository.get_all_with_statistics(db)
            )

    # Get images for each location (up to 3 per location)
    location_images_map = {}
    for location, _, _ in locations_data:
        query = db.query(Image).filter(Image.location_id == location.id)

        # Apply time range filters if provided
        if time_start is not None:
            query = query.filter(Image.upload_timestamp >= time_start)
        if time_end is not None:
            query = query.filter(Image.upload_timestamp <= time_end)

        # Get most recent 3 images with spottings eagerly loaded
        images = (
            query.options(selectinload(Image.spottings))
            .order_by(Image.upload_timestamp.desc())
            .limit(3)
            .all()
        )
        location_images_map[location.id] = images

    # Build response with locations, images, and statistics
    locations_response = []

    for location, loc_unique_species, loc_spottings in locations_data:
        images = location_images_map.get(location.id, [])

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
                    image_id=UUID(image.id),  # type: ignore[arg-type]
                    location_id=UUID(image.location_id),  # type: ignore[arg-type]
                    upload_timestamp=image.upload_timestamp,  # type: ignore[arg-type]
                    detections=detections,
                )
            )

        # Count images with animals using SQL aggregation
        # Count distinct images that have spottings (with filters applied)
        images_with_animals_query = (
            db.query(Image.id)
            .join(Spotting, Spotting.image_id == Image.id)
            .filter(Image.location_id == location.id)
        )

        # Apply time range filters if provided
        if time_start is not None:
            images_with_animals_query = images_with_animals_query.filter(
                Image.upload_timestamp >= time_start
            )
        if time_end is not None:
            images_with_animals_query = images_with_animals_query.filter(
                Image.upload_timestamp <= time_end
            )

        images_with_animals = images_with_animals_query.distinct().count()

        locations_response.append(
            LocationResponse(
                id=UUID(location.id),
                name=location.name,
                longitude=location.longitude,
                latitude=location.latitude,
                description=location.description,
                total_unique_species=loc_unique_species,
                total_spottings=loc_spottings,
                images=image_responses,
                total_images_with_animals=images_with_animals,
            )
        )

    # Use SQL-aggregated totals (already calculated above)
    final_total_unique_species = total_unique_species
    final_total_spottings = total_spottings

    return LocationsResponse(
        locations=locations_response,
        total_unique_species=final_total_unique_species,
        total_spottings=final_total_spottings,
    )


@router.post(
    "/",
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
            id=UUID(location.id),
            name=location.name,
            longitude=location.longitude,
            latitude=location.latitude,
            description=location.description,
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
def get_location(location_id: UUID, db: Session = Depends(get_db)) -> LocationResponse:
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

    # Get up to 3 most recent images with spottings eagerly loaded
    images = (
        db.query(Image)
        .filter(Image.location_id == str(location_id))
        .options(selectinload(Image.spottings))
        .order_by(Image.upload_timestamp.desc())
        .limit(3)
        .all()
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
                image_id=UUID(image.id),
                location_id=UUID(image.location_id),
                upload_timestamp=image.upload_timestamp,
                detections=detections,
            )
        )

    # Count images with animals
    images_with_animals = sum(
        1 for img_resp in image_responses if len(img_resp.detections) > 0
    )

    return LocationResponse(
        id=UUID(location.id),
        name=location.name,
        longitude=location.longitude,
        latitude=location.latitude,
        description=location.description,
        total_unique_species=total_unique_species,
        total_spottings=total_spottings,
        images=image_responses,
        total_images_with_animals=images_with_animals,
    )
