"""Repository for image data access operations."""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from src.api.images.image_models import Image
from src.api.locations.location_models import Location, Spotting

logger = logging.getLogger(__name__)


class ImageRepository:
    """Repository for image data access operations."""

    @staticmethod
    def create(
        db: Session,
        location_id: UUID,
        base64_data: str,
        upload_timestamp: Optional[datetime] = None,
        processed: bool = False,
    ) -> Image:
        """Create new image record.

        Args:
            db: Database session
            location_id: UUID of the location
            base64_data: Base64 encoded image data
            upload_timestamp: Optional timestamp to use for upload (defaults to current time)
            processed: Whether the image has been processed

        Returns:
            Created Image object
        """
        image_kwargs = {
            "location_id": str(location_id),
            "base64_data": base64_data,
            "processed": processed,
        }
        if upload_timestamp is not None:
            image_kwargs["upload_timestamp"] = upload_timestamp
        else:
            image_kwargs["upload_timestamp"] = datetime.utcnow()

        image = Image(**image_kwargs)
        db.add(image)
        db.commit()
        db.refresh(image)
        return image

    @staticmethod
    def get_by_id(db: Session, image_id: UUID) -> Optional[Image]:
        """Retrieve image by ID.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            Image object or None if not found
        """
        return db.query(Image).filter(Image.id == str(image_id)).first()

    @staticmethod
    def get_by_location_id(
        db: Session,
        location_id: UUID,
        time_start: Optional[datetime] = None,
        time_end: Optional[datetime] = None,
        limit: Optional[int] = None,
        species_filter: Optional[str] = None,
    ) -> List[Image]:
        """Get images for a specific location with optional filters.

        Args:
            db: Database session
            location_id: UUID of the location
            time_start: Optional start timestamp filter
            time_end: Optional end timestamp filter
            limit: Optional limit on number of results
            species_filter: Optional species filter (case-insensitive)

        Returns:
            List of Image objects
        """
        if species_filter:
            query = (
                db.query(Image)
                .join(Spotting, Image.id == Spotting.image_id)
                .filter(Image.location_id == str(location_id))
                .filter(Spotting.species.ilike(f"%{species_filter}%"))
                .distinct()
            )
        else:
            query = db.query(Image).filter(Image.location_id == str(location_id))

        if time_start is not None:
            query = query.filter(Image.upload_timestamp >= time_start)
        if time_end is not None:
            query = query.filter(Image.upload_timestamp <= time_end)

        query = query.options(selectinload(Image.spottings)).order_by(
            Image.upload_timestamp.desc()
        )

        if limit is not None:
            query = query.limit(limit)

        return query.all()

    @staticmethod
    def get_all_locations(db: Session) -> List[Location]:
        """Get all locations.

        Args:
            db: Database session

        Returns:
            List of all Location objects
        """
        return db.query(Location).all()

    @staticmethod
    def update_processed(db: Session, image_id: UUID, processed: bool) -> None:
        """Update the processed status of an image.

        Args:
            db: Database session
            image_id: UUID of the image
            processed: New processed status
        """
        image = db.query(Image).filter(Image.id == str(image_id)).first()
        if image:
            image.processed = processed  # type: ignore[assignment]
            db.commit()
