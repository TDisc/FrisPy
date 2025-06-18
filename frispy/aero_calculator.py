import math
import logging
from frispy.model import Model # Assuming frispy.model.Model is the correct path

def calculate_aero_coefficients(model: Model) -> dict:
    """
    Calculates aerodynamic coefficients (lift, drag, pitch) for a given model
    across a range of angles of attack.

    Args:
        model: An instance of frispy.model.Model.

    Returns:
        A dictionary where keys are angles of attack in degrees (int) and
        values are dictionaries containing "lift", "drag", and "pitch"
        coefficients (float). Errors during calculation for a specific angle
        will store an "error" message for that angle's entry.
    """
    results = {}
    for angle_degrees in range(-90, 91):  # -90 to +90 inclusive
        angle_radians = math.radians(angle_degrees)
        try:
            cl = model.C_lift(angle_radians)
            cd = model.C_drag(angle_radians)
            cy = model.C_y(angle_radians)
            results[angle_degrees] = {"lift": cl, "drag": cd, "pitch": cy}
        except Exception as e:
            # Log the error and potentially skip this angle or return partial results
            logging.error(f"Error calculating coefficients for angle {angle_degrees} degrees: {str(e)}")
            results[angle_degrees] = {"error": str(e)}
    return results
