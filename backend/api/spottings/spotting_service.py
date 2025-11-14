"""Service for spotting-related business logic."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from api.spottings.spotting_repository import SpottingRepository

logger = logging.getLogger(__name__)


class SpottingService:
    """Service for spotting-related business logic."""

    def __init__(self, repository: Optional[SpottingRepository] = None):
        """Initialize spotting service.

        Args:
            repository: Optional spotting repository (will create default if not provided)
        """
        self.repository = repository or SpottingRepository()

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
        # Transform detection dictionaries to repository format (business logic)
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

        # Use repository for data access
        return self.repository.create_batch(db, spottings_data)

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
        # Get aggregated data from repository
        results = self.repository.get_aggregated_by_location(db)

        # Transform to response format (business logic)
        aggregated_spottings = []
        for result in results:
            location_id = result.id

            # Get unique species for this location
            animals = self.repository.get_unique_species_by_location(
                db, UUID(location_id)
            )

            # Get most recent image_id for this location
            # This is a business logic concern - we need to query Image model
            from api.images.image_repository import ImageRepository

            image_repo = ImageRepository()
            most_recent_images = image_repo.get_by_location_id(
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
        # Calculate time range based on period (business logic)
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

        # Determine granularity (default if not provided) - business logic
        if granularity is None:
            if period == "day":
                granularity = "hourly"
            elif period == "year":
                granularity = "weekly"
            else:
                granularity = "daily"

        # Validate granularity - business logic
        if granularity not in ["hourly", "daily", "weekly"]:
            raise ValueError(
                f"Invalid granularity: {granularity}. Must be 'hourly', 'daily', or 'weekly'"
            )

        # Validate granularity compatibility with period - business logic
        if period == "day" and granularity == "weekly":
            raise ValueError("Cannot use 'weekly' granularity with 'day' period")

        # Set time delta based on granularity - business logic
        if granularity == "hourly":
            time_delta = timedelta(hours=1)
        elif granularity == "daily":
            time_delta = timedelta(days=1)
        elif granularity == "weekly":
            time_delta = timedelta(weeks=1)

        # Get spottings from repository
        spottings = self.repository.get_by_time_range(
            db, start_time, end_time, location_id, limit
        )

        # Group by time period and species (business logic)
        period_data: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for spotting in spottings:
            # Truncate timestamp to the appropriate interval based on granularity
            if granularity == "hourly":
                period_start = spotting.detection_timestamp.replace(
                    minute=0, second=0, microsecond=0
                )
            elif granularity == "daily":
                period_start = spotting.detection_timestamp.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif granularity == "weekly":
                # Group by week (Monday as start of week)
                days_since_monday = spotting.detection_timestamp.weekday()
                period_start = spotting.detection_timestamp.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=days_since_monday)

            period_key = period_start.isoformat() + "Z"
            period_data[period_key][spotting.species] += 1

        # Convert to response format (business logic)
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
