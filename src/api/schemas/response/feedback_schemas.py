from marshmallow import Schema, fields


class FeedbackCommentResponseSchema(Schema):
    """Schema for feedback comment data in responses"""
    id = fields.UUID()
    content = fields.String()
    page = fields.Integer(allow_none=True)
    position_x = fields.Float(allow_none=True)
    position_y = fields.Float(allow_none=True)
    created_at = fields.DateTime()


class FeedbackResponseSchema(Schema):
    """Schema for feedback data in responses"""
    id = fields.UUID()
    thesis_id = fields.UUID()
    thesis_title = fields.String(allow_none=True)
    advisor_id = fields.UUID()
    advisor_name = fields.String(allow_none=True)
    overall_comments = fields.String()
    rating = fields.Integer(allow_none=True)
    recommendations = fields.String(allow_none=True)
    comments = fields.List(fields.Nested(FeedbackCommentResponseSchema))
    created_at = fields.DateTime()
    updated_at = fields.DateTime(allow_none=True)
    version_id = fields.UUID(allow_none=True)
    version_number = fields.Integer(allow_none=True)
