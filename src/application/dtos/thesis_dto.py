from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

from src.domain.value_objects.status import ThesisStatus, ThesisType


@dataclass
class ThesisCreateDTO:
    """DTO for thesis creation"""
    title: str
    thesis_type: str
    description: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class ThesisUpdateDTO:
    """DTO for thesis update"""
    title: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class ThesisStatusUpdateDTO:
    """DTO for thesis status update"""
    status: str


@dataclass
class ThesisFileDTO:
    """DTO for thesis file information"""
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    upload_date: datetime


@dataclass
class AdvisorAssignmentDTO:
    """DTO for advisor assignment"""
    advisor_id: UUID


@dataclass
class ThesisResponseDTO:
    """DTO for thesis response"""
    id: UUID
    title: str
    student_id: UUID
    student_name: Optional[str] = None
    advisor_id: Optional[UUID] = None
    advisor_name: Optional[str] = None
    thesis_type: str
    status: str
    version: int
    description: Optional[str] = None
    file_info: Optional[ThesisFileDTO] = None
    download_url: Optional[str] = None
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)

    @classmethod
    def from_entity(cls, thesis, student_name=None, advisor_name=None, download_url=None):
        """Create DTO from Thesis entity"""
        file_info = None
        if thesis.file_path and thesis.file_name:
            file_info = ThesisFileDTO(
                file_name=thesis.file_name,
                file_path=thesis.file_path,
                file_size=thesis.file_size or 0,
                file_type=thesis.file_type or "unknown",
                upload_date=thesis.updated_at or thesis.created_at
            )

        return cls(
            id=thesis.id,
            title=thesis.title,
            student_id=thesis.student_id,
            student_name=student_name,
            advisor_id=thesis.advisor_id,
            advisor_name=advisor_name,
            thesis_type=thesis.thesis_type.value,
            status=thesis.status.value,
            version=thesis.version,
            description=thesis.description,
            file_info=file_info,
            download_url=download_url,
            submitted_at=thesis.submitted_at,
            approved_at=thesis.approved_at,
            rejected_at=thesis.rejected_at,
            created_at=thesis.created_at,
            updated_at=thesis.updated_at,
            metadata=thesis.metadata
        )


@dataclass
class ThesisSearchDTO:
    """DTO for thesis search parameters"""
    query: Optional[str] = None
    student_id: Optional[UUID] = None
    advisor_id: Optional[UUID] = None
    status: Optional[str] = None
    thesis_type: Optional[str] = None
    department: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = 20
    offset: int = 0
