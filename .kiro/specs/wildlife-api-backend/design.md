# Design Document

## Overview

The Wildlife API Backend is a minimal FastAPI application that provides REST endpoints for managing wildlife camera locations, uploading images, and retrieving animal detection data. The system integrates with the existing `wildlife_processor` CLI to perform image analysis and stores all data in a SQLite database.

The API is designed to be stateless, lightweight, and focused on core CRUD operations without authentication or complex business logic.

## Architecture

### High-Level Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP/JSON
       ▼
┌─────────────────────────────────┐
│      FastAPI Application        │
│  ┌──────────────────────────┐  │
│  │   API Endpoints Layer    │  │
│  └────────────┬─────────────┘  │
│               │                 │
│  ┌────────────▼─────────────┐  │
│  │   Service Layer          │  │
│  │  - Location Service      │  │
│  │  - Image Service         │  │
│  │  - Spotting Service      │  │
│  └────────────┬─────────────┘  │
│               │                 │
│  ┌────────────▼─────────────┐  │
│  │   Database Layer         │  │
│  │  (SQLAlchemy ORM)        │  │
│  └────────────┬─────────────┘  │
└───────────────┼─────────────────┘
                │
       ┌────────▼────────┐
       │  SQLite Database│
       └─────────────────┘
                │
       ┌────────▼────────────────┐
       │  Wildlife Processor Core│
       │  (ModelManager + Utils) │
       └─────────────────────────┘
```

### Directory Structure

```
api/
├── main.py                 # FastAPI app initialization and endpoint definitions
├── database.py             # Database connection and session management
├── models.py               # SQLAlchemy ORM models
├── schemas.py              # Pydantic models for request/response validation
├── services.py             # Business logic layer
├── processor_integration.py # Integration with wildlife_processor CLI
└── tests/
    └── test_integration.py # Integration tests for all endpoints
```

## Components and Interfaces

### 1. FastAPI Application (main.py)

**Responsibilities:**
- Define REST endpoints
- Handle HTTP request/response
- Validate input using Pydantic schemas
- Coordinate between services

**Endpoints:**

```python
GET    /locations                    # List all locations
POST   /locations                    # Create new location
GET    /locations/{location_id}     # Get specific location
POST   /locations/{location_id}/image # Upload image to location
GET    /images/{image_id}            # Get image with detections
GET    /spottings                    # Get aggregated spotting data
```

### 2. Database Models (models.py)

**Location Model:**
```python
class Location(Base):
    id: UUID (primary key, default=uuid4)
    name: str (unique, indexed)
    longitude: float
    latitude: float
    description: str (nullable)
    created_at: datetime
```

**Image Model:**
```python
class Image(Base):
    id: UUID (primary key, default=uuid4)
    location_id: UUID (foreign key -> Location.id)
    base64_data: str (text, stores base64 encoded image)
    upload_timestamp: datetime
    processed: bool (default False)
```

**Spotting Model:**
```python
class Spotting(Base):
    id: UUID (primary key, default=uuid4)
    image_id: UUID (foreign key -> Image.id)
    species: str (indexed)
    confidence: float
    bbox_x: int
    bbox_y: int
    bbox_width: int
    bbox_height: int
    detection_timestamp: datetime
    classification_model: str
    is_uncertain: bool
```

**Relationships:**
- Location → Image (one-to-many)
- Image → Spotting (one-to-many)

### 3. Pydantic Schemas (schemas.py)

**Request/Response Models:**

```python
# Location schemas
class LocationCreate(BaseModel):
    name: str
    longitude: float
    latitude: float
    description: Optional[str] = None

class LocationResponse(BaseModel):
    id: UUID
    name: str
    longitude: float
    latitude: float
    description: Optional[str]

# Image schemas
class ImageUploadResponse(BaseModel):
    image_id: UUID
    location_id: UUID
    upload_timestamp: datetime
    detections_count: int

class BoundingBoxResponse(BaseModel):
    x: int
    y: int
    width: int
    height: int

class DetectionResponse(BaseModel):
    species: str
    confidence: float
    bounding_box: BoundingBoxResponse
    classification_model: str
    is_uncertain: bool

class ImageDetailResponse(BaseModel):
    image_id: UUID
    location_id: UUID
    raw: str  # base64 encoded image
    upload_timestamp: datetime
    detections: List[DetectionResponse]

# Spotting schemas
class SpottingLocationResponse(BaseModel):
    pos: Dict[str, float]  # {"longitude": x, "latitude": y}
    animals: List[str]  # unique species names
    ts_last_spotting: datetime
    ts_last_image: datetime
    image_id: UUID
```

### 4. Service Layer (services.py)

**LocationService:**
- `get_all_locations()` - Retrieve all locations
- `get_location_by_id(location_id)` - Get specific location
- `create_location(data)` - Create new location

**ImageService:**
- `save_image(location_id, file_data)` - Save uploaded image as base64
- `get_image_by_id(image_id)` - Retrieve image with detections
- `process_image(image_id)` - Trigger wildlife processor on image

**SpottingService:**
- `save_detections(image_id, detections)` - Store individual detection results in spottings table
- `get_aggregated_spottings()` - Query and aggregate spottings by location, returning:
  - Location coordinates (from locations table)
  - Unique list of species detected at that location
  - Most recent spotting timestamp
  - Most recent image timestamp
  - Most recent image_id

### 5. Wildlife Processor Integration (processor_integration.py)

**ProcessorClient:**
- `process_image_data(image_bytes, location_name, timestamp)` - Process image using wildlife_processor core
- Returns list of `AnimalDetection` objects

**Implementation approach:**
- Convert base64 to image bytes
- Use `wildlife_processor.core.models.ModelManager` for detection/classification
- Use `wildlife_processor.utils.image_utils` for image loading and preprocessing
- Create `ImageMetadata` object with location and timestamp
- Call `ModelManager.process_image()` directly with preprocessed image
- Parse detection results into database-ready format
- No temporary files needed - process in memory

## Data Models

### Database Schema

```sql
CREATE TABLE locations (
    id TEXT PRIMARY KEY,  -- UUID stored as TEXT
    name TEXT UNIQUE NOT NULL,
    longitude REAL NOT NULL,
    latitude REAL NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE images (
    id TEXT PRIMARY KEY,  -- UUID stored as TEXT
    location_id TEXT NOT NULL,
    base64_data TEXT NOT NULL,
    upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT 0,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
);

CREATE TABLE spottings (
    id TEXT PRIMARY KEY,  -- UUID stored as TEXT
    image_id TEXT NOT NULL,
    species TEXT NOT NULL,
    confidence REAL NOT NULL,
    bbox_x INTEGER NOT NULL,
    bbox_y INTEGER NOT NULL,
    bbox_width INTEGER NOT NULL,
    bbox_height INTEGER NOT NULL,
    detection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    classification_model TEXT NOT NULL,
    is_uncertain BOOLEAN DEFAULT 0,
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE
);

CREATE INDEX idx_locations_name ON locations(name);
CREATE INDEX idx_spottings_species ON spottings(species);
CREATE INDEX idx_spottings_image_id ON spottings(image_id);
```

### Data Flow for Image Upload

1. Client uploads **single image file** to `POST /locations/{location_id}/image`
2. FastAPI receives `UploadFile` object
3. Read file bytes and encode to base64
4. Save to `images` table with `processed=False`
5. **Synchronously** call `ProcessorClient.process_image_data()` with image bytes
   - This instantiates ModelManager from wildlife_processor.core
   - Processes the single image in-memory
   - Returns list of detections for this one image
6. Wildlife processor returns list of detections (individual animal detections)
7. Save each detection to `spottings` table (one row per detected animal)
8. Update `images.processed=True`
9. Return response with image_id and detection count
10. **Note:** Each upload request processes exactly one image synchronously before responding

### Data Flow for GET /spottings

1. Client requests `GET /spottings`
2. Query joins `locations`, `images`, and `spottings` tables
3. Group results by location_id
4. For each location, aggregate:
   - Distinct species names (from spottings.species)
   - MAX(spottings.detection_timestamp) as ts_last_spotting
   - MAX(images.upload_timestamp) as ts_last_image
   - Most recent image_id (image with latest upload_timestamp)
5. Return array of aggregated spotting data per location

## Error Handling

### HTTP Status Codes

- `200 OK` - Successful GET requests
- `201 Created` - Successful POST requests
- `404 Not Found` - Resource doesn't exist (location_id, image_id)
- `422 Unprocessable Entity` - Invalid request data (Pydantic validation)
- `500 Internal Server Error` - Processing failures, database errors

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Specific Error Scenarios

1. **Location not found** - Return 404 when uploading to non-existent location
2. **Image not found** - Return 404 when requesting non-existent image
3. **Processing failure** - If wildlife processor fails, still save image but return empty detections list
4. **Invalid image format** - Return 422 if uploaded file is not a valid image
5. **Database constraint violations** - Return 422 for duplicate location names

## Testing Strategy

### Integration Tests (test_integration.py)

Use `TestClient` from FastAPI to test all endpoints:

**Test Cases:**

1. **test_create_and_get_locations**
   - POST /locations with valid data
   - Verify 201 response
   - GET /locations and verify location appears
   - GET /locations/{id} and verify details

2. **test_upload_image_to_location**
   - Create a test location
   - POST image file to /locations/{id}/image
   - Verify 201 response with image_id
   - Verify image is stored in database

3. **test_upload_image_invalid_location**
   - POST image to non-existent location_id
   - Verify 404 response

4. **test_get_image_with_detections**
   - Upload image with known animals
   - GET /images/{id}
   - Verify base64 data is returned
   - Verify detections array contains species and bounding boxes

5. **test_get_spottings_aggregated**
   - Create multiple locations with images
   - Upload images with various detections
   - GET /spottings
   - Verify aggregated data structure
   - Verify correct timestamps and animal lists

6. **test_get_image_not_found**
   - GET /images/99999
   - Verify 404 response

**Test Setup:**
- Use in-memory SQLite database (`:memory:`)
- Create test fixtures for sample images
- Mock or use actual wildlife processor (depending on test speed requirements)
- Clean up database after each test

**Test Execution:**
- Run with pytest
- Use `TestClient` for synchronous testing
- No need for async test client (keep it simple)

## Implementation Notes

### Minimal Design Principles

1. **No authentication** - All endpoints are public
2. **No pagination** - Return all results (acceptable for MVP)
3. **No caching** - Direct database queries
4. **No async database** - Use synchronous SQLAlchemy (simpler)
5. **No file storage** - Everything in SQLite as base64
6. **No background tasks** - Process images synchronously during upload (one image per request)
7. **Single file approach** - Keep related code together where possible
8. **Synchronous processing** - Each POST /locations/{id}/image processes exactly one image before responding

### Dependencies

```toml
[project]
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "python-multipart>=0.0.6",  # For file uploads
    "pytest>=7.4.0",
    "httpx>=0.25.0",  # For TestClient
]
```

### Database Initialization

- Create tables on application startup using SQLAlchemy metadata
- Use `create_all()` method
- No migrations needed for MVP (Alembic not required)

### Wildlife Processor Integration

- Import directly from `wildlife_processor.core` package
- Use `ModelManager` for detection and classification
- Use `image_utils` for preprocessing (load_image, preprocess_image_for_pytorch_wildlife)
- Process images in memory (no temporary files)
- Use default model region ("europe" or "general")
- Handle processor exceptions gracefully
- Return empty detections list if processing fails (don't fail the upload)
