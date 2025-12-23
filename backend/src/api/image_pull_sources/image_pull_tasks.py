"""Celery beat task for automated image pulling."""

import logging

from src.api.database import SessionLocal
from src.api.image_pull_sources.image_pull_service import ImagePullService
from src.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="image_pull.pull_all_sources", bind=True)
def pull_all_sources_task(self, max_files_per_source: int = 10) -> dict:
    """Celery beat task to pull and process images from all active sources.

    This task runs periodically (configured in beat schedule) and processes
    new images from all active external sources.

    Args:
        self: Celery task instance (bound)
        max_files_per_source: Maximum number of files to process per source

    Returns:
        Dictionary with summary of processing results
    """
    logger.info("Starting scheduled image pull task")

    db = SessionLocal()
    try:
        service = ImagePullService.factory()

        results = service.process_all_sources(
            db=db, max_files_per_source=max_files_per_source
        )

        total_processed = sum(r.get("processed_count", 0) for r in results)
        total_sources = len(results)

        logger.info(
            f"Completed image pull task: processed {total_processed} images "
            f"from {total_sources} sources"
        )

        return {
            "total_sources": total_sources,
            "total_images_processed": total_processed,
            "sources": results,
            "success": True,
        }

    except Exception as exc:
        logger.error(f"Error in scheduled image pull task: {exc}", exc_info=True)
        return {
            "total_sources": 0,
            "total_images_processed": 0,
            "sources": [],
            "success": False,
            "error": str(exc),
        }
    finally:
        db.close()
