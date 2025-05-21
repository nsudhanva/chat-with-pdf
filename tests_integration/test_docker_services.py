import os
import requests
import pytest

# Get service ports from environment variables, with defaults
BACKEND_PORT = os.environ.get("BACKEND_PORT", "8000")
UPLOAD_SERVICE_PORT = os.environ.get("UPLOAD_SERVICE_PORT", "8050")
FRONTEND_PORT = os.environ.get("FRONTEND_PORT", "3000")

BASE_URL_BACKEND = f"http://localhost:{BACKEND_PORT}"
BASE_URL_UPLOAD_SERVICE = f"http://localhost:{UPLOAD_SERVICE_PORT}"
BASE_URL_FRONTEND = f"http://localhost:{FRONTEND_PORT}"


@pytest.mark.integration
def test_backend_health_check():
    """Test the backend service's /api/health endpoint."""
    response = requests.get(f"{BASE_URL_BACKEND}/api/health")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "healthy"
    assert json_response["service"] == "backend"


@pytest.mark.integration
def test_upload_service_health_check():
    """Test the upload service's /health endpoint."""
    response = requests.get(f"{BASE_URL_UPLOAD_SERVICE}/health")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "healthy"
    assert json_response["service"] == "upload_service"


@pytest.mark.integration
def test_frontend_connectivity():
    """Test basic connectivity to the frontend service."""
    response = requests.get(f"{BASE_URL_FRONTEND}/")
    assert response.status_code == 200
    # Check for some static text that is unlikely to change, e.g., from title in app.html
    # This makes the test more robust than just checking for 200
    assert "<title>Chat with PDF</title>" in response.text


@pytest.mark.integration
def test_list_conversations_empty():
    """Test listing conversations, expecting an empty list for a fresh setup."""
    # This endpoint requires authentication, which complicates the test setup.
    # For now, we'll assume that if the /api/health endpoint (which doesn't require auth)
    # is working, other API endpoints are likely reachable.
    # A more comprehensive test would involve setting up auth or using a test user.
    # Let's test a non-auth endpoint if available, or simply skip if all require auth.
    # The current /api/conversations endpoint requires auth.
    # We will check if /api/health (tested above) is sufficient for now.
    # If a simple, non-authenticated list endpoint exists, that would be better.
    # For now, we'll rely on the backend health check.
    #
    # Example if a non-auth endpoint like /api/public-info existed:
    # response = requests.get(f"{BASE_URL_BACKEND}/api/public-info")
    # assert response.status_code == 200
    # assert response.json() == {"some_default_info": "details"}
    #
    # Since /api/conversations requires auth, and we don't have a simple non-auth list endpoint,
    # we will skip this specific test for now to keep the initial setup simple.
    # The health checks confirm service availability and basic routing.
    pytest.skip("Skipping list_conversations test as it requires authentication setup.")

# To run these tests:
# 1. Ensure your Docker Compose environment is up and running.
#    (docker-compose up -d)
# 2. Install pytest and requests if you haven't already (pip install pytest requests)
# 3. Run pytest from the root of your project:
#    pytest tests_integration/test_docker_services.py
#    or simply: pytest
#
#    You might need to set the environment variables for ports if they differ from defaults:
#    BACKEND_PORT=xxxx UPLOAD_SERVICE_PORT=yyyy FRONTEND_PORT=zzzz pytest tests_integration/test_docker_services.py
#
# Note: If tests fail due to connection errors, ensure that:
#   - Docker containers are running and healthy.
#   - Ports in docker-compose.yml and .env match those used here.
#   - There are no firewall issues blocking localhost connections to these ports.
