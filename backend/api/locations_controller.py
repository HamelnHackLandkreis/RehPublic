"""Controller for locations endpoints with images and filtering."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from api.database import get_db
from api.models import Image, Location, Spotting
from api.schemas import (
    BoundingBoxResponse,
    DetectionResponse,
    LocationResponse,
    LocationsResponse,
    SpottingImageResponse,
)
from api.services import ImageService, LocationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/locations2",
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
):
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

    location_service = LocationService()

    # Get locations (filtered by distance if parameters provided)
    if latitude is not None and longitude is not None and distance_range is not None:
        # Filter locations by distance
        all_locations = db.query(Location).all()
        locations_in_range = []
        for loc in all_locations:
            distance = ImageService.haversine_distance(
                latitude, longitude, loc.latitude, loc.longitude
            )
            if distance <= distance_range:
                locations_in_range.append(loc.id)

        if not locations_in_range:
            return LocationsResponse(
                locations=[],
                total_unique_species=0,
                total_spottings=0,
            )

        # Get locations with statistics for filtered locations
        locations_data = []
        all_species = set()
        total_spottings_count = 0

        for loc_id in locations_in_range:
            location = location_service.get_location_by_id(db, UUID(loc_id))
            if not location:
                continue

            spottings = (
                db.query(Spotting)
                .join(Image, Spotting.image_id == Image.id)
                .filter(Image.location_id == loc_id)
                .all()
            )
            unique_species = set(spotting.species for spotting in spottings)
            locations_data.append((location, len(unique_species), len(spottings)))
            all_species.update(unique_species)
            total_spottings_count += len(spottings)

        total_unique_species = len(all_species)
        total_spottings = total_spottings_count
    else:
        # Get all locations with statistics
        locations_data, total_unique_species, total_spottings = (
            location_service.get_all_locations_with_statistics(db)
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
    all_species_global = set()
    total_spottings_global = 0

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
                all_species_global.add(spotting.species)
                total_spottings_global += 1

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

    # Use global counts if filtering by location, otherwise use pre-calculated totals
    if latitude is not None and longitude is not None and distance_range is not None:
        final_total_unique_species = len(all_species_global)
        final_total_spottings = total_spottings_global
    else:
        final_total_unique_species = total_unique_species
        final_total_spottings = total_spottings

    return LocationsResponse(
        locations=locations_response,
        total_unique_species=final_total_unique_species,
        total_spottings=final_total_spottings,
    )
