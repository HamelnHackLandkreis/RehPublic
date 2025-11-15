"""Controller for image endpoints."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from api.database import get_db
from api.images.image_service import ImageService
from api.images.images_schemas import ImageDetailResponse, ImageUploadResponse

logger = logging.getLogger(__name__)

router = APIRouter()
upload_router = APIRouter()
ImageService


@upload_router.post(
    "/{location_id}/image",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["images"],
)
async def upload_image(
    location_id: UUID,
    file: UploadFile = File(...),
    upload_timestamp: Optional[datetime] = Query(
        None,
        description="Optional ISO 8601 timestamp for the upload (e.g., 2024-01-01T12:00:00). If not provided, current time is used.",
    ),
    db: Session = Depends(get_db),
    image_service: ImageService = Depends(ImageService.factory),
):
    """Upload an image to a specific location and process it for animal detection.

    This endpoint:
    1. Validates the location exists
    2. Saves the image as base64 in the database
    3. Synchronously processes the image using the wildlife processor
    4. Stores all detected animals in the spottings table
    5. Returns the image ID and detection count

    Args:
        location_id: UUID of the location
        file: Uploaded image file
        upload_timestamp: Optional ISO 8601 timestamp for the upload
        db: Database session
        image_service: Image service instance

    Returns:
        Image upload response with image_id and detection count

    Raises:
        HTTPException: 404 if location not found, 500 on processing error
    """
    try:
        file_bytes = await file.read()

        result = image_service.upload_and_process_image(
            db, location_id, file_bytes, upload_timestamp
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to upload and process image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}",
        )


@router.get(
    "/{image_id}",
    response_model=ImageDetailResponse,
    status_code=status.HTTP_200_OK,
    tags=["images"],
)
def get_image(
    image_id: UUID,
    db: Session = Depends(get_db),
    image_service: ImageService = Depends(ImageService.factory),
):
    """Get image with detection data.

    Returns the base64-encoded image along with all detected animals
    including species, confidence scores, and bounding boxes.

    Args:
        image_id: UUID of the image
        db: Database session
        image_service: Image service instance

    Returns:
        Image details with base64 data and detections

    Raises:
        HTTPException: 404 if image not found
    """
    result = image_service.get_image_with_detections(db, image_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )

    return result


@router.get(
    "/{image_id}/base64",
    status_code=status.HTTP_200_OK,
    tags=["images"],
)
def get_image_base64(
    image_id: UUID,
    db: Session = Depends(get_db),
    image_service: ImageService = Depends(ImageService.factory),
):
    """Get image directly by image ID for use in img src tags.

    Returns the image as raw bytes with proper content-type headers.
    This endpoint can be used directly in HTML img src tags:
    <img src="/images/{image_id}/base64" />

    Args:
        image_id: UUID of the image
        db: Database session
        image_service: Image service instance

    Returns:
        Raw image bytes with appropriate image content-type (image/jpeg, image/png, etc.)

    Raises:
        HTTPException: 404 if image not found, 500 if image decoding fails
    """
    result = image_service.get_image_bytes(db, image_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )

    image_bytes, content_type = result

    return Response(
        content=image_bytes,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        },
    )
