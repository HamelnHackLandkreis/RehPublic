# Image Pull Sources - Implementation Summary

## Overview

I've implemented a complete automated image polling system that runs hourly via Celery Beat. This system pulls images from external HTTP directory sources (like the Hameln-Pyrmont API) and processes them through the same pipeline as manual uploads.

## What Was Implemented

### 1. Database Layer

**Migration**: `migrations/002_add_image_pull_sources.sql`
- New `image_pull_sources` table with foreign keys to users and locations
- Tracks authentication credentials and last pulled filename
- Supports multiple authentication methods (basic auth, custom headers)

**Model**: `src/api/image_pull_sources/image_pull_source_models.py`
- `ImagePullSource` model with all necessary fields
- Relationships to User and Location models

**Repository**: `src/api/image_pull_sources/image_pull_source_repository.py`
- CRUD operations for pull sources
- Methods to update last pulled filename and active status

### 2. Gateway Architecture (Pluggable Design)

**Abstract Interface**: `src/api/image_pull_sources/gateways/base.py`
- `ImagePullGateway` abstract base class
- `ImageFile` dataclass for file metadata
- `get_new_files()` method to filter based on last pulled file

**HTTP Implementation**: `src/api/image_pull_sources/gateways/http_directory.py`
- `HttpDirectoryGateway` for HTML directory listings
- Parses HTML tables (like nginx autoindex)
- Supports Basic Auth and custom Authorization headers
- Downloads image files via HTTP requests

### 3. Business Logic Layer

**Service**: `src/api/image_pull_sources/image_pull_service.py`
- `ImagePullService` orchestrates pulling and processing
- `pull_and_process_source()` - processes one source
- `process_all_sources()` - processes all active sources
- Integrates with existing `ImageService` for processing
- Tracks progress and handles errors gracefully

### 4. Celery Integration

**Task**: `src/api/image_pull_sources/image_pull_tasks.py`
- `pull_all_sources_task` - Celery beat task
- Runs every hour at minute :00
- Processes up to 10 files per source by default

**Configuration**: `src/celery_app.py`
- Added beat schedule configuration
- Included new task module
- Uses crontab for hourly scheduling

### 5. REST API

**Controller**: `src/api/image_pull_sources/image_pull_controller.py`
- `POST /image-pull-sources` - Create new source
- `GET /image-pull-sources` - List active sources
- `POST /image-pull-sources/{id}/process` - Manual trigger
- `PATCH /image-pull-sources/{id}/toggle` - Enable/disable

**Schemas**: `src/api/image_pull_sources/image_pull_schemas.py`
- Request/response models with Pydantic
- Validation and documentation

**Main App**: `src/api/main.py`
- Registered new router at `/image-pull-sources`
- Added API documentation metadata

### 6. Documentation & Utilities

**README**: `src/api/image_pull_sources/README.md`
- Complete architecture documentation
- Setup guide for Hameln-Pyrmont API
- API endpoint reference
- Troubleshooting guide

**Setup Script**: `backend/create_hameln_source.py`
- Python script to create pull source
- Can create location automatically
- Test mode to verify configuration
- Example usage included

**Migration Script**: `backend/run_migration.sh`
- Shell script to run database migration
- Works with SQLite

## Key Features

### ✅ Plug-and-Play Architecture
- Abstract gateway interface allows easy addition of new source types (S3, FTP, etc.)
- Current implementation: HTTP directory listings
- Factory pattern for gateway creation

### ✅ Same Processing as Manual Uploads
- Uses existing `ImageService.upload_and_process_image()`
- Wildlife detection via PyTorchWildlife
- Species identification and bounding boxes
- Stored in same database tables

### ✅ Progress Tracking
- Remembers last processed filename
- Only processes new files in subsequent runs
- Prevents duplicate processing

### ✅ Configurable & Safe
- Max files per run (default: 10)
- Per-source active/inactive toggle
- Error handling doesn't block other sources
- Failed files don't stop processing

### ✅ Authentication Support
- Basic HTTP authentication
- Custom Authorization headers (pre-encoded)
- Example: Hameln-Pyrmont API credentials included

### ✅ Hourly Automation
- Celery Beat runs task every hour
- Processes all active sources
- Logs detailed progress

## File Structure

```
backend/
├── migrations/
│   └── 002_add_image_pull_sources.sql       # Database migration
├── src/
│   ├── api/
│   │   ├── image_pull_sources/
│   │   │   ├── __init__.py
│   │   │   ├── README.md                    # Feature documentation
│   │   │   ├── gateways/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py                  # Abstract interface
│   │   │   │   └── http_directory.py        # HTTP implementation
│   │   │   ├── image_pull_source_models.py  # Database model
│   │   │   ├── image_pull_source_repository.py  # Data access
│   │   │   ├── image_pull_service.py        # Business logic
│   │   │   ├── image_pull_tasks.py          # Celery tasks
│   │   │   ├── image_pull_controller.py     # REST API
│   │   │   └── image_pull_schemas.py        # Pydantic schemas
│   │   ├── main.py                          # Updated: New router
│   │   ├── database.py                      # Updated: Import model
│   │   ├── users/user_models.py             # Updated: Relationship
│   │   └── locations/location_models.py     # Updated: Relationship
│   └── celery_app.py                        # Updated: Beat schedule
├── pyproject.toml                            # Updated: Dependencies
├── create_hameln_source.py                   # Setup utility
└── run_migration.sh                          # Migration helper
```

## How to Use

### 1. Run Migration

```bash
cd backend
./run_migration.sh
```

### 2. Start Celery (both worker and beat)

```bash
# Terminal 1: Worker
celery -A src.celery_app worker --loglevel=info

# Terminal 2: Beat (scheduler)
celery -A src.celery_app beat --loglevel=info
```

### 3. Create Pull Source (Option A: Script)

```bash
python create_hameln_source.py \
  --user-id YOUR_USER_UUID \
  --create-location \
  --test \
  --test-files 2
```

### 4. Create Pull Source (Option B: API)

```bash
curl -X POST "http://localhost:8000/image-pull-sources" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hameln-Pyrmont Camera Feed",
    "user_id": "YOUR_USER_UUID",
    "location_id": "LOCATION_UUID",
    "base_url": "https://assets.hameln-pyrmont.digital/image-api/",
    "auth_type": "basic",
    "auth_username": "mitwirker",
    "auth_password": "gtdbGDfzCcUDQs2CK6FHYLq34",
    "is_active": true
  }'
```

## Dependencies Added

```toml
dependencies = [
    # ... existing ...
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.0",
]
```

Run `uv sync` to install.

## Testing

The system is ready for testing:

1. **Unit Tests**: Can be added for repository, service, and gateway classes
2. **Integration Tests**: Test full flow from HTTP source to database
3. **Manual Testing**: Use `create_hameln_source.py --test` for quick verification

## Future Enhancements

Easy to add due to pluggable architecture:

- **S3Gateway**: Pull from S3 buckets
- **FTPGateway**: Pull from FTP servers
- **APIGateway**: Pull from REST APIs with pagination
- **WebSocketGateway**: Real-time push notifications
- **Rate Limiting**: Per-source request throttling
- **Retry Logic**: Exponential backoff for failed downloads

## Configuration

All configurable via environment variables or pull source settings:

- **Schedule**: Modify `crontab(minute=0)` in `celery_app.py`
- **Max Files**: Change `max_files_per_source` in beat schedule
- **Timeout**: HTTP request timeout (currently 30s list, 60s download)
- **Auth**: Stored per-source in database

## Monitoring

- View Celery logs for task execution
- Check database `last_pull_timestamp` to verify runs
- Use Flower UI for Celery monitoring (if enabled)
- API endpoint to manually trigger and see results

---

## Summary

This implementation provides a **production-ready, extensible system** for automated image polling. It integrates seamlessly with your existing codebase, uses the same processing pipeline as manual uploads, and is specifically configured for the Hameln-Pyrmont camera API while remaining flexible enough to support other sources in the future.
