# Wildlife Camera API - cURL Examples

## Quick Start Scripts

Two bash scripts are provided for testing:

### 1. Automated Flow Test (`test_api_flow.sh`)
Runs the complete flow automatically:
```bash
./test_api_flow.sh
```

This script will:
- Create a location called "camera1"
- Upload an image from test_bilder directory
- Retrieve the image with detections
- Display a summary

### 2. Simple Commands (`test_api_simple.sh`)
Shows individual curl commands for manual testing:
```bash
./test_api_simple.sh
```

---

## Manual cURL Commands

### Step 1: Create Location "camera1"

```bash
curl -X POST "http://localhost:8000/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "camera1",
    "longitude": 10.5,
    "latitude": 52.3,
    "description": "Test camera location"
  }'
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "camera1",
  "longitude": 10.5,
  "latitude": 52.3,
  "description": "Test camera location"
}
```

**Save the `id` value - you'll need it for the next step!**

---

### Step 2: Upload Image to Location

Replace `LOCATION_ID` with the ID from Step 1:

```bash
curl -X POST "http://localhost:8000/locations/LOCATION_ID/image" \
  -F "file=@../test_bilder/Aufnahme_250603_0253_BYWP9.jpg"
```

**Example with actual ID:**
```bash
curl -X POST "http://localhost:8000/locations/550e8400-e29b-41d4-a716-446655440000/image" \
  -F "file=@../test_bilder/Aufnahme_250603_0253_BYWP9.jpg"
```

**Expected Response:**
```json
{
  "image_id": "660e8400-e29b-41d4-a716-446655440001",
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "upload_timestamp": "2025-11-08T13:30:45.123456",
  "detections_count": 2
}
```

**Save the `image_id` value - you'll need it for the next step!**

---

### Step 3: Get Specific Image with Detections

Replace `IMAGE_ID` with the ID from Step 2:

```bash
curl -X GET "http://localhost:8000/images/IMAGE_ID"
```

**Example with actual ID:**
```bash
curl -X GET "http://localhost:8000/images/660e8400-e29b-41d4-a716-446655440001"
```

**Expected Response:**
```json
{
  "image_id": "660e8400-e29b-41d4-a716-446655440001",
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "raw": "iVBORw0KGgoAAAANSUhEUgAA...",
  "upload_timestamp": "2025-11-08T13:30:45.123456",
  "detections": [
    {
      "species": "deer",
      "confidence": 0.85,
      "bounding_box": {
        "x": 100,
        "y": 150,
        "width": 200,
        "height": 250
      },
      "classification_model": "AI4GAmazonRainforest",
      "is_uncertain": false
    }
  ]
}
```

---

## Additional Useful Commands

### Get All Locations
```bash
curl -X GET "http://localhost:8000/locations"
```

### Get Specific Location
```bash
curl -X GET "http://localhost:8000/locations/LOCATION_ID"
```

### Get Aggregated Spottings (for map view)
```bash
curl -X GET "http://localhost:8000/spottings"
```

**Response:**
```json
[
  {
    "pos": {
      "longitude": 10.5,
      "latitude": 52.3
    },
    "animals": ["deer", "fox"],
    "ts_last_spotting": "2025-11-08T13:30:45.123456",
    "ts_last_image": "2025-11-08T13:30:45.123456",
    "image_id": "660e8400-e29b-41d4-a716-446655440001"
  }
]
```

### API Root (Info)
```bash
curl -X GET "http://localhost:8000/"
```

---

## Pretty Print with jq

If you have `jq` installed, you can pretty-print the JSON responses:

```bash
curl -X GET "http://localhost:8000/locations" | jq '.'
```

---

## Complete Flow Example

Here's a complete example with actual commands (replace IDs as you go):

```bash
# 1. Create location
LOCATION_RESPONSE=$(curl -s -X POST "http://localhost:8000/locations" \
  -H "Content-Type: application/json" \
  -d '{"name": "camera1", "longitude": 10.5, "latitude": 52.3, "description": "Test camera"}')

echo $LOCATION_RESPONSE

# Extract location ID (requires jq)
LOCATION_ID=$(echo $LOCATION_RESPONSE | jq -r '.id')
echo "Location ID: $LOCATION_ID"

# 2. Upload image
IMAGE_RESPONSE=$(curl -s -X POST "http://localhost:8000/locations/${LOCATION_ID}/image" \
  -F "file=@../test_bilder/Aufnahme_250603_0253_BYWP9.jpg")

echo $IMAGE_RESPONSE

# Extract image ID (requires jq)
IMAGE_ID=$(echo $IMAGE_RESPONSE | jq -r '.image_id')
echo "Image ID: $IMAGE_ID"

# 3. Get image with detections
curl -X GET "http://localhost:8000/images/${IMAGE_ID}" | jq '.'
```

---

## Testing with Different Images

You can test with any image from the bilder or test_bilder directories:

```bash
# Using different test images
curl -X POST "http://localhost:8000/locations/LOCATION_ID/image" \
  -F "file=@../test_bilder/Aufnahme_250605_2029_BYWP9.jpg"

curl -X POST "http://localhost:8000/locations/LOCATION_ID/image" \
  -F "file=@../test_bilder/Aufnahme_250612_0001_BYWP9.jpg"
```

---

## Error Handling Examples

### 404 - Location Not Found
```bash
curl -X POST "http://localhost:8000/locations/invalid-uuid/image" \
  -F "file=@../test_bilder/Aufnahme_250603_0253_BYWP9.jpg"
```

**Response:**
```json
{
  "detail": "Location with id invalid-uuid not found"
}
```

### 404 - Image Not Found
```bash
curl -X GET "http://localhost:8000/images/invalid-uuid"
```

**Response:**
```json
{
  "detail": "Image with id invalid-uuid not found"
}
```

---

## Notes

- Make sure the API server is running: `uvicorn api.main:app --reload`
- The API runs on `http://localhost:8000` by default
- Image processing happens synchronously, so uploads may take a few seconds
- All IDs are UUIDs in the format: `550e8400-e29b-41d4-a716-446655440000`
- Images are stored as base64 in the database
- The `raw` field in image responses contains the base64-encoded image data
