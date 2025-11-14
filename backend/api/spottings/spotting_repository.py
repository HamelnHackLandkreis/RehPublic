"""Repository for spotting data access operations."""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from api.models import Image, Location, Spotting

logger = logging.getLogger(__name__)


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
            .filter(Image.location_id == location_id)
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
    ) -> List:
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

        return query.all()

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
