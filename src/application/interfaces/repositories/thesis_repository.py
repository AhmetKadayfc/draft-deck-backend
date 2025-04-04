from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from uuid import UUID

from src.domain.entities.thesis import Thesis
from src.domain.value_objects.status import ThesisStatus, ThesisType


class ThesisRepository(ABC):
    """Interface for thesis repository operations"""

    @abstractmethod
    def create(self, thesis: Thesis) -> Thesis:
        """Create a new thesis"""
        pass

    @abstractmethod
    def get_by_id(self, thesis_id: UUID) -> Optional[Thesis]:
        """Get a thesis by ID"""
        pass

    @abstractmethod
    def update(self, thesis: Thesis) -> Thesis:
        """Update a thesis"""
        pass

    @abstractmethod
    def delete(self, thesis_id: UUID) -> bool:
        """Delete a thesis"""
        pass

    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Get all theses with pagination"""
        pass

    @abstractmethod
    def get_by_student(self, student_id: UUID, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Get theses by student ID with pagination"""
        pass

    @abstractmethod
    def get_by_advisor(self, advisor_id: UUID, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Get theses by advisor ID with pagination"""
        pass

    @abstractmethod
    def get_by_status(self, status: ThesisStatus, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Get theses by status with pagination"""
        pass

    @abstractmethod
    def get_by_type(self, thesis_type: ThesisType, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Get theses by type with pagination"""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Search theses by title or description"""
        pass

    @abstractmethod
    def get_versions(self, thesis_id: UUID) -> List[Thesis]:
        """Get all versions of a thesis"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict:
        """Get thesis statistics"""
        pass
