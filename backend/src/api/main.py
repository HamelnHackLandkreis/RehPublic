"""FastAPI application for wildlife camera API."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.api.config import validate_auth0_config
from src.api.database import init_db
from src.api.image_pull_sources.image_pull_controller import (
    router as image_pull_sources_router,
)
from src.api.images.images_controller import (
    router as images_router,
    upload_router as image_upload_router,
)
from src.api.locations.locations_controller import router as locations_router
from src.api.middleware.auth import create_authentication_middleware
from src.api.root.root_controller import router as root_router
from src.api.statistics.statistics_controller import router as statistics_router
from src.api.user_detections.user_detections_controller import (
    router as user_detections_router,
)
from src.api.users.user_controller import router as users_router
from src.api.wikipedia.wikipedia_controller import router as wikipedia_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with Swagger/OpenAPI documentation
app = FastAPI(
    title="Wildlife Camera API",
    description="""
    API for managing wildlife camera locations, images, and animal detections.

    ## Features

    * **Location Management**: Create and retrieve camera locations with GPS coordinates, search within geographic and time ranges
    * **Image Upload**: Upload images to specific locations with automatic animal detection
    * **Detection Results**: Retrieve images with detected animals, species, and bounding boxes
    * **Wikipedia Integration**: Fetch Wikipedia articles for animal species

    ## API Documentation

    * **Swagger UI**: Available at `/docs` - Interactive API documentation
    * **ReDoc**: Available at `/redoc` - Alternative API documentation
    * **OpenAPI Schema**: Available at `/openapi.json` - Machine-readable API schema
    """,
    version="0.1.0",
    docs_url="/docs",  # Swagger UI endpoint
    redoc_url="/redoc",  # ReDoc endpoint
    openapi_url="/openapi.json",  # OpenAPI schema endpoint
    contact={
        "name": "Wildlife Camera API",
    },
    license_info={
        "name": "MIT",
    },
    tags_metadata=[
        {
            "name": "locations",
            "description": "Operations for managing camera locations with GPS coordinates.",
        },
        {
            "name": "images",
            "description": "Operations for uploading and retrieving images with animal detections.",
        },
        {
            "name": "image_pull_sources",
            "description": "Configure and manage automated image pulling from external sources.",
        },
        {
            "name": "user-detections",
            "description": "Track manual user identifications and compare with automated detections.",
        },
        {
            "name": "wikipedia",
            "description": "Fetch Wikipedia articles for animal species.",
        },
        {
            "name": "statistics",
            "description": "Get statistics for animal spottings grouped by time periods.",
        },
        {
            "name": "users",
            "description": "User profile and settings management.",
        },
    ],
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware to handle proxy headers correctly
# This ensures FastAPI uses X-Forwarded-Proto for scheme detection
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Adjust to your specific domains in production
)

# Register authentication middleware
create_authentication_middleware(app)

# Include routers
app.include_router(locations_router, prefix="/locations", tags=["locations"])
app.include_router(images_router, prefix="/images", tags=["images"])
app.include_router(
    image_upload_router, prefix="/locations", tags=["images"]
)  # For /locations/{id}/image endpoint
app.include_router(
    image_pull_sources_router, prefix="/image-pull-sources", tags=["image_pull_sources"]
)
app.include_router(statistics_router, prefix="/statistics", tags=["statistics"])
app.include_router(
    user_detections_router, prefix="/user-detections", tags=["user-detections"]
)
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(wikipedia_router, prefix="/wikipedia", tags=["wikipedia"])
app.include_router(root_router, tags=["root"])


@app.on_event("startup")
def startup_event() -> None:
    """Initialize database on startup."""
    logger.info("Validating Auth0 configuration...")
    validate_auth0_config()
    logger.info("Auth0 configuration validated successfully")

    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
