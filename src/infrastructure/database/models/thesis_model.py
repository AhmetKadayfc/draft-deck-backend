import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text, ForeignKey, JSON
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from src.infrastructure.database.connection import Base
from src.domain.value_objects.status import ThesisStatus, ThesisType


class ThesisModel(Base):
    """SQLAlchemy model for theses"""
    __tablename__ = "theses"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    student_id = Column(CHAR(36), ForeignKey(
        "users.id"), nullable=False, index=True)
    advisor_id = Column(CHAR(36), ForeignKey(
        "users.id"), nullable=True, index=True)
    thesis_type = Column(Enum(ThesisType.DRAFT.value, ThesisType.FINAL.value),
                         nullable=False, default=ThesisType.DRAFT.value)
    status = Column(Enum(*ThesisStatus.values()),
                    nullable=False, default=ThesisStatus.DRAFT.value, index=True)
    version = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)
    file_path = Column(String(255), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(100), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    _metadata = Column(JSON, nullable=True)

    # Relationships
    student = relationship("UserModel", foreign_keys=[
                           student_id], backref="theses")
    advisor = relationship("UserModel", foreign_keys=[
                           advisor_id], backref="supervised_theses")

    def to_entity(self):
        """Convert model to domain entity"""
        from src.domain.entities.thesis import Thesis

        metadata_dict = {}
        if self._metadata:
            if isinstance(self._metadata, str):
                try:
                    metadata_dict = json.loads(self._metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata_dict = {}
            else:
                metadata_dict = self._metadata

        return Thesis(
            id=uuid.UUID(self.id),
            title=self.title,
            student_id=uuid.UUID(self.student_id),
            advisor_id=uuid.UUID(self.advisor_id) if self.advisor_id else None,
            thesis_type=ThesisType(self.thesis_type),
            status=ThesisStatus(self.status),
            version=self.version,
            description=self.description,
            file_path=self.file_path,
            file_name=self.file_name,
            file_size=self.file_size,
            file_type=self.file_type,
            submitted_at=self.submitted_at,
            approved_at=self.approved_at,
            rejected_at=self.rejected_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=metadata_dict
        )

    @classmethod
    def from_entity(cls, thesis):
        """Create model from domain entity"""
        metadata_json = None
        if thesis._metadata:
            if isinstance(thesis._metadata, dict):
                metadata_json = thesis._metadata
            else:
                try:
                    metadata_json = json.loads(thesis._metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata_json = {}

        return cls(
            id=str(thesis.id),
            title=thesis.title,
            student_id=str(thesis.student_id),
            advisor_id=str(thesis.advisor_id) if thesis.advisor_id else None,
            thesis_type=thesis.thesis_type.value,
            status=thesis.status.value,
            version=thesis.version,
            description=thesis.description,
            file_path=thesis.file_path,
            file_name=thesis.file_name,
            file_size=thesis.file_size,
            file_type=thesis.file_type,
            submitted_at=thesis.submitted_at,
            approved_at=thesis.approved_at,
            rejected_at=thesis.rejected_at,
            created_at=thesis.created_at,
            updated_at=thesis.updated_at,
            metadata=metadata_json
        )
