from marshmallow import Schema, fields, validate, validates, ValidationError


class FeedbackCommentCreateSchema(Schema):
    """Schema for feedback comment creation in requests"""
    content = fields.String(
        required=True,
        error_messages={"required": "Comment content is required"}
    )
    page = fields.Integer(allow_none=True)
    position_x = fields.Float(allow_none=True)
    position_y = fields.Float(allow_none=True)


class FeedbackCreateSchema(Schema):
    """Schema for feedback creation request validation"""
    thesis_id = fields.UUID(
        required=True,
        error_messages={"required": "Thesis ID is required"}
    )
    overall_comments = fields.String(
        required=True,
        error_messages={"required": "Overall comments are required"}
    )
    rating = fields.Integer(
        validate=validate.Range(
            min=1, max=5, error="Rating must be between 1 and 5"),
        allow_none=True
    )
    recommendations = fields.String(allow_none=True)
    comments = fields.List(fields.Nested(
        FeedbackCommentCreateSchema), allow_none=True)
    version_id = fields.UUID(allow_none=True)


class FeedbackUpdateSchema(Schema):
    """Schema for feedback update request validation"""
    overall_comments = fields.String()
    rating = fields.Integer(
        validate=validate.Range(
            min=1, max=5, error="Rating must be between 1 and 5"),
        allow_none=True
    )
    recommendations = fields.String(allow_none=True)
    comments = fields.List(fields.Nested(
        FeedbackCommentCreateSchema), allow_none=True)


class FeedbackExportSchema(Schema):
    """Schema for feedback export request validation"""
    thesis_id = fields.UUID(
        required=True,
        error_messages={"required": "Thesis ID is required"}
    )
    feedback_id = fields.UUID(allow_none=True)
    include_inline_comments = fields.Boolean(default=True)
    include_overall_comments = fields.Boolean(default=True)
    include_original_document = fields.Boolean(default=False)
    highlight_comments = fields.Boolean(default=True)
