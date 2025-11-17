"""Repository for location data access operations."""

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from src.api.images.image_models import Image
from src.api.locations.location_models import Location, Spotting

logger = logging.getLogger(__name__)


class LocationRepository:
    """Repository for location data access operations."""

    @staticmethod
    def get_all(db: Session) -> List[Location]:
        """Retrieve all locations.

        Args:
            db: Database session

        Returns:
            List of all locations
        """
        return db.query(Location).all()

    @staticmethod
    def get_by_id(db: Session, location_id: UUID) -> Optional[Location]:
        """Get specific location by ID.

        Args:
            db: Database session
            location_id: UUID of the location

        Returns:
            Location object or None if not found
        """
        return db.query(Location).filter(Location.id == str(location_id)).first()

    @staticmethod
    def create(
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

    @staticmethod
    def get_spottings_for_location(db: Session, location_id: UUID) -> List[Spotting]:
        """Get all spottings for images belonging to a location.

        Args:
            db: Database session
            location_id: UUID of the location

        Returns:
            List of Spotting objects
        """
        return (
            db.query(Spotting)
            .join(Image, Spotting.image_id == Image.id)
            .filter(Image.location_id == str(location_id))
            .all()
        )

    @staticmethod
    def get_all_with_statistics(
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
    def get_by_id_with_statistics(
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
    def get_locations_in_range(
        db: Session,
        latitude: float,
        longitude: float,
        distance_range: float,
    ) -> List[Location]:
        """Get all locations within a distance range from a center point.

        Uses Haversine formula to calculate distance.

        Args:
            db: Database session
            latitude: Center latitude
            longitude: Center longitude
            distance_range: Maximum distance in kilometers

        Returns:
            List of Location objects within range
        """
        from math import asin, cos, radians, sin, sqrt

        all_locations = db.query(Location).all()
        locations_in_range = []

        for location in all_locations:
            # Haversine formula
            lat1, lon1 = radians(latitude), radians(longitude)
            lat2, lon2 = radians(location.latitude), radians(location.longitude)

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            distance_km = 6371 * c  # Earth radius in km

            if distance_km <= distance_range:
                locations_in_range.append(location)

        return locations_in_range


class SpottingRepository:
    """Repository for spotting data access operations."""

    @staticmethod
    def create(
        db: Session,
        image_id: UUID,
        species: str,
        confidence: float,
        bbox_x: int,
        bbox_y: int,
        bbox_width: int,
        bbox_height: int,
        classification_model: str,
        is_uncertain: bool,
        detection_timestamp: Optional[datetime] = None,
    ) -> Spotting:
        """Create a new spotting.

        Args:
            db: Database session
            image_id: UUID of the image
            species: Species name
            confidence: Confidence score
            bbox_x: Bounding box x coordinate
            bbox_y: Bounding box y coordinate
            bbox_width: Bounding box width
            bbox_height: Bounding box height
            classification_model: Model used for classification
            is_uncertain: Whether the detection is uncertain
            detection_timestamp: Optional timestamp for the detection

        Returns:
            Created Spotting object
        """
        spotting = Spotting(
            image_id=str(image_id),
            species=species,
            confidence=confidence,
            bbox_x=bbox_x,
            bbox_y=bbox_y,
            bbox_width=bbox_width,
            bbox_height=bbox_height,
            classification_model=classification_model,
            is_uncertain=is_uncertain,
            detection_timestamp=detection_timestamp,
        )
        db.add(spotting)
        db.commit()
        db.refresh(spotting)
        return spotting

    @staticmethod
    def create_batch(
        db: Session,
        spottings_data: List[dict],
    ) -> List[Spotting]:
        """Create multiple spottings in a batch.

        Args:
            db: Database session
            spottings_data: List of spotting dictionaries

        Returns:
            List of created Spotting objects
        """
        spottings = []
        for data in spottings_data:
            spotting = Spotting(**data)
            db.add(spotting)
            spottings.append(spotting)

        db.commit()
        return spottings

    @staticmethod
    def get_by_image_id(db: Session, image_id: UUID) -> List[Spotting]:
        """Get all spottings for an image.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            List of Spotting objects
        """
        return db.query(Spotting).filter(Spotting.image_id == str(image_id)).all()

    @staticmethod
    def get_aggregated_by_location(db: Session) -> List:
        """Get aggregated spotting data grouped by location.

        Args:
            db: Database session

        Returns:
            List of aggregated results
        """
        from sqlalchemy import func

        return (
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

    @staticmethod
    def get_unique_species_by_location(db: Session, location_id: UUID) -> List[str]:
        """Get unique species for a location.

        Args:
            db: Database session
            location_id: UUID of the location

        Returns:
            List of unique species names
        """
        species_list = (
            db.query(Spotting.species)
            .join(Image, Spotting.image_id == Image.id)
            .filter(Image.location_id == str(location_id))
            .distinct()
            .all()
        )
        return [species[0] for species in species_list]

    @staticmethod
    def get_by_time_range(
        db: Session,
        start_time: datetime,
        end_time: datetime,
        location_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Tuple[str, datetime]]:
        """Get spottings within a time range.

        Args:
            db: Database session
            start_time: Start timestamp
            end_time: End timestamp
            location_id: Optional location ID filter
            limit: Optional limit on number of results

        Returns:
            List of (species, detection_timestamp) tuples
        """
        query = db.query(Spotting.species, Spotting.detection_timestamp).filter(
            Spotting.detection_timestamp >= start_time,
            Spotting.detection_timestamp <= end_time,
        )

        if location_id:
            query = query.join(Image, Spotting.image_id == Image.id).filter(
                Image.location_id == location_id
            )

        query = query.order_by(Spotting.detection_timestamp.desc())

        if limit is not None:
            query = query.limit(limit)

        return query.all()  # type: ignore[return-value]

    @staticmethod
    def get_by_species(db: Session, species: str) -> List[Spotting]:
        """Get all spottings for a specific species.

        Args:
            db: Database session
            species: Species name

        Returns:
            List of Spotting objects
        """
        return (
            db.query(Spotting)
            .filter(Spotting.species == species)
            .order_by(Spotting.detection_timestamp.desc())
            .all()
        )

    @staticmethod
    def get_animal_spottings_with_location(
        db: Session,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Tuple[List[Tuple[Spotting, Image, Location]], int]:
        """Get spottings with species "animal" joined with Image and Location.

        Args:
            db: Session
            limit: Optional limit on number of results
            offset: Optional offset for pagination

        Returns:
            Tuple of (list of (Spotting, Image, Location) tuples, total count)
        """
        query = (
            db.query(Spotting, Image, Location)
            .join(Image, Spotting.image_id == Image.id)
            .join(Location, Image.location_id == Location.id)
            .filter(Spotting.species == "animal")
            .order_by(Spotting.detection_timestamp.desc())
        )

        total_count = query.count()

        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return (query.all(), total_count)  # type: ignore[return-value]

    @staticmethod
    def get_location_statistics(
        db: Session,
        location_id: str,
        species_filter: Optional[str] = None,
        time_start: Optional[datetime] = None,
        time_end: Optional[datetime] = None,
    ) -> Tuple[int, int, int, int]:
        """Get statistics for a specific location.

        Args:
            db: Database session
            location_id: Location ID
            species_filter: Optional species filter (case-insensitive)
            time_start: Optional start timestamp filter
            time_end: Optional end timestamp filter

        Returns:
            Tuple of (unique_species_count, total_spottings_count, total_images_count, images_with_animals_count)
        """
        base_query = (
            db.query(Spotting)
            .join(Image, Spotting.image_id == Image.id)
            .filter(Image.location_id == location_id)
        )

        if species_filter:
            base_query = base_query.filter(
                Spotting.species.ilike(f"%{species_filter}%")
            )

        if time_start is not None:
            base_query = base_query.filter(Image.upload_timestamp >= time_start)
        if time_end is not None:
            base_query = base_query.filter(Image.upload_timestamp <= time_end)

        unique_species_count = (
            base_query.with_entities(Spotting.species).distinct().count()
        )
        total_spottings_count = base_query.count()

        images_query = db.query(Image).filter(Image.location_id == location_id)
        if time_start is not None:
            images_query = images_query.filter(Image.upload_timestamp >= time_start)
        if time_end is not None:
            images_query = images_query.filter(Image.upload_timestamp <= time_end)
        total_images_count = images_query.count()

        images_with_animals_query = (
            db.query(Image.id)
            .join(Spotting, Spotting.image_id == Image.id)
            .filter(Image.location_id == location_id)
        )

        if species_filter:
            images_with_animals_query = images_with_animals_query.filter(
                Spotting.species.ilike(f"%{species_filter}%")
            )

        if time_start is not None:
            images_with_animals_query = images_with_animals_query.filter(
                Image.upload_timestamp >= time_start
            )
        if time_end is not None:
            images_with_animals_query = images_with_animals_query.filter(
                Image.upload_timestamp <= time_end
            )

        images_with_animals_count = images_with_animals_query.distinct().count()

        return (
            unique_species_count,
            total_spottings_count,
            total_images_count,
            images_with_animals_count,
        )

    @staticmethod
    def get_global_statistics(
        db: Session,
        location_ids: List[str],
        species_filter: Optional[str] = None,
        time_start: Optional[datetime] = None,
        time_end: Optional[datetime] = None,
    ) -> Tuple[int, int]:
        """Get global statistics across multiple locations.

        Args:
            db: Database session
            location_ids: List of location IDs
            species_filter: Optional species filter (case-insensitive)
            time_start: Optional start timestamp filter
            time_end: Optional end timestamp filter

        Returns:
            Tuple of (unique_species_count, total_spottings_count)
        """
        if not location_ids:
            return (0, 0)

        global_base_query = (
            db.query(Spotting)
            .join(Image, Spotting.image_id == Image.id)
            .filter(Image.location_id.in_(location_ids))
        )

        if species_filter:
            global_base_query = global_base_query.filter(
                Spotting.species.ilike(f"%{species_filter}%")
            )

        if time_start is not None:
            global_base_query = global_base_query.filter(
                Image.upload_timestamp >= time_start
            )
        if time_end is not None:
            global_base_query = global_base_query.filter(
                Image.upload_timestamp <= time_end
            )

        unique_species_count = (
            global_base_query.with_entities(Spotting.species).distinct().count()
        )
        total_spottings_count = global_base_query.count()

        return (unique_species_count, total_spottings_count)
