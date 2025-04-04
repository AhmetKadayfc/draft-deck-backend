from marshmallow import Schema, fields


class ThesisFileInfoSchema(Schema):
    """Schema for thesis file information in responses"""
    file_name = fields.String()
    file_path = fields.String()
    file_size = fields.Integer()
    file_type = fields.String()
    upload_date = fields.DateTime()


class ThesisResponseSchema(Schema):
    """Schema for thesis data in responses"""
    id = fields.UUID()
    title = fields.String()
    student_id = fields.UUID()
    student_name = fields.String(allow_none=True)
    advisor_id = fields.UUID(allow_none=True)
    advisor_name = fields.String(allow_none=True)
    thesis_type = fields.String()
    status = fields.String()
    version = fields.Integer()
    description = fields.String(allow_none=True)
    file_info = fields.Nested(ThesisFileInfoSchema, allow_none=True)
    download_url = fields.String(allow_none=True)
    submitted_at = fields.DateTime(allow_none=True)
    approved_at = fields.DateTime(allow_none=True)
    rejected_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime(allow_none=True)
    metadata = fields.Dict()


class ThesisVersionResponseSchema(Schema):
    """Schema for thesis version data in responses"""
    id = fields.UUID()
    thesis_id = fields.UUID()
    version_number = fields.Integer()
    file_name = fields.String(allow_none=True)
    file_size = fields.Integer(allow_none=True)
    file_type = fields.String(allow_none=True)
    download_url = fields.String(allow_none=True)
    changes_description = fields.String(allow_none=True)
    submitted_by = fields.UUID()
    submitter_name = fields.String(allow_none=True)
    created_at = fields.DateTime()
