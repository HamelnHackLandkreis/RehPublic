# Image Pull Sources - Automated Image Polling

This feature enables automatic polling and processing of images from external HTTP directory sources. Images are fetched hourly by a Celery Beat scheduler and processed through the same pipeline as manually uploaded images.

## Architecture

The implementation follows a clean, pluggable architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     Celery Beat Schedule                     │
│                    (Runs every hour)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 Image Pull Task                              │
│         (image_pull_tasks.py)                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Image Pull Service                              │
│         (image_pull_service.py)                              │
│  • Coordinates pulling and processing                        │
│  • Tracks last processed file                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Gateway Interface (Abstract)                    │
│         (gateways/base.py)                                   │
│  • Pluggable design for different sources                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         HTTP Directory Gateway Implementation                │
│         (gateways/http_directory.py)                         │
│  • Parses HTML directory listings                            │
│  • Supports Basic Auth & Custom Headers                      │
│  • Downloads image files                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Image Service                                   │
│         (image_service.py)                                   │
│  • Same processing as manual uploads                         │
│  • Wildlife detection & species identification               │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

```sql
CREATE TABLE image_pull_sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL,              -- User to associate images with
    location_id TEXT NOT NULL,          -- Location to associate images with
    base_url TEXT NOT NULL,             -- URL to poll
    auth_type TEXT NOT NULL,            -- 'basic', 'header', or 'none'
    auth_username TEXT,                 -- For basic auth
    auth_password TEXT,                 -- For basic auth
    auth_header TEXT,                   -- Pre-encoded auth header
    last_pulled_filename TEXT,          -- Tracks progress
    last_pull_timestamp TIMESTAMP,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (location_id) REFERENCES locations(id)
);
```

## Example: Setting Up for Hameln-Pyrmont API

### Step 1: Create Location (if not exists)

```bash
curl -X POST "https://your-api.com/locations" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hameln-Pyrmont Wildlife Camera",
    "latitude": 52.1035,
    "longitude": 9.3476,
    "description": "Automated camera from Hameln-Pyrmont"
  }'
```

### Step 2: Create Image Pull Source

```bash
curl -X POST "https://your-api.com/image-pull-sources" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hameln-Pyrmont Camera Feed",
    "location_id": "LOCATION_UUID_FROM_STEP_1",
    "base_url": "https://assets.hameln-pyrmont.digital/image-api/",
    "auth_type": "basic",
    "auth_username": "mitwirker",
    "auth_password": "gtdbGDfzCcUDQs2CK6FHYLq34",
    "is_active": true
  }'
```

**Note**: The `user_id` is automatically extracted from the JWT token (authenticated user), so you don't need to include it in the request body.

Or using pre-encoded Basic Auth header:

```bash
curl -X POST "https://your-api.com/image-pull-sources" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hameln-Pyrmont Camera Feed",
    "location_id": "LOCATION_UUID_FROM_STEP_1",
    "base_url": "https://assets.hameln-pyrmont.digital/image-api/",
    "auth_type": "header",
    "auth_header": "Basic bWl0d2lya2VyOmd0ZGJHRGZ6Q2NVRFFzMkNLNkZIWUxxMzQ=",
    "is_active": true
  }'
```

### Step 3: Manual Test (Optional)

Trigger a manual pull to test the configuration:

```bash
curl -X POST "https://your-api.com/image-pull-sources/SOURCE_UUID/process?max_files=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## API Endpoints

### Create Image Pull Source
- **POST** `/image-pull-sources`
- Creates a new image pull source configuration

### List Active Sources
- **GET** `/image-pull-sources`
- Lists all active image pull sources

### Manually Process Source
- **POST** `/image-pull-sources/{source_id}/process?max_files=10`
- Manually trigger processing of a specific source

### Toggle Source Active Status
- **PATCH** `/image-pull-sources/{source_id}/toggle?is_active=true`
- Enable or disable a source

## Celery Beat Schedule

The task runs automatically every hour:

```python
celery_app.conf.beat_schedule = {
    "pull-images-every-hour": {
        "task": "image_pull.pull_all_sources",
        "schedule": crontab(minute=0),  # Every hour at :00
        "kwargs": {"max_files_per_source": 10},
    },
}
```

## Starting Celery Beat

To enable automated polling, start the Celery beat scheduler:

```bash
# Start Celery worker (processes tasks)
celery -A src.celery_app worker --loglevel=info

# Start Celery beat (schedules tasks)
celery -A src.celery_app beat --loglevel=info
```

Or use Docker Compose (if configured):

```yaml
celery-beat:
  build: ./backend
  command: celery -A src.celery_app beat --loglevel=info
  depends_on:
    - redis
  environment:
    - REDIS_URL=redis://redis:6379/0
```

## How It Works

1. **Every Hour**: Celery Beat triggers the `pull_all_sources_task`
2. **Query Active Sources**: Retrieves all sources where `is_active=true`
3. **For Each Source**:
   - Creates appropriate gateway (e.g., HttpDirectoryGateway)
   - Lists all files from the directory
   - Filters to new files (after `last_pulled_filename`)
   - Downloads and processes up to `max_files_per_source` (default: 10)
   - Updates `last_pulled_filename` after each successful file
4. **Process Images**: Uses the same `ImageService.upload_and_process_image()` as manual uploads
5. **Results**: Each image gets wildlife detection and is stored with spottings

## Extending with New Gateway Types

The gateway interface is abstract and pluggable. To add support for S3, FTP, or other sources:

```python
# Example: S3 Gateway
from src.api.image_pull_sources.gateways.base import ImageFile, ImagePullGateway

class S3Gateway(ImagePullGateway):
    def __init__(self, bucket_name: str, access_key: str, secret_key: str):
        self.s3_client = boto3.client('s3', ...)

    def list_files(self) -> list[ImageFile]:
        # List objects from S3 bucket
        ...

    def download_file(self, image_file: ImageFile) -> bytes:
        # Download from S3
        ...
```

Then update the service to use the new gateway:

```python
def create_gateway(self, pull_source: ImagePullSource) -> ImagePullGateway:
    if pull_source.source_type == "s3":
        return S3Gateway.from_pull_source(pull_source)
    elif pull_source.source_type == "http":
        return HttpDirectoryGateway.from_pull_source(pull_source)
    # ... more types
```

## Monitoring

Check Celery logs for processing status:

```bash
# View worker logs
docker logs -f wildlife-processor-celery-worker

# View beat logs
docker logs -f wildlife-processor-celery-beat

# Monitor with Flower (if enabled)
open http://localhost:5555
```

## Security Considerations

- **Credentials Storage**: Consider using environment variables or secrets management for sensitive credentials
- **HTTPS Only**: Always use HTTPS URLs for external sources
- **Rate Limiting**: The `max_files_per_source` parameter prevents overwhelming the system
- **Error Handling**: Failed files don't block subsequent files; processing continues

## Troubleshooting

### No Images Being Pulled

1. Check if source is active: `GET /image-pull-sources`
2. Verify Celery beat is running: `celery -A src.celery_app inspect scheduled`
3. Check logs for errors
4. Manually trigger: `POST /image-pull-sources/{id}/process`

### Authentication Errors

- Verify credentials are correct
- Test with `curl` directly to the source
- Check if auth_type matches the requirement (basic vs header)

### Images Not Appearing After Pull

- Check `last_pulled_filename` is being updated
- Verify the location_id exists
- Check image processing logs for detection errors

## Development

Run migrations:

```bash
sqlite3 wildlife_camera.db < migrations/002_add_image_pull_sources.sql
```

Install dependencies:

```bash
uv sync
```

Run tests (when implemented):

```bash
pytest tests/unit/test_image_pull_*.py
pytest tests/integration/test_image_pull_integration.py
```
