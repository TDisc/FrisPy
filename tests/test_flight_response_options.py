import gzip
import json
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from service.flight_response import ResponseOptions, format_flight_result


@pytest.fixture
def trajectory():
    n = 40
    return SimpleNamespace(
        pos=[[1.23456789, -2.34567891, 0.12345678] for _ in range(n)],
        times=np.linspace(0, 1.23456789, n),
        v=[np.array([12.3456789, -0.12345678, 0.12345678]) for _ in range(n)],
        qx=np.full(n, 0.123456789), qy=np.full(n, -0.234567891),
        qz=np.full(n, 0.345678912), qw=np.full(n, 0.9),
        gamma=[i * 0.123456789 for i in range(n)],
    )


@pytest.fixture
def simulation(trajectory):
    with patch('service.main.compute_trajectory', return_value=trajectory) as compute:
        yield compute


PAYLOAD = dict(disc_name='ultrastar', v=20, spin=-80,
               uphill_degrees=0, hyzer_degrees=0, nose_up_degrees=0)
ENDPOINTS = [
    ('/api/flight_path', PAYLOAD, None),
    ('/api/flight_path_from_summary',
     dict(speedMph=60, rotPerSec=10, flight_numbers=dict(speed=12, glide=5, turn=-1, fade=2)), None),
    ('/api/flight_paths', dict(PAYLOAD, disc_names=['ultrastar', 'wraith']), 'ultrastar'),
    ('/api/flight_paths', dict(PAYLOAD, disc_numbers=[dict(speed=12, glide=5, turn=-1, fade=2)]), '0'),
]


@pytest.mark.parametrize('endpoint,payload,key', ENDPOINTS)
def test_legacy_and_lossless_compression(client, simulation, endpoint, payload, key):
    plain = client.post(endpoint, json=payload)
    advertised = client.post(endpoint, json=payload, headers={'Accept-Encoding': 'gzip'})
    assert plain.status_code == advertised.status_code == 200
    assert plain.data == advertised.data
    assert 'Content-Encoding' not in advertised.headers
    compressed = client.post(endpoint, json=dict(payload, response_options={'compression': 'gzip'}),
                             headers={'Accept-Encoding': 'gzip'})
    assert compressed.status_code == 200
    assert compressed.headers['Content-Encoding'] == 'gzip'
    assert compressed.mimetype == 'application/json'
    assert 'Accept-Encoding' in compressed.vary
    assert int(compressed.headers['Content-Length']) == len(compressed.data)
    assert len(compressed.data) < len(plain.data)
    assert gzip.decompress(compressed.data) == plain.data


@pytest.mark.parametrize('accept,compressed', [
    (None, False), ('br', False), ('gzip;q=0', False),
    ('*;q=0.5', True), ('gzip;q=0, *;q=1', False), ('gzip;q=0.5', True),
])
def test_encoding_negotiation(client, simulation, accept, compressed):
    headers = {} if accept is None else {'Accept-Encoding': accept}
    response = client.post('/api/flight_path',
                           json=dict(PAYLOAD, response_options={'compression': 'gzip'}), headers=headers)
    assert response.status_code == 200
    assert ('Content-Encoding' in response.headers) == compressed
    assert 'Accept-Encoding' in response.vary


@pytest.mark.parametrize('endpoint,payload,key', ENDPOINTS)
@pytest.mark.parametrize('profile,include_spin', [('full', True), ('render', True), ('render', False)])
def test_compact_preserves_samples_and_profiles(client, simulation, endpoint, payload, key, profile, include_spin):
    options = dict(version=2, profile=profile, include_spin=include_spin, compression='gzip')
    response = client.post(endpoint, json=dict(payload, response_options=options),
                           headers={'Accept-Encoding': 'gzip'})
    assert response.status_code == 200
    data = json.loads(gzip.decompress(response.data))
    result = data if key is None else data[key]
    assert all(len(values) == 40 for values in result.values())
    assert result['p'][0] == [1.235, -2.346, 0.123]
    assert result['qx'][0] == 0.123457
    assert result['t'][-1] == 1.23456789
    assert ('v' in result) == (profile == 'full')
    assert ('gamma' in result) == include_spin


def test_compact_without_compression(client, simulation):
    response = client.post('/api/flight_path', json=dict(PAYLOAD, response_options={'version': 2}),
                           headers={'Accept-Encoding': 'gzip'})
    assert response.status_code == 200
    assert 'Content-Encoding' not in response.headers
    assert response.json['v'][0] == [12.346, -0.123, 0.123]
    assert 'gamma' in response.json


@pytest.mark.parametrize('options', [
    None, [], 'gzip', {'version': True}, {'version': 1.0}, {'version': 3},
    {'compression': 'br'}, {'compression': []}, {'profile': 'render'},
    {'include_spin': False}, {'version': 2, 'profile': 'unknown'},
    {'version': 2, 'include_spin': 0}, {'version': 2, 'include_spin': False},
    {'versoin': 2},
])
@pytest.mark.parametrize('endpoint,payload,key', ENDPOINTS)
def test_invalid_options_fail_before_simulation(client, simulation, options, endpoint, payload, key):
    response = client.post(endpoint, json=dict(payload, response_options=options))
    assert response.status_code == 400
    simulation.assert_not_called()


def test_rounding_does_not_merge_close_timestamps_or_mutate_input():
    source = {'t': [0.0, 0.000001, 0.000002], 'p': [[0.123456, 0, 1]] * 3}
    result = format_flight_result(source, ResponseOptions(version=2))
    assert result['t'] == source['t']
    assert source['p'][0][0] == 0.123456
    assert result['p'][0][0] == 0.123


def test_tiny_response_is_not_expanded(client, simulation):
    response = client.post('/api/flight_paths', json={'response_options': {'compression': 'gzip'}},
                           headers={'Accept-Encoding': 'gzip'})
    assert response.status_code == 200
    assert response.json == {}
    assert 'Content-Encoding' not in response.headers


def test_real_flight_compact_error_bounds(client):
    plain = client.post('/api/flight_path', json=PAYLOAD).json
    response = client.post('/api/flight_path',
                           json=dict(PAYLOAD, response_options={'version': 2, 'compression': 'gzip'}),
                           headers={'Accept-Encoding': 'gzip'})
    compact = json.loads(gzip.decompress(response.data))
    assert len(compact['t']) == len(plain['t'])
    assert np.all(np.diff(compact['t']) > 0)
    for field, tolerance in [('p', 0.0005), ('v', 0.0005), ('t', 0.000005),
                             ('qx', 0.0000005), ('qy', 0.0000005),
                             ('qz', 0.0000005), ('qw', 0.0000005), ('gamma', 0.000005)]:
        assert np.max(np.abs(np.asarray(compact[field]) - np.asarray(plain[field]))) <= tolerance + 1e-12

@pytest.mark.parametrize('compact', [False, True])
def test_websocket_chunks_preserve_boundaries_and_solver_state(compact):
    from service.main import inc_send_over_websocket
    from unittest.mock import MagicMock
    disc = MagicMock()
    chunk1 = SimpleNamespace(pos=[[1.12345678, 0, 1], [2.12345678, 0, 0.5]],
        times=np.array([0., 1.000000001]), v=[np.array([1., 0, 0])]*2,
        qx=np.array([0., 0.]), qy=np.array([0., 0.]), qz=np.array([0., 0.]), qw=np.array([1., 1.]),
        gamma=[0., 1.123456789], z=np.array([1., 0.5]))
    chunk2 = SimpleNamespace(**vars(chunk1))
    chunk2.times=np.array([1.000000001,1.000000002])
    chunk2.z=np.array([0.5,0.])
    socket=MagicMock();socket.connected=True
    options=ResponseOptions(version=2 if compact else 1)
    with patch('service.main.compute_trajectory',side_effect=[chunk1,chunk2]) as compute:
        assert inc_send_over_websocket(disc,0,socket,options)
    first,second,terminal=[json.loads(call.args[0]) for call in socket.send.call_args_list]
    assert first['t'][-1]==second['t'][0]==1.000000001
    assert second['t'][1]>second['t'][0]
    assert first['p'][0][0]==(1.123 if compact else 1.12345678)
    assert 'v' in first and 'gamma' in first
    assert terminal=={}
    assert disc.set_initial_conditions_from_prev_results.call_args_list[0].args[0] is chunk1
    assert compute.call_args_list[1].args[2]==chunk1.times[-1]


def test_websocket_rejects_gzip():
    from service.flight_response import parse_websocket_response_options
    from werkzeug.exceptions import BadRequest
    with pytest.raises(BadRequest,match='WebSocket compression'):
        parse_websocket_response_options({'response_options':{'compression':'gzip'}})
