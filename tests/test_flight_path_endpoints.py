import json
from unittest.mock import patch, MagicMock
import numpy as np

# client fixture is provided by conftest.py

# Helper to create mock trajectory data
def create_mock_trajectory_results():
    mock_results = MagicMock()
    # pos is often used as a list of lists directly
    mock_results.pos = np.array([[0,0,1],[1,1,0.5],[2,2,0]]).tolist()
    # times and v are iterated, and .tolist() is called on their elements
    mock_results.times = [np.array([0.0, 0.1]), np.array([0.1,0.2]), np.array([0.2,0.3])]
    mock_results.v = [np.array([10,0,0]), np.array([9,1,-1]), np.array([8,2,-2])]
    # qx, qy, qz, qw have .tolist() called on them directly
    mock_results.qx = np.array([1.0, 0.9, 0.8])
    mock_results.qy = np.array([0.0, 0.1, 0.15])
    mock_results.qz = np.array([0.0, 0.1, 0.15])
    mock_results.qw = np.array([1.0, 0.95, 0.9]) # qw typically close to 1 for non-inverted flight
    # gamma is iterated and its elements are used directly (numbers)
    mock_results.gamma = np.array([0.0, 0.05, 0.1]).tolist()
    return mock_results

@patch('service.main.compute_trajectory')
def test_flight_path_success_with_disc_name(mock_compute_trajectory, client):
    """Test successful flight path retrieval using disc_name."""
    mock_compute_trajectory.return_value = create_mock_trajectory_results()

    payload = {
        "disc_name": "ultrastar",
        "v": 20,
        "spin": -10,
        "uphill_degrees": 0,
        "hyzer_degrees": 0,
        "nose_up_degrees": 0
    }
    response = client.post("/api/flight_path", json=payload)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "p" in data
    assert "t" in data
    assert "v" in data
    assert len(data["p"]) == 3

@patch('service.main.compute_trajectory')
def test_flight_path_success_with_flight_numbers(mock_compute_trajectory, client):
    """Test successful flight path retrieval using flight_numbers."""
    mock_compute_trajectory.return_value = create_mock_trajectory_results()

    payload = {
        "flight_numbers": {"speed": 10, "glide": 5, "turn": -1, "fade": 2},
        "v": 20,
        "spin": -10,
        "uphill_degrees": 0,
        "hyzer_degrees": 0,
        "nose_up_degrees": 0
    }
    response = client.post("/api/flight_path", json=payload)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "p" in data
    assert "t" in data
    assert "v" in data
    assert len(data["p"]) == 3

def test_flight_path_missing_required_fields(client):
    """Test error response when required flight parameters are missing."""
    payload = {
        "disc_name": "ultrastar"
    }
    response = client.post("/api/flight_path", json=payload)
    assert response.status_code == 500

def test_flight_path_invalid_disc_name(client):
    """Test error response for an invalid disc_name when flight_numbers are also missing."""
    payload = {
        "disc_name": "non_existent_disc_rpslngag",
        "v": 20,
        "spin": -10,
        "uphill_degrees": 0,
        "hyzer_degrees": 0,
        "nose_up_degrees": 0
    }
    response = client.post("/api/flight_path", json=payload)
    assert response.status_code == 500

# Tests for /api/flight_paths (plural)

@patch('service.main.compute_trajectory')
def test_flight_paths_success_with_disc_names(mock_compute_trajectory, client):
    """Test successful flight paths retrieval using a list of disc_names."""
    mock_compute_trajectory.return_value = create_mock_trajectory_results()

    payload = {
        "disc_names": ["ultrastar", "wraith"],
        "v": 15,
        "spin": -12,
        "uphill_degrees": 0,
        "hyzer_degrees": 5,
        "nose_up_degrees": 2
    }
    response = client.post("/api/flight_paths", json=payload)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert "ultrastar" in data
    assert "wraith" in data
    assert "p" in data["ultrastar"]
    assert "t" in data["ultrastar"]
    assert "v" in data["ultrastar"]
    assert len(data["ultrastar"]["p"]) == 3
    assert mock_compute_trajectory.call_count == 2

@patch('service.main.compute_trajectory')
def test_flight_paths_success_with_disc_numbers(mock_compute_trajectory, client):
    """Test successful flight paths retrieval using a list of disc_numbers."""
    mock_compute_trajectory.return_value = create_mock_trajectory_results()

    payload = {
        "disc_numbers": [
            {"speed": 10, "glide": 5, "turn": -1, "fade": 2},
            {"speed": 7, "glide": 4, "turn": 0, "fade": 1}
        ],
        "v": 15,
        "spin": -12,
        "uphill_degrees": 0,
        "hyzer_degrees": 5,
        "nose_up_degrees": 2
    }
    response = client.post("/api/flight_paths", json=payload)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert "0" in data
    assert "1" in data
    assert "p" in data["0"]
    assert "t" in data["0"]
    assert "v" in data["0"]
    assert len(data["0"]["p"]) == 3
    assert mock_compute_trajectory.call_count == 2

def test_flight_paths_empty_request(client):
    """Test response for an empty request or missing disc_names/disc_numbers."""
    payload = {
        "v": 15,
        "spin": -12,
        "uphill_degrees": 0,
        "hyzer_degrees": 5,
        "nose_up_degrees": 2
    }
    response = client.post("/api/flight_paths", json=payload)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert len(data) == 0

    response_empty_json = client.post("/api/flight_paths", json={})
    assert response_empty_json.status_code == 200
    data_empty_json = json.loads(response_empty_json.data)
    assert isinstance(data_empty_json, dict)
    assert len(data_empty_json) == 0

def test_flight_paths_missing_required_params(client):
    """Test error response when other required parameters (e.g., v, spin) are missing."""
    payload = {
        "disc_names": ["ultrastar"],
        "uphill_degrees": 0,
        "hyzer_degrees": 5,
        "nose_up_degrees": 2
    }
    response = client.post("/api/flight_paths", json=payload)
    assert response.status_code == 500

# Tests for /api/flight_path_from_summary

@patch('service.main.compute_trajectory')
def test_flight_path_from_summary_success(mock_compute_trajectory, client):
    """Test successful flight path retrieval from a throw summary."""
    mock_compute_trajectory.return_value = create_mock_trajectory_results()

    payload = {
        "speedMph": 60,
        "rotPerSec": 10,
        "noseAngle": 2,
        "hyzerAngle": 5,
        "uphillAngle": 0,
        "flight_numbers": {"speed": 12, "glide": 5, "turn": -1, "fade": 2}
    }
    response = client.post("/api/flight_path_from_summary", json=payload)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "p" in data
    assert "t" in data
    assert "v" in data
    assert len(data["p"]) == 3
    mock_compute_trajectory.assert_called_once()

@patch('service.main.compute_trajectory')
def test_flight_path_from_summary_missing_flight_numbers(mock_compute_trajectory, client):
    """Test error response when flight_numbers (or estimatedFlightNumbers) are missing."""
    payload = {
        "speedMph": 60,
        "rotPerSec": 10,
        "noseAngle": 2,
        "hyzerAngle": 5
    }
    response = client.post("/api/flight_path_from_summary", json=payload)
    assert response.status_code == 500
    mock_compute_trajectory.assert_not_called()

@patch('service.main.compute_trajectory')
def test_flight_path_from_summary_uses_estimated_flight_numbers(mock_compute_trajectory, client):
    """Test that estimatedFlightNumbers are used if flight_numbers are missing."""
    mock_compute_trajectory.return_value = create_mock_trajectory_results()

    payload = {
        "speedMph": 55,
        "rotPerSec": 9,
        "noseAngle": 1,
        "hyzerAngle": 3,
        "estimatedFlightNumbers": {"speed": 10, "glide": 4, "turn": -2, "fade": 1}
    }
    response = client.post("/api/flight_path_from_summary", json=payload)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "p" in data
    mock_compute_trajectory.assert_called_once()
