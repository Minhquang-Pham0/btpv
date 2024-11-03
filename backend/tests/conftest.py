import pytest
from fastapi.testclient import TestClient
from ..main import app

@pytest.fixture(scope="function")
def client():
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client

# Set default event loop scope for pytest-asyncio
def pytest_configure(config):
    config.addinivalue_line(
        "asyncio_mode",
        "strict"
    )
    config.addinivalue_line(
        "asyncio_fixture_loop_scope",
        "function"
    )