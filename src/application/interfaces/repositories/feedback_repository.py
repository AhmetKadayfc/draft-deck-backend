from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from uuid import UUID

from src.domain.entities.feedback import Feedback


class FeedbackRepository(ABC):
    """Interface for feedback repository operations"""

    @abstractmethod
    def create(self, feedback: Feedback) -> Feedback:
        """Create a new feedback"""
        pass

    @abstractmethod
    def get_by_id(self, feedback_id: UUID) -> Optional[Feedback]:
        """Get a feedback by ID"""
        pass

    @abstractmethod
    def update(self, feedback: Feedback) -> Feedback:
        """Update a feedback"""
        pass

    @abstractmethod
    def delete(self, feedback_id: UUID) -> bool:
        """Delete a feedback"""
        pass

    @abstractmethod
    def get_by_thesis(self, thesis_id: UUID) -> List[Feedback]:
        """Get all feedback for a thesis"""
        pass

    @abstractmethod
    def get_by_advisor(self, advisor_id: UUID, limit: int = 100, offset: int = 0) -> List[Feedback]:
        """Get feedback by advisor ID with pagination"""
        pass

    @abstractmethod
    def get_by_thesis_and_advisor(self, thesis_id: UUID, advisor_id: UUID) -> Optional[Feedback]:
        """Get feedback for a thesis by a specific advisor"""
        pass

    @abstractmethod
    def get_latest_by_thesis(self, thesis_id: UUID) -> Optional[Feedback]:
        """Get the latest feedback for a thesis"""
        pass

    @abstractmethod
    def get_feedback_stats(self, advisor_id: Optional[UUID] = None) -> Dict:
        """Get feedback statistics, optionally filtered by advisor"""
        pass
