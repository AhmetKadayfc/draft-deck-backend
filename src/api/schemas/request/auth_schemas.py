from marshmallow import Schema, fields, validate, validates, validates_schema, ValidationError
import re

from src.domain.value_objects.status import UserRole


class LoginSchema(Schema):
    """Schema for login request validation"""
    email = fields.Email(required=True, error_messages={
                         "required": "Email is required"})
    password = fields.String(required=True, error_messages={
                             "required": "Password is required"})


class RegisterSchema(Schema):
    """Schema for user registration request validation"""
    email = fields.Email(required=True, error_messages={
                         "required": "Email is required"})
    password = fields.String(
        required=True,
        validate=validate.Length(
            min=8, error="Password must be at least 8 characters long"),
        error_messages={"required": "Password is required"}
    )
    first_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={"required": "First name is required"}
    )
    last_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={"required": "Last name is required"}
    )
    role = fields.String(
        required=True,
        validate=validate.OneOf(UserRole.values(), error="Invalid role"),
        error_messages={"required": "Role is required"}
    )
    department = fields.String(
        validate=validate.Length(max=100),
        allow_none=True
    )
    student_id = fields.String(
        validate=validate.Length(max=50),
        allow_none=True
    )

    @validates("student_id")
    def validate_student_id(self, value):
        """Validate student_id is present for student role"""
        role = self.get_attribute("role")
        if role == UserRole.STUDENT.value and not value:
            raise ValidationError(
                "Student ID is required for student accounts")


class PasswordResetRequestSchema(Schema):
    """Schema for password reset request validation"""
    email = fields.Email(required=True, error_messages={
                         "required": "Email is required"})


class PasswordResetSchema(Schema):
    """Schema for password reset confirmation validation"""
    token = fields.String(
        required=True,
        error_messages={"required": "Token is required"}
    )
    new_password = fields.String(
        required=True,
        validate=validate.Length(
            min=8, error="Password must be at least 8 characters long"),
        error_messages={"required": "New password is required"}
    )


class EmailVerificationSchema(Schema):
    """Schema for email verification"""
    email = fields.Email(required=True, error_messages={"required": "Email is required"})
    code = fields.String(required=True, validate=validate.Length(equal=5), error_messages={
        "required": "Verification code is required", 
        "equal": "Verification code must be 5 digits"
    })
    
    @validates_schema
    def validate_fields(self, data, **kwargs):
        # Ensure code is only digits
        if not data.get("code", "").isdigit():
            raise ValidationError("Verification code must contain only digits", "code")
