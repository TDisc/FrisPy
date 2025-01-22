import time
import json
import math
import os
import logging
from typing import Dict

import numpy as np
from flask import Flask, request
from scipy.spatial.transform import Rotation

from frispy import Disc, Discs, Environment
from frispy.wind import ConstantWind
from flask_cors import CORS
from flask_sock import Sock
from frispy.disc import FrisPyResults

# import google.cloud.logging
# client = google.cloud.logging.Client()
# client.setup_logging()

app = Flask(__name__)
CORS(app)
sock = Sock(app)


@sock.route('/api/ws/flight_path')
def ws_flight_path(s):
    try:
        data = s.receive(2)
        if data is None:
            return

        content = json.loads(data)
        gamma = content.get('gamma', 0)
        disc = create_disc(content)
        inc_send_over_websocket(disc, gamma, s)
    finally:
        s.close()


@sock.route('/api/ws/flight_path_from_summary')
def ws_flight_path_from_summary(s):
    try:
        data = s.receive(2)
        if data is None:
            return

        content = json.loads(data)
        content = to_flight_path_request(content)

        disc = create_disc(content)
        inc_send_over_websocket(disc, 0, s)
    finally:
        s.close()


def inc_send_over_websocket(disc, gamma, s) -> bool:
    results = compute_trajectory(disc, 1.0)
    s.send(json.dumps(to_result(gamma, results)))
    disc.set_initial_conditions_from_prev_results(results)
    while results.z[-1] > 1e-6:
        # bail early if socket is closed
        if not s.connected:
            return False
        results = compute_trajectory(disc, 1.0, results.times[-1])
        s.send(json.dumps(to_result(gamma, results)))
        disc.set_initial_conditions_from_prev_results(results)
    # send empty object to signal end of flight
    s.send("{}")
    return True


# same as flight_path, but with multiple discs
@app.route('/api/flight_paths', methods=['POST'])
def flight_paths():
    content = request.json
    discs = content.get('disc_names')
    res = {}
    if discs:
        for discName in discs:
            content['disc_name'] = discName
            disc = create_disc(content)
            result = compute_trajectory(disc)
            res[discName] = to_result(content.get('gamma', 0), result)
    else:
        discs = content.get('disc_numbers')
        for index, discNumbers in enumerate(discs):
            content['flight_numbers'] = discNumbers
            disc = create_disc(content)
            result = compute_trajectory(disc)
            res[index] = to_result(content.get('gamma', 0), result)

    return res


# this method assumes the disc velocity is in the X direction.
# This library uses Z as up so Y points to the left (if X is straight ahead)
# This does not handle rotation of the disc in the resulting quaternion
# but a gamma param is sent to rotate after.
# units are all in SI units. m, m/s, rad/s, unless noted in the name.
@app.route('/api/flight_path', methods=['POST'])
def flight_path():
    content = request.json
    disc = create_disc(content)
    result = compute_trajectory(disc)
    return to_result(content.get('gamma', 0), result)


# send over the throw summary to get the flight directly.
# Add a "z" to set the release height in meters, default is 1m
# Add flight_numbers to use a specific flight numbers
@app.route('/api/flight_path_from_summary', methods=['POST'])
def flight_path_from_summary():
    content = request.json
    content = to_flight_path_request(content)
    disc = create_disc(content)
    result = compute_trajectory(disc)
    return to_result(0, result)


def create_disc(content) -> Disc:
    model = Discs.from_string(content.get('disc_name'))
    if not model:
        model = Discs.from_flight_numbers(content['flight_numbers'])
    v = content['v']
    spin = content['spin']
    wx = 0
    if "wx" in content:
        wx = content["wx"]

    wy = 0
    if "wy" in content:
        wy = content["wy"]
    z = 1
    if "z" in content:
        z = content["z"]

    # m/s
    wind_speed = 0
    if "wind_speed" in content:
        wind_speed = content["wind_speed"]

    # 0 wind angle means tailwind, 90 deg is right to left
    # radians
    wind_angle = 0
    if "wind_angle" in content:
        wind_angle = content["wind_angle"]

    wind = ConstantWind(np.array([math.cos(wind_angle), math.sin(wind_angle), 0]) * wind_speed)

    # measured in kg/m^3
    air_density = 1.225  # 15C / 59F
    if "air_density" in content:
        air_density = content["air_density"]

    a = content['uphill_degrees'] * math.pi / 180
    hyzer = content['hyzer_degrees']
    nose_up = content['nose_up_degrees']
    disc = Disc(model, {"vx": math.cos(a) * v,
                        "dgamma": spin,
                        "dphi": wx,
                        "dtheta": wy,
                        "vz": math.sin(a) * v,
                        "z": z,
                        "nose_up": nose_up,
                        "hyzer": hyzer
                },
                environment=Environment(wind=wind, air_density=air_density))

    return disc


def compute_trajectory(disc: Disc, flight_max_seconds: float = 15.0, startTime: float = 0.0) -> FrisPyResults:
    try:
        # time request and log
        start_time = time.time()
        result = compute_trajectory_internal(disc, flight_max_seconds, startTime)
        end_time = time.time()

        computed_seconds = result.times[-1] - result.times[0]
        elapsed_time = end_time - start_time
        logging.info("computed %s seconds of trajectory in %s seconds", computed_seconds, elapsed_time)
        return result
    except Exception as e:
        logging.error("failed to process flight e: %s, content: %s", e, disc)

        # add retry on exception
        result = compute_trajectory_internal(disc, flight_max_seconds, startTime)
        return result


def compute_trajectory_internal(disc: Disc, flight_max_seconds: float, startTime: float) -> FrisPyResults:
    hz = abs(disc.initial_conditions['dgamma']) / math.pi / 2
    # In order to get a smooth output for the rotation of the disc
    # we need to have enough samples to spin in the correct direction
    max_step = 0.1
    if hz > 4.5:
        max_step = 0.45 / hz
    return disc.compute_trajectory(**{"max_step": max_step, "rtol": 5e-4, "atol": 1e-7,
                                      "t_span": (startTime, startTime + flight_max_seconds)})


def to_result(gamma, result):
    res = {
        'p': result.pos,
        't': [i.tolist() for i in result.times],
        'v': [i.tolist() for i in result.v],
        'qx': result.qx.tolist(),
        'qy': result.qy.tolist(),
        'qz': result.qz.tolist(),
        'qw': result.qw.tolist(),
        'gamma': [i + gamma for i in result.gamma],
    }
    return res


def to_flight_path_request(throw_summary: Dict) -> Dict:
    speed_mph_to_mps = 0.44704  # Conversion factor from mph to mps

    flight_path_request = {
        "z": 1,
        "uphill_degrees": throw_summary.get("uphillAngle", 0),
        "v": throw_summary.get("speedMph", 0) * speed_mph_to_mps,
        "spin": -throw_summary.get("rotPerSec", 0) * 2 * math.pi,
        "nose_up_degrees": throw_summary.get("noseAngle", 0),
        "hyzer_degrees": throw_summary.get("hyzerAngle", 0),
    }
    flight_path_request.update(throw_summary)

    gamma = throw_summary.get("gamma", 0)
    wx = throw_summary.get("wx", 0)
    wy = throw_summary.get("wy", 0)

    ang_velocity = np.array([wx, wy, 0])
    ang_velocity = Rotation.from_euler("Z", gamma).apply(ang_velocity)

    flight_path_request["wx"] = ang_velocity[0]
    flight_path_request["wy"] = -ang_velocity[1]
    flight_path_request["gamma"] = 0

    flight_numbers = throw_summary.get("flight_numbers", None)
    if not flight_numbers:
        flight_numbers = throw_summary.get("estimatedFlightNumbers", None)

    if flight_numbers:
        flight_path_request["flight_numbers"] = flight_numbers
    else:
        raise ValueError("Must specify flight_numbers")

    return flight_path_request


@app.route("/")
def hello_world():
    return "Frispy service!"


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
