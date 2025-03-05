import pytest
from datetime import datetime
from challenge.match_evaluator import EnhancedTenantMatchEvaluator


@pytest.fixture
def tenant_data():
    """Create tenant data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1990-01-01",
        "gender": "male",
        "nationality": "US",
        "location": "New York"
    }


@pytest.fixture
def exact_match_data():
    """Create an exact match for testing."""
    return {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1990-01-01",
        "gender": "male",
        "nationality": "US",
        "location": "New York",
        "risk_type": "low"
    }


@pytest.fixture
def partial_match_data():
    """Create a partial match for testing."""
    return {
        "id": 2,
        "first_name": "Johnny",
        "last_name": "Doe",
        "dob": "1991-01-01",
        "gender": "male",
        "nationality": "UK",
        "location": "London",
        "risk_type": "medium"
    }


@pytest.fixture
def non_match_data():
    """Create a non-match for testing."""
    return {
        "id": 3,
        "first_name": "Jane",
        "last_name": "Smith",
        "dob": "1980-05-15",
        "gender": "female",
        "nationality": "CA",
        "location": "Toronto",
        "risk_type": "high"
    }


@pytest.fixture
def pipeline_data(exact_match_data, partial_match_data, non_match_data):
    """Create pipeline data for testing."""
    return {
        "pipeline": [
            {
                "type": "refinitiv-blacklist",
                "results": [
                    exact_match_data,
                    partial_match_data,
                    non_match_data
                ]
            }
        ]
    }


def test_evaluator_initialization(tenant_data):
    """Test that the evaluator initializes correctly."""
    evaluator = EnhancedTenantMatchEvaluator(tenant_data)
    assert evaluator.tenant_data is not None
    assert evaluator.threshold == 0.7
    assert 'name_parts' in evaluator.tenant_data
    assert isinstance(evaluator.tenant_data['dob'], datetime)


def test_normalize_tenant_data(tenant_data):
    """Test the _normalize_tenant_data method."""
    evaluator = EnhancedTenantMatchEvaluator({})
    normalized = evaluator._normalize_tenant_data(tenant_data)
    assert 'name_parts' in normalized
    assert 'john' in normalized['name_parts']
    assert 'doe' in normalized['name_parts']
    assert isinstance(normalized['dob'], datetime)


def test_normalize_name():
    """Test the _normalize_name method."""
    evaluator = EnhancedTenantMatchEvaluator({})
    assert evaluator._normalize_name("John Doe") == "john doe"
    assert evaluator._normalize_name("John-Doe") == "johndoe"
    assert evaluator._normalize_name("John O'Doe") == "john odoe"
    assert evaluator._normalize_name("") == ""
    assert evaluator._normalize_name(None) == ""


def test_calculate_name_similarity():
    """Test the _calculate_name_similarity method."""
    evaluator = EnhancedTenantMatchEvaluator({})
    assert evaluator._calculate_name_similarity("John Doe", "John Doe") == 1.0
    assert evaluator._calculate_name_similarity("John Doe", "Johnny Doe") > 0.8
    assert evaluator._calculate_name_similarity("John Doe", "Jane Smith") < 0.5
    assert evaluator._calculate_name_similarity("", "John Doe") == 0.0
    assert evaluator._calculate_name_similarity("John Doe", "") == 0.0
    assert evaluator._calculate_name_similarity("", "") == 0.0


def test_compare_dates():
    """Test the _compare_dates method."""
    evaluator = EnhancedTenantMatchEvaluator({})
    date1 = datetime(1990, 1, 1)
    date2 = datetime(1990, 1, 1)
    date3 = datetime(1990, 2, 1)
    date4 = datetime(1991, 1, 1)

    assert evaluator._compare_dates(date1, date2) == 1.0
    assert evaluator._compare_dates(date1, date3) == 0.5  # Same year
    assert evaluator._compare_dates(date1, date4) == 0.0  # Different year
    assert evaluator._compare_dates(None, date1) == 0.0
    assert evaluator._compare_dates(date1, None) == 0.0
    assert evaluator._compare_dates(None, None) == 0.0


def test_evaluate_match(tenant_data, exact_match_data, partial_match_data, non_match_data):
    """Test the evaluate_match method."""
    evaluator = EnhancedTenantMatchEvaluator(tenant_data)

    # Test exact match
    result = evaluator.evaluate_match(exact_match_data)
    assert result['relevance_score'] > 0.9
    assert result['match_category'] == "HIGH_RELEVANCE"
    assert len(result['match_reasons']) > 0
    assert len(result['mismatch_reasons']) == 0

    # Test partial match
    result = evaluator.evaluate_match(partial_match_data)
    assert result['relevance_score'] > 0.5
    assert result['match_category'] in ["MEDIUM_RELEVANCE", "HIGH_RELEVANCE"]
    assert len(result['match_reasons']) > 0
    assert len(result['mismatch_reasons']) > 0

    # Test non-match
    result = evaluator.evaluate_match(non_match_data)
    assert result['relevance_score'] < 0.5
    assert result['match_category'] in ["LOW_RELEVANCE", "NOT_RELEVANT"]
    assert len(result['match_reasons']) < len(result['mismatch_reasons'])


def test_evaluate_matches(tenant_data, exact_match_data, partial_match_data, non_match_data):
    """Test the evaluate_matches method."""
    evaluator = EnhancedTenantMatchEvaluator(tenant_data)
    matches = [exact_match_data, partial_match_data, non_match_data]
    results = evaluator.evaluate_matches(matches)

    assert len(results) == 3
    assert results[0]['relevance_score'] > results[1]['relevance_score'] > results[2]['relevance_score']


def test_extract_matches_from_pipeline(tenant_data, pipeline_data):
    """Test the extract_matches_from_pipeline method."""
    evaluator = EnhancedTenantMatchEvaluator(tenant_data)
    matches = evaluator.extract_matches_from_pipeline(pipeline_data)

    assert len(matches) == 3
    assert matches[0]['id'] == 1
    assert matches[1]['id'] == 2
    assert matches[2]['id'] == 3


def test_evaluate_pipeline_data(tenant_data, pipeline_data):
    """Test the evaluate_pipeline_data method."""
    evaluator = EnhancedTenantMatchEvaluator(tenant_data)
    result = evaluator.evaluate_pipeline_data(pipeline_data)

    assert 'original_pipeline_data' in result
    assert 'evaluated_matches' in result
    assert 'match_counts' in result
    assert len(result['evaluated_matches']) == 3
    assert 'HIGH_RELEVANCE' in result['match_counts']
    assert 'MEDIUM_RELEVANCE' in result['match_counts']
    assert 'LOW_RELEVANCE' in result['match_counts']
    assert 'NOT_RELEVANT' in result['match_counts']
    assert sum(result['match_counts'].values()) == 3


def test_evaluate_tenant(tenant_data, pipeline_data):
    """Test the evaluate_tenant method."""
    evaluator = EnhancedTenantMatchEvaluator(tenant_data)
    result = evaluator.evaluate_tenant(pipeline_data)

    assert 'original_pipeline_data' in result
    assert 'evaluated_matches' in result
    assert 'match_counts' in result
    assert len(result['evaluated_matches']) == 3

