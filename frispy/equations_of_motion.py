from typing import Dict, Union

import numpy as np
import math

from frispy.environment import Environment
from frispy.model import Model
from scipy.spatial.transform import Rotation

class EOM:
    """
    ``EOM`` is short for "equations of motion" is used to run the ODE solver
    from `scipy`. It takes in a model for the disc, the trajectory object,
    the environment, and implements the functions for calculating forces
    and torques.
    """

    def __init__(
        self,
        environment: Environment = Environment(),
        model: Model = Model(),
    ):
        self._environment = environment
        self._model = model

    @property
    def environment(self) -> Environment:
        return self._environment

    @property
    def model(self) -> Model:
        return self._model

    def compute_forces(
        self,
        rotation: Rotation,
        velocity: np.ndarray,
        ang_velocity: np.ndarray,
    ) -> Dict[str, Union[float, np.ndarray, Dict[str, np.ndarray]]]:
        """
        Compute the lift, drag, and gravitational forces on the disc.

        Args:
        TODO
        """
        res = EOM.calculate_intermediate_quantities(rotation, velocity, ang_velocity)
        aoa = res["angle_of_attack"]
        v_norm = np.linalg.norm(velocity)
        vhat = velocity / v_norm
        force_amplitude = (
            0.5
            * self.environment.air_density
            * (velocity @ velocity)
            * self.model.area
        )
        # Compute the lift and drag forces
        res["F_lift"] = (
            self.model.C_lift(aoa)
            * force_amplitude
            * np.cross(vhat, res["unit_vectors"]["yhat"])
        )
        res["F_side"] = (
                self.model.C_side(aoa, v_norm, ang_velocity[2])
                * force_amplitude
                * res["unit_vectors"]["yhat"]
        )
        res["F_drag"] = self.model.C_drag(aoa) * force_amplitude * (-vhat)
        # Compute gravitational force
        res["F_grav"] = (
            self.model.mass
            * self.environment.g
            * self.environment.grav_vector
        )
        res["F_total"] = res["F_lift"] + res["F_drag"] + res["F_grav"] + res["F_side"]
        res["Acc"] = res["F_total"] / self.model.mass
        return res

    def compute_torques(
        self,
        velocity: np.ndarray,
        ang_velocity: np.ndarray,
        rotation: Rotation,
        res: Dict[str, Union[float, np.ndarray, Dict[str, np.ndarray]]],
    ) -> Dict[str, Union[float, np.ndarray, Dict[str, np.ndarray]]]:

        aoa = res["angle_of_attack"]
        res["torque_amplitude"] = (
            0.5
            * self.environment.air_density
            * (velocity @ velocity)
            * self.model.diameter
            * self.model.area
        )

        i_xx = self.model.I_xx
        i_zz = self.model.I_zz
        torque = res["torque_amplitude"]
        wz = ang_velocity[2]
        v_norm = np.linalg.norm(velocity)

        # Handle pitch and roll as precession around Z and not a change to angular velocity.
        roll = self.model.C_y(aoa) * torque * res["unit_vectors"]["xhat"]
        pitch_up = self.model.C_x(aoa, v_norm, wz) * torque * res["unit_vectors"]["yhat"]

        wobble = res["w"]
        w = (roll + pitch_up) / (i_zz * wz)
        w += wobble

        # https://www.euclideanspace.com/physics/kinematics/angularvelocity/QuaternionDifferentiation2.pdf
        w_norm = np.linalg.norm(w)
        if math.isclose(0, w_norm):
            wquat = Rotation.from_quat([0, 0, 0, 1])
        else:
            wquat = Rotation.from_quat([w[0], w[1], w[2], 0]) * rotation

        self.compute_wobble_precession(ang_velocity, torque, res)
        res["dq"] = wquat.as_quat() * w_norm / 2
        return res

    def compute_wobble_precession(
            self,
            ang_velocity: np.ndarray,
            torque: float,
            res: Dict[str, Union[float, np.ndarray, Dict[str, np.ndarray]]]):
        i_xx = self.model.I_xx
        i_zz = self.model.I_zz
        wx, wy, wz = ang_velocity

        # Dampen angular velocity
        dampening = self.model.dampening_factor
        dampening_z = self.model.dampening_z
        acc = np.array([wx * dampening / i_xx, wy * dampening / i_xx, wz * dampening_z / i_zz]) * torque

        # Handle wobble by precession of angular velocity
        delta_moment = self.model.I_zz - self.model.I_xx
        acc += delta_moment / i_xx * 2*wz * np.array([-wy, wx, 0])

        res["T"] = acc

    def compute_derivatives(
        self, time: float, coordinates: np.ndarray
    ) -> np.ndarray:
        """
        Right hand side of the ordinary differential equations. This is
        supplied to :meth:`scipy.integrate.solve_ivp`. See `this page
        <https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html#scipy.integrate.solve_ivp>`_
        for more information about its `fun` argument.

        .. todo::

           Implement the disc hitting the ground as a (Callable) scipy
           event object.

        Args:
          time (float): instantanious time of the system
          coordinates (np.ndarray): kinematic variables of the disc

        Returns:
          derivatives of all coordinates
        """
        x, y, z, vx, vy, vz, qx, qy, qz, qw, dphi, dtheta, dgamma = coordinates
        velocity = np.array([vx, vy, vz])
        rotation: Rotation = Rotation.from_quat([qx, qy, qz, qw])
        rot_array = rotation.as_quat()
        # angular velocity is defined relative to z after rotaiton
        ang_velocity = np.array([dphi, dtheta, dgamma])
        result = self.compute_forces(rotation, velocity, ang_velocity)
        result = self.compute_torques(velocity, ang_velocity, rotation, result)
        derivatives = np.array(
            [
                vx,
                vy,
                vz,
                result["Acc"][0],  # x component of acceleration
                result["Acc"][1],  # y component of acceleration
                result["Acc"][2],  # z component of acceleration
                result["dq"][0],
                result["dq"][1],
                result["dq"][2],
                result["dq"][3],
                result["T"][0],  # x component of ang. acc.
                result["T"][1],  # y component of ang. acc.
                result["T"][2],  # gamma component of ang. acc.
            ]
        )
        return derivatives

    @staticmethod
    def expand_quaternion(qx: float, qy: float, qz: float, qw: float) -> Rotation:
        vector = np.array([qx, qy, qz, qw])
        return Rotation.from_quat(vector)


    @staticmethod
    def calculate_intermediate_quantities(
            rotation: Rotation,
            velocity: np.ndarray,
            ang_velocity: np.ndarray,
    ) -> Dict[str, Union[float, np.ndarray, Dict[str, np.ndarray]]]:
        """
        Compute intermediate quantities on the way to computing the time
        derivatives of the kinematic variables.

        Args:
        TODO
        """
        # Rotation matrix
        R = rotation.as_matrix()
        # Unit vectors
        zhat = R @ np.array([0, 0, 1])
        v_dot_zhat = velocity @ zhat
        v_in_plane = velocity - zhat * v_dot_zhat
        xhat = v_in_plane / np.linalg.norm(v_in_plane)
        yhat = np.cross(zhat, xhat)

        # Angle of attack
        angle_of_attack = -np.arctan(v_dot_zhat / np.linalg.norm(v_in_plane))

        # wobble is only the in x and y axis relative to zhat
        w = R @ np.array([ang_velocity[0], ang_velocity[1], 0])
        return {
            "unit_vectors": {"xhat": xhat, "yhat": yhat, "zhat": zhat},
            "angle_of_attack": angle_of_attack,
            "w": w,
        }
