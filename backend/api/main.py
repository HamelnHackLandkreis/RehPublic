"""FastAPI application for wildlife camera API."""

import logging
from typing import List
from uuid import UUID

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from api.database import get_db, init_db
from api.schemas import (
    BoundingBoxResponse,
    DetectionResponse,
    ImageDetailResponse,
    ImageUploadResponse,
    LocationCreate,
    LocationResponse,
    SpottingLocationResponse,
)
from api.models import Spotting
from api.services import ImageService, LocationService, SpottingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Wildlife Camera API",
    description="API for managing wildlife camera locations, images, and animal detections",
    version="0.1.0"
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


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


@app.get("/locations", response_model=List[LocationResponse], status_code=status.HTTP_200_OK)
def get_locations(db: Session = Depends(get_db)):
    """Get all camera locations.

    Returns:
        List of all locations with name, longitude, latitude, and description
    """
    locations = location_service.get_all_locations(db)
    return locations


@app.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    location_data: LocationCreate,
    db: Session = Depends(get_db)
):
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
            description=location_data.description
        )
        return location
    except Exception as e:
        logger.error(f"Failed to create location: {e}")
        error_msg = str(e)
        
        # Handle duplicate location name
        if "UNIQUE constraint failed: locations.name" in error_msg or "duplicate" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Location with name '{location_data.name}' already exists"
            )
        
        # Generic error for other cases
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create location. Please check your input data."
        )


@app.get("/locations/{location_id}", response_model=LocationResponse, status_code=status.HTTP_200_OK)
def get_location(
    location_id: UUID,
    db: Session = Depends(get_db)
):
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
            detail=f"Location with id {location_id} not found"
        )
    return location


@app.post(
    "/locations/{location_id}/image",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_image(
    location_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
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
            detail=f"Location with id {location_id} not found"
        )

    try:
        # Read file bytes
        file_bytes = await file.read()

        # Save image to database
        image = image_service.save_image(db, location_id, file_bytes)

        # Process image synchronously
        logger.info(f"Processing image {image.id} for location {location.name}")
        detections = image_service.process_image(db, image, location.name)

        # Save detections
        spotting_service.save_detections(db, UUID(image.id), detections)

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
            detections_count=len(detections)
        )

    except Exception as e:
        logger.error(f"Failed to upload and process image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )


@app.get("/images/{image_id}", response_model=ImageDetailResponse, status_code=status.HTTP_200_OK)
def get_image(
    image_id: UUID,
    db: Session = Depends(get_db)
):
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
            detail=f"Image with id {image_id} not found"
        )

    # Get all spottings for this image
    spottings = db.query(Spotting).filter(
        Spotting.image_id == str(image_id)
    ).all()

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
                height=spotting.bbox_height
            ),
            classification_model=spotting.classification_model,
            is_uncertain=spotting.is_uncertain
        )
        detections.append(detection)

    return ImageDetailResponse(
        image_id=UUID(image.id),
        location_id=UUID(image.location_id),
        raw=image.base64_data,
        upload_timestamp=image.upload_timestamp,
        detections=detections
    )


@app.get("/spottings", response_model=List[SpottingLocationResponse], status_code=status.HTTP_200_OK)
def get_spottings(db: Session = Depends(get_db)):
    """Get aggregated spotting data for map view.

    Returns spotting data grouped by location, including:
    - Location coordinates (longitude, latitude)
    - List of unique animal species detected at that location
    - Timestamp of most recent spotting
    - Timestamp of most recent image
    - ID of most recent image

    Returns:
        List of aggregated spotting data per location
    """
    spottings = spotting_service.get_aggregated_spottings(db)
    
    # Convert to response models
    response = []
    for spotting in spottings:
        response.append(SpottingLocationResponse(
            pos=spotting['pos'],
            animals=spotting['animals'],
            ts_last_spotting=spotting['ts_last_spotting'],
            ts_last_image=spotting['ts_last_image'],
            image_id=UUID(spotting['image_id']) if spotting['image_id'] else None
        ))
    
    return response


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
            "spottings": "/spottings"
        }
    }
