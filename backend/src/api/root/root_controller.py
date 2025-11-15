"""Controller for root endpoint."""

from typing import Dict

from fastapi import APIRouter, status

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
def root() -> Dict[str, str | Dict[str, str]]:
    """Root endpoint with API information."""
    return {
        "name": "Wildlife Camera API",
        "version": "0.1.0",
        "endpoints": {
            "locations": "/locations",
            "upload_image": "/locations/{location_id}/image",
            "get_image": "/images/{image_id}",
            "get_image_base64": "/images/{image_id}/base64",
            "spottings": "/spottings",
            "animal_spottings": "/spottings/animal",
            "statistics": "/statistics",
            "create_user_detection": "/user-detections",
            "get_user_detection_stats": "/user-detections/{image_id}",
            "wikipedia_articles": "/wikipedia/articles",
        },
    }


@router.get("/health", status_code=status.HTTP_200_OK)
def health() -> Dict[str, str]:
    """Health endpoint."""
    return {"status": "ok"}
