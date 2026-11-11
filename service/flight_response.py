"""Opt-in HTTP transport and rendering formats; never change solver precision."""

import gzip
from dataclasses import dataclass

from flask import jsonify, request
from werkzeug.exceptions import BadRequest


@dataclass(frozen=True)
class ResponseOptions:
    version: int = 1
    compression: str = "identity"
    profile: str = "full"
    include_spin: bool = True


def parse_response_options(content):
    options = content.get("response_options", {})
    if not isinstance(options, dict):
        raise BadRequest("response_options must be an object")
    allowed = {"version", "compression", "profile", "include_spin"}
    if options.keys() - allowed:
        raise BadRequest("Unknown response_options field")
    version = options.get("version", 1)
    compression = options.get("compression", "identity")
    profile = options.get("profile", "full")
    include_spin = options.get("include_spin", True)
    if type(version) is not int or version not in (1, 2):
        raise BadRequest("response_options.version must be 1 or 2")
    if compression not in ("identity", "gzip"):
        raise BadRequest("response_options.compression must be identity or gzip")
    if profile not in ("full", "render"):
        raise BadRequest("response_options.profile must be full or render")
    if type(include_spin) is not bool:
        raise BadRequest("response_options.include_spin must be a boolean")
    if version == 1 and ("profile" in options or "include_spin" in options):
        raise BadRequest("profile and include_spin require response version 2")
    if profile != "render" and not include_spin:
        raise BadRequest("include_spin=false requires the render profile")
    return ResponseOptions(version, compression, profile, include_spin)


def parse_websocket_response_options(content):
    options = parse_response_options(content)
    if options.compression != "identity":
        raise BadRequest("WebSocket compression is not supported")
    return options


def format_flight_result(result, options):
    if options.version == 1:
        return result
    precision = {"p": 3, "v": 3, "t": 5, "qx": 6, "qy": 6,
                 "qz": 6, "qw": 6, "gamma": 5}

    def rounded(value, digits):
        if isinstance(value, list):
            return [rounded(item, digits) for item in value]
        return round(float(value), digits)

    compact = {
        key: value if key == "t" else rounded(value, precision[key])
        for key, value in result.items()
        if not (options.profile == "render" and
                (key == "v" or (key == "gamma" and not options.include_spin)))
    }
    # Exact timestamps preserve short steps and shared WebSocket chunk boundaries.
    return compact


def flight_response(data, options):
    response = jsonify(data)
    if options.compression != "gzip":
        return response
    response.vary.add("Accept-Encoding")
    # The body opt-in alone does not prove the client can decode gzip.
    if request.accept_encodings.quality("gzip") <= 0:
        return response
    raw = response.get_data()
    compressed = gzip.compress(raw, compresslevel=1, mtime=0)
    if len(compressed) < len(raw):
        response.set_data(compressed)
        response.headers["Content-Encoding"] = "gzip"
    return response
