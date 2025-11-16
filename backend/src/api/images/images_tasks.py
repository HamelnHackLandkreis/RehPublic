"""Celery tasks for image processing - works like a controller."""

import logging
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID
from src.api.images.image_models import Image

# Import service here to avoid circular imports
from src.api.database import SessionLocal
from src.api.images.image_service import ImageService
from src.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="images.process_image", bind=True, max_retries=3)
def process_image_task(
    self,
    image_id: str,
    image_base64: str,
    model_region: str = "europe",
    timestamp: Optional[str] = None,
) -> Dict:
    """Process image using wildlife detection models.

    This task works like a controller - it receives the request and delegates
    to the service layer for business logic.

    Args:
        self: Celery task instance (bound)
        image_id: UUID of the image as string
        image_base64: Base64-encoded image data
        model_region: Regional model to use for classification
        timestamp: Optional ISO format timestamp string

    Returns:
        Dict with image_id, detections count, and success status
    """
    try:
        logger.info(f"Processing image {image_id} with region {model_region}")

        # Parse timestamp if provided
        detection_timestamp = None
        if timestamp:
            detection_timestamp = datetime.fromisoformat(timestamp)

        # Create database session
        db = SessionLocal()
        try:
            # Get image service
            image_service = ImageService.factory()

            # Process image using service (synchronous processing within task)

            # Create temporary image object for processing
            temp_image = Image()
            temp_image.id = image_id
            temp_image.base64_data = image_base64

            detections = image_service.process_image(db=db, image=temp_image)

            # Save detections using service
            if detections:
                image_service.spotting_service.save_detections(
                    db=db,
                    image_id=UUID(image_id),
                    detections=detections,
                    detection_timestamp=detection_timestamp,
                )

            # Mark image as processed
            image_service.mark_as_processed(db=db, image_id=UUID(image_id))

            db.commit()

            logger.info(
                f"Successfully processed image {image_id}: "
                f"found {len(detections)} detections"
            )

            return {
                "image_id": image_id,
                "detections_count": len(detections),
                "detected_species": [d["species"] for d in detections],
                "success": True,
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error(f"Error processing image {image_id}: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2**self.request.retries)
