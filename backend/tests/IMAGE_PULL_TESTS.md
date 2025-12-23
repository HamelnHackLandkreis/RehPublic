# Image Pull Sources - Test Coverage Summary

This document summarizes the comprehensive test suite created for the image pull sources functionality.

## Test Structure

The test suite is organized into unit tests and integration tests, following the project's established patterns:

```
tests/
├── unit/api/image_pull_sources/
│   ├── test_image_pull_service.py          # 11 tests
│   ├── test_image_pull_source_repository.py # 12 tests
│   ├── test_http_directory_gateway.py       # 20 tests
│   └── test_image_pull_tasks.py             # 6 tests
└── integration/api/image_pull_sources/
    └── test_image_pull_controller.py        # 11 tests
```

**Total: 60 tests**

## Unit Tests

### 1. ImagePullService Tests (`test_image_pull_service.py`)

Tests the core service that orchestrates image pulling and processing.

**Test Classes:**
- `TestImagePullServiceFactory`: Factory method creation
- `TestImagePullServicePullAndProcessSource`: Pull and process functionality
  - Success case with multiple files
  - Source not found error handling
  - Inactive source handling
  - No new files scenario
  - Max files limit enforcement
  - Error handling during processing
- `TestImagePullServiceProcessAllSources`: Processing all active sources
  - Multiple sources success
  - No active sources
  - Handling errors in individual sources
- `TestImagePullServiceProcessSingleFile`: Single file processing

**Coverage:** 11 tests

### 2. ImagePullSourceRepository Tests (`test_image_pull_source_repository.py`)

Tests the repository layer for database operations.

**Test Classes:**
- `TestImagePullSourceRepositoryCreate`: Creating pull sources
  - Basic authentication
  - Header authentication
  - Inactive sources
- `TestImagePullSourceRepositoryGetById`: Retrieving sources by ID
  - Found cases
  - Not found cases
- `TestImagePullSourceRepositoryGetAllActive`: Listing active sources
- `TestImagePullSourceRepositoryUpdateLastPulled`: Updating sync progress
- `TestImagePullSourceRepositoryUpdateActiveStatus`: Toggling active status

**Coverage:** 12 tests

### 3. HttpDirectoryGateway Tests (`test_http_directory_gateway.py`)

Tests the HTTP directory listing gateway implementation.

**Test Classes:**
- `TestHttpDirectoryGatewayInit`: Initialization with different auth types
  - Basic auth
  - Header auth
  - No auth
  - URL normalization
- `TestHttpDirectoryGatewayListFiles`: Directory listing
  - Successful listing
  - Filtering non-images
  - HTTP error handling
  - Empty directory
  - Sorting by filename
- `TestHttpDirectoryGatewayDownloadFile`: File downloading
  - Successful download
  - HTTP error handling
- `TestHttpDirectoryGatewayIsImageFile`: Image file detection
  - Various image formats
  - Non-image files
- `TestHttpDirectoryGatewayFromPullSource`: Factory method
- `TestHttpDirectoryGatewayGetNewFiles`: New file detection
  - No previous pull
  - After specific file
  - Last pulled file not found

**Coverage:** 20 tests

### 4. ImagePullTasks Tests (`test_image_pull_tasks.py`)

Tests the Celery task that runs automated syncing.

**Test Class:**
- `TestPullAllSourcesTask`: Celery beat task
  - Successful execution
  - No sources available
  - Error handling
  - Default parameters
  - Session cleanup
  - Totals calculation

**Coverage:** 6 tests

## Integration Tests

### 5. ImagePullController Tests (`test_image_pull_controller.py`)

Tests the REST API endpoints end-to-end.

**Test Classes:**
- `TestCreatePullSource`: POST /image-pull-sources/
  - Basic auth creation
  - Header auth creation
  - Inactive source creation
  - Authentication requirement
- `TestListPullSources`: GET /image-pull-sources/
  - Empty list
  - Multiple sources
  - Authentication requirement
- `TestProcessPullSource`: POST /image-pull-sources/{id}/process
  - Successful manual sync
  - Source not found
  - Authentication requirement
- `TestTogglePullSource`: PATCH /image-pull-sources/{id}/toggle
  - Toggle to inactive
  - Toggle to active
  - Source not found
  - Authentication requirement

**Coverage:** 11 tests

## Test Patterns Used

### Fixtures
- `mock_session`: Mocked database session
- `mock_repository`: Mocked repository
- `mock_image_service`: Mocked image service
- `mock_gateway`: Mocked gateway
- `sample_pull_source`: Sample pull source object
- `sample_image_files`: Sample image file list

### Mocking Strategy
- Uses `pytest.MonkeyPatch` for patching dependencies
- Uses `Mock` from `unittest.mock` for creating test doubles
- Follows project conventions (prefer `Mock` over `MagicMock`)

### Testing Principles
- Tests follow AAA pattern (Arrange, Act, Assert)
- Each test has a single responsibility
- Tests are independent and can run in any order
- Use descriptive test names that explain what is being tested
- Comprehensive error case coverage
- Follow ReST docstring format as per project standards

## Running the Tests

### Run all image pull tests:
```bash
make backend-test
```

### Run only unit tests:
```bash
cd backend
PYTHONPATH=src uv run pytest tests/unit/api/image_pull_sources/ -v
```

### Run only integration tests:
```bash
cd backend
PYTHONPATH=src uv run pytest tests/integration/api/image_pull_sources/ -v
```

### Run with coverage:
```bash
cd backend
PYTHONPATH=src uv run pytest tests/unit/api/image_pull_sources/ --cov=src/api/image_pull_sources --cov-report=html
```

## Test Results

All 49 unit tests pass successfully:
- HttpDirectoryGateway: 20/20 ✓
- ImagePullService: 11/11 ✓
- ImagePullSourceRepository: 12/12 ✓
- ImagePullTasks: 6/6 ✓

## Database Cleanup

The `conftest.py` has been updated to include `ImagePullSource` cleanup between tests:

```python
from src.api.image_pull_sources.image_pull_source_models import ImagePullSource

db.query(ImagePullSource).delete()
```

This ensures tests start with a clean slate and don't interfere with each other.

## Continuous Integration

These tests are automatically run as part of the project's test suite and should be kept green. Any new functionality added to image pull sources should include corresponding tests following these patterns.
