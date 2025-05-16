from uuid import UUID
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class FeedbackCommentCreateDTO:
    """DTO for feedback comment creation"""
    content: str
    page: Optional[int] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None


@dataclass
class FeedbackCommentResponseDTO:
    """DTO for feedback comment response"""
    id: UUID
    content: str
    page: Optional[int] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    created_at: datetime = None


@dataclass
class FeedbackCreateDTO:
    """DTO for feedback creation"""
    thesis_id: UUID
    overall_comments: str
    rating: Optional[int] = None
    recommendations: Optional[str] = None
    comments: List[FeedbackCommentCreateDTO] = field(default_factory=list)


@dataclass
class FeedbackUpdateDTO:
    """DTO for feedback update"""
    overall_comments: Optional[str] = None
    rating: Optional[int] = None
    recommendations: Optional[str] = None


@dataclass
class FeedbackResponseDTO:
    """DTO for feedback response"""
    id: UUID
    thesis_id: UUID
    advisor_id: UUID
    overall_comments: str
    thesis_title: Optional[str] = None
    advisor_name: Optional[str] = None
    rating: Optional[int] = None
    recommendations: Optional[str] = None
    comments: List[FeedbackCommentResponseDTO] = field(default_factory=list)
    created_at: datetime = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_entity(cls, feedback, thesis_title=None, advisor_name=None):
        """Create DTO from Feedback entity"""
        comments = [
            FeedbackCommentResponseDTO(
                id=comment.id,
                content=comment.content,
                page=comment.page,
                position_x=comment.position_x,
                position_y=comment.position_y,
                created_at=comment.created_at
            )
            for comment in feedback.comments
        ]

        return cls(
            id=feedback.id,
            thesis_id=feedback.thesis_id,
            thesis_title=thesis_title,
            advisor_id=feedback.advisor_id,
            advisor_name=advisor_name,
            overall_comments=feedback.overall_comments,
            rating=feedback.rating,
            recommendations=feedback.recommendations,
            comments=comments,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at
        )


@dataclass
class FeedbackExportDTO:
    """DTO for feedback export options"""
    thesis_id: UUID
    feedback_id: Optional[UUID] = None
    include_inline_comments: bool = True
    include_overall_comments: bool = True
    include_original_document: bool = False
    highlight_comments: bool = True
