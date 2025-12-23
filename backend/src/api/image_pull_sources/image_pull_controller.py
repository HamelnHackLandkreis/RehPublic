"""Controller for image pull source endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.image_pull_sources.image_pull_source_repository import (
    ImagePullSourceRepository,
)
from src.api.image_pull_sources.image_pull_schemas import (
    ImagePullSourceCreate,
    ImagePullSourceResponse,
    PullSourceProcessResult,
)
from src.api.image_pull_sources.image_pull_service import ImagePullService
from src.api.models import auth0_sub_to_uuid

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=ImagePullSourceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["image_pull_sources"],
)
def create_pull_source(
    request: Request,
    source_data: ImagePullSourceCreate,
    db: Session = Depends(get_db),
) -> ImagePullSourceResponse:
    """Create a new image pull source.

    Args:
        request: FastAPI request object
        source_data: Image pull source creation data
        db: Database session

    Returns:
        Created image pull source

    Raises:
        HTTPException: 401 if not authenticated
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    auth0_sub = request.state.user.sub
    user_id = auth0_sub_to_uuid(auth0_sub)

    repository = ImagePullSourceRepository()
    source = repository.create(
        db=db,
        name=source_data.name,
        user_id=user_id,
        location_id=source_data.location_id,
        base_url=source_data.base_url,
        auth_type=source_data.auth_type,
        auth_username=source_data.auth_username,
        auth_password=source_data.auth_password,
        auth_header=source_data.auth_header,
        is_active=source_data.is_active,
    )

    return ImagePullSourceResponse.model_validate(source)


@router.get(
    "/",
    response_model=list[ImagePullSourceResponse],
    status_code=status.HTTP_200_OK,
    tags=["image_pull_sources"],
)
def list_pull_sources(
    request: Request,
    db: Session = Depends(get_db),
) -> list[ImagePullSourceResponse]:
    """List all active image pull sources.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        List of image pull sources

    Raises:
        HTTPException: 401 if not authenticated
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    repository = ImagePullSourceRepository()
    sources = repository.get_all_active(db)

    return [ImagePullSourceResponse.model_validate(s) for s in sources]


@router.post(
    "/{source_id}/process",
    response_model=PullSourceProcessResult,
    status_code=status.HTTP_200_OK,
    tags=["image_pull_sources"],
)
def process_pull_source(
    request: Request,
    source_id: UUID,
    max_files: int = 10,
    db: Session = Depends(get_db),
) -> PullSourceProcessResult:
    """Manually trigger processing of a specific image pull source.

    Args:
        request: FastAPI request object
        source_id: UUID of the image pull source
        max_files: Maximum number of files to process
        db: Database session

    Returns:
        Processing result

    Raises:
        HTTPException: 401 if not authenticated, 404 if source not found
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    service = ImagePullService.factory()

    try:
        result = service.pull_and_process_source(
            db=db, source_id=source_id, max_files=max_files
        )
        return PullSourceProcessResult(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to process source {source_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process source: {str(e)}",
        )


@router.patch(
    "/{source_id}/toggle",
    response_model=ImagePullSourceResponse,
    status_code=status.HTTP_200_OK,
    tags=["image_pull_sources"],
)
def toggle_pull_source(
    request: Request,
    source_id: UUID,
    is_active: bool,
    db: Session = Depends(get_db),
) -> ImagePullSourceResponse:
    """Toggle active status of an image pull source.

    Args:
        request: FastAPI request object
        source_id: UUID of the image pull source
        is_active: New active status
        db: Database session

    Returns:
        Updated image pull source

    Raises:
        HTTPException: 401 if not authenticated, 404 if source not found
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    repository = ImagePullSourceRepository()
    source = repository.get_by_id(db, source_id)

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image pull source {source_id} not found",
        )

    repository.update_active_status(db, source_id, is_active)

    updated_source = repository.get_by_id(db, source_id)
    return ImagePullSourceResponse.model_validate(updated_source)
