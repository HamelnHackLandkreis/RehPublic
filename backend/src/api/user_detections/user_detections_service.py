"""Service for user detection business logic."""

import logging
from typing import Dict
from uuid import UUID

from sqlalchemy.orm import Session

from src.api.user_detections.user_detection_models import UserDetection
from src.api.user_detections.user_detection_repository import UserDetectionRepository

logger = logging.getLogger(__name__)


class UserDetectionService:
    """Service for user detection operations."""

    def __init__(self, repository: UserDetectionRepository | None = None) -> None:
        """Initialize user detection service.

        Args:
            repository: Optional user detection repository (will create default if not provided)
        """
        self.repository = repository or UserDetectionRepository()

    @classmethod
    def factory(cls) -> "UserDetectionService":
        """Factory method to create UserDetectionService instance.

        Returns:
            UserDetectionService instance
        """
        return cls()

    def create_user_detection(
        self,
        db: Session,
        image_id: UUID,
        species: str,
        user_session_id: str | None = None,
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
        return self.repository.create(
            db=db,
            image_id=image_id,
            species=species,
            user_session_id=user_session_id,
        )

    def get_user_detections_for_image(self, db: Session, image_id: UUID) -> Dict:
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
        return self.repository.get_stats_for_image(db=db, image_id=image_id)
