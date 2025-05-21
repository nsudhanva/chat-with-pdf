import pytest
from app.web import create_app
from app.web.config import Config


@pytest.fixture
def app_instance():
    """Create and configure a new app instance for each test."""
    # Basic config for testing; ideally, use a dedicated test config
    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Use in-memory DB for tests
        CELERY = { # Mock Celery config for tests
            "broker_url": "memory://",
            "task_ignore_result": True,
            "broker_connection_retry_on_startup": False,
        }
        # Ensure other necessary configs from the main Config are inherited or set
        # For example, if OPENAI_API_KEY is used at app creation/blueprint registration:
        OPENAI_API_KEY = "test_key" 


    app = create_app()
    app.config.from_object(TestConfig)
    return app


@pytest.fixture
def client(app_instance):
    """A test client for the app."""
    return app_instance.test_client()


def test_backend_health_endpoint(client):
    """Test the /api/health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "healthy"
    assert json_data["service"] == "backend"
