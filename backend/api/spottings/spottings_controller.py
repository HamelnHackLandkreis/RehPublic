"""Controller for spotting endpoints."""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.images.image_service import ImageService
from api.locations.location_repository import LocationRepository
from api.models import Image, Location, Spotting
from api.schemas import (
    AnimalSpottingResponse,
    AnimalSpottingsResponse,
    BoundingBoxResponse,
    DetectionResponse,
    LocationWithImagesResponse,
    SpottingImageResponse,
    SpottingsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize dependencies
image_service = ImageService()
location_repository = LocationRepository()


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
    # Get images within range (limited to 5 per location)
    # If species filter is provided, only get images that have spottings matching that species
    images = image_service.get_images_in_range(
        db=db,
        latitude=latitude,
        longitude=longitude,
        distance_range=distance_range,
        time_start=time_start,
        time_end=time_end,
        limit_per_location=5,
        species_filter=species,
    )

    # Group images by location
    images_by_location = defaultdict(list)
    location_map = {}

    for image in images:
        location_id = image.location_id

        # Fetch location if not already cached
        if location_id not in location_map:
            location = location_repository.get_by_id(db, UUID(location_id))
            if location:
                location_map[location_id] = location

        # Get all spottings for this image
        # Spottings are already loaded via eager loading in get_images_in_range
        spottings = image.spottings

        # Convert spottings to detection responses
        # If species filter was applied, images are already filtered to only include those with matching spottings
        # But we still filter spottings here for display to show only matching spottings
        detections = []
        for spotting in spottings:
            # Apply species filter for display if provided
            if species:
                # Use case-insensitive partial matching (same pattern as query filter)
                if species.lower() not in spotting.species.lower():
                    continue

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

        # Add image (it's already filtered by the query if species filter was provided)
        images_by_location[location_id].append(
            SpottingImageResponse(
                image_id=UUID(image.id),
                location_id=UUID(image.location_id),
                upload_timestamp=image.upload_timestamp,
                detections=detections,
            )
        )

    # Build response with locations and their images
    locations_response = []
    location_ids_list = list(location_map.keys())

    for location_id, location_images in images_by_location.items():
        if location_id in location_map:
            location = location_map[location_id]

            # Calculate per-location statistics from ALL spottings at this location
            # (not just the returned images, to match /locations endpoint behavior)
            # Use SQL aggregations for efficiency
            base_query = (
                db.query(Spotting)
                .join(Image, Spotting.image_id == Image.id)
                .filter(Image.location_id == location_id)
            )

            # Apply species filter if provided
            if species:
                base_query = base_query.filter(Spotting.species.ilike(f"%{species}%"))

            # Apply time range filters if provided
            if time_start is not None:
                base_query = base_query.filter(Image.upload_timestamp >= time_start)
            if time_end is not None:
                base_query = base_query.filter(Image.upload_timestamp <= time_end)

            # Get unique species count using SQL DISTINCT COUNT aggregation
            location_unique_species_count = (
                base_query.with_entities(Spotting.species).distinct().count()
            )

            # Get total spottings count using SQL COUNT aggregation
            location_spottings_count = base_query.count()

            # Get total images count for this location (with filters applied)
            images_query = db.query(Image).filter(Image.location_id == location_id)
            if time_start is not None:
                images_query = images_query.filter(Image.upload_timestamp >= time_start)
            if time_end is not None:
                images_query = images_query.filter(Image.upload_timestamp <= time_end)
            total_images_count = images_query.count()

            # Count images with animals using SQL aggregation
            # Count distinct images that have spottings (with filters applied)
            images_with_animals_query = (
                db.query(Image.id)
                .join(Spotting, Spotting.image_id == Image.id)
                .filter(Image.location_id == location_id)
            )

            # Apply species filter if provided
            if species:
                images_with_animals_query = images_with_animals_query.filter(
                    Spotting.species.ilike(f"%{species}%")
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
                LocationWithImagesResponse(
                    id=UUID(location.id),
                    name=location.name,
                    longitude=location.longitude,
                    latitude=location.latitude,
                    description=location.description,
                    images=location_images,
                    total_images=total_images_count,
                    total_unique_species=location_unique_species_count,
                    total_spottings=location_spottings_count,
                    total_images_with_animals=images_with_animals,
                )
            )

    # Calculate global totals using SQL aggregations across all locations in range
    if location_ids_list:
        global_base_query = (
            db.query(Spotting)
            .join(Image, Spotting.image_id == Image.id)
            .filter(Image.location_id.in_(location_ids_list))
        )

        # Apply species filter if provided
        if species:
            global_base_query = global_base_query.filter(
                Spotting.species.ilike(f"%{species}%")
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
        global_unique_species_count = (
            global_base_query.with_entities(Spotting.species).distinct().count()
        )

        # Get global total spottings count using SQL COUNT aggregation
        global_total_spottings_count = global_base_query.count()
    else:
        global_unique_species_count = 0
        global_total_spottings_count = 0

    return SpottingsResponse(
        locations=locations_response,
        total_unique_species=global_unique_species_count,
        total_spottings=global_total_spottings_count,
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
        # Query all spottings with species "animal"
        query = (
            db.query(Spotting, Image, Location)
            .join(Image, Spotting.image_id == Image.id)
            .join(Location, Image.location_id == Location.id)
            .filter(Spotting.species == "animal")
            .order_by(Spotting.detection_timestamp.desc())
        )

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination if provided
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        # Execute query
        results = query.all()

        # Build response
        spottings = []
        for spotting, image, location in results:
            spottings.append(
                AnimalSpottingResponse(
                    spotting_id=UUID(spotting.id),
                    image_id=UUID(image.id),
                    location_id=UUID(location.id),
                    location_name=location.name,
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
                    detection_timestamp=spotting.detection_timestamp,
                    upload_timestamp=image.upload_timestamp,
                )
            )

        return AnimalSpottingsResponse(spottings=spottings, total_count=total_count)
    except Exception as e:
        logger.error(f"Failed to get animal spottings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get animal spottings: {str(e)}",
        )
