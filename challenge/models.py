from marshmallow import Schema, fields, validate


class DateField(fields.Date):
    """Custom Date field that can handle both string and datetime objects."""
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return super()._serialize(value, attr, obj, **kwargs)


class TenantSchema(Schema):
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    dob = DateField(required=True)  # Using custom DateField
    gender = fields.Str()
    nationality = fields.Str()
    location = fields.Str()


class MatchResultSchema(Schema):
    id = fields.Int(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    dob = DateField(required=True)  # Using custom DateField
    gender = fields.Str()
    nationality = fields.Str()
    location = fields.Str()
    risk_type = fields.Str()
    relevance_score = fields.Float(required=True)
    match_category = fields.Str(required=True)
    match_label = fields.Str(required=True)
    match_reasons = fields.List(fields.Str())
    mismatch_reasons = fields.List(fields.Str())


class PipelineStepSchema(Schema):
    type = fields.Str(required=True)
    results = fields.List(fields.Dict())


class PipelineDataSchema(Schema):
    pipeline = fields.List(fields.Nested(PipelineStepSchema))


class EvaluationRequestSchema(Schema):
    tenant = fields.Nested(TenantSchema, required=True)
    pipeline_data = fields.Nested(PipelineDataSchema, required=True)


class EvaluationResponseSchema(Schema):
    evaluated_matches = fields.List(fields.Nested(MatchResultSchema), required=True)
    match_counts = fields.Dict(keys=fields.Str(), values=fields.Int(), required=True)

