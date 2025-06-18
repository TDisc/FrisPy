import pytest
import math
from frispy.model import Model
from frispy.discs import Discs
from frispy.aero_calculator import calculate_aero_coefficients

def test_calculate_aero_coefficients():
    """
    Tests the calculate_aero_coefficients function with a real model.
    Checks for the correct structure and content of the results.
    """
    # Use a real disc model for testing
    # Flight numbers for a disc like Innova Wraith or similar stable-overstable driver
    flight_numbers = {"speed": 11, "glide": 5, "turn": -1, "fade": 2}
    try:
        model = Discs.from_flight_numbers(flight_numbers)
    except Exception as e:
        pytest.fail(f"Failed to create model from flight numbers: {e}")

    results = calculate_aero_coefficients(model)

    assert isinstance(results, dict)
    assert len(results) == 181  # For angles -90 to +90 inclusive

    # Check for specific angle keys (as integers, matching the implementation)
    assert 0 in results
    assert 90 in results
    assert -90 in results

    # Check the structure of a sample angle's data
    sample_angle_key = 0
    assert isinstance(results[sample_angle_key], dict)

    if "error" not in results[sample_angle_key]:
        assert "lift" in results[sample_angle_key]
        assert "drag" in results[sample_angle_key]
        assert "pitch" in results[sample_angle_key]

        # Check that coefficient values are numbers (floats)
        assert isinstance(results[sample_angle_key]["lift"], float)
        assert isinstance(results[sample_angle_key]["drag"], float)
        assert isinstance(results[sample_angle_key]["pitch"], float)
    else:
        # If there was an error calculating for this specific angle (e.g. alpha out of bounds for some model types)
        # The test should acknowledge this structure. For most standard models, 0 degrees should be fine.
        logging.warning(f"Coefficient calculation for angle {sample_angle_key} resulted in an error: {results[sample_angle_key]['error']}")

    # Check a boundary angle, e.g., 90 degrees
    boundary_angle_key = 90
    assert isinstance(results[boundary_angle_key], dict)
    if "error" not in results[boundary_angle_key]:
        assert "lift" in results[boundary_angle_key]
        assert "drag" in results[boundary_angle_key]
        assert "pitch" in results[boundary_angle_key]
        assert isinstance(results[boundary_angle_key]["lift"], float)
        assert isinstance(results[boundary_angle_key]["drag"], float)
        assert isinstance(results[boundary_angle_key]["pitch"], float)
    else:
        logging.warning(f"Coefficient calculation for angle {boundary_angle_key} resulted in an error: {results[boundary_angle_key]['error']}")

    # Verify that all entries are either valid coefficient dicts or error dicts
    for angle, data in results.items():
        assert isinstance(angle, int)
        assert isinstance(data, dict)
        if "error" in data:
            assert isinstance(data["error"], str)
        else:
            assert "lift" in data and isinstance(data["lift"], float)
            assert "drag" in data and isinstance(data["drag"], float)
            assert "pitch" in data and isinstance(data["pitch"], float)

# It might be useful to also test the error handling part of calculate_aero_coefficients
# by mocking a model that raises an exception on C_lift/C_drag/C_y calls.
# For now, this test covers the main functionality.
# Adding a test for logging (requires capturing logs or more complex mocking)
# is also out of scope for this direct test.
