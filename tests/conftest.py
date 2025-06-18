import pytest
from service.main import app # Assuming service.main is the correct path to your Flask app

@pytest.fixture
def client():
    """A test client for the app."""
    with app.test_client() as client:
        yield client
