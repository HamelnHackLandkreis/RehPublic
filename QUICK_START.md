# Quick Start Guide - Image Pull Sources

## Prerequisites

1. Database migrations applied
2. Redis running (for Celery)
3. Backend API running
4. User account created

## Step 1: Run Migration

```bash
cd backend
./run_migration.sh
```

## Step 2: Start Celery Services

You need **two terminals** for Celery:

**Terminal 1 - Worker** (processes tasks):
```bash
cd backend
celery -A src.celery_app worker --loglevel=info
```

**Terminal 2 - Beat** (schedules hourly tasks):
```bash
cd backend
celery -A src.celery_app beat --loglevel=info
```

## Step 3: Create Image Pull Source

### Option A: Using the Helper Script (Recommended)

```bash
# Get your user ID first (from your JWT token or database)
USER_ID="your-user-uuid-here"

# Create location and test the pull (does NOT activate)
python backend/create_hameln_source.py \
  --user-id $USER_ID \
  --create-location \
  --test \
  --test-files 2

# If test succeeds, activate it via API:
curl -X PATCH "http://localhost:8000/image-pull-sources/SOURCE_ID/toggle?is_active=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Option B: Using the API Directly

```bash
# 1. Create a location (if needed)
LOCATION_RESPONSE=$(curl -X POST "http://localhost:8000/locations" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hameln-Pyrmont Wildlife Camera",
    "latitude": 52.1035,
    "longitude": 9.3476,
    "description": "Automated wildlife camera"
  }')

LOCATION_ID=$(echo $LOCATION_RESPONSE | jq -r '.id')

# 2. Create the pull source
curl -X POST "http://localhost:8000/image-pull-sources" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Hameln-Pyrmont Camera Feed\",
    \"location_id\": \"$LOCATION_ID\",
    \"base_url\": \"https://assets.hameln-pyrmont.digital/image-api/\",
    \"auth_type\": \"basic\",
    \"auth_username\": \"mitwirker\",
    \"auth_password\": \"gtdbGDfzCcUDQs2CK6FHYLq34\",
    \"is_active\": true
  }"
```

**Note**: `user_id` is automatically extracted from your JWT token - no need to include it!

## Step 4: Verify Setup

### Check Active Sources
```bash
curl -X GET "http://localhost:8000/image-pull-sources" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Manual Test (processes 2 files immediately)
```bash
curl -X POST "http://localhost:8000/image-pull-sources/SOURCE_ID/process?max_files=2" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Check Celery Beat Schedule
```bash
celery -A src.celery_app inspect scheduled
```

## Step 5: Monitor

Watch Celery logs for hourly processing:
```bash
# Worker logs show processing details
tail -f celery-worker.log

# Beat logs show scheduling
tail -f celery-beat.log
```

## Troubleshooting

### Problem: No images being pulled

**Check if Celery Beat is running:**
```bash
ps aux | grep "celery.*beat"
```

**Check if source is active:**
```bash
curl -X GET "http://localhost:8000/image-pull-sources" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" | jq
```

**Manually trigger to see error:**
```bash
curl -X POST "http://localhost:8000/image-pull-sources/SOURCE_ID/process?max_files=1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Problem: Authentication errors

Test credentials directly:
```bash
curl -u "mitwirker:gtdbGDfzCcUDQs2CK6FHYLq34" \
  https://assets.hameln-pyrmont.digital/image-api/
```

### Problem: Images pulled but not processed

Check worker logs for processing errors:
```bash
celery -A src.celery_app events
```

## Configuration

### Change Schedule

Edit `backend/src/celery_app.py`:

```python
celery_app.conf.beat_schedule = {
    "pull-images-every-hour": {
        "task": "image_pull.pull_all_sources",
        "schedule": crontab(minute=0),  # Every hour
        # OR: crontab(minute=0, hour='*/2')  # Every 2 hours
        # OR: crontab(minute=0, hour=8)       # Daily at 8am
        "kwargs": {"max_files_per_source": 10},
    },
}
```

### Change Max Files Per Run

Two options:

1. **In beat schedule** (affects automatic runs):
   ```python
   "kwargs": {"max_files_per_source": 20},  # Process up to 20 files
   ```

2. **In manual API call** (one-time):
   ```bash
   curl -X POST ".../process?max_files=50" ...
   ```

## Complete Docker Compose Example

Add to your `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery-worker:
    build: ./backend
    command: celery -A src.celery_app worker --loglevel=info
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://...
    volumes:
      - ./backend:/app

  celery-beat:
    build: ./backend
    command: celery -A src.celery_app beat --loglevel=info
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://...
    volumes:
      - ./backend:/app
```

Then:
```bash
docker-compose up -d redis celery-worker celery-beat
```

## Next Steps

1. ✅ Monitor first automatic run (wait for next hour)
2. ✅ Check database for new images
3. ✅ Verify detections are being created
4. ✅ Set up monitoring/alerting if needed
5. ✅ Add more sources if needed

## Getting Help

- Check logs: `backend/src/api/image_pull_sources/README.md`
- Architecture: `IMPLEMENTATION_SUMMARY.md`
- Issues: Check Celery worker logs for detailed errors
