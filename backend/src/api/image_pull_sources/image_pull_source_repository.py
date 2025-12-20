"""Repository for image pull source database operations."""

from uuid import UUID

from sqlalchemy.orm import Session

from src.api.image_pull_sources.image_pull_source_models import ImagePullSource


class ImagePullSourceRepository:
    """Repository for image pull source CRUD operations."""

    def get_all_active(self, db: Session) -> list[ImagePullSource]:
        """Get all active image pull sources.

        Args:
            db: Database session

        Returns:
            List of active ImagePullSource objects
        """
        return (
            db.query(ImagePullSource)
            .filter(ImagePullSource.is_active == True)  # noqa: E712
            .all()
        )

    def get_by_id(self, db: Session, source_id: UUID) -> ImagePullSource | None:
        """Get image pull source by ID.

        Args:
            db: Database session
            source_id: UUID of the source

        Returns:
            ImagePullSource object or None if not found
        """
        return (
            db.query(ImagePullSource)
            .filter(ImagePullSource.id == str(source_id))
            .first()
        )

    def update_last_pulled(self, db: Session, source_id: UUID, filename: str) -> None:
        """Update the last pulled filename and timestamp.

        Args:
            db: Database session
            source_id: UUID of the source
            filename: Name of the last pulled file
        """
        from datetime import datetime

        source = self.get_by_id(db, source_id)
        if not source:
            return

        source.last_pulled_filename = filename
        source.last_pull_timestamp = datetime.utcnow()
        db.commit()

    def create(
        self,
        db: Session,
        name: str,
        user_id: UUID,
        location_id: UUID,
        base_url: str,
        auth_type: str = "basic",
        auth_username: str | None = None,
        auth_password: str | None = None,
        auth_header: str | None = None,
        is_active: bool = True,
    ) -> ImagePullSource:
        """Create a new image pull source.

        Args:
            db: Database session
            name: Name of the source
            user_id: UUID of the user
            location_id: UUID of the location
            base_url: Base URL to pull images from
            auth_type: Authentication type (basic, header, none)
            auth_username: Username for basic auth
            auth_password: Password for basic auth
            auth_header: Auth header value for header auth
            is_active: Whether the source is active

        Returns:
            Created ImagePullSource object
        """
        source = ImagePullSource(
            name=name,
            user_id=str(user_id),
            location_id=str(location_id),
            base_url=base_url,
            auth_type=auth_type,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_header=auth_header,
            is_active=is_active,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    def update_active_status(
        self, db: Session, source_id: UUID, is_active: bool
    ) -> None:
        """Update the active status of a source.

        Args:
            db: Database session
            source_id: UUID of the source
            is_active: New active status
        """
        source = self.get_by_id(db, source_id)
        if not source:
            return

        source.is_active = is_active
        db.commit()

    def get_by_user_id(self, db: Session, user_id: UUID) -> list[ImagePullSource]:
        """Get all image pull sources owned by a specific user.

        Args:
            db: Database session
            user_id: UUID of the user

        Returns:
            List of ImagePullSource objects owned by the user
        """
        return (
            db.query(ImagePullSource)
            .filter(ImagePullSource.user_id == str(user_id))
            .all()
        )
