"""Service for automated image pulling and processing."""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from src.api.image_pull_sources.gateways.base import ImageFile, ImagePullGateway
from src.api.image_pull_sources.gateways.http_directory import HttpDirectoryGateway
from src.api.image_pull_sources.image_pull_source_models import ImagePullSource
from src.api.image_pull_sources.image_pull_source_repository import (
    ImagePullSourceRepository,
)
from src.api.images.image_service import ImageService

logger = logging.getLogger(__name__)


class ImagePullService:
    """Service for pulling and processing images from external sources.

    This service orchestrates the process of:
    1. Fetching image files from external sources
    2. Processing them through the image service
    3. Tracking which files have been processed
    """

    def __init__(
        self,
        repository: ImagePullSourceRepository | None = None,
        image_service: ImageService | None = None,
    ) -> None:
        """Initialize image pull service.

        Args:
            repository: Optional pull source repository
            image_service: Optional image service for processing
        """
        self.repository = repository or ImagePullSourceRepository()
        self.image_service = image_service or ImageService()

    @classmethod
    def factory(cls) -> "ImagePullService":
        """Factory method to create ImagePullService instance.

        Returns:
            ImagePullService instance
        """
        return cls()

    def create_gateway(self, pull_source: ImagePullSource) -> ImagePullGateway:
        """Create an appropriate gateway for the pull source.

        Args:
            pull_source: ImagePullSource model instance

        Returns:
            Configured gateway instance

        Raises:
            ValueError: If the source type is not supported
        """
        return HttpDirectoryGateway.from_pull_source(pull_source)

    def pull_and_process_source(
        self, db: Session, source_id: UUID, max_files: int = 10
    ) -> dict:
        """Pull new images from a source and process them.

        Args:
            db: Database session
            source_id: UUID of the image pull source
            max_files: Maximum number of files to process in one run

        Returns:
            Dictionary with processing results

        Raises:
            ValueError: If source not found
        """
        source = self.repository.get_by_id(db, source_id)
        if not source:
            raise ValueError(f"Image pull source {source_id} not found")

        if not source.is_active:
            logger.info(f"Source {source.name} is inactive, skipping")
            return {
                "source_id": str(source_id),
                "source_name": source.name,
                "processed_count": 0,
                "status": "inactive",
            }

        logger.info(f"Processing source: {source.name}")

        gateway = self.create_gateway(source)

        new_files = gateway.get_new_files(source.last_pulled_filename)

        if not new_files:
            logger.info(f"No new files for source {source.name}")
            return {
                "source_id": str(source_id),
                "source_name": source.name,
                "processed_count": 0,
                "status": "no_new_files",
            }

        files_to_process = new_files[:max_files]
        logger.info(
            f"Found {len(new_files)} new files, processing {len(files_to_process)}"
        )

        processed_images = []
        last_processed_filename = None

        for image_file in files_to_process:
            try:
                result = self._process_single_file(db, source, gateway, image_file)
                processed_images.append(result)
                last_processed_filename = image_file.filename

            except Exception as e:
                logger.error(
                    f"Failed to process {image_file.filename} from {source.name}: {e}",
                    exc_info=True,
                )
                break

        if last_processed_filename:
            self.repository.update_last_pulled(db, source_id, last_processed_filename)

        logger.info(
            f"Processed {len(processed_images)} images for source {source.name}"
        )

        return {
            "source_id": str(source_id),
            "source_name": source.name,
            "processed_count": len(processed_images),
            "processed_images": processed_images,
            "status": "success",
        }

    def _process_single_file(
        self,
        db: Session,
        source: ImagePullSource,
        gateway: ImagePullGateway,
        image_file: ImageFile,
    ) -> dict:
        """Process a single image file.

        Args:
            db: Database session
            source: ImagePullSource model instance
            gateway: Gateway for downloading the file
            image_file: ImageFile to process

        Returns:
            Dictionary with processing result
        """
        logger.info(f"Processing file: {image_file.filename}")

        file_bytes = gateway.download_file(image_file)

        result = self.image_service.upload_and_process_image(
            db=db,
            location_id=UUID(source.location_id),
            file_bytes=file_bytes,
            user_id=UUID(source.user_id),
            upload_timestamp=None,
            async_processing=True,
        )

        logger.info(
            f"Successfully processed {image_file.filename}: "
            f"image_id={result.image_id}, detections={result.detections_count}"
        )

        return {
            "filename": image_file.filename,
            "image_id": str(result.image_id),
            "detections_count": result.detections_count,
        }

    def process_all_sources(
        self, db: Session, max_files_per_source: int = 10
    ) -> list[dict]:
        """Process all active image pull sources.

        Args:
            db: Database session
            max_files_per_source: Maximum files to process per source

        Returns:
            List of processing results for each source
        """
        active_sources = self.repository.get_all_active(db)

        if not active_sources:
            logger.info("No active image pull sources found")
            return []

        logger.info(f"Processing {len(active_sources)} active sources")

        results = []
        for source in active_sources:
            try:
                result = self.pull_and_process_source(
                    db, UUID(source.id), max_files=max_files_per_source
                )
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Failed to process source {source.name}: {e}", exc_info=True
                )
                results.append(
                    {
                        "source_id": source.id,
                        "source_name": source.name,
                        "processed_count": 0,
                        "status": "error",
                        "error": str(e),
                    }
                )

        return results
