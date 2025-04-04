from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from ..exceptions.domain_exceptions import ValidationException


@dataclass
class FeedbackComment:
    """Comment within a feedback"""
    content: str
    page: Optional[int] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Feedback:
    """Feedback entity for thesis submissions"""
    thesis_id: UUID
    advisor_id: UUID
    overall_comments: str
    id: UUID = field(default_factory=uuid4)
    comments: List[FeedbackComment] = field(default_factory=list)
    rating: Optional[int] = None
    recommendations: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate feedback data"""
        if not self.thesis_id:
            raise ValidationException("Thesis ID is required")

        if not self.advisor_id:
            raise ValidationException("Advisor ID is required")

        if not self.overall_comments:
            raise ValidationException("Overall comments are required")

        if self.rating is not None and (self.rating < 1 or self.rating > 5):
            raise ValidationException("Rating must be between 1 and 5")

    def add_comment(self, content: str, page: Optional[int] = None,
                    position_x: Optional[float] = None, position_y: Optional[float] = None) -> UUID:
        """Add a new comment to the feedback"""
        comment = FeedbackComment(
            content=content,
            page=page,
            position_x=position_x,
            position_y=position_y
        )
        self.comments.append(comment)
        self.updated_at = datetime.utcnow()
        return comment.id

    def update_comment(self, comment_id: UUID, content: str) -> bool:
        """Update an existing comment"""
        for comment in self.comments:
            if comment.id == comment_id:
                comment.content = content
                self.updated_at = datetime.utcnow()
                return True
        return False

    def remove_comment(self, comment_id: UUID) -> bool:
        """Remove a comment from the feedback"""
        initial_count = len(self.comments)
        self.comments = [
            comment for comment in self.comments if comment.id != comment_id]

        if len(self.comments) < initial_count:
            self.updated_at = datetime.utcnow()
            return True
        return False

    def update_overall_feedback(self, overall_comments: Optional[str] = None,
                                rating: Optional[int] = None,
                                recommendations: Optional[str] = None):
        """Update overall feedback information"""
        if overall_comments:
            self.overall_comments = overall_comments

        if rating is not None:
            if rating < 1 or rating > 5:
                raise ValidationException("Rating must be between 1 and 5")
            self.rating = rating

        if recommendations:
            self.recommendations = recommendations

        self.updated_at = datetime.utcnow()
        self._validate()
