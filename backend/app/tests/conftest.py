import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv
import os

# Load test environment variables
test_env_path = os.path.join(os.path.dirname(__file__), '.env.test')
load_dotenv(test_env_path, override=True)  # Override existing env variables

from app.main import app  # Import app after loading environment variables

@pytest.fixture(scope="function")
def client():
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client