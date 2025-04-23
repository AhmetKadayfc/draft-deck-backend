from marshmallow import Schema, fields, validate, validates, ValidationError

from src.domain.value_objects.status import ThesisStatus, ThesisType


class ThesisCreateSchema(Schema):
    """Schema for thesis creation request validation"""
    title = fields.String(
        required=True,
        validate=validate.Length(min=3, max=255),
        error_messages={"required": "Title is required"}
    )
    thesis_type = fields.String(
        required=True,
        validate=validate.OneOf(ThesisType.values(),
                                error="Invalid thesis type"),
        error_messages={"required": "Thesis type is required"}
    )
    description = fields.String(allow_none=True)
    metadata = fields.Dict(allow_none=True)


class ThesisUpdateSchema(Schema):
    """Schema for thesis update request validation"""
    title = fields.String(
        validate=validate.Length(min=3, max=255),
    )
    thesis_type = fields.String(
        validate=validate.OneOf(ThesisType.values(),
                               error="Invalid thesis type")
    )
    description = fields.String(allow_none=True)
    metadata = fields.Dict(allow_none=True)


class ThesisStatusUpdateSchema(Schema):
    """Schema for thesis status update request validation"""
    status = fields.String(
        required=True,
        validate=validate.OneOf(ThesisStatus.values(), error="Invalid status"),
        error_messages={"required": "Status is required"}
    )


class ThesisVersionCreateSchema(Schema):
    """Schema for creating a new thesis version"""
    changes_description = fields.String(allow_none=True)
    # Note: file will be handled from request.files
