# Implementation Plan

- [x] 1. Set up FastAPI project structure and dependencies
  - Create `api/` directory in backend folder
  - Create `pyproject.toml` or update existing with FastAPI dependencies (fastapi, uvicorn, sqlalchemy, python-multipart, pytest, httpx)
  - Create `__init__.py` files for Python package structure
  - _Requirements: 5.1_

- [x] 2. Implement database models and initialization
  - Create `api/models.py` with SQLAlchemy ORM models for Location, Image, and Spotting tables
  - Use UUID primary keys (stored as TEXT in SQLite)
  - Define foreign key relationships (Location → Image, Image → Spotting)
  - Create indexes on location name, spotting species, and spotting image_id
  - Create `api/database.py` with SQLAlchemy engine, session management, and Base metadata
  - Implement database initialization function that creates tables on startup
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 3. Create Pydantic schemas for request/response validation
  - Create `api/schemas.py` with Pydantic models
  - Implement LocationCreate and LocationResponse schemas
  - Implement ImageUploadResponse schema with UUID fields
  - Implement BoundingBoxResponse and DetectionResponse schemas
  - Implement ImageDetailResponse schema with base64 raw field
  - Implement SpottingLocationResponse schema with aggregated data structure
  - _Requirements: 1.1, 1.2, 2.1, 2.5, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 4. Implement wildlife processor integration
  - Create `api/processor_integration.py` with ProcessorClient class
  - Implement `process_image_data(image_bytes, location_name, timestamp)` method
  - Import ModelManager from `wildlife_processor.core.models`
  - Import image utilities from `wildlife_processor.utils.image_utils`
  - Convert image bytes to format compatible with wildlife processor
  - Call ModelManager.process_image() with preprocessed image data
  - Parse detection results and return list of detection dictionaries
  - Handle exceptions gracefully and return empty list on failure
  - _Requirements: 2.3, 2.4_

- [x] 5. Implement service layer for business logic
  - Create `api/services.py` with LocationService, ImageService, and SpottingService classes
  - Implement LocationService methods: get_all_locations(), get_location_by_id(), create_location()
  - Implement ImageService methods: save_image(), get_image_by_id(), process_image()
  - Implement SpottingService methods: save_detections(), get_aggregated_spottings()
  - Implement aggregation query for spottings grouped by location with distinct species, max timestamps
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 6. Implement FastAPI endpoints
  - Create `api/main.py` with FastAPI application initialization
  - Implement GET /locations endpoint returning all locations
  - Implement POST /locations endpoint for creating new locations
  - Implement POST /locations/{location_id}/image endpoint with UploadFile parameter
  - Implement synchronous image processing in upload endpoint (read bytes, save to DB, call processor, save detections)
  - Implement GET /images/{image_id} endpoint returning image data with detections
  - Implement GET /spottings endpoint returning aggregated spotting data
  - Add error handling for 404 (location not found, image not found) and 422 (validation errors)
  - Add database session dependency injection
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [x] 7. Write integration tests
  - Create `api/tests/test_integration.py` with pytest test cases
  - Implement test_create_and_get_locations test
  - Implement test_upload_image_to_location test with sample image
  - Implement test_upload_image_invalid_location test verifying 404 response
  - Implement test_get_image_with_detections test
  - Implement test_get_spottings_aggregated test with multiple locations and images
  - Implement test_get_image_not_found test verifying 404 response
  - Use TestClient from fastapi.testclient for endpoint testing
  - Use in-memory SQLite database for test isolation
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
