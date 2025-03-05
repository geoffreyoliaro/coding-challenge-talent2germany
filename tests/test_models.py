import pytest
from datetime import datetime, date
from marshmallow import ValidationError
from challenge.models import (
    TenantSchema, MatchResultSchema, PipelineStepSchema,
    PipelineDataSchema, EvaluationRequestSchema, EvaluationResponseSchema,
    DateField
)


def test_date_field_serialization():
    """Test that the DateField can serialize both strings and datetime objects."""
    field = DateField()

    # Test with a datetime object
    dt = datetime(2020, 1, 1)
    assert field._serialize(dt, 'dob', {}) == '2020-01-01'

    # Test with a date object
    d = date(2020, 1, 1)
    assert field._serialize(d, 'dob', {}) == '2020-01-01'

    # Test with a string
    assert field._serialize('2020-01-01', 'dob', {}) == '2020-01-01'

    # Test with None
    assert field._serialize(None, 'dob', {}) is None


def test_tenant_schema():
    """Test the TenantSchema."""
    schema = TenantSchema()

    # Test valid data
    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'dob': '1990-01-01',
        'gender': 'male',
        'nationality': 'US',
        'location': 'New York'
    }
    result = schema.load(data)
    assert result['first_name'] == 'John'
    assert result['last_name'] == 'Doe'
    assert result['dob'] == '1990-01-01'

    # Test missing required fields
    with pytest.raises(ValidationError):
        schema.load({})

    # Test serialization
    serialized = schema.dump(data)
    assert serialized['first_name'] == 'John'
    assert serialized['dob'] == '1990-01-01'


def test_match_result_schema():
    """Test the MatchResultSchema."""
    schema = MatchResultSchema()

    # Test valid data
    data = {
        'id': 1,
        'first_name': 'John',
        'last_name': 'Doe',
        'dob': '1990-01-01',
        'gender': 'male',
        'nationality': 'US',
        'location': 'New York',
        'risk_type': 'low',
        'relevance_score': 0.95,
        'match_category': 'HIGH_RELEVANCE',
        'match_label': 'Highly Relevant Match',
        'match_reasons': ['Name is a strong match (0.95)'],
        'mismatch_reasons': []
    }
    result = schema.load(data)
    assert result['id'] == 1
    assert result['relevance_score'] == 0.95

    # Test missing required fields
    with pytest.raises(ValidationError):
        schema.load({})

    # Test serialization
    serialized = schema.dump(data)
    assert serialized['id'] == 1
    assert serialized['relevance_score'] == 0.95


def test_pipeline_step_schema():
    """Test the PipelineStepSchema."""
    schema = PipelineStepSchema()

    # Test valid data
    data = {
        'type': 'refinitiv-blacklist',
        'results': [
            {'id': 1, 'name': 'John Doe'}
        ]
    }
    result = schema.load(data)
    assert result['type'] == 'refinitiv-blacklist'
    assert len(result['results']) == 1

    # Test missing required fields
    with pytest.raises(ValidationError):
        schema.load({})


def test_pipeline_data_schema():
    """Test the PipelineDataSchema."""
    schema = PipelineDataSchema()

    # Test valid data
    data = {
        'pipeline': [
            {
                'type': 'refinitiv-blacklist',
                'results': [
                    {'id': 1, 'name': 'John Doe'}
                ]
            }
        ]
    }
    result = schema.load(data)
    assert len(result['pipeline']) == 1
    assert result['pipeline'][0]['type'] == 'refinitiv-blacklist'

    # Test empty pipeline
    result = schema.load({'pipeline': []})
    assert result['pipeline'] == []


def test_evaluation_request_schema():
    """Test the EvaluationRequestSchema."""
    schema = EvaluationRequestSchema()

    # Test valid data
    data = {
        'tenant': {
            'first_name': 'John',
            'last_name': 'Doe',
            'dob': '1990-01-01'
        },
        'pipeline_data': {
            'pipeline': [
                {
                    'type': 'refinitiv-blacklist',
                    'results': [
                        {'id': 1, 'name': 'John Doe'}
                    ]
                }
            ]
        }
    }
    result = schema.load(data)
    assert result['tenant']['first_name'] == 'John'
    assert len(result['pipeline_data']['pipeline']) == 1

    # Test missing required fields
    with pytest.raises(ValidationError):
        schema.load({})


def test_evaluation_response_schema():
    """Test the EvaluationResponseSchema."""
    schema = EvaluationResponseSchema()

    # Test valid data
    data = {
        'evaluated_matches': [
            {
                'id': 1,
                'first_name': 'John',
                'last_name': 'Doe',
                'dob': '1990-01-01',
                'relevance_score': 0.95,
                'match_category': 'HIGH_RELEVANCE',
                'match_label': 'Highly Relevant Match',
                'match_reasons': ['Name is a strong match (0.95)'],
                'mismatch_reasons': []
            }
        ],
        'match_counts': {
            'HIGH_RELEVANCE': 1,
            'MEDIUM_RELEVANCE': 0,
            'LOW_RELEVANCE': 0,
            'NOT_RELEVANT': 0
        }
    }
    result = schema.load(data)
    assert len(result['evaluated_matches']) == 1
    assert result['match_counts']['HIGH_RELEVANCE'] == 1

    # Test missing required fields
    with pytest.raises(ValidationError):
        schema.load({})

