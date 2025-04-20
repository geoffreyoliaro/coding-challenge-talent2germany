from flask import Flask, request, jsonify, render_template, abort, redirect, url_for, session
from marshmallow import ValidationError
from challenge.match_evaluator import EnhancedTenantMatchEvaluator
from challenge.models import EvaluationRequestSchema, EvaluationResponseSchema
import json
import uuid

app = Flask(__name__)
app.secret_key = 'tenant-screening-secret-key'  # Required for session
app.config['DEBUG'] = True  # Enable debug mode

# Store results temporarily in memory (in a real app, use a database)
results_store = {}


@app.errorhandler(400)
def bad_request(error):
    """Return JSON instead of HTML for 400 errors."""
    if request.path.startswith('/api/'):
        return jsonify({"error": "Bad Request", "message": str(error)}), 400
    return render_template('error.html', error=error), 400


@app.errorhandler(404)
def not_found(error):
    """Return JSON instead of HTML for 404 errors."""
    if request.path.startswith('/api/'):
        return jsonify({"error": "Not Found", "message": "The requested resource was not found"}), 404
    return render_template('error.html', error=error), 404


@app.errorhandler(500)
def server_error(error):
    """Return JSON instead of HTML for 500 errors."""
    if request.path.startswith('/api/'):
        return jsonify({"error": "Server Error", "message": str(error)}), 500
    return render_template('error.html', error=error), 500


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/evaluate', methods=['POST'])
def api_evaluate_tenant():
    """API endpoint for tenant evaluation."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    schema = EvaluationRequestSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    evaluator = EnhancedTenantMatchEvaluator(data['tenant'])
    results = evaluator.evaluate_tenant(data['pipeline_data'])

    response_schema = EvaluationResponseSchema()
    response_data = response_schema.dump({
        'evaluated_matches': results['evaluated_matches'],
        'match_counts': results['match_counts']
    })

    # Add tenant info to the response for the UI
    response_data['tenant_info'] = data['tenant']

    return jsonify(response_data)


@app.route('/input', methods=['GET'])
def input_form():
    """Display the input form for tenant evaluation."""
    return render_template('input.html')


@app.route('/evaluate', methods=['POST'])
def evaluate_tenant():
    """Process the tenant evaluation form and redirect to results."""
    try:
        # Get JSON data from form
        json_data = request.form.get('json_input', '')
        if not json_data:
            return render_template('input.html', error="No JSON data provided")

        # Parse JSON
        data = json.loads(json_data)

        # Validate with schema
        schema = EvaluationRequestSchema()
        validated_data = schema.load(data)

        # Process data
        evaluator = EnhancedTenantMatchEvaluator(validated_data['tenant'])
        results = evaluator.evaluate_tenant(validated_data['pipeline_data'])

        # Prepare response
        response_schema = EvaluationResponseSchema()
        response_data = response_schema.dump({
            'evaluated_matches': results['evaluated_matches'],
            'match_counts': results['match_counts']
        })

        # Add tenant info to the response for the UI
        response_data['tenant_info'] = validated_data['tenant']

        # Store results with a unique ID
        result_id = str(uuid.uuid4())
        results_store[result_id] = {
            'results': response_data,
            'json_input': json_data,
            'json_output': json.dumps(response_data, indent=2)
        }

        # Redirect to results page
        return redirect(url_for('view_results', result_id=result_id))

    except json.JSONDecodeError as e:
        return render_template('input.html', error=f"Invalid JSON: {str(e)}", json_input=json_data)
    except ValidationError as e:
        return render_template('input.html', error=f"Validation error: {str(e)}", json_input=json_data)
    except Exception as e:
        return render_template('input.html', error=f"Error: {str(e)}", json_input=json_data)


@app.route('/results/<result_id>', methods=['GET'])
def view_results(result_id):
    """Display the results of tenant evaluation."""
    if result_id not in results_store:
        return render_template('error.html', error="Results not found. They may have expired."), 404

    result_data = results_store[result_id]
    return render_template(
        'results.html',
        results=result_data['results'],
        json_input=result_data['json_input'],
        json_output=result_data['json_output'],
        result_id=result_id
    )


@app.route('/sample-data')
def sample_data():
    """Return sample data for testing."""
    sample = {
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
                        },
                        {
                            "id": 3,
                            "first_name": "John",
                            "last_name": "Smith",
                            "dob": "1990-01-01",
                            "gender": "male",
                            "nationality": "US",
                            "location": "Chicago",
                            "risk_type": "high"
                        }
                    ]
                }
            ]
        }
    }
    return jsonify(sample)


if __name__ == '__main__':
    app.run(debug=True)

