import uuid
import json
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

from src.infrastructure.database.connection import Base


class FeedbackCommentModel(Base):
    """SQLAlchemy model for feedback comments"""
    __tablename__ = "feedback_comments"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    feedback_id = Column(CHAR(36), ForeignKey(
        "feedback.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    page = Column(Integer, nullable=True)
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    feedback = relationship("FeedbackModel", back_populates="comments")

    def to_entity(self):
        """Convert model to domain entity"""
        from src.domain.entities.feedback import FeedbackComment

        return FeedbackComment(
            id=uuid.UUID(self.id),
            content=self.content,
            page=self.page,
            position_x=self.position_x,
            position_y=self.position_y,
            created_at=self.created_at
        )

    @classmethod
    def from_entity(cls, comment, feedback_id):
        """Create model from domain entity"""
        return cls(
            id=str(comment.id),
            feedback_id=feedback_id,
            content=comment.content,
            page=comment.page,
            position_x=comment.position_x,
            position_y=comment.position_y,
            created_at=comment.created_at
        )


class FeedbackModel(Base):
    """SQLAlchemy model for feedback"""
    __tablename__ = "feedback"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thesis_id = Column(CHAR(36), ForeignKey(
        "theses.id"), nullable=False, index=True)
    advisor_id = Column(CHAR(36), ForeignKey(
        "users.id"), nullable=False, index=True)
    overall_comments = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)
    recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    thesis = relationship("ThesisModel", backref="feedback")
    advisor = relationship("UserModel", backref="provided_feedback")
    comments = relationship(
        "FeedbackCommentModel", back_populates="feedback", cascade="all, delete-orphan")

    def to_entity(self):
        """Convert model to domain entity"""
        from src.domain.entities.feedback import Feedback

        comments = [comment.to_entity() for comment in self.comments]

        feedback = Feedback(
            id=uuid.UUID(self.id),
            thesis_id=uuid.UUID(self.thesis_id),
            advisor_id=uuid.UUID(self.advisor_id),
            overall_comments=self.overall_comments,
            rating=self.rating,
            recommendations=self.recommendations,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

        # Set comments directly to avoid validation during creation
        feedback.comments = comments

        return feedback

    @classmethod
    def from_entity(cls, feedback):
        """Create model from domain entity"""
        model = cls(
            id=str(feedback.id),
            thesis_id=str(feedback.thesis_id),
            advisor_id=str(feedback.advisor_id),
            overall_comments=feedback.overall_comments,
            rating=feedback.rating,
            recommendations=feedback.recommendations,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at
        )

        return model
