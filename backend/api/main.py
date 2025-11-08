"""FastAPI application for wildlife camera API."""

import base64
import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, selectinload

from api.database import get_db, init_db
from api.locations_controller import router as locations_router
from api.schemas import (
    BoundingBoxResponse,
    DetectionResponse,
    ImageDetailResponse,
    ImageUploadResponse,
    LocationCreate,
    LocationResponse,
    LocationsResponse,
    LocationWithImagesResponse,
    SpeciesCountResponse,
    SpottingImageResponse,
    SpottingsResponse,
    StatisticsResponse,
    TimePeriodStatisticsResponse,
    UserDetectionCreate,
    UserDetectionResponse,
    UserDetectionStatsResponse,
    WikipediaArticleResponse,
    WikipediaArticlesRequest,
)
from api.models import Image, Location, Spotting
from api.services import (
    ImageService,
    LocationService,
    SpottingService,
    UserDetectionService,
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
    ],
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://135.181.78.114:9001",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
location_service = LocationService()
image_service = ImageService()
spotting_service = SpottingService()
user_detection_service = UserDetectionService()
wikipedia_service = WikipediaService()

# Include routers
app.include_router(locations_router)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")


@app.get(
    "/locations",
    response_model=LocationsResponse,
    status_code=status.HTTP_200_OK,
    tags=["locations"],
)
def get_locations(
    latitude: Optional[float] = Query(
        None,
        description="Center latitude for location filter (decimal degrees, e.g., 50.123). If provided, longitude and distance_range are required.",
    ),
    longitude: Optional[float] = Query(
        None,
        description="Center longitude for location filter (decimal degrees, e.g., 10.456). If provided, latitude and distance_range are required.",
    ),
    distance_range: Optional[float] = Query(
        None,
        description="Maximum distance from center location in kilometers (km). Required if latitude/longitude are provided. Example: 5.0 for 5 km radius",
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
    """Get camera locations with spotting statistics and images.

    Returns locations with:
    - Location data (id, name, coordinates, description)
    - Spotting statistics (total_unique_species, total_spottings)
    - Up to 3 most recent images per location with detections
    - total_images_with_animals count per location

    Optional filters:
    - latitude/longitude/distance_range: Filter locations within distance range
    - time_start/time_end: Filter images by upload timestamp

    Returns:
        LocationsResponse containing:
        - locations: List of locations with images and statistics
        - total_unique_species: Total number of unique species detected across all locations
        - total_spottings: Total number of animal detections across all locations
    """
    # Validate filter parameters
    if (
        latitude is not None or longitude is not None or distance_range is not None
    ) and (latitude is None or longitude is None or distance_range is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="If filtering by location, latitude, longitude, and distance_range must all be provided",
        )

    # Get locations (filtered by distance if parameters provided)
    if latitude is not None and longitude is not None and distance_range is not None:
        # Filter locations by distance
        all_locations = db.query(Location).all()
        locations_in_range = []
        for loc in all_locations:
            distance = ImageService.haversine_distance(
                latitude, longitude, loc.latitude, loc.longitude
            )
            if distance <= distance_range:
                locations_in_range.append(loc.id)

        if not locations_in_range:
            return LocationsResponse(
                locations=[],
                total_unique_species=0,
                total_spottings=0,
            )

        # Get locations with statistics for filtered locations
        locations_data = []
        all_species = set()
        total_spottings_count = 0

        for loc_id in locations_in_range:
            location = location_service.get_location_by_id(db, UUID(loc_id))
            if not location:
                continue

            spottings = (
                db.query(Spotting)
                .join(Image, Spotting.image_id == Image.id)
                .filter(Image.location_id == loc_id)
                .all()
            )
            unique_species = set(spotting.species for spotting in spottings)
            locations_data.append((location, len(unique_species), len(spottings)))
            all_species.update(unique_species)
            total_spottings_count += len(spottings)

        total_unique_species = len(all_species)
        total_spottings = total_spottings_count
    else:
        # Get all locations with statistics
        locations_data, total_unique_species, total_spottings = (
            location_service.get_all_locations_with_statistics(db)
        )

    # Get images for each location (up to 3 per location)
    location_images_map = {}
    for location, _, _ in locations_data:
        query = db.query(Image).filter(Image.location_id == location.id)

        # Apply time range filters if provided
        if time_start is not None:
            query = query.filter(Image.upload_timestamp >= time_start)
        if time_end is not None:
            query = query.filter(Image.upload_timestamp <= time_end)

        # Get most recent 3 images with spottings eagerly loaded
        images = (
            query.options(selectinload(Image.spottings))
            .order_by(Image.upload_timestamp.desc())
            .limit(3)
            .all()
        )
        location_images_map[location.id] = images

    # Build response with locations, images, and statistics
    locations_response = []
    all_species_global = set()
    total_spottings_global = 0

    for location, loc_unique_species, loc_spottings in locations_data:
        images = location_images_map.get(location.id, [])

        # Convert images to SpottingImageResponse
        image_responses = []
        for image in images:
            spottings = image.spottings
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
                all_species_global.add(spotting.species)
                total_spottings_global += 1

            image_responses.append(
                SpottingImageResponse(
                    image_id=UUID(image.id),
                    location_id=UUID(image.location_id),
                    upload_timestamp=image.upload_timestamp,
                    detections=detections,
                )
            )

        # Count images with animals
        images_with_animals = sum(
            1 for img_resp in image_responses if len(img_resp.detections) > 0
        )

        locations_response.append(
            LocationResponse(
                id=UUID(location.id),
                name=location.name,
                longitude=location.longitude,
                latitude=location.latitude,
                description=location.description,
                total_unique_species=loc_unique_species,
                total_spottings=loc_spottings,
                images=image_responses,
                total_images_with_animals=images_with_animals,
            )
        )

    # Use global counts if filtering by location, otherwise use pre-calculated totals
    if latitude is not None and longitude is not None and distance_range is not None:
        final_total_unique_species = len(all_species_global)
        final_total_spottings = total_spottings_global
    else:
        final_total_unique_species = total_unique_species
        final_total_spottings = total_spottings

    return LocationsResponse(
        locations=locations_response,
        total_unique_species=final_total_unique_species,
        total_spottings=final_total_spottings,
    )


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
        return LocationResponse(
            id=UUID(location.id),
            name=location.name,
            longitude=location.longitude,
            latitude=location.latitude,
            description=location.description,
            total_unique_species=0,
            total_spottings=0,
            images=[],
            total_images_with_animals=0,
        )
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
    """Get specific location by ID with spotting statistics.

    Args:
        location_id: UUID of the location

    Returns:
        Location details with:
        - Location data (id, name, coordinates, description)
        - total_unique_species: Total number of unique species detected at this location
        - total_spottings: Total number of animal detections at this location

    Raises:
        HTTPException: 404 if location not found
    """
    result = location_service.get_location_by_id_with_statistics(db, location_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with id {location_id} not found",
        )

    location, total_unique_species, total_spottings = result

    # Get up to 3 most recent images with spottings eagerly loaded
    images = (
        db.query(Image)
        .filter(Image.location_id == str(location_id))
        .options(selectinload(Image.spottings))
        .order_by(Image.upload_timestamp.desc())
        .limit(3)
        .all()
    )

    # Convert images to SpottingImageResponse
    image_responses = []
    for image in images:
        spottings = image.spottings
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

        image_responses.append(
            SpottingImageResponse(
                image_id=UUID(image.id),
                location_id=UUID(image.location_id),
                upload_timestamp=image.upload_timestamp,
                detections=detections,
            )
        )

    # Count images with animals
    images_with_animals = sum(
        1 for img_resp in image_responses if len(img_resp.detections) > 0
    )

    return LocationResponse(
        id=UUID(location.id),
        name=location.name,
        longitude=location.longitude,
        latitude=location.latitude,
        description=location.description,
        total_unique_species=total_unique_species,
        total_spottings=total_spottings,
        images=image_responses,
        total_images_with_animals=images_with_animals,
    )


@app.post(
    "/locations/{location_id}/image",
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
        image = image_service.save_image(
            db, location_id, file_bytes, upload_timestamp=upload_timestamp
        )

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

        # Mark image as processed - query fresh to avoid stale object issues
        image_to_update = image_service.get_image_by_id(db, UUID(image.id))
        if image_to_update:
            image_to_update.processed = True
            db.commit()
        else:
            logger.warning(
                f"Image {image.id} not found when trying to mark as processed"
            )

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
    status_code=status.HTTP_200_OK,
    tags=["images"],
)
def get_image_base64(image_id: UUID, db: Session = Depends(get_db)):
    """Get image directly by image ID for use in img src tags.

    Returns the image as raw bytes with proper content-type headers.
    This endpoint can be used directly in HTML img src tags:
    <img src="/images/{image_id}/base64" />

    Args:
        image_id: UUID of the image

    Returns:
        Raw image bytes with appropriate image content-type (image/jpeg, image/png, etc.)

    Raises:
        HTTPException: 404 if image not found, 500 if image decoding fails
    """
    image = image_service.get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )

    # Decode base64 to bytes
    try:
        image_bytes = base64.b64decode(image.base64_data)
    except Exception as e:
        logger.error(f"Failed to decode base64 image {image_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decode image data",
        )

    # Detect image type from magic bytes (first few bytes)
    content_type = "image/jpeg"  # Default to JPEG
    if len(image_bytes) >= 4:
        # Check for PNG
        if image_bytes[:4] == b"\x89PNG":
            content_type = "image/png"
        # Check for GIF
        elif image_bytes[:3] == b"GIF":
            content_type = "image/gif"
        # Check for WebP
        elif (
            len(image_bytes) >= 12
            and image_bytes[:4] == b"RIFF"
            and image_bytes[8:12] == b"WEBP"
        ):
            content_type = "image/webp"
        # JPEG is default (starts with FF D8)

    return Response(
        content=image_bytes,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        },
    )


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

    Response also includes:
    - total_unique_species: Total number of unique species detected across all locations
    - total_spottings: Total number of animal detections across all locations

    Query Parameters:
        latitude: Center latitude in decimal degrees (e.g., 50.123)
        longitude: Center longitude in decimal degrees (e.g., 10.456)
        distance_range: Maximum distance in kilometers (km) from center location. Must be > 0.
        time_start: Optional start timestamp in ISO 8601 format (inclusive).
                   Examples: "2024-01-01T00:00:00", "2024-01-01"
        time_end: Optional end timestamp in ISO 8601 format (inclusive).
                 Examples: "2024-12-31T23:59:59", "2024-12-31"

    Returns:
        Response with locations array, each containing location data and images (max 3 per location),
        plus total_unique_species and total_spottings counts

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
        # Spottings are already loaded via eager loading in get_images_in_range
        spottings = image.spottings

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
    all_species = set()
    total_spottings_count = 0

    for location_id, location_images in images_by_location.items():
        if location_id in location_map:
            location = location_map[location_id]
            # Count images that contain animals (have at least one detection)
            images_with_animals = sum(
                1
                for image_response in location_images
                if len(image_response.detections) > 0
            )
            locations_response.append(
                LocationWithImagesResponse(
                    id=UUID(location.id),
                    name=location.name,
                    longitude=location.longitude,
                    latitude=location.latitude,
                    description=location.description,
                    images=location_images,
                    total_images_with_animals=images_with_animals,
                )
            )
            # Count spottings and collect unique species
            for image_response in location_images:
                total_spottings_count += len(image_response.detections)
                for detection in image_response.detections:
                    all_species.add(detection.species)

    return SpottingsResponse(
        locations=locations_response,
        total_unique_species=len(all_species),
        total_spottings=total_spottings_count,
    )


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


@app.get(
    "/statistics",
    response_model=StatisticsResponse,
    status_code=status.HTTP_200_OK,
    tags=["statistics"],
)
def get_statistics(
    period: str = Query(
        "day",
        description="Time period range: 'day' (current day), 'week' (last 7 days), or 'month' (last 30 days)",
        regex="^(day|week|month)$",
    ),
    granularity: Optional[str] = Query(
        None,
        description="Grouping granularity: 'hourly', 'daily', or 'weekly'. If not provided, defaults based on period (day=hourly, week/month=daily)",
        regex="^(hourly|daily|weekly)$",
    ),
    db: Session = Depends(get_db),
):
    """Get statistics for animal spottings grouped by time period.

    Returns statistics grouped by time intervals:
    - period="day": Current day (00:00 to now)
    - period="week": Last 7 days
    - period="month": Last 30 days

    Granularity options:
    - "hourly": Group by hour
    - "daily": Group by day
    - "weekly": Group by week

    Each time period includes:
    - start_time and end_time (ISO 8601 format)
    - species array with name and count
    - total_spottings count

    Query Parameters:
        period: Time period range - "day", "week", or "month" (default: "day")
        granularity: Grouping granularity - "hourly", "daily", or "weekly" (optional, auto-selected if not provided)

    Returns:
        Statistics response with list of time periods and their species counts

    Example:
        GET /statistics?period=day&granularity=hourly
        GET /statistics?period=week&granularity=daily
        GET /statistics?period=month&granularity=weekly
    """
    try:
        stats_data = spotting_service.get_statistics(
            db, period=period, granularity=granularity
        )

        # Convert to response models
        statistics = []
        for stat in stats_data:
            species_list = [
                SpeciesCountResponse(name=species["name"], count=species["count"])
                for species in stat["species"]
            ]
            statistics.append(
                TimePeriodStatisticsResponse(
                    start_time=stat["start_time"],
                    end_time=stat["end_time"],
                    species=species_list,
                    total_spottings=stat["total_spottings"],
                )
            )

        return StatisticsResponse(statistics=statistics)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@app.post(
    "/user-detections",
    response_model=UserDetectionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["user-detections"],
)
def create_user_detection(
    detection: UserDetectionCreate,
    db: Session = Depends(get_db),
):
    """Submit a manual user identification for an image.

    This endpoint allows users to record what species they think they see in an image.
    These manual identifications are stored separately from automated AI detections
    and can be used for:
    - Validating AI detection accuracy
    - Collecting training data
    - Gamification (e.g., matching game where users identify animals)
    - Community engagement and citizen science

    Args:
        detection: User detection data including image_id, species, and optional session_id

    Returns:
        Created user detection with ID and timestamp

    Raises:
        HTTPException: 404 if image not found, 500 on server error

    Example:
        POST /user-detections
        {
            "image_id": "0812161d-dfc7-4f53-b3bd-1da415e5bbb6",
            "species": "Red deer",
            "user_session_id": "user-123-session-abc"
        }
    """
    # Validate that image exists
    image = image_service.get_image_by_id(db, detection.image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {detection.image_id} not found",
        )

    try:
        user_detection = user_detection_service.create_user_detection(
            db=db,
            image_id=detection.image_id,
            species=detection.species,
            user_session_id=detection.user_session_id,
        )

        return UserDetectionResponse(
            id=UUID(user_detection.id),
            image_id=UUID(user_detection.image_id),
            species=user_detection.species,
            user_session_id=user_detection.user_session_id,
            detection_timestamp=user_detection.detection_timestamp,
        )
    except Exception as e:
        logger.error(f"Failed to create user detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user detection: {str(e)}",
        )


@app.get(
    "/user-detections/{image_id}",
    response_model=UserDetectionStatsResponse,
    status_code=status.HTTP_200_OK,
    tags=["user-detections"],
)
def get_user_detection_stats(
    image_id: UUID,
    db: Session = Depends(get_db),
):
    """Get user detection statistics for a specific image.

    Returns aggregated data showing:
    - What species users have identified (with counts)
    - Total number of user identifications
    - What species the AI detected automatically

    This is useful for:
    - Comparing user identifications with AI detections
    - Showing consensus among users
    - Validating detection accuracy
    - Displaying statistics in a matching game

    Args:
        image_id: UUID of the image

    Returns:
        Statistics comparing user detections with automated AI detections

    Raises:
        HTTPException: 404 if image not found

    Example Response:
        {
            "image_id": "0812161d-dfc7-4f53-b3bd-1da415e5bbb6",
            "user_detections": [
                {"name": "Red deer", "count": 15},
                {"name": "Wild boar", "count": 3}
            ],
            "total_user_detections": 18,
            "automated_detections": ["Red deer", "European badger"]
        }
    """
    # Validate that image exists
    image = image_service.get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found",
        )

    try:
        stats = user_detection_service.get_user_detections_for_image(db, image_id)

        return UserDetectionStatsResponse(
            image_id=image_id,
            user_detections=[
                SpeciesCountResponse(name=species["name"], count=species["count"])
                for species in stats["user_detections"]
            ],
            total_user_detections=stats["total_user_detections"],
            automated_detections=stats["automated_detections"],
        )
    except Exception as e:
        logger.error(f"Failed to get user detection stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user detection stats: {str(e)}",
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
            "statistics": "/statistics",
            "create_user_detection": "/user-detections",
            "get_user_detection_stats": "/user-detections/{image_id}",
            "wikipedia_articles": "/wikipedia/articles",
        },
    }
