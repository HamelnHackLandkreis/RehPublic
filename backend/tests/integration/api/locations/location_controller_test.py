"""Integration tests for location controller endpoints."""


def test_create_and_get_locations(client):
    """Test creating and retrieving locations."""
    # Create a location
    location_data = {
        "name": "Forest Trail 1",
        "longitude": 10.5,
        "latitude": 52.3,
        "description": "Trail camera in forest",
    }

    response = client.post("/locations", json=location_data)
    assert response.status_code == 201
    created_location = response.json()
    assert created_location["name"] == location_data["name"]
    assert created_location["longitude"] == location_data["longitude"]
    assert created_location["latitude"] == location_data["latitude"]
    assert "id" in created_location
    assert "total_unique_species" in created_location
    assert "total_spottings" in created_location
    assert created_location["total_unique_species"] == 0
    assert created_location["total_spottings"] == 0

    location_id = created_location["id"]

    # Get all locations
    response = client.get("/locations")
    assert response.status_code == 200
    locations_data = response.json()
    assert "locations" in locations_data
    assert "total_unique_species" in locations_data
    assert "total_spottings" in locations_data
    locations = locations_data["locations"]
    assert len(locations) == 1
    assert locations[0]["id"] == location_id
    assert isinstance(locations_data["total_unique_species"], int)
    assert isinstance(locations_data["total_spottings"], int)
    # Check that each location has its own totals
    assert "total_unique_species" in locations[0]
    assert "total_spottings" in locations[0]
    assert isinstance(locations[0]["total_unique_species"], int)
    assert isinstance(locations[0]["total_spottings"], int)

    # Get specific location
    response = client.get(f"/locations/{location_id}")
    assert response.status_code == 200
    location = response.json()
    assert location["id"] == location_id
    assert location["name"] == location_data["name"]
    assert "total_unique_species" in location
    assert "total_spottings" in location
    assert isinstance(location["total_unique_species"], int)
    assert isinstance(location["total_spottings"], int)
