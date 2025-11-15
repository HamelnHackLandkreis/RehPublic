"""Service for spotting-related business logic."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from api.locations.location_repository import LocationRepository

if TYPE_CHECKING:
    from api.images.image_repository import ImageRepository
    from api.images.image_service import ImageService
from api.images.images_schemas import (
    BoundingBoxResponse,
    DetectionResponse,
    SpottingImageResponse,
)
from api.locations.locations_schemas import (
    AnimalSpottingResponse,
    AnimalSpottingsResponse,
    LocationWithImagesResponse,
    SpottingsResponse,
)
from api.locations.location_repository import SpottingRepository

logger = logging.getLogger(__name__)


class SpottingService:
    """Service for spotting-related business logic."""

    def __init__(
        self,
        repository: Optional[SpottingRepository] = None,
        image_service: Optional[object] = None,
        image_repository: Optional[object] = None,
        location_repository: Optional[LocationRepository] = None,
    ) -> None:
        """Initialize spotting service.

        Args:
            repository: Optional spotting repository (will create default if not provided)
            image_service: Optional image service (will create default if not provided)
            image_repository: Optional image repository (will create default if not provided)
            location_repository: Optional location repository (will create default if not provided)
        """
        self.repository = repository or SpottingRepository()
        self._image_service = image_service
        self._image_repository = image_repository
        self.location_repository = location_repository or LocationRepository()

    @property
    def image_service(self) -> ImageService:
        """Lazy load image service to avoid circular imports."""
        if self._image_service is None:
            from api.images.image_service import ImageService

            self._image_service = ImageService(
                spotting_service=self,
                spotting_repository=self.repository,
            )
        return self._image_service  # type: ignore[return-value]

    @property
    def image_repository(self) -> ImageRepository:
        """Lazy load image repository to avoid circular imports."""
        if self._image_repository is None:
            from api.images.image_repository import ImageRepository

            self._image_repository = ImageRepository()
        return self._image_repository  # type: ignore[return-value]

    @classmethod
    def factory(cls) -> SpottingService:
        """Factory method to create SpottingService instance.

        Returns:
            SpottingService instance
        """
        return cls()

    def save_detections(
        self,
        db: Session,
        image_id: UUID,
        detections: List[Dict],
        detection_timestamp: Optional[datetime] = None,
    ) -> List:
        """Store detection results.

        Args:
            db: Database session
            image_id: UUID of the image
            detections: List of detection dictionaries
            detection_timestamp: Optional timestamp for the detection

        Returns:
            List of created Spotting objects
        """
        spottings_data = []
        for detection in detections:
            bbox = detection["bounding_box"]
            spottings_data.append(
                {
                    "image_id": str(image_id),
                    "species": detection["species"],
                    "confidence": detection["confidence"],
                    "bbox_x": bbox["x"],
                    "bbox_y": bbox["y"],
                    "bbox_width": bbox["width"],
                    "bbox_height": bbox["height"],
                    "classification_model": detection["classification_model"],
                    "is_uncertain": detection["is_uncertain"],
                    "detection_timestamp": detection_timestamp,
                }
            )

        return self.repository.create_batch(db, spottings_data)

    def get_spottings_by_location(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        distance_range: float,
        species_filter: Optional[str] = None,
        time_start: Optional[datetime] = None,
        time_end: Optional[datetime] = None,
    ) -> SpottingsResponse:
        """Get spottings grouped by location with statistics.

        Args:
            db: Database session
            latitude: Center latitude
            longitude: Center longitude
            distance_range: Maximum distance in kilometers
            species_filter: Optional species filter (case-insensitive)
            time_start: Optional start timestamp filter
            time_end: Optional end timestamp filter

        Returns:
            SpottingsResponse with locations and statistics
        """
        images = self.image_service.get_images_in_range(
            db=db,
            latitude=latitude,
            longitude=longitude,
            distance_range=distance_range,
            time_start=time_start,
            time_end=time_end,
            limit_per_location=5,
            species_filter=species_filter,
        )

        from collections import defaultdict

        images_by_location = defaultdict(list)
        location_map = {}

        for image in images:
            location_id = image.location_id

            if location_id not in location_map:
                location = self.location_repository.get_by_id(db, UUID(location_id))  # type: ignore[arg-type]
                if location:
                    location_map[location_id] = location

            spottings = image.spottings

            detections = []
            for spotting in spottings:
                if species_filter:
                    if species_filter.lower() not in spotting.species.lower():
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

            images_by_location[location_id].append(
                SpottingImageResponse(
                    image_id=UUID(image.id),  # type: ignore[arg-type]
                    location_id=UUID(image.location_id),  # type: ignore[arg-type]
                    upload_timestamp=image.upload_timestamp,  # type: ignore[arg-type]
                    detections=detections,
                )
            )

        locations_response = []
        location_ids_list = list(location_map.keys())

        for location_id, location_images in images_by_location.items():
            if location_id in location_map:
                location = location_map[location_id]

                (
                    unique_species_count,
                    total_spottings_count,
                    total_images_count,
                    images_with_animals_count,
                ) = self.repository.get_location_statistics(
                    db,
                    location_id,  # type: ignore[arg-type]
                    species_filter=species_filter,
                    time_start=time_start,
                    time_end=time_end,
                )

                locations_response.append(
                    LocationWithImagesResponse(
                        id=UUID(location.id),  # type: ignore[arg-type]
                        name=location.name,  # type: ignore[arg-type]
                        longitude=location.longitude,  # type: ignore[arg-type]
                        latitude=location.latitude,  # type: ignore[arg-type]
                        description=location.description,  # type: ignore[arg-type]
                        images=location_images,
                        total_images=total_images_count,
                        total_unique_species=unique_species_count,
                        total_spottings=total_spottings_count,
                        total_images_with_animals=images_with_animals_count,
                    )
                )

        (
            global_unique_species_count,
            global_total_spottings_count,
        ) = self.repository.get_global_statistics(
            db,
            location_ids_list,  # type: ignore[arg-type]
            species_filter=species_filter,
            time_start=time_start,
            time_end=time_end,
        )

        return SpottingsResponse(
            locations=locations_response,
            total_unique_species=global_unique_species_count,
            total_spottings=global_total_spottings_count,
        )

    def get_animal_spottings(
        self,
        db: Session,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> AnimalSpottingsResponse:
        """Get all spottings with species "animal".

        Args:
            db: Database session
            limit: Optional limit on number of results
            offset: Optional offset for pagination

        Returns:
            AnimalSpottingsResponse with spottings and total count
        """
        results, total_count = self.repository.get_animal_spottings_with_location(
            db, limit=limit, offset=offset
        )

        spottings = []
        for spotting, image, location in results:
            spottings.append(
                AnimalSpottingResponse(
                    spotting_id=UUID(spotting.id),  # type: ignore[arg-type]
                    image_id=UUID(image.id),  # type: ignore[arg-type]
                    location_id=UUID(location.id),  # type: ignore[arg-type]
                    location_name=location.name,  # type: ignore[arg-type]
                    species=spotting.species,  # type: ignore[arg-type]
                    confidence=spotting.confidence,  # type: ignore[arg-type]
                    bounding_box=BoundingBoxResponse(
                        x=spotting.bbox_x,  # type: ignore[arg-type]
                        y=spotting.bbox_y,  # type: ignore[arg-type]
                        width=spotting.bbox_width,  # type: ignore[arg-type]
                        height=spotting.bbox_height,  # type: ignore[arg-type]
                    ),
                    classification_model=spotting.classification_model,  # type: ignore[arg-type]
                    is_uncertain=spotting.is_uncertain,  # type: ignore[arg-type]
                    detection_timestamp=spotting.detection_timestamp,  # type: ignore[arg-type]
                    upload_timestamp=image.upload_timestamp,  # type: ignore[arg-type]
                )
            )

        return AnimalSpottingsResponse(spottings=spottings, total_count=total_count)

    def get_aggregated_spottings(self, db: Session) -> List[Dict]:
        """Get spotting summary grouped by location.

        Returns aggregated data with:
        - Location coordinates
        - Unique list of species detected at that location
        - Most recent spotting timestamp
        - Most recent image timestamp
        - Most recent image_id

        Args:
            db: Database session

        Returns:
            List of aggregated spotting dictionaries
        """
        results = self.repository.get_aggregated_by_location(db)

        aggregated_spottings = []
        for result in results:
            location_id = result.id  # type: ignore[assignment]

            animals = self.repository.get_unique_species_by_location(
                db,
                UUID(location_id),  # type: ignore[arg-type]
            )

            most_recent_images = self.image_repository.get_by_location_id(
                db, UUID(location_id), limit=1
            )

            spotting_data = {
                "pos": {"longitude": result.longitude, "latitude": result.latitude},
                "animals": animals,
                "ts_last_spotting": result.ts_last_spotting,
                "ts_last_image": result.ts_last_image,
                "image_id": most_recent_images[0].id if most_recent_images else None,
            }
            aggregated_spottings.append(spotting_data)

        return aggregated_spottings

    def get_statistics(
        self,
        db: Session,
        period: str = "day",
        granularity: Optional[str] = None,
        limit: Optional[int] = None,
        location_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get statistics for spottings grouped by time period.

        Args:
            db: Database session
            period: Time period range - "day", "week", "month", or "year"
            granularity: Grouping granularity - "hourly", "daily", or "weekly".
                         If None, defaults based on period (day=hourly, week/month=daily, year=weekly)
            limit: Maximum number of spottings to include before aggregation (optional)
            location_id: Optional location ID to filter spottings by location

        Returns:
            List of statistics dictionaries with time periods and species counts
        """
        now = datetime.utcnow()
        if period == "day":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now
        elif period == "week":
            start_time = now - timedelta(days=7)
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now
        elif period == "month":
            start_time = now - timedelta(days=30)
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now
        elif period == "year":
            start_time = now - timedelta(days=365)
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now
        else:
            raise ValueError(
                f"Invalid period: {period}. Must be 'day', 'week', 'month', or 'year'"
            )

        if granularity is None:
            if period == "day":
                granularity = "hourly"
            elif period == "year":
                granularity = "weekly"
            else:
                granularity = "daily"

        if granularity not in ["hourly", "daily", "weekly"]:
            raise ValueError(
                f"Invalid granularity: {granularity}. Must be 'hourly', 'daily', or 'weekly'"
            )

        if period == "day" and granularity == "weekly":
            raise ValueError("Cannot use 'weekly' granularity with 'day' period")

        if granularity == "hourly":
            time_delta = timedelta(hours=1)
        elif granularity == "daily":
            time_delta = timedelta(days=1)
        elif granularity == "weekly":
            time_delta = timedelta(weeks=1)

        spottings = self.repository.get_by_time_range(
            db, start_time, end_time, location_id, limit
        )

        period_data: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for species, detection_timestamp in spottings:
            if granularity == "hourly":
                period_start = detection_timestamp.replace(
                    minute=0, second=0, microsecond=0
                )
            elif granularity == "daily":
                period_start = detection_timestamp.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif granularity == "weekly":
                days_since_monday = detection_timestamp.weekday()
                period_start = detection_timestamp.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=days_since_monday)

            period_key = period_start.isoformat() + "Z"
            period_data[period_key][species] += 1

        statistics = []
        for period_start_str in sorted(period_data.keys()):
            period_start = datetime.fromisoformat(
                period_start_str.replace("Z", "+00:00")
            )
            period_end = period_start + time_delta - timedelta(seconds=1)

            species_counts = period_data[period_start_str]
            species_list = [
                {"name": species, "count": count}
                for species, count in sorted(species_counts.items())
            ]
            total_spottings = sum(species_counts.values())

            statistics.append(
                {
                    "start_time": period_start,
                    "end_time": period_end,
                    "species": species_list,
                    "total_spottings": total_spottings,
                }
            )

        return statistics
