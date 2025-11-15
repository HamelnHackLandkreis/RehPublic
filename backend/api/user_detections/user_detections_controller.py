"""Controller for user detection endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.images.image_service import ImageService
from api.user_detections.user_detections_schemas import (
    UserDetectionCreate,
    UserDetectionResponse,
    UserDetectionStatsResponse,
)
from api.user_detections.user_detection_repository import UserDetectionRepository

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize dependencies
image_service = ImageService()
user_detection_repository = UserDetectionRepository()


@router.post(
    "",
    response_model=UserDetectionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["user-detections"],
)
def create_user_detection(
    detection: UserDetectionCreate,
    db: Session = Depends(get_db),
) -> UserDetectionResponse:
    """Submit a manual user identification for an image.

    This endpoint allows users to record what species they think they see in an image.
    These manual identifications are stored separately from automated AI detections
    and can be used for:
    - Validating AI detection accuracy
    - Collecting training data
    - Gamification (e.g., matching game where users identify animals)
    - Community engagement and citizen science

    Args:
        detection: User detection data including image_id, species, and optional session_id

    Returns:
        Created user detection with ID and timestamp

    Raises:
        HTTPException: 404 if image not found, 500 on server error

    Example:
        POST /user-detections
        {
            "image_id": "0812161d-dfc7-4f53-b3bd-1da415e5bbb6",
            "species": "Red deer",
            "user_session_id": "user-123-session-abc"
        }
    """
    # Validate that image exists
    image = image_service.get_image_by_id(db, detection.image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {detection.image_id} not found",
        )

    try:
        user_detection = user_detection_repository.create(
            db=db,
            image_id=detection.image_id,
            species=detection.species,
            user_session_id=detection.user_session_id,
        )

        return UserDetectionResponse(
            id=UUID(user_detection.id),  # type: ignore[arg-type]
            image_id=UUID(user_detection.image_id),  # type: ignore[arg-type]
            species=user_detection.species,  # type: ignore[arg-type]
            user_session_id=user_detection.user_session_id,  # type: ignore[arg-type]
            detection_timestamp=user_detection.detection_timestamp,  # type: ignore[arg-type]
        )
    except Exception as e:
        logger.error(f"Failed to create user detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user detection: {str(e)}",
        )


@router.get(
    "/{image_id}",
    response_model=UserDetectionStatsResponse,
    status_code=status.HTTP_200_OK,
    tags=["user-detections"],
)
def get_user_detection_stats(
    image_id: UUID,
    db: Session = Depends(get_db),
) -> UserDetectionStatsResponse:
    """Get user detection statistics for a specific image.

    Returns aggregated data showing:
    - What species users have identified (with counts)
    - Total number of user identifications
    - What species the AI detected automatically

    This is useful for:
    - Comparing user identifications with AI detections
    - Showing consensus among users
    - Validating detection accuracy
    - Displaying statistics in a matching game

    Args:
        image_id: UUID of the image

    Returns:
        Statistics comparing user detections with automated AI detections

    Raises:
        HTTPException: 404 if image not found

    Example Response:
        {
            "image_id": "0812161d-dfc7-4f53-b3bd-1da415e5bbb6",
            "user_detections": [
                {"name": "Red deer", "count": 15},
                {"name": "Wild boar", "count": 3}
            ],
            "total_user_detections": 18,
            "automated_detections": ["Red deer", "European badger"]
        }
    """
    # Validate that image exists
    image = image_service.get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )

    try:
        stats = user_detection_repository.get_stats_for_image(db, image_id)

        from api.statistics.statistics_schemas import SpeciesCountResponse

        return UserDetectionStatsResponse(
            image_id=image_id,
            user_detections=[
                SpeciesCountResponse(name=species["name"], count=species["count"])
                for species in stats["user_detections"]
            ],
            total_user_detections=stats["total_user_detections"],
            automated_detections=stats["automated_detections"],
        )
    except Exception as e:
        logger.error(f"Failed to get user detection stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user detection stats: {str(e)}",
        )
