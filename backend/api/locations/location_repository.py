"""Repository for location data access operations."""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from api.images.image_models import Image
from api.locations.location_models import Location
from api.spottings.spotting_models import Spotting

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
