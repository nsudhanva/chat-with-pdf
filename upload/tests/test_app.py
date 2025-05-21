import pytest
import os
# Need to make sure 'upload.app' can be imported.
# This might require adjusting PYTHONPATH or the test execution context.
# For now, assuming 'upload' is on the path or tests are run from a place where it's discoverable.
from upload.app import app as upload_app


@pytest.fixture
def client():
    """A test client for the upload app."""
    # Configure the app for testing
    upload_app.config["TESTING"] = True
    # Set a specific UPLOAD_FOLDER for tests if necessary, or ensure the default is okay.
    # For the /health endpoint, UPLOAD_FOLDER isn't critical.
    # upload_app.config["UPLOAD_FOLDER"] = "test_uploads" 
    # os.makedirs(upload_app.config["UPLOAD_FOLDER"], exist_ok=True)

    with upload_app.test_client() as client:
        yield client
    
    # Clean up test uploads folder if created
    # if upload_app.config["UPLOAD_FOLDER"] == "test_uploads":
    #     import shutil
    #     shutil.rmtree("test_uploads", ignore_errors=True)


def test_upload_service_health_endpoint(client):
    """Test the /health endpoint of the upload service."""
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "healthy"
    assert json_data["service"] == "upload_service"
