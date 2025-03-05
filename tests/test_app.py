import json
import pytest
from challenge.app import app


@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def valid_request_data():
    """Create valid request data for testing."""
    return {
        "tenant": {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "gender": "male",
            "nationality": "US",
            "location": "New York"
        },
        "pipeline_data": {
            "pipeline": [
                {
                    "type": "refinitiv-blacklist",
                    "results": [
                        {
                            "id": 1,
                            "first_name": "John",
                            "last_name": "Doe",
                            "dob": "1990-01-01",
                            "gender": "male",
                            "nationality": "US",
                            "location": "New York",
                            "risk_type": "low"
                        },
                        {
                            "id": 2,
                            "first_name": "Johnny",
                            "last_name": "Doe",
                            "dob": "1991-01-01",
                            "gender": "male",
                            "nationality": "UK",
                            "location": "London",
                            "risk_type": "medium"
                        }
                    ]
                }
            ]
        }
    }


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "Welcome to the Tenant Screening Match Evaluator API"


def test_evaluate_endpoint_valid_data(client, valid_request_data):
    """Test the evaluate endpoint with valid data."""
    response = client.post('/evaluate',
                           json=valid_request_data,
                           content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "evaluated_matches" in data
    assert "match_counts" in data
    assert len(data["evaluated_matches"]) == 2

    # Check that the first match has a high relevance score
    assert data["evaluated_matches"][0]["relevance_score"] > 0.8
    assert data["evaluated_matches"][0]["match_category"] == "HIGH_RELEVANCE"

    # Check that match counts are present
    assert "HIGH_RELEVANCE" in data["match_counts"]
    assert "MEDIUM_RELEVANCE" in data["match_counts"]
    assert "LOW_RELEVANCE" in data["match_counts"]
    assert "NOT_RELEVANT" in data["match_counts"]


def test_evaluate_endpoint_invalid_json(client):
    """Test the evaluate endpoint with invalid JSON."""
    response = client.post('/evaluate',
                           data="This is not JSON",
                           content_type='application/json')
    assert response.status_code == 415
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Request must be JSON"


def test_evaluate_endpoint_missing_required_fields(client):
    """Test the evaluate endpoint with missing required fields."""
    invalid_data = {
        "tenant": {
            "first_name": "John"
            # Missing last_name and dob
        },
        "pipeline_data": {
            "pipeline": []
        }
    }
    response = client.post('/evaluate',
                           json=invalid_data,
                           content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "tenant" in data
    assert "last_name" in data["tenant"]
    assert "dob" in data["tenant"]


def test_evaluate_endpoint_empty_pipeline(client):
    """Test the evaluate endpoint with an empty pipeline."""
    data = {
        "tenant": {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01"
        },
        "pipeline_data": {
            "pipeline": []
        }
    }
    response = client.post('/evaluate',
                           json=data,
                           content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "evaluated_matches" in data
    assert "match_counts" in data
    assert len(data["evaluated_matches"]) == 0
    assert data["match_counts"]["HIGH_RELEVANCE"] == 0
    assert data["match_counts"]["MEDIUM_RELEVANCE"] == 0
    assert data["match_counts"]["LOW_RELEVANCE"] == 0
    assert data["match_counts"]["NOT_RELEVANT"] == 0

