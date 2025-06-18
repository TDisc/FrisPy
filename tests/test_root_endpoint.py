# client fixture is provided by conftest.py

def test_hello_world_endpoint(client):
    """Test the GET / endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.data.decode('utf-8') == "Frispy service!"
