"""Service for image-related business logic."""

from __future__ import annotations

import base64
import logging
import math
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from src.adapters.image_processor_adapter import ProcessorClient
from src.api.images.image_models import Image
from src.api.images.image_repository import ImageRepository
from src.api.locations.location_repository import LocationRepository
from src.api.images.s3_service import S3Service

if TYPE_CHECKING:
    from src.api.locations.location_repository import SpottingRepository
    from src.api.locations.locations_service import SpottingService
from src.api.images.images_schemas import (
    BoundingBoxResponse,
    DetectionResponse,
    ImageDetailResponse,
    ImageUploadResponse,
)

logger = logging.getLogger(__name__)


class ImageService:
    """Service for image-related business logic."""

    def __init__(
        self,
        repository: ImageRepository | None = None,
        location_repository: LocationRepository | None = None,
        spotting_repository: object | None = None,
        spotting_service: object | None = None,
        processor_client: ProcessorClient | None = None,
        s3_service: S3Service | None = None,
    ) -> None:
        """Initialize image service.

        Args:
            repository: Optional image repository (will create default if not provided)
            location_repository: Optional location repository (will create default if not provided)
            spotting_repository: Optional spotting repository (will create default if not provided)
            spotting_service: Optional spotting service (will create default if not provided)
            processor_client: Optional processor client (will create default if not provided)
            s3_service: Optional S3 service (will create default if not provided)
        """
        self.repository = repository or ImageRepository()
        self.location_repository = location_repository or LocationRepository()
        self._spotting_repository = spotting_repository
        self._spotting_service = spotting_service
        self.processor_client = processor_client or ProcessorClient(
            model_region="europe"
        )
        self.s3_service = s3_service or S3Service()

    @property
    def spotting_repository(self) -> SpottingRepository:
        """Lazy load spotting repository to avoid circular imports."""
        if self._spotting_repository is None:
            from src.api.locations.location_repository import SpottingRepository

            self._spotting_repository = SpottingRepository()
        return self._spotting_repository  # type: ignore[return-value]

    @property
    def spotting_service(self) -> SpottingService:
        """Lazy load spotting service to avoid circular imports."""
        if self._spotting_service is None:
            from src.api.locations.locations_service import SpottingService

            self._spotting_service = SpottingService(
                image_service=self,
                image_repository=self.repository,
            )
        return self._spotting_service  # type: ignore[return-value]

    @classmethod
    def factory(cls) -> ImageService:
        """Factory method to create ImageService instance.

        Returns:
            ImageService instance
        """
        return cls()

    def save_image(
        self,
        db: Session,
        location_id: UUID,
        file_bytes: bytes,
        user_id: UUID,
        upload_timestamp: datetime | None = None,
        celery_task_id: str | None = None,
    ) -> Image:
        """Save uploaded image to S3 and create DB record.

        Args:
            db: Database session
            location_id: UUID of the location
            file_bytes: Raw image bytes
            user_id: UUID of the user uploading the image
            upload_timestamp: Optional timestamp to use for upload (defaults to current time)
            celery_task_id: Optional Celery task ID for async processing

        Returns:
            Created Image object
        """
        # Generate object key
        timestamp_str = (upload_timestamp or datetime.utcnow()).strftime(
            "%Y%m%d_%H%M%S"
        )
        s3_key = f"location_{location_id}/{timestamp_str}_{user_id}.jpg"

        # Upload to S3
        self.s3_service.upload_file(file_bytes, s3_key, content_type="image/jpeg")

        return self.repository.create(
            db=db,
            location_id=location_id,
            base64_data=None,  # No longer storing base64
            user_id=user_id,
            upload_timestamp=upload_timestamp,
            processed=False,
            processing_status="uploading",
            celery_task_id=celery_task_id,
            s3_key=s3_key,
        )

    def get_image_by_id(self, db: Session, image_id: UUID) -> Image | None:
        """Retrieve image by ID.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            Image object or None if not found
        """
        return self.repository.get_by_id(db, image_id)

    def get_image_with_detections(
        self, db: Session, image_id: UUID
    ) -> ImageDetailResponse | None:
        """Get image with detection data.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            ImageDetailResponse or None if image not found
        """
        image = self.repository.get_by_id(db, image_id)
        if not image:
            return None

        spottings = self.spotting_repository.get_by_image_id(db, image_id)

        detections = []
        for spotting in spottings:
            detection = DetectionResponse(
                species=spotting.species,  # type: ignore[arg-type]
                confidence=spotting.confidence,  # type: ignore[arg-type]
                bounding_box=BoundingBoxResponse(
                    x=spotting.bbox_x,  # type: ignore[arg-type]
                    y=spotting.bbox_y,  # type: ignore[arg-type]
                    width=spotting.bbox_width,  # type: ignore[arg-type]
                    height=spotting.bbox_height,  # type: ignore[arg-type]
                ),
                classification_model=spotting.classification_model,  # type: ignore[arg-type]
                is_uncertain=spotting.is_uncertain,  # type: ignore[arg-type]
            )
            detections.append(detection)

        # Retrieve image content for base64 response (compatibility)
        try:
            image_bytes, _ = self.get_image_bytes(db, image_id)  # type: ignore
            raw_data = base64.b64encode(image_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to retrieve image content for {image_id}: {e}")
            raw_data = ""

        return ImageDetailResponse(
            image_id=UUID(str(image.id)),  # type: ignore[arg-type]
            location_id=UUID(str(image.location_id)),  # type: ignore[arg-type]
            raw=raw_data,
            upload_timestamp=image.upload_timestamp,  # type: ignore[arg-type]
            detections=detections,
            processing_status=str(image.processing_status) or "completed",  # type: ignore[arg-type]
            processed=bool(image.processed),  # type: ignore[arg-type]
        )

    def get_image_bytes(self, db: Session, image_id: UUID) -> Tuple[bytes, str] | None:
        """Get image bytes and content type.

        Args:
            db: Database session
            image_id: UUID of the image

        Returns:
            Tuple of (image_bytes, content_type) or None if image not found
        """
        image = self.repository.get_by_id(db, image_id)
        if not image:
            return None

        try:
            # Type casting for static analysis, though SQLAlchemy models return python types at runtime
            s3_key = str(image.s3_key) if image.s3_key else None
            base64_data = str(image.base64_data) if image.base64_data else None

            if s3_key:
                image_bytes = self.s3_service.get_file(s3_key)
            elif base64_data:
                image_bytes = base64.b64decode(base64_data)
            else:
                raise ValueError("No image data found (neither S3 key nor base64)")
        except Exception as e:
            logger.error(f"Failed to retrieve image {image_id}: {e}")
            raise ValueError(f"Failed to retrieve image data: {e}")

        content_type = self._detect_content_type(image_bytes)

        return (image_bytes, content_type)

    @staticmethod
    def _detect_content_type(image_bytes: bytes) -> str:
        """Detect image content type from magic bytes.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Content type string (e.g., 'image/jpeg')
        """
        content_type = "image/jpeg"
        if len(image_bytes) >= 4:
            if image_bytes[:4] == b"\x89PNG":
                content_type = "image/png"
            elif image_bytes[:3] == b"GIF":
                content_type = "image/gif"
            elif (
                len(image_bytes) >= 12
                and image_bytes[:4] == b"RIFF"
                and image_bytes[8:12] == b"WEBP"
            ):
                content_type = "image/webp"

        return content_type

    def process_image(self, db: Session, image: Image) -> List[Dict]:
        """Trigger wildlife processor on image synchronously.

        Args:
            db: Database session
            image: Image object to process

        Returns:
            List of detection dictionaries
        """
        s3_key = str(image.s3_key) if image.s3_key else None
        base64_data = str(image.base64_data) if image.base64_data else None

        if s3_key:
            image_bytes = self.s3_service.get_file(s3_key)
        elif base64_data:
            image_bytes = base64.b64decode(base64_data)
        else:
            raise ValueError("No image data available for processing")

        detections = self.processor_client.process_image_data(image_bytes=image_bytes)

        return detections

    def upload_and_process_image(
        self,
        db: Session,
        location_id: UUID,
        file_bytes: bytes,
        user_id: UUID,
        upload_timestamp: datetime | None = None,
        async_processing: bool = True,
    ) -> ImageUploadResponse:
        """Upload and process an image.

        Args:
            db: Database session
            location_id: UUID of the location
            file_bytes: Raw image bytes
            user_id: UUID of the user uploading the image
            upload_timestamp: Optional timestamp to use for upload
            async_processing: If True, process image asynchronously with Celery (default: True)

        Returns:
            ImageUploadResponse with upload results

        Raises:
            ValueError: If location not found
        """
        location = self.location_repository.get_by_id(db, location_id)
        if not location:
            raise ValueError(f"Location with id {location_id} not found")

        # Encode bytes to base64 string for passing to async task (Celery serializer friendly)
        # Note: Ideally we'd pass the S3 key to the worker, but keeping legacy adapter signature for now
        # Actually, passing base64 is heavy. We should optimize this later to pass S3 key.
        # For now, we are saving to S3 first, so we have the key.

        image = self.save_image(
            db=db,
            location_id=location_id,
            file_bytes=file_bytes,
            user_id=user_id,
            upload_timestamp=upload_timestamp,
            celery_task_id=None,  # Will be set below if async
        )

        if async_processing:
            logger.info(
                f"Queuing async processing for image {image.id} at location {location.name}"
            )

            # TODO: Update ProcessorClient to accept s3_key to avoid passing large payload
            # For now, we must read back from S3 or re-use file_bytes to pass base64 to the legacy adapter
            image_base64 = base64.b64encode(file_bytes).decode("utf-8")

            # Use adapter to dispatch async task
            task_id = self.processor_client.process_image_async(
                image_id=UUID(str(image.id)),  # type: ignore[arg-type]
                image_base64=image_base64,  # Still passing base64 to worker for now
                model_region="europe",
                timestamp=upload_timestamp,
            )

            # Update image with task_id and set status to detecting
            image.celery_task_id = task_id  # type: ignore
            image.processing_status = "detecting"  # type: ignore
            db.commit()
            db.refresh(image)

            return ImageUploadResponse(
                image_id=UUID(str(image.id)),  # type: ignore[arg-type]
                location_id=UUID(str(image.location_id)),  # type: ignore[arg-type]
                upload_timestamp=image.upload_timestamp,  # type: ignore[arg-type]
                detections_count=0,
                detected_species=[],
                task_id=task_id,
                processing_status="detecting",
            )

        logger.info(
            f"Processing image {image.id} synchronously for location {location.name}"
        )
        detections = self.process_image(db, image)
        if detections:
            self.spotting_service.save_detections(
                db,
                UUID(str(image.id)),  # type: ignore[arg-type]
                detections,
                detection_timestamp=upload_timestamp,
            )

        self.mark_as_processed(db, UUID(str(image.id)))  # type: ignore[arg-type]

        logger.info(
            f"Successfully processed image {image.id}: "
            f"found {len(detections)} detections"
        )

        return ImageUploadResponse(
            image_id=UUID(str(image.id)),  # type: ignore[arg-type]
            location_id=UUID(str(image.location_id)),  # type: ignore[arg-type]
            upload_timestamp=image.upload_timestamp,  # type: ignore[arg-type]
            detections_count=len(detections),
            detected_species=[detection["species"] for detection in detections],
            processing_status="detecting",
        )

    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on Earth in kilometers.

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point

        Returns:
            Distance in kilometers
        """
        R = 6371.0

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def get_images_in_range(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        distance_range: float,
        requesting_user_id: UUID | None = None,
        time_start: datetime | None = None,
        time_end: datetime | None = None,
        limit_per_location: int = 3,
        species_filter: str | None = None,
        only_my_images: bool = False,
    ) -> List[Image]:
        """Get images within a distance range from a location and optional time range.
        Limits to the most recent N images per location.
        If species_filter is provided, only returns images that have spottings matching that species.
        Applies privacy filtering if requesting_user_id is provided.

        Args:
            db: Database session
            latitude: Center latitude in decimal degrees
            longitude: Center longitude in decimal degrees
            distance_range: Maximum distance in kilometers (km) from center location
            requesting_user_id: Optional UUID of the user making the request (for privacy filtering)
            time_start: Optional start timestamp in ISO 8601 format (inclusive)
            time_end: Optional end timestamp in ISO 8601 format (inclusive)
            limit_per_location: Maximum number of images to return per location (default: 3)
            species_filter: Optional species name filter (case-insensitive). If provided, only returns images with spottings matching this species.

        Returns:
            List of Image objects within the specified range (max limit_per_location per location)
        """
        all_locations = self.repository.get_all_locations(db)

        locations_in_range = []
        for location in all_locations:
            distance = self.haversine_distance(
                latitude,
                longitude,
                float(location.latitude),
                float(location.longitude),
            )
            if distance <= distance_range:
                locations_in_range.append(location.id)

        if not locations_in_range:
            return []

        all_images = []
        for location_id in locations_in_range:
            location_images = self.repository.get_by_location_id(
                db=db,
                location_id=UUID(str(location_id)),
                requesting_user_id=requesting_user_id,
                time_start=time_start,
                time_end=time_end,
                limit=limit_per_location,
                species_filter=species_filter,
                only_my_images=only_my_images,
            )
            all_images.extend(location_images)

        all_images.sort(key=lambda img: img.upload_timestamp, reverse=True)

        return all_images

    def mark_as_processed(self, db: Session, image_id: UUID) -> None:
        """Mark an image as processed.

        Args:
            db: Database session
            image_id: UUID of the image
        """
        self.repository.update_processed(db, image_id, processed=True)
