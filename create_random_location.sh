#!/bin/bash
# Create a random location using curl

# Generate random coordinates (Germany area: lat 47-55, lon 5-15)
RANDOM_LAT=$(awk "BEGIN {printf \"%.6f\", 47 + rand() * 8}")
RANDOM_LON=$(awk "BEGIN {printf \"%.6f\", 5 + rand() * 10}")
TIMESTAMP=$(date +%s)

curl -X POST "http://localhost:8000/locations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IlJYSlNlcFVDN2pLU3FqRkI3OWpyZyJ9.eyJpc3MiOiJodHRwczovL3JlaHB1YmxpYy5ldS5hdXRoMC5jb20vIiwic3ViIjoiZ29vZ2xlLW9hdXRoMnwxMDU0MjEwNDIwNzU2NjI2MTU0NTciLCJhdWQiOlsiaHR0cHM6Ly9hcGkucmVocHVibGljLmNvbSIsImh0dHBzOi8vcmVocHVibGljLmV1LmF1dGgwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE3NjQ0MjY0NjcsImV4cCI6MTc2NDUxMjg2Nywic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsImF6cCI6IkJPcFZ3UVBnaTN5QWVhRm9BVVl0OEgySG84dHdmQXh6In0.VfUgpE90ArNEId9q406dgDw0afjgYWnj8O4-X5LTIWmRgoDXGKJhv6Z921zKVvOA2hiVvGHgCFwzrqt5Yd8bEKNHKFWBfCwoYCMflqhEttyw_XCXmJLwzBz2V_0QN_xAYWbWURdSDRq31expjPQyURRnTMqFcvCF5BgiS6Hc26TquI1jG9t87CHj8C6KkyLR_CsoSgYp-9HhnRs28sGw2XE3NRG0Nx6RUN42tJMC2n14JPCQUX2ula7SoTCM4tw4I0zSYOCTseR8mMHBsor34ThQbnGk5dQEnUepc1Dq5T63WHfxq3RIh06nW7x1UYy0a2c3YAf8-oraxT1DtxgXOQ" \
  -d "{
    \"name\": \"Random Location ${TIMESTAMP}\",
    \"longitude\": ${RANDOM_LON},
    \"latitude\": ${RANDOM_LAT},
    \"description\": \"Randomly generated location for testing\"
  }"
