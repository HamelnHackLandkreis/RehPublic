#!/bin/bash
# Create a random location using curl

# Generate random coordinates (Germany area: lat 47-55, lon 5-15)
RANDOM_LAT=$(awk "BEGIN {printf \"%.6f\", 47 + rand() * 8}")
RANDOM_LON=$(awk "BEGIN {printf \"%.6f\", 5 + rand() * 10}")
TIMESTAMP=$(date +%s)

curl -X POST "http://localhost:8000/locations" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Random Location ${TIMESTAMP}\",
    \"longitude\": ${RANDOM_LON},
    \"latitude\": ${RANDOM_LAT},
    \"description\": \"Randomly generated location for testing\"
  }"
