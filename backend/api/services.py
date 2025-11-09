"""Service layer for business logic."""

import base64
import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from api.models import Image, Location, Spotting, UserDetection
from api.processor_integration import ProcessorClient

logger = logging.getLogger(__name__)


class LocationService:
    """Service for location-related operations."""

    @staticmethod
    def get_all_locations(db: Session) -> List[Location]:
        """Retrieve all locations.

        Args:
            db: Database session

        Returns:
            List of all locations
        """
        return db.query(Location).all()

    @staticmethod
    def get_all_locations_with_statistics(
        db: Session,
    ) -> Tuple[List[Tuple[Location, int, int]], int, int]:
        """Retrieve all locations with spotting statistics.

        Args:
            db: Database session

        Returns:
            Tuple containing:
            - List of tuples (location, unique_species_count, spottings_count) for each location
            - Total number of unique species detected across all locations
            - Total number of animal detections across all locations
        """
        locations = db.query(Location).all()

        # Calculate per-location statistics
        location_stats = []
        all_species = set()
        total_spottings_count = 0

        for location in locations:
            spottings = (
                db.query(Spotting)
                .join(Image, Spotting.image_id == Image.id)
                .filter(Image.location_id == location.id)
                .all()
            )
            unique_species = set(spotting.species for spotting in spottings)
            location_stats.append((location, len(unique_species), len(spottings)))
            all_species.update(unique_species)
            total_spottings_count += len(spottings)

        return location_stats, len(all_species), total_spottings_count

    @staticmethod
    def get_location_by_id(db: Session, location_id: UUID) -> Optional[Location]:
        """Get specific location by ID.

        Args:
            db: Database session
            location_id: UUID of the location

        Returns:
            Location object or None if not found
        """
        return db.query(Location).filter(Location.id == str(location_id)).first()

    @staticmethod
    def get_location_by_id_with_statistics(
        db: Session, location_id: UUID
    ) -> Optional[Tuple[Location, int, int]]:
        """Get specific location by ID with spotting statistics.

        Args:
            db: Database session
            location_id: UUID of the location

        Returns:
            Tuple containing:
            - Location object or None if not found
            - Total number of unique species detected at this location
            - Total number of animal detections at this location
        """
        location = db.query(Location).filter(Location.id == str(location_id)).first()
        if not location:
            return None

        # Get all spottings for images belonging to this location
        spottings = (
            db.query(Spotting)
            .join(Image, Spotting.image_id == Image.id)
            .filter(Image.location_id == str(location_id))
            .all()
        )

        unique_species = set(spotting.species for spotting in spottings)
        total_spottings_count = len(spottings)

        return location, len(unique_species), total_spottings_count

    @staticmethod
    def create_location(
        db: Session,
        name: str,
        longitude: float,
        latitude: float,
        description: Optional[str] = None,
    ) -> Location:
        """Create new location.

        Args:
            db: Database session
            name: Location name
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            description: Optional description

        Returns:
            Created Location object
        """
        location = Location(
            name=name, longitude=longitude, latitude=latitude, description=description
        )
        db.add(location)
        db.commit()
        db.refresh(location)
        return location


class ImageService:
    """Service for image-related operations."""

    def __init__(self, processor_client: Optional[ProcessorClient] = None):
        """Initialize image service.

        Args:
            processor_client: Optional processor client (will create default if not provided)
        """
        self.processor_client = processor_client or ProcessorClient(
            model_region="europe"
        )

    def save_image(
        self,
        db: Session,
        location_id: UUID,
        file_bytes: bytes,
        upload_timestamp: Optional[datetime] = None,
    ) -> Image:
        """Save uploaded image as base64.

        Args:
            db: Database session
            location_id: UUID of the location
            file_bytes: Raw image bytes
            upload_timestamp: Optional timestamp to use for upload (defaults to current time)

        Returns:
            Created Image object
        """
        # Encode to base64
        base64_data = base64.b64encode(file_bytes).decode("utf-8")

        # Create image record
        image_kwargs = {
            "location_id": str(location_id),
            "base64_data": base64_data,
            "processed": False,
        }
        # Always set upload_timestamp explicitly to ensure it's preserved
        if upload_timestamp is not None:
            image_kwargs["upload_timestamp"] = upload_timestamp
        else:
            image_kwargs["upload_timestamp"] = datetime.utcnow()

        image = Image(**image_kwargs)
        db.add(image)
        db.commit()
        db.refresh(image)
        return image

    def get_image_by_id(self, db: Session, image_id: UUID) -> Optional[Image]:
        """Retrieve image with detections.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            Image object or None if not found
        """
        return db.query(Image).filter(Image.id == str(image_id)).first()

    def process_image(
        self, db: Session, image: Image, location_name: str
    ) -> List[Dict]:
        """Trigger wildlife processor on image.

        Args:
            db: Database session
            image: Image object to process
            location_name: Name of the location

        Returns:
            List of detection dictionaries
        """
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image.base64_data)

        # Process image
        detections = self.processor_client.process_image_data(
            image_bytes=image_bytes,
            location_name=location_name,
            timestamp=image.upload_timestamp,
        )

        return detections

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on Earth in kilometers.

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point

        Returns:
            Distance in kilometers
        """
        # Earth radius in kilometers
        R = 6371.0

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    @staticmethod
    def get_images_in_range(
        db: Session,
        latitude: float,
        longitude: float,
        distance_range: float,
        time_start: Optional[datetime] = None,
        time_end: Optional[datetime] = None,
        limit_per_location: int = 3,
        species_filter: Optional[str] = None,
    ) -> List[Image]:
        """Get images within a distance range from a location and optional time range.
        Limits to the most recent N images per location.
        If species_filter is provided, only returns images that have spottings matching that species.

        Args:
            db: Database session
            latitude: Center latitude in decimal degrees
            longitude: Center longitude in decimal degrees
            distance_range: Maximum distance in kilometers (km) from center location
            time_start: Optional start timestamp in ISO 8601 format (inclusive)
            time_end: Optional end timestamp in ISO 8601 format (inclusive)
            limit_per_location: Maximum number of images to return per location (default: 3)
            species_filter: Optional species name filter (case-insensitive). If provided, only returns images with spottings matching this species.

        Returns:
            List of Image objects within the specified range (max limit_per_location per location)
        """
        # Get all locations
        all_locations = db.query(Location).all()

        # Filter locations within distance range
        locations_in_range = []
        for location in all_locations:
            distance = ImageService.haversine_distance(
                latitude, longitude, location.latitude, location.longitude
            )
            if distance <= distance_range:
                locations_in_range.append(location.id)

        if not locations_in_range:
            return []

        # Get top N images per location
        all_images = []
        for location_id in locations_in_range:
            # Query images for this location
            if species_filter:
                # If species filter is provided, join with Spotting and filter by species
                # This ensures we only get images that have spottings matching the species
                query = (
                    db.query(Image)
                    .join(Spotting, Image.id == Spotting.image_id)
                    .filter(Image.location_id == location_id)
                    .filter(Spotting.species.ilike(f"%{species_filter}%"))
                    .distinct()
                )
            else:
                query = db.query(Image).filter(Image.location_id == location_id)

            # Apply time range filters if provided
            if time_start is not None:
                query = query.filter(Image.upload_timestamp >= time_start)
            if time_end is not None:
                query = query.filter(Image.upload_timestamp <= time_end)

            # Get most recent N images for this location with spottings eagerly loaded
            location_images = (
                query.options(selectinload(Image.spottings))
                .order_by(Image.upload_timestamp.desc())
                .limit(limit_per_location)
                .all()
            )
            all_images.extend(location_images)

        # Sort all images by upload timestamp descending
        all_images.sort(key=lambda img: img.upload_timestamp, reverse=True)

        return all_images


class SpottingService:
    """Service for spotting-related operations."""

    @staticmethod
    def save_detections(
        db: Session,
        image_id: UUID,
        detections: List[Dict],
        detection_timestamp: Optional[datetime] = None,
    ) -> List[Spotting]:
        """Store detection results.

        Args:
            db: Database session
            image_id: UUID of the image
            detections: List of detection dictionaries

        Returns:
            List of created Spotting objects
        """
        spottings = []
        for detection in detections:
            bbox = detection["bounding_box"]
            spotting = Spotting(
                image_id=str(image_id),
                species=detection["species"],
                confidence=detection["confidence"],
                bbox_x=bbox["x"],
                bbox_y=bbox["y"],
                bbox_width=bbox["width"],
                bbox_height=bbox["height"],
                classification_model=detection["classification_model"],
                is_uncertain=detection["is_uncertain"],
                detection_timestamp=detection_timestamp,
            )
            db.add(spotting)
            spottings.append(spotting)

        db.commit()
        return spottings

    @staticmethod
    def get_aggregated_spottings(db: Session) -> List[Dict]:
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
        # Query to get aggregated data per location
        results = (
            db.query(
                Location.id,
                Location.longitude,
                Location.latitude,
                func.max(Spotting.detection_timestamp).label("ts_last_spotting"),
                func.max(Image.upload_timestamp).label("ts_last_image"),
            )
            .join(Image, Location.id == Image.location_id)
            .join(Spotting, Image.id == Spotting.image_id)
            .group_by(Location.id, Location.longitude, Location.latitude)
            .all()
        )

        aggregated_spottings = []
        for result in results:
            location_id = result.id

            # Get unique species for this location
            species_list = (
                db.query(Spotting.species)
                .join(Image, Spotting.image_id == Image.id)
                .filter(Image.location_id == location_id)
                .distinct()
                .all()
            )
            animals = [species[0] for species in species_list]

            # Get most recent image_id for this location
            most_recent_image = (
                db.query(Image.id)
                .filter(Image.location_id == location_id)
                .order_by(Image.upload_timestamp.desc())
                .first()
            )

            spotting_data = {
                "pos": {"longitude": result.longitude, "latitude": result.latitude},
                "animals": animals,
                "ts_last_spotting": result.ts_last_spotting,
                "ts_last_image": result.ts_last_image,
                "image_id": most_recent_image[0] if most_recent_image else None,
            }
            aggregated_spottings.append(spotting_data)

        return aggregated_spottings

    @staticmethod
    def get_statistics(
        db: Session,
        period: str = "day",
        granularity: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Get statistics for spottings grouped by time period.

        Args:
            db: Database session
            period: Time period range - "day", "week", "month", or "year"
            granularity: Grouping granularity - "hourly", "daily", or "weekly".
                         If None, defaults based on period (day=hourly, week/month=daily, year=weekly)
            limit: Maximum number of spottings to include before aggregation (optional)

        Returns:
            List of statistics dictionaries with time periods and species counts
        """
        # Calculate time range based on period
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

        # Determine granularity (default if not provided)
        if granularity is None:
            if period == "day":
                granularity = "hourly"
            elif period == "year":
                granularity = "weekly"
            else:
                granularity = "daily"

        # Validate granularity
        if granularity not in ["hourly", "daily", "weekly"]:
            raise ValueError(
                f"Invalid granularity: {granularity}. Must be 'hourly', 'daily', or 'weekly'"
            )

        # Validate granularity compatibility with period
        if period == "day" and granularity == "weekly":
            raise ValueError("Cannot use 'weekly' granularity with 'day' period")

        # Set time delta and grouping logic based on granularity
        if granularity == "hourly":
            time_delta = timedelta(hours=1)
        elif granularity == "daily":
            time_delta = timedelta(days=1)
        elif granularity == "weekly":
            time_delta = timedelta(weeks=1)

        # Query spottings in the time range
        query = (
            db.query(Spotting.species, Spotting.detection_timestamp)
            .filter(
                Spotting.detection_timestamp >= start_time,
                Spotting.detection_timestamp <= end_time,
            )
            .order_by(Spotting.detection_timestamp.desc())
        )

        # Apply limit if provided (limit before aggregation for performance)
        if limit is not None:
            query = query.limit(limit)

        spottings = query.all()

        # Group by time period and species
        period_data = defaultdict(lambda: defaultdict(int))

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

        # Convert to response format
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


class UserDetectionService:
    """Service for user detection operations."""

    @staticmethod
    def create_user_detection(
        db: Session,
        image_id: UUID,
        species: str,
        user_session_id: Optional[str] = None,
    ) -> "UserDetection":
        """Create a new user detection (manual identification).

        Args:
            db: Database session
            image_id: UUID of the image
            species: Species name identified by user
            user_session_id: Optional session ID for tracking

        Returns:
            Created UserDetection object
        """
        from api.models import UserDetection

        user_detection = UserDetection(
            image_id=str(image_id),
            species=species,
            user_session_id=user_session_id,
        )
        db.add(user_detection)
        db.commit()
        db.refresh(user_detection)
        return user_detection

    @staticmethod
    def get_user_detections_for_image(db: Session, image_id: UUID) -> Dict[str, any]:
        """Get user detection statistics for a specific image.

        Returns counts of each species identified by users, plus the automated detections.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            Dictionary with user_detections (species counts), total_user_detections, and automated_detections
        """
        from api.models import UserDetection, Spotting

        # Get user detections
        user_detections = (
            db.query(UserDetection)
            .filter(UserDetection.image_id == str(image_id))
            .all()
        )

        # Count species from user detections
        species_counts = defaultdict(int)
        for detection in user_detections:
            species_counts[detection.species] += 1

        # Get automated detections (from AI)
        automated_detections = (
            db.query(Spotting.species)
            .filter(Spotting.image_id == str(image_id))
            .distinct()
            .all()
        )
        automated_species = [species[0] for species in automated_detections]

        return {
            "user_detections": [
                {"name": species, "count": count}
                for species, count in sorted(species_counts.items())
            ],
            "total_user_detections": len(user_detections),
            "automated_detections": automated_species,
        }


class WikipediaService:
    """Service for fetching Wikipedia article data."""

    WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    WIKIPEDIA_BASE_URL = "https://en.wikipedia.org/wiki/"

    def __init__(self):
        """Initialize Wikipedia service with LRU cache."""
        self._cache = {}  # Manual cache for async function

    @lru_cache(maxsize=128)
    def _get_cached_article(self, title: str) -> Optional[Dict]:
        """Internal cache lookup method.

        This method serves as a cache key storage. The actual data
        is stored in self._cache to work with async operations.

        Args:
            title: Article title

        Returns:
            Cached article data or None
        """
        return self._cache.get(title)

    def _set_cached_article(self, title: str, data: Optional[Dict]) -> None:
        """Store article data in cache.

        Args:
            title: Article title
            data: Article data to cache
        """
        self._cache[title] = data
        # Trigger the lru_cache to register this key
        self._get_cached_article(title)

    async def fetch_article(self, title: str) -> Optional[Dict]:
        """Fetch a single Wikipedia article summary with caching.

        Args:
            title: Article title

        Returns:
            Dictionary with article data or None if not found
        """
        # Check cache first
        cached_data = self._cache.get(title)
        if cached_data is not None:
            logger.info(f"Wikipedia article retrieved from cache: {title}")
            return cached_data

        try:
            # Wikipedia requires a User-Agent header to prevent abuse
            headers = {
                "User-Agent": "WildlifeCameraAPI/0.1 (Educational project; contact: your-email@example.com)"
            }

            async with httpx.AsyncClient(headers=headers) as client:
                # Encode title for URL
                encoded_title = title.replace(" ", "_")
                url = f"{self.WIKIPEDIA_API_URL}{encoded_title}"

                response = await client.get(url, timeout=10.0)

                if response.status_code == 404:
                    logger.warning(f"Wikipedia article not found: {title}")
                    # Cache the None result to avoid repeated failed lookups
                    self._set_cached_article(title, None)
                    return None

                response.raise_for_status()
                data = response.json()

                # Extract relevant fields - use extract for longer text content
                article_data = {
                    "title": data.get("title", title),
                    "description": data.get(
                        "extract"
                    ),  # This contains the full paragraph(s)
                    "image_url": data.get("thumbnail", {}).get("source")
                    if "thumbnail" in data
                    else None,
                    "article_url": data.get("content_urls", {})
                    .get("desktop", {})
                    .get("page", f"{self.WIKIPEDIA_BASE_URL}{encoded_title}"),
                }

                # Cache the successful result
                self._set_cached_article(title, article_data)
                logger.info(f"Wikipedia article fetched and cached: {title}")

                return article_data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Wikipedia article '{title}': {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching Wikipedia article '{title}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching Wikipedia article '{title}': {e}")
            return None

    async def fetch_articles(self, titles: List[str]) -> List[Dict]:
        """Fetch multiple Wikipedia articles.

        Args:
            titles: List of article titles

        Returns:
            List of article data dictionaries (excluding failed fetches)
        """
        results = []

        for title in titles:
            article_data = await self.fetch_article(title)
            if article_data:
                results.append(article_data)

        return results


class UserDetectionService:
    """Service for user detection operations."""

    @staticmethod
    def create_user_detection(
        db: Session, image_id: UUID, species: str, user_session_id: Optional[str] = None
    ) -> UserDetection:
        """Create a new user detection.

        Args:
            db: Database session
            image_id: UUID of the image
            species: Name of the species detected by the user
            user_session_id: Optional session ID to track user submissions

        Returns:
            Created UserDetection object

        Raises:
            Exception: If database operation fails
        """
        try:
            user_detection = UserDetection(
                image_id=str(image_id),
                species=species,
                user_session_id=user_session_id,
            )

            db.add(user_detection)
            db.commit()
            db.refresh(user_detection)

            logger.info(
                f"Created user detection for image {image_id}, species: {species}"
            )
            return user_detection

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create user detection: {e}")
            raise

    @staticmethod
    def get_user_detections_for_image(db: Session, image_id: UUID) -> Dict:
        """Get aggregated user detection statistics for an image.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            Dictionary containing:
            - user_detections: List of species with counts
            - total_user_detections: Total number of user submissions
            - automated_detections: List of AI-detected species

        Raises:
            Exception: If database operation fails
        """
        try:
            # Get user detections grouped by species
            user_detections = (
                db.query(
                    UserDetection.species,
                    func.count(UserDetection.id).label("count"),
                )
                .filter(UserDetection.image_id == str(image_id))
                .group_by(UserDetection.species)
                .all()
            )

            # Get automated detections for comparison
            automated_detections = (
                db.query(Spotting.species)
                .filter(Spotting.image_id == str(image_id))
                .distinct()
                .all()
            )

            # Calculate total user detections
            total_user_detections = sum(count for _, count in user_detections)

            result = {
                "user_detections": [
                    {"name": species, "count": count}
                    for species, count in user_detections
                ],
                "total_user_detections": total_user_detections,
                "automated_detections": [
                    species for (species,) in automated_detections
                ],
            }

            logger.info(
                f"Retrieved user detection stats for image {image_id}: "
                f"{total_user_detections} total submissions"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to get user detection stats: {e}")
            raise
