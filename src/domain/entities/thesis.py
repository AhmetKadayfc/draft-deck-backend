from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID, uuid4

from ..value_objects.status import ThesisStatus, ThesisType
from ..exceptions.domain_exceptions import ValidationException, InvalidStatusTransitionException
from ..value_objects.status import VALID_STATUS_TRANSITIONS


@dataclass
class Thesis:
    """Thesis entity for the thesis management system"""
    title: str
    student_id: UUID
    thesis_type: ThesisType
    id: UUID = field(default_factory=uuid4)
    advisor_id: Optional[UUID] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    description: Optional[str] = None
    status: ThesisStatus = ThesisStatus.DRAFT
    version: int = 1
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate thesis data"""
        if not self.title:
            raise ValidationException("Thesis title is required")

        if not self.student_id:
            raise ValidationException("Student ID is required")

        if self.thesis_type not in [ThesisType.DRAFT, ThesisType.FINAL]:
            raise ValidationException("Invalid thesis type")

        if self.status not in [status for status in ThesisStatus]:
            raise ValidationException("Invalid thesis status")

    def update_status(self, new_status: ThesisStatus):
        """Update thesis status with validation for valid state transitions"""
        if new_status not in VALID_STATUS_TRANSITIONS.get(self.status, []):
            raise InvalidStatusTransitionException(
                self.status.value, new_status.value)

        self.status = new_status
        self.updated_at = datetime.utcnow()

        # Update related timestamps based on status
        if new_status == ThesisStatus.SUBMITTED:
            self.submitted_at = datetime.utcnow()
        elif new_status == ThesisStatus.APPROVED:
            self.approved_at = datetime.utcnow()
        elif new_status == ThesisStatus.REJECTED:
            self.rejected_at = datetime.utcnow()

    def update_file_info(self, file_path: str, file_name: str, file_size: int, file_type: str):
        """Update file information"""
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        self.file_type = file_type
        self.updated_at = datetime.utcnow()

    def assign_advisor(self, advisor_id: UUID):
        """Assign an advisor to the thesis"""
        self.advisor_id = advisor_id
        self.updated_at = datetime.utcnow()

    def update_metadata(self, key: str, value: any):
        """Update thesis metadata"""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def increment_version(self):
        """Increment thesis version for new submissions"""
        self.version += 1
        self.updated_at = datetime.utcnow()

    def update_title_description(self, title: Optional[str] = None, description: Optional[str] = None):
        """Update thesis title and/or description"""
        if title:
            self.title = title

        if description:
            self.description = description

        self.updated_at = datetime.utcnow()
        self._validate()
