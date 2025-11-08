"""FastAPI application for wildlife camera API."""

import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from api.database import get_db, init_db
from api.schemas import (
    BoundingBoxResponse,
    DetectionResponse,
    ImageBase64Response,
    ImageDetailResponse,
    ImageUploadResponse,
    LocationCreate,
    LocationResponse,
    LocationWithImagesResponse,
    SpottingImageResponse,
    SpottingLocationResponse,
    SpottingsResponse,
    WikipediaArticleResponse,
    WikipediaArticlesRequest,
)
from api.models import Spotting
from api.services import (
    ImageService,
    LocationService,
    SpottingService,
    WikipediaService,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with Swagger/OpenAPI documentation
app = FastAPI(
    title="Wildlife Camera API",
    description="""
    API for managing wildlife camera locations, images, and animal detections.
    
    ## Features
    
    * **Location Management**: Create and retrieve camera locations with GPS coordinates
    * **Image Upload**: Upload images to specific locations with automatic animal detection
    * **Detection Results**: Retrieve images with detected animals, species, and bounding boxes
    * **Spotting Search**: Search for images within geographic and time ranges
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
            "name": "spottings",
            "description": "Search for images within geographic and time ranges.",
        },
        {
            "name": "wikipedia",
            "description": "Fetch Wikipedia articles for animal species.",
        },
    ],
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
location_service = LocationService()
image_service = ImageService()
spotting_service = SpottingService()
wikipedia_service = WikipediaService()


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


@app.get(
    "/locations",
    response_model=List[LocationResponse],
    status_code=status.HTTP_200_OK,
    tags=["locations"],
)
def get_locations(db: Session = Depends(get_db)):
    """Get all camera locations.

    Returns:
        List of all locations with name, longitude, latitude, and description
    """
    locations = location_service.get_all_locations(db)
    return locations


@app.post(
    "/locations",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["locations"],
)
def create_location(location_data: LocationCreate, db: Session = Depends(get_db)):
    """Create a new camera location.

    Args:
        location_data: Location data including name, coordinates, and description

    Returns:
        Created location with generated ID
    """
    try:
        location = location_service.create_location(
            db=db,
            name=location_data.name,
            longitude=location_data.longitude,
            latitude=location_data.latitude,
            description=location_data.description,
        )
        return location
    except Exception as e:
        logger.error(f"Failed to create location: {e}")
        error_msg = str(e)

        # Handle duplicate location name
        if (
            "UNIQUE constraint failed: locations.name" in error_msg
            or "duplicate" in error_msg.lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Location with name '{location_data.name}' already exists",
            )

        # Generic error for other cases
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create location. Please check your input data.",
        )


@app.get(
    "/locations/{location_id}",
    response_model=LocationResponse,
    status_code=status.HTTP_200_OK,
)
def get_location(location_id: UUID, db: Session = Depends(get_db)):
    """Get specific location by ID.

    Args:
        location_id: UUID of the location

    Returns:
        Location details

    Raises:
        HTTPException: 404 if location not found
    """
    location = location_service.get_location_by_id(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found",
        )
    return location


@app.post(
    "/locations/{location_id}/image",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["images"],
)
async def upload_image(
    location_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db)
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

    Returns:
        Image upload response with image_id and detection count

    Raises:
        HTTPException: 404 if location not found
    """
    # Validate location exists
    location = location_service.get_location_by_id(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found",
        )

    try:
        # Read file bytes
        file_bytes = await file.read()

        # Save image to database
        image = image_service.save_image(db, location_id, file_bytes)

        # Process image synchronously
        logger.info(f"Processing image {image.id} for location {location.name}")
        detections = image_service.process_image(db, image, location.name)
        if detections:
            # Save detections
            spotting_service.save_detections(
                db,
                UUID(image.id),
                detections,
            )

        # Mark image as processed
        image.processed = True
        db.commit()

        logger.info(
            f"Successfully processed image {image.id}: "
            f"found {len(detections)} detections"
        )

        return ImageUploadResponse(
            image_id=UUID(image.id),
            location_id=UUID(image.location_id),
            upload_timestamp=image.upload_timestamp,
            detections_count=len(detections),
            detected_species=[detection["species"] for detection in detections],
        )

    except Exception as e:
        logger.error(f"Failed to upload and process image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}",
        )


@app.get(
    "/images/{image_id}",
    response_model=ImageDetailResponse,
    status_code=status.HTTP_200_OK,
    tags=["images"],
)
def get_image(image_id: UUID, db: Session = Depends(get_db)):
    """Get image with detection data.

    Returns the base64-encoded image along with all detected animals
    including species, confidence scores, and bounding boxes.

    Args:
        image_id: UUID of the image

    Returns:
        Image details with base64 data and detections

    Raises:
        HTTPException: 404 if image not found
    """
    image = image_service.get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )

    # Get all spottings for this image
    spottings = db.query(Spotting).filter(Spotting.image_id == str(image_id)).all()

    # Convert spottings to detection responses
    detections = []
    for spotting in spottings:
        detection = DetectionResponse(
            species=spotting.species,
            confidence=spotting.confidence,
            bounding_box=BoundingBoxResponse(
                x=spotting.bbox_x,
                y=spotting.bbox_y,
                width=spotting.bbox_width,
                height=spotting.bbox_height,
            ),
            classification_model=spotting.classification_model,
            is_uncertain=spotting.is_uncertain,
        )
        detections.append(detection)

    return ImageDetailResponse(
        image_id=UUID(image.id),
        location_id=UUID(image.location_id),
        raw=image.base64_data,
        upload_timestamp=image.upload_timestamp,
        detections=detections,
    )


@app.get(
    "/images/{image_id}/base64",
    response_model=ImageBase64Response,
    status_code=status.HTTP_200_OK,
    tags=["images"],
)
def get_image_base64(image_id: UUID, db: Session = Depends(get_db)):
    """Get base64-encoded image data by image ID.

    Returns only the base64-encoded image data for the specified image ID.
    This endpoint is useful when you have an image ID from the /spottings endpoint
    and need to fetch the actual image data.

    Args:
        image_id: UUID of the image

    Returns:
        Image base64 data response with image_id and base64_data

    Raises:
        HTTPException: 404 if image not found
    """
    image = image_service.get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )

    return ImageBase64Response(image_id=UUID(image.id), base64_data=image.base64_data)


@app.get(
    "/spottings",
    response_model=SpottingsResponse,
    status_code=status.HTTP_200_OK,
    tags=["spottings"],
)
def get_spottings(
    latitude: float = Query(
        ...,
        description="Center latitude for location search (decimal degrees, e.g., 50.123)",
    ),
    longitude: float = Query(
        ...,
        description="Center longitude for location search (decimal degrees, e.g., 10.456)",
    ),
    distance_range: float = Query(
        ...,
        description="Maximum distance from center location in kilometers (km). Example: 5.0 for 5 km radius",
        gt=0,
    ),
    time_start: Optional[datetime] = Query(
        None,
        description="Start timestamp for time range filter (ISO 8601 format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD). Inclusive. Example: 2024-01-01T00:00:00",
    ),
    time_end: Optional[datetime] = Query(
        None,
        description="End timestamp for time range filter (ISO 8601 format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD). Inclusive. Example: 2024-12-31T23:59:59",
    ),
    db: Session = Depends(get_db),
):
    """Get images within a location and time range, grouped by location.

    Returns up to 3 most recent images per location that are:
    - Within the specified distance range from the center location (distance_range in kilometers)
    - Within the optional time range (if provided, using ISO 8601 datetime format)

    Response is grouped by location, where each location contains:
    - Location data (id, name, coordinates, description)
    - List of images with detections (species, confidence, bounding boxes)
    - Note: Base64 image data is NOT included. Use /images/{image_id}/base64 to fetch it.

    Query Parameters:
        latitude: Center latitude in decimal degrees (e.g., 50.123)
        longitude: Center longitude in decimal degrees (e.g., 10.456)
        distance_range: Maximum distance in kilometers (km) from center location. Must be > 0.
        time_start: Optional start timestamp in ISO 8601 format (inclusive).
                   Examples: "2024-01-01T00:00:00", "2024-01-01"
        time_end: Optional end timestamp in ISO 8601 format (inclusive).
                 Examples: "2024-12-31T23:59:59", "2024-12-31"

    Returns:
        Response with locations array, each containing location data and images (max 3 per location)

    Example:
        GET /spottings?latitude=50.0&longitude=10.0&distance_range=5.0&time_start=2024-01-01T00:00:00&time_end=2024-12-31T23:59:59
    """
    # Get images within range (limited to 3 per location)
    images = image_service.get_images_in_range(
        db=db,
        latitude=latitude,
        longitude=longitude,
        distance_range=distance_range,
        time_start=time_start,
        time_end=time_end,
        limit_per_location=3,
    )

    # Group images by location
    images_by_location = defaultdict(list)
    location_map = {}

    for image in images:
        location_id = image.location_id

        # Fetch location if not already cached
        if location_id not in location_map:
            location = location_service.get_location_by_id(db, UUID(location_id))
            if location:
                location_map[location_id] = location

        # Get all spottings for this image
        spottings = db.query(Spotting).filter(Spotting.image_id == str(image.id)).all()

        # Convert spottings to detection responses
        detections = []
        for spotting in spottings:
            detection = DetectionResponse(
                species=spotting.species,
                confidence=spotting.confidence,
                bounding_box=BoundingBoxResponse(
                    x=spotting.bbox_x,
                    y=spotting.bbox_y,
                    width=spotting.bbox_width,
                    height=spotting.bbox_height,
                ),
                classification_model=spotting.classification_model,
                is_uncertain=spotting.is_uncertain,
            )
            detections.append(detection)

        # Add image to location group
        images_by_location[location_id].append(
            SpottingImageResponse(
                image_id=UUID(image.id),
                location_id=UUID(image.location_id),
                upload_timestamp=image.upload_timestamp,
                detections=detections,
            )
        )

    # Build response with locations and their images
    locations_response = []
    for location_id, location_images in images_by_location.items():
        if location_id in location_map:
            location = location_map[location_id]
            locations_response.append(
                LocationWithImagesResponse(
                    id=UUID(location.id),
                    name=location.name,
                    longitude=location.longitude,
                    latitude=location.latitude,
                    description=location.description,
                    images=location_images,
                )
            )

    return SpottingsResponse(locations=locations_response)


@app.post(
    "/wikipedia/articles",
    response_model=List[WikipediaArticleResponse],
    status_code=status.HTTP_200_OK,
    tags=["wikipedia"],
)
async def get_wikipedia_articles(request: WikipediaArticlesRequest):
    """Fetch Wikipedia articles with main image, description, and link.

    This endpoint fetches data from the Wikipedia API for the provided article titles.
    For each article, it returns:
    - title: The article title
    - description: A short description or extract from the article
    - image_url: URL to the main/thumbnail image (if available)
    - article_url: Direct link to the Wikipedia article

    Args:
        request: List of Wikipedia article titles to fetch

    Returns:
        List of Wikipedia article data (articles not found will be omitted)

    Example:
        POST /wikipedia/articles
        {
            "titles": ["Red deer", "Wild boar", "European badger"]
        }
    """
    try:
        articles = await wikipedia_service.fetch_articles(request.titles)
        return articles
    except Exception as e:
        logger.error(f"Failed to fetch Wikipedia articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Wikipedia articles: {str(e)}",
        )


@app.get("/", status_code=status.HTTP_200_OK)
def root():
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
            "wikipedia_articles": "/wikipedia/articles",
        },
    }
