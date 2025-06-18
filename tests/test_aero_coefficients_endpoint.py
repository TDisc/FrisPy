import json

# client fixture is provided by conftest.py

def test_aero_coefficients_success(client):
    """Test successful retrieval of aerodynamic coefficients."""
    flight_numbers = {"speed": 10, "glide": 5, "turn": -1, "fade": 2}
    response = client.post("/api/aero_coefficients", json={"flight_numbers": flight_numbers})

    assert response.status_code == 200
    data = json.loads(response.data)

    assert isinstance(data, dict)
    # Check for 181 keys, from -90 to 90 inclusive
    assert len(data.keys()) == 181
    assert "-90" in data
    assert "0" in data
    assert "90" in data

    # Check structure for a sample angle
    sample_angle_data = data["0"]
    assert isinstance(sample_angle_data, dict)
    assert "lift" in sample_angle_data
    assert "drag" in sample_angle_data
    assert "pitch" in sample_angle_data

    # Check data types for coefficients
    assert isinstance(sample_angle_data["lift"], (int, float))
    assert isinstance(sample_angle_data["drag"], (int, float))
    assert isinstance(sample_angle_data["pitch"], (int, float))

def test_aero_coefficients_missing_flight_numbers(client):
    """Test error response when flight_numbers are missing."""
    response = client.post("/api/aero_coefficients", json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Missing flight_numbers in request body"

def test_aero_coefficients_invalid_flight_numbers_type(client):
    """Test error response when flight_numbers is not an object."""
    response = client.post("/api/aero_coefficients", json={"flight_numbers": "invalid_type"})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "flight_numbers must be an object"

def test_aero_coefficients_invalid_flight_numbers_content(client):
    """Test error response for invalid content in flight_numbers (e.g., missing fields)."""
    # This test assumes Discs.from_flight_numbers will raise an error if fields are missing.
    # The exact error message might depend on the frispy library's implementation.
    flight_numbers = {"speed": 10} # Missing glide, turn, fade
    response = client.post("/api/aero_coefficients", json={"flight_numbers": flight_numbers})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    # The error message from Discs.from_flight_numbers can be specific.
    # For now, we check that it starts with "Invalid flight_numbers:"
    assert data["error"].startswith("Invalid flight_numbers:")
