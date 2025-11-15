#!/bin/bash

# Simple curl commands to test the Wildlife Camera API
# Run these commands one by one, replacing the IDs as needed

API_BASE="http://localhost:8000"

echo "=== 1. Create location 'camera1' ==="
curl -X POST "${API_BASE}/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "camera1",
    "longitude": 9.302881164301331,
    "latitude": 52.09403285834788,
    "description": "Test camera location"
  }'

echo -e "\n\n"

echo "=== 2. Upload image to location ==="
echo "Replace LOCATION_ID with the ID from step 1"
echo "Replace IMAGE_PATH with your image file path"
echo ""
echo "curl -X POST \"${API_BASE}/locations/LOCATION_ID/image\" \\"
echo "  -F \"file=@../test_bilder/Aufnahme_250603_0253_BYWP9.jpg\""

echo -e "\n\n"

echo "=== 3. Get image with detections ==="
echo "Replace IMAGE_ID with the ID from step 2"
echo ""
echo "curl -X GET \"${API_BASE}/images/IMAGE_ID\""

echo -e "\n\n"

echo "=== Bonus: Get all locations ==="
curl -X GET "${API_BASE}/locations"

echo -e "\n\n"

echo "=== Bonus: Get aggregated spottings ==="
curl -X GET "${API_BASE}/spottings"
