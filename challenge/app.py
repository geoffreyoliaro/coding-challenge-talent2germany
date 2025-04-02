from flask import Flask, request, jsonify, render_template, abort, redirect, url_for, session, send_file
from marshmallow import ValidationError
from challenge.match_evaluator import EnhancedTenantMatchEvaluator
from challenge.models import EvaluationRequestSchema, EvaluationResponseSchema
from challenge.pdf_generator import TenantScreeningPDFGenerator
import json
import uuid
from datetime import date, datetime
import os


# Create a custom JSON encoder for handling dates
class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that can handle date and datetime objects."""

    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


# Create Flask app with explicit template folder
#template_dir = r"C:\Users\user\OneDrive\Desktop\test-coding-challenge\coding-challenge-talent2germany\templates"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = 'tenant-screening-secret-key'  # Required for session

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


@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    """Generate a PDF report from tenant screening results."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    try:
        # Get the evaluation results from the request
        data = request.json

        # Validate that we have the necessary data
        if 'evaluated_matches' not in data or 'match_counts' not in data or 'tenant_info' not in data:
            return jsonify({"error": "Missing required data for PDF generation"}), 400

        # Generate the PDF
        pdf_generator = TenantScreeningPDFGenerator()
        pdf_buffer = pdf_generator.generate_pdf(data)

        # Generate a filename based on tenant name
        tenant_name = f"{data['tenant_info'].get('first_name', 'Unknown')}_{data['tenant_info'].get('last_name', 'Tenant')}"
        filename = f"tenant_screening_{tenant_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Return the PDF as a downloadable file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500


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

        # Convert any date objects to strings before storing
        json_output = json.dumps(response_data, cls=CustomJSONEncoder, indent=2)

        # Store results with a unique ID
        result_id = str(uuid.uuid4())
        results_store[result_id] = {
            'results': response_data,
            'json_input': json_data,
            'json_output': json_output
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


@app.route('/download-pdf/<result_id>', methods=['GET'])
def download_pdf(result_id):
    """Generate and download a PDF report for a specific result."""
    if result_id not in results_store:
        return render_template('error.html', error="Results not found. They may have expired."), 404

    try:
        # Get the results data
        result_data = results_store[result_id]
        results = result_data['results']

        # Generate the PDF
        pdf_generator = TenantScreeningPDFGenerator()
        pdf_buffer = pdf_generator.generate_pdf(results)

        # Generate a filename based on tenant name
        tenant_info = results.get('tenant_info', {})
        tenant_name = f"{tenant_info.get('first_name', 'Unknown')}_{tenant_info.get('last_name', 'Tenant')}"
        filename = f"tenant_screening_{tenant_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Return the PDF as a downloadable file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return render_template('error.html', error=f"PDF generation failed: {str(e)}"), 500


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

