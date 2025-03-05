from flask import Flask, request, jsonify
from marshmallow import ValidationError
from match_evaluator import EnhancedTenantMatchEvaluator
from models import EvaluationRequestSchema, EvaluationResponseSchema

app = Flask(__name__)


@app.route('/evaluate', methods=['POST'])
def evaluate_tenant():
    schema = EvaluationRequestSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    evaluator = EnhancedTenantMatchEvaluator(data['tenant'])
    results = evaluator.evaluate_tenant(data['pipeline_data'])

    response_schema = EvaluationResponseSchema()
    return jsonify(response_schema.dump({
        'evaluated_matches': results['evaluated_matches'],
        'match_counts': results['match_counts']
    }))


@app.route('/')
def root():
    return jsonify({"message": "Welcome to the Tenant Screening Match Evaluator API"})


if __name__ == '__main__':
    app.run(debug=True)
