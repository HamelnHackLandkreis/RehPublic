# Wildlife Camera API

A minimal FastAPI backend for managing wildlife camera locations, uploading images, and retrieving animal detection data.

## Features

- **Location Management**: Create and retrieve camera locations with GPS coordinates
- **Image Upload**: Upload images to specific locations with automatic animal detection
- **Detection Results**: Retrieve images with detected animals, species, and bounding boxes
- **Spotting Aggregation**: View aggregated animal sightings by location for map visualization

## Installation

The API dependencies are included in the main `pyproject.toml`. Install with:

```bash
cd backend
uv sync
```

## Running the API

Start the development server:

```bash
cd backend
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### Locations

- `GET /locations` - List all camera locations
- `POST /locations` - Create a new location
- `GET /locations/{location_id}` - Get specific location

### Images

- `POST /locations/{location_id}/image` - Upload image to location (processes synchronously)
- `GET /images/{image_id}` - Get image with detection data

### Spottings

- `GET /spottings` - Get aggregated spotting data for map view

## Testing

Run integration tests:

```bash
cd backend
pytest api/tests/test_integration.py -v
```

## Database

The API uses SQLite with the database file stored at `backend/wildlife_camera.db`.

Tables:
- `locations` - Camera locations with GPS coordinates
- `images` - Uploaded images stored as base64
- `spottings` - Individual animal detections with bounding boxes

## Architecture

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Request/response validation
- **Wildlife Processor Core** - Animal detection and classification

## Example Usage

### Create a location

```bash
curl -X POST "http://localhost:8000/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Forest Trail 1",
    "longitude": 10.5,
    "latitude": 52.3,
    "description": "Trail camera in forest"
  }'
```

### Upload an image

```bash
curl -X POST "http://localhost:8000/locations/{location_id}/image" \
  -F "file=@path/to/image.jpg"
```

### Get spottings

```bash
curl "http://localhost:8000/spottings"
```
