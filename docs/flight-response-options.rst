Opt-in flight responses
=======================

These options apply to POST /api/flight_path, /api/flight_path_from_summary,
and /api/flight_paths, plus the two /api/ws/flight_path endpoints (including
/api/ws/flight_path_from_summary). Requests without
response_options retain the existing full-precision, uncompressed JSON response,
even if the client advertises gzip support. Physics and solver settings are unchanged.

Stage 1: lossless transport compression
--------------------------------------

Add this member to the existing flight request body::

    "response_options": {"version": 1, "compression": "gzip"}

The HTTP client must also advertise gzip in Accept-Encoding. Both opt-ins are
required. Clients such as browsers manage Accept-Encoding themselves; do not
manually decompress a response already decoded by the networking library.

The response remains application/json. When compressed it carries
Content-Encoding: gzip and a Content-Length describing the encoded bytes.
Vary: Accept-Encoding is added for requests opting into gzip. Missing or
unacceptable gzip support falls back to identity encoding. Tiny responses remain
uncompressed if gzip would increase their size. Always inspect Content-Encoding
rather than assuming the response is compressed. Gzip level 1 is used to limit
CPU overhead. No new runtime dependency is required.

Stage 2: compact numerical output
--------------------------------

All fields, reduced precision::

    "response_options": {
        "version": 2,
        "compression": "gzip",
        "profile": "full"
    }

Rendering fields, retaining spin animation::

    "response_options": {
        "version": 2,
        "compression": "gzip",
        "profile": "render",
        "include_spin": true
    }

The render profile omits v (velocity). Set include_spin to false only for
consumers that do not need gamma; the web spin animation uses gamma. Quaternions
are not changed to incorporate gamma when gamma is omitted. All positions,
timestamps, quaternions, and sample counts retain their existing array layout.
Batch responses retain their existing disc-name/index keys. Options apply to
every flight in the batch. There is no response envelope or downsampling.

Version 2 rounds only the serialized output:

* p: 3 decimal places in metres (0.5 mm maximum error per component).
* v: 3 decimal places in metres/second.
* t: exact original timestamps in seconds.
* qx, qy, qz, qw: 6 decimal places.
* gamma: 5 decimal places in radians, including any requested gamma offset.

Timestamps always retain their original precision to preserve tiny solver steps
and shared streaming boundaries. Clients should normalize rounded quaternions
before operations requiring exact unit length. Compact values are intended for
display; use version 1 for analytics requiring full precision, particularly
finite differences of position over short time intervals.

Version defaults to 1, compression to identity, profile to full, and include_spin
to true. Version 2 can be requested without compression. profile and include_spin
are only accepted with version 2; include_spin=false requires profile=render.
Unknown options, unsupported values, and incorrect types return HTTP 400 before
simulation. Brotli and binary formats are not supported in this initial rollout.

Rollout and measurement
-----------------------

Deploy with defaults unchanged. Opt a test client into stage 1, verify automatic
decoding and measure encoded bytes, request-to-response time and first rendered
frame on real mobile connections. Then opt that client into stage 2 and compare
flight appearance, landing position, and spin orientation. Compare p50/p95 under
matched concurrency and network conditions. Cloud request latency alone does not
measure client parsing/rendering. Removing response_options rolls back both stages.

WebSocket compact output
------------------------

Include response_options in the initial JSON message. Version 2 and profile full
retain all samples, velocity, and gamma for V2 spin processing. Chunk boundaries,
termination marker ({}), and physics are unchanged. Compact formatting only changes
sent values; continuing solver state always uses the original full-precision results.
Use compression=identity (the default). Requesting gzip on a WebSocket is rejected;
WebSocket compression is not implemented. Invalid options close the socket without
running a simulation. Existing clients omitting options receive legacy messages.

The V2 gateway requests version 2/profile full automatically, HTTP gzip for full
responses, and identity transport for WebSockets. Direct FrisPy clients must still
opt in themselves. Deploy FrisPy before the companion V2 gateway for upstream savings.
