"""Repository for user detection data access operations."""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from api.models import Spotting, UserDetection

logger = logging.getLogger(__name__)


class UserDetectionRepository:
    """Repository for user detection data access operations."""

    @staticmethod
    def create(
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
    def get_by_image_id_grouped_by_species(db: Session, image_id: UUID) -> List:
        """Get user detections for an image grouped by species.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            List of (species, count) tuples
        """
        return (
            db.query(
                UserDetection.species,
                func.count(UserDetection.id).label("count"),
            )
            .filter(UserDetection.image_id == str(image_id))
            .group_by(UserDetection.species)
            .all()
        )

    @staticmethod
    def get_automated_detections_by_image_id(db: Session, image_id: UUID) -> List[str]:
        """Get automated detections (spottings) for an image.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            List of unique species names
        """
        automated_detections = (
            db.query(Spotting.species)
            .filter(Spotting.image_id == str(image_id))
            .distinct()
            .all()
        )
        return [species for (species,) in automated_detections]

    @staticmethod
    def get_stats_for_image(db: Session, image_id: UUID) -> Dict:
        """Get aggregated statistics for an image.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            Dictionary with user_detections, total_user_detections, and automated_detections

        Raises:
            Exception: If database operation fails
        """
        try:
            user_detections = (
                UserDetectionRepository.get_by_image_id_grouped_by_species(db, image_id)
            )
            automated_detections = (
                UserDetectionRepository.get_automated_detections_by_image_id(
                    db, image_id
                )
            )

            total_user_detections = sum(count for _, count in user_detections)

            result = {
                "user_detections": [
                    {"name": species, "count": count}
                    for species, count in user_detections
                ],
                "total_user_detections": total_user_detections,
                "automated_detections": automated_detections,
            }

            logger.info(
                f"Retrieved user detection stats for image {image_id}: "
                f"{total_user_detections} total submissions"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to get user detection stats: {e}")
            raise
