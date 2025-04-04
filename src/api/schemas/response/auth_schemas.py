from marshmallow import Schema, fields


class UserResponseSchema(Schema):
    """Schema for user data in responses"""
    id = fields.UUID()
    email = fields.Email()
    first_name = fields.String()
    last_name = fields.String()
    role = fields.String()
    department = fields.String(allow_none=True)
    student_id = fields.String(allow_none=True)
    is_active = fields.Boolean()
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)


class TokenResponseSchema(Schema):
    """Schema for authentication token responses"""
    access_token = fields.String()
    refresh_token = fields.String()
    token_type = fields.String()
    expires_in = fields.Integer()
    user = fields.Nested(UserResponseSchema)
