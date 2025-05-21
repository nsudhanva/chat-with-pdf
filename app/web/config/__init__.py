import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SESSION_PERMANENT = True
    # IMPORTANT: The default SECRET_KEY is for development only and MUST be overridden in production!
    # Generate a strong, random key and set it as an environment variable.
    SECRET_KEY = os.environ.get("SECRET_KEY", "a_default_secret_key") 
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///./default.db"
    )
    UPLOAD_URL = os.environ.get("UPLOAD_URL", "/tmp/uploads")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_openai_api_key_here")
    CELERY = {
        "broker_url": os.environ.get("REDIS_URI", "redis://localhost:6379/0"),
        "task_ignore_result": True,
        "broker_connection_retry_on_startup": True,  # Changed to True for robustness
    }
