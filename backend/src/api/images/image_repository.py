"""Repository for image data access operations."""

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from src.api.images.image_models import Image
from src.api.locations.location_models import Location, Spotting
from src.api.users.user_models import User

logger = logging.getLogger(__name__)


class ImageRepository:
    """Repository for image data access operations."""

    @staticmethod
    def create(
        db: Session,
        location_id: UUID,
        base64_data: str,
        user_id: UUID,
        upload_timestamp: datetime | None = None,
        processed: bool = False,
        processing_status: str = "uploading",
        celery_task_id: str | None = None,
    ) -> Image:
        """Create new image record.

        Args:
            db: Database session
            location_id: UUID of the location
            base64_data: Base64 encoded image data
            user_id: UUID of the user uploading the image
            upload_timestamp: Timestamp to use for upload (defaults to current time) or None
            processed: Whether the image has been processed
            processing_status: Processing status (uploading, detecting, completed, failed)
            celery_task_id: Celery task ID for async processing or None

        Returns:
            Created Image object
        """
        image_kwargs = {
            "location_id": str(location_id),
            "base64_data": base64_data,
            "user_id": str(user_id),
            "processed": processed,
            "processing_status": processing_status,
            "celery_task_id": celery_task_id,
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
    def update_status(
        db: Session,
        image_id: UUID,
        processing_status: str,
        processed: bool = False,
    ) -> Image | None:
        """Update image processing status.

        Args:
            db: Database session
            image_id: UUID of the image
            processing_status: New processing status
            processed: Whether processing is complete

        Returns:
            Updated Image object or None if not found
        """
        image = db.query(Image).filter(Image.id == str(image_id)).first()
        if image:
            image.processing_status = processing_status
            image.processed = processed
            db.commit()
            db.refresh(image)
        return image

    @staticmethod
    def get_by_id(db: Session, image_id: UUID) -> Image | None:
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
        requesting_user_id: UUID | None = None,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
        limit: int | None = None,
        species_filter: str | None = None,
        only_my_images: bool = False,
    ) -> List[Image]:
        """Get images for a specific location with optional filters and privacy rules.

        Args:
            db: Database session
            location_id: UUID of the location
            requesting_user_id: UUID of the user making the request (for privacy filtering) or None
            time_start: Start timestamp filter or None
            time_end: End timestamp filter or None
            limit: Limit on number of results or None
            species_filter: Species filter (case-insensitive) or None

        Returns:
            List of Image objects (filtered by privacy rules if requesting_user_id provided)
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

        # Apply privacy filtering if requesting_user_id is provided
        if requesting_user_id:
            requesting_user_id_str = str(requesting_user_id)
            if only_my_images:
                # Only show images belonging to the requesting user
                query = query.filter(Image.user_id == requesting_user_id_str)
            else:
                # Show public images OR images belonging to the requesting user
                query = query.outerjoin(User, Image.user_id == User.id).filter(
                    User.privacy_public | (Image.user_id == requesting_user_id_str)
                )

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
    def get_visible_images(
        db: Session,
        requesting_user_id: UUID,
        location_ids: List[str] | None = None,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
        species_filter: str | None = None,
    ) -> List[Image]:
        """Get images visible to the requesting user based on privacy settings.

        Returns images where:
        - User's privacy_public is True, OR
        - Image belongs to the requesting user

        Args:
            db: Database session
            requesting_user_id: UUID of the user making the request
            location_ids: List of location IDs to filter by or None
            time_start: Start timestamp filter or None
            time_end: End timestamp filter or None
            species_filter: Species filter (case-insensitive) or None

        Returns:
            List of Image objects visible to the requesting user
        """
        if species_filter:
            query = (
                db.query(Image)
                .join(Spotting, Image.id == Spotting.image_id)
                .filter(Spotting.species.ilike(f"%{species_filter}%"))
                .distinct()
            )
        else:
            query = db.query(Image)

        # Apply privacy filtering
        requesting_user_id_str = str(requesting_user_id)
        query = query.outerjoin(User, Image.user_id == User.id).filter(
            User.privacy_public | (Image.user_id == requesting_user_id_str)
        )

        if location_ids:
            query = query.filter(Image.location_id.in_(location_ids))

        if time_start is not None:
            query = query.filter(Image.upload_timestamp >= time_start)
        if time_end is not None:
            query = query.filter(Image.upload_timestamp <= time_end)

        query = query.options(selectinload(Image.spottings)).order_by(
            Image.upload_timestamp.desc()
        )

        return query.all()

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
