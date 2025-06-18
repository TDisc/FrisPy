import pytest
import json
import math

# client fixture is provided by conftest.py

# Define Throw Scenarios and Expected Payloads
destroyer_payload = {
    "disc_name": "destroyer", "v": 24.36, "spin": -133.7,
    "nose_up_degrees": 1.15, "hyzer_degrees": 7.8, "uphill_degrees": 2.79,
    "wx": -13.2, "wy": -8.88
}

xcal_fn_payload = {
    "flight_numbers": {"speed": 12, "glide": 5, "turn": -1, "fade": 2}, # Corresponds to Innova XCaliber
    "v": 24.58672, "spin": -116.52, "nose_up_degrees": -3,
    "hyzer_degrees": 0, "uphill_degrees": 8, "wx": 0, "wy": 0
}

ultrastar_straight_payload = {
    "disc_name": "ultrastar", "v": 15, "spin": -80,
    "nose_up_degrees": 0, "hyzer_degrees": 0, "uphill_degrees": 0,
    "wx": 0, "wy": 0
}

# Placeholder for baseline values - these will be determined by running the requests once
# and then hardcoded into the actual tests.
# Example: baseline_destroyer = [x, y, z]

# Note: For the actual implementation, the baseline capture will be done first,
# then these test functions will be filled with the hardcoded expected_landing_point.

def get_landing_point(client, payload):
    response = client.post("/api/flight_path", json=payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    positions = data['p']
    actual_landing_point = positions[-1]
    # Round to a reasonable precision for baselining, e.g., 3 decimal places
    return [round(coord, 3) for coord in actual_landing_point]

# --- Test functions will be implemented after baseline capture ---
# For now, I will create one test to capture the first baseline, then comment it out
# and use the value to build the real test. I'll repeat for each payload.

# Step 1: Capture Baselines (Example for Destroyer - will run this, get value, then write permanent test)
# def test_capture_baseline_destroyer(client):
#     landing_point = get_landing_point(client, destroyer_payload)
#     print(f"Destroyer Baseline: {landing_point}")
#     # Manually record this output

# def test_capture_baseline_xcal_fn(client):
#     landing_point = get_landing_point(client, xcal_fn_payload)
#     print(f"XCal FN Baseline: {landing_point}")
#     # Manually record this output

# def test_capture_baseline_ultrastar_straight(client):
#     landing_point = get_landing_point(client, ultrastar_straight_payload)
#     print(f"Ultrastar Straight Baseline: {landing_point}")
#     # Manually record this output

# After baselines are captured and recorded, these functions will be implemented:

# Baseline values captured in previous steps:
expected_destroyer_landing_point = [82.047, -1.759, 0.0] # z was -0.0, using 0.0
expected_xcal_fn_landing_point = [109.006, -7.995, 0.0]   # z was -0.0, using 0.0
expected_ultrastar_straight_landing_point = [17.604, -0.699, 0.0] # z was -0.0, using 0.0

def test_smoke_destroyer_throw(client):
    response = client.post("/api/flight_path", json=destroyer_payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    actual_landing_point = data['p'][-1]

    assert math.isclose(actual_landing_point[0], expected_destroyer_landing_point[0], abs_tol=1.0)
    assert math.isclose(actual_landing_point[1], expected_destroyer_landing_point[1], abs_tol=1.0)
    assert math.isclose(actual_landing_point[2], expected_destroyer_landing_point[2], abs_tol=0.1)

def test_smoke_xcal_fn_throw(client):
    response = client.post("/api/flight_path", json=xcal_fn_payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    actual_landing_point = data['p'][-1]

    assert math.isclose(actual_landing_point[0], expected_xcal_fn_landing_point[0], abs_tol=1.0)
    assert math.isclose(actual_landing_point[1], expected_xcal_fn_landing_point[1], abs_tol=1.0)
    assert math.isclose(actual_landing_point[2], expected_xcal_fn_landing_point[2], abs_tol=0.1)

def test_smoke_ultrastar_straight_throw(client):
    response = client.post("/api/flight_path", json=ultrastar_straight_payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    actual_landing_point = data['p'][-1]

    assert math.isclose(actual_landing_point[0], expected_ultrastar_straight_landing_point[0], abs_tol=1.0)
    assert math.isclose(actual_landing_point[1], expected_ultrastar_straight_landing_point[1], abs_tol=1.0)
    assert math.isclose(actual_landing_point[2], expected_ultrastar_straight_landing_point[2], abs_tol=0.1)
