from fastapi.testclient import TestClient
import sys
import os

# Add the backend directory to the path to allow importing 'main'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app  # Import the FastAPI app instance

client = TestClient(app)

def test_read_root():
    """
    Test the root endpoint ('/').
    It should redirect to the '/docs' endpoint.
    TestClient does not follow redirects by default, so we check for 307 status.
    """
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary Redirect
    assert response.headers["location"] == "/docs"

def test_health_check():
    """
    Test the health check endpoint ('/health').
    It should return a 200 status code and a JSON body {"status": "healthy"}.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}