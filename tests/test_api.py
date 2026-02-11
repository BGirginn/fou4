import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app, get_pm

# Create a mock ProjectManager
mock_pm = MagicMock()
mock_pm.get_finding_stats.return_value = {"total": 10}
mock_pm.get_findings.return_value = []

# Override dependencies
app.dependency_overrides[get_pm] = lambda: mock_pm

client = TestClient(app)

def test_health_check_public():
    """Health check should be public."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root_public():
    """Root endpoint should be public."""
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()

@patch("api.main._load_api_key")
def test_api_auth_middleware_missing_key_config(mock_load_key):
    """If no key is configured, API should be open."""
    # Simulate no key configured
    mock_load_key.return_value = ""
    
    # We need to make sure the request is processed, so mock the endpoint response indirectly
    # by ensuring mock_pm is used.
    response = client.get("/api/projects/1/findings/stats")
    
    # Needs to be 200 OK
    assert response.status_code == 200
    assert response.json() == {"total": 10}

@patch("api.main._load_api_key")
def test_api_auth_middleware_valid_key(mock_load_key):
    """With key configured, correct key allows access."""
    mock_load_key.return_value = "secret123"
    headers = {"X-API-Key": "secret123"}
    
    response = client.get("/api/projects/1/findings/stats", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"total": 10}

@patch("api.main._load_api_key")
def test_api_auth_middleware_invalid_key(mock_load_key):
    """With key configured, wrong key returns 401."""
    mock_load_key.return_value = "secret123"
    headers = {"X-API-Key": "wrong_key"}
    
    response = client.get("/api/projects/1/findings/stats", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}

@patch("api.main._load_api_key")
def test_api_auth_middleware_no_key_provided(mock_load_key):
    """With key configured, missing key returns 401."""
    mock_load_key.return_value = "secret123"
    
    response = client.get("/api/projects/1/findings/stats")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}
