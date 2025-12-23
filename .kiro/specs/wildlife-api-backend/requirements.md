# Requirements Document

## Introduction

This document specifies the requirements for a minimal FastAPI backend that exposes wildlife camera detection data through REST endpoints. The system integrates with the existing CLI-based wildlife processor to provide API access to locations, images, and animal spottings stored in a SQLite database.

## Glossary

- **API Backend**: The FastAPI application that exposes REST endpoints for wildlife camera data
- **Location**: A geographic point where a wildlife camera is installed, identified by coordinates and metadata
- **Image**: A wildlife camera photograph stored as base64-encoded data with associated metadata
- **Spotting**: A detected animal occurrence within an image, including species identification and bounding box coordinates
- **Detection Result**: The output from the wildlife processor CLI containing species, confidence scores, and bounding boxes
- **SQLite Database**: The embedded relational database storing all location, image, and spotting data

## Requirements

### Requirement 1

**User Story:** As a wildlife researcher, I want to retrieve all camera locations, so that I can see where cameras are deployed

#### Acceptance Criteria

1. WHEN a GET request is made to `/locations`, THE API Backend SHALL return a JSON array containing all locations
2. THE API Backend SHALL include name, longitude, latitude, and description fields for each location in the response
3. THE API Backend SHALL return HTTP status 200 for successful requests to `/locations`

### Requirement 2

**User Story:** As a wildlife researcher, I want to upload images to specific camera locations, so that I can process new wildlife photographs

#### Acceptance Criteria

1. WHEN a POST request with an image file is made to `/locations/{location_id}/image`, THE API Backend SHALL accept the uploaded file
2. THE API Backend SHALL store the uploaded image as base64-encoded data in the SQLite Database
3. THE API Backend SHALL invoke the wildlife processor CLI to generate detection results for the uploaded image
4. THE API Backend SHALL store detection results including species, confidence scores, and bounding boxes in the SQLite Database
5. THE API Backend SHALL return HTTP status 201 with the created image ID upon successful upload
6. IF the location_id does not exist, THEN THE API Backend SHALL return HTTP status 404

### Requirement 3

**User Story:** As a wildlife researcher, I want to retrieve a specific image with its detection data, so that I can view what animals were detected

#### Acceptance Criteria

1. WHEN a GET request is made to `/images/{image_id}`, THE API Backend SHALL return a JSON response containing the image data
2. THE API Backend SHALL include the base64-encoded image in a `raw` field in the response
3. THE API Backend SHALL include all detection results with species names, confidence scores, and bounding box coordinates in the response
4. THE API Backend SHALL return HTTP status 200 for successful requests
5. IF the image_id does not exist, THEN THE API Backend SHALL return HTTP status 404

### Requirement 4

**User Story:** As a wildlife researcher, I want to view all animal spottings on a map, so that I can visualize wildlife activity across locations

#### Acceptance Criteria

1. WHEN a GET request is made to `/spottings`, THE API Backend SHALL return a JSON array of spotting summaries
2. THE API Backend SHALL include position data with longitude and latitude for each spotting location
3. THE API Backend SHALL include a list of detected animal species for each location
4. THE API Backend SHALL include the timestamp of the most recent spotting at each location
5. THE API Backend SHALL include the timestamp of the most recent image at each location
6. THE API Backend SHALL include the image_id of the most recent image at each location
7. THE API Backend SHALL return HTTP status 200 for successful requests

### Requirement 5

**User Story:** As a developer, I want a SQLite database schema, so that location, image, and spotting data can be persisted

#### Acceptance Criteria

1. THE API Backend SHALL create a `locations` table with columns for id, name, longitude, latitude, and description
2. THE API Backend SHALL create an `images` table with columns for id, location_id, base64_data, upload_timestamp, and foreign key to locations
3. THE API Backend SHALL create a `spottings` table with columns for id, image_id, species, confidence, bounding_box_data, detection_timestamp, and foreign key to images
4. THE API Backend SHALL initialize the database schema on application startup if tables do not exist

### Requirement 6

**User Story:** As a developer, I want integration tests for all endpoints, so that I can verify the API works correctly

#### Acceptance Criteria

1. THE API Backend SHALL include integration tests that verify GET `/locations` returns location data
2. THE API Backend SHALL include integration tests that verify POST `/locations/{location_id}/image` accepts and processes images
3. THE API Backend SHALL include integration tests that verify GET `/images/{image_id}` returns image and detection data
4. THE API Backend SHALL include integration tests that verify GET `/spottings` returns aggregated spotting data
5. THE API Backend SHALL include integration tests that verify appropriate HTTP status codes for error conditions
