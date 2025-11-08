#!/bin/bash

# Wildlife Camera API - Test Flow Script
# This script demonstrates the complete workflow:
# 1. Create a location
# 2. Upload an image to that location
# 3. Retrieve the image with detections

set -e  # Exit on error

API_BASE="http://localhost:8000"

echo "=========================================="
echo "Wildlife Camera API - Test Flow"
echo "=========================================="
echo ""

# Step 1: Create a location called "camera1"
echo "Step 1: Creating location 'camera1'..."
LOCATION_RESPONSE=$(curl -s -X POST "${API_BASE}/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "camera1",
    "longitude": 10.5,
    "latitude": 52.3,
    "description": "Test camera location"
  }')

echo "Response: $LOCATION_RESPONSE"
echo ""

# Extract location_id from response
LOCATION_ID=$(echo $LOCATION_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$LOCATION_ID" ]; then
  echo "Error: Failed to create location or extract location ID"
  exit 1
fi

echo "✓ Location created with ID: $LOCATION_ID"
echo ""

# Step 2: Upload an image to this location
echo "Step 2: Uploading image to location $LOCATION_ID..."

# Check if a test image exists, otherwise use one from the test_bilder directory
if [ -f "../test_bilder/Aufnahme_250603_0253_BYWP9.jpg" ]; then
  IMAGE_PATH="../test_bilder/Aufnahme_250603_0253_BYWP9.jpg"
elif [ -f "../bilder/Aufnahme_250601_0857_BYWP9.jpg" ]; then
  IMAGE_PATH="../bilder/Aufnahme_250601_0857_BYWP9.jpg"
else
  echo "Error: No test image found. Please provide an image path."
  exit 1
fi

echo "Using image: $IMAGE_PATH"

UPLOAD_RESPONSE=$(curl -s -X POST "${API_BASE}/locations/${LOCATION_ID}/image" \
  -F "file=@${IMAGE_PATH}")

echo "Response: $UPLOAD_RESPONSE"
echo ""

# Extract image_id from response
IMAGE_ID=$(echo $UPLOAD_RESPONSE | grep -o '"image_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$IMAGE_ID" ]; then
  echo "Error: Failed to upload image or extract image ID"
  exit 1
fi

echo "✓ Image uploaded and processed with ID: $IMAGE_ID"
echo ""

# Step 3: Get the specific image with detections
echo "Step 3: Retrieving image $IMAGE_ID with detections..."
IMAGE_RESPONSE=$(curl -s -X GET "${API_BASE}/images/${IMAGE_ID}")

# Pretty print the response (if jq is available)
if command -v jq &> /dev/null; then
  echo "$IMAGE_RESPONSE" | jq '.'
else
  echo "$IMAGE_RESPONSE"
fi
echo ""

# Extract detection count
DETECTION_COUNT=$(echo $IMAGE_RESPONSE | grep -o '"detections":\[[^]]*\]' | grep -o '{' | wc -l | tr -d ' ')

echo "✓ Image retrieved successfully"
echo "  - Image ID: $IMAGE_ID"
echo "  - Location ID: $LOCATION_ID"
echo "  - Detections found: $DETECTION_COUNT"
echo ""

echo "=========================================="
echo "Test flow completed successfully!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  Location ID: $LOCATION_ID"
echo "  Image ID: $IMAGE_ID"
echo "  Detections: $DETECTION_COUNT"
