from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from application.interfaces.repositories.feedback_repository import FeedbackRepository
from domain.entities.feedback import Feedback
from infrastructure.database.models.feedback_model import FeedbackModel, FeedbackCommentModel
from domain.exceptions.domain_exceptions import EntityNotFoundException, ValidationException


class FeedbackRepositoryImpl(FeedbackRepository):
    """SQLAlchemy implementation of FeedbackRepository"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, feedback: Feedback) -> Feedback:
        """Create a new feedback"""
        try:
            # Create feedback
            feedback_model = FeedbackModel.from_entity(feedback)
            self.session.add(feedback_model)
            self.session.flush()  # Flush to get the ID

            # Create comments
            for comment in feedback.comments:
                comment_model = FeedbackCommentModel.from_entity(
                    comment, feedback_model.id)
                self.session.add(comment_model)

            self.session.commit()

            # Refresh to get all relationships
            self.session.refresh(feedback_model)

            return feedback_model.to_entity()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValidationException(f"Failed to create feedback: {str(e)}")

    def get_by_id(self, feedback_id: UUID) -> Optional[Feedback]:
        """Get a feedback by ID"""
        feedback_model = self.session.query(FeedbackModel).filter(
            FeedbackModel.id == str(feedback_id)).first()

        if not feedback_model:
            return None

        return feedback_model.to_entity()

    def update(self, feedback: Feedback) -> Feedback:
        """Update a feedback"""
        feedback_model = self.session.query(FeedbackModel).filter(
            FeedbackModel.id == str(feedback.id)).first()

        if not feedback_model:
            raise EntityNotFoundException("Feedback", feedback.id)

        try:
            # Update main feedback fields
            feedback_model.overall_comments = feedback.overall_comments
            feedback_model.rating = feedback.rating
            feedback_model.recommendations = feedback.recommendations

            # Handle comments - first delete existing comments
            self.session.query(FeedbackCommentModel).filter(
                FeedbackCommentModel.feedback_id == str(feedback.id)
            ).delete()

            # Add updated comments
            for comment in feedback.comments:
                comment_model = FeedbackCommentModel.from_entity(
                    comment, str(feedback.id))
                self.session.add(comment_model)

            self.session.commit()
            self.session.refresh(feedback_model)

            return feedback_model.to_entity()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValidationException(f"Failed to update feedback: {str(e)}")

    def delete(self, feedback_id: UUID) -> bool:
        """Delete a feedback"""
        feedback_model = self.session.query(FeedbackModel).filter(
            FeedbackModel.id == str(feedback_id)).first()

        if not feedback_model:
            return False

        try:
            # Comments will be deleted automatically due to cascade
            self.session.delete(feedback_model)
            self.session.commit()
            return True
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def get_by_thesis(self, thesis_id: UUID) -> List[Feedback]:
        """Get all feedback for a thesis"""
        feedback_models = (
            self.session.query(FeedbackModel)
            .filter(FeedbackModel.thesis_id == str(thesis_id))
            .order_by(desc(FeedbackModel.created_at))
            .all()
        )

        return [model.to_entity() for model in feedback_models]

    def get_by_advisor(self, advisor_id: UUID, limit: int = 100, offset: int = 0) -> List[Feedback]:
        """Get feedback by advisor ID with pagination"""
        feedback_models = (
            self.session.query(FeedbackModel)
            .filter(FeedbackModel.advisor_id == str(advisor_id))
            .order_by(desc(FeedbackModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [model.to_entity() for model in feedback_models]

    def get_by_thesis_and_advisor(self, thesis_id: UUID, advisor_id: UUID) -> Optional[Feedback]:
        """Get feedback for a thesis by a specific advisor"""
        feedback_model = (
            self.session.query(FeedbackModel)
            .filter(
                FeedbackModel.thesis_id == str(thesis_id),
                FeedbackModel.advisor_id == str(advisor_id)
            )
            .order_by(desc(FeedbackModel.created_at))
            .first()
        )

        if not feedback_model:
            return None

        return feedback_model.to_entity()

    def get_latest_by_thesis(self, thesis_id: UUID) -> Optional[Feedback]:
        """Get the latest feedback for a thesis"""
        feedback_model = (
            self.session.query(FeedbackModel)
            .filter(FeedbackModel.thesis_id == str(thesis_id))
            .order_by(desc(FeedbackModel.created_at))
            .first()
        )

        if not feedback_model:
            return None

        return feedback_model.to_entity()

    def get_feedback_stats(self, advisor_id: Optional[UUID] = None) -> Dict:
        """Get feedback statistics, optionally filtered by advisor"""
        query = self.session.query(FeedbackModel)

        if advisor_id:
            query = query.filter(FeedbackModel.advisor_id == str(advisor_id))

        # Total feedback count
        total_count = query.count()

        # Average rating
        avg_rating = (
            query.with_entities(func.avg(FeedbackModel.rating))
            .scalar() or 0
        )

        # Count of feedback by rating
        rating_counts = {}
        for rating in range(1, 6):  # Assuming 1-5 rating scale
            count = (
                query.filter(FeedbackModel.rating == rating)
                .count()
            )
            rating_counts[rating] = count

        # Feedback per month (last 6 months)
        feedback_per_month = (
            query.with_entities(
                func.year(FeedbackModel.created_at).label('year'),
                func.month(FeedbackModel.created_at).label('month'),
                func.count(FeedbackModel.id).label('count')
            )
            .group_by('year', 'month')
            .order_by(desc('year'), desc('month'))
            .limit(6)
            .all()
        )

        monthly_data = [
            {"year": year, "month": month, "count": count}
            for year, month, count in feedback_per_month
        ]

        # Average comment count per feedback
        avg_comment_count = (
            self.session.query(
                func.avg(
                    self.session.query(func.count(FeedbackCommentModel.id))
                    .filter(FeedbackCommentModel.feedback_id == FeedbackModel.id)
                    .correlate(FeedbackModel)
                    .scalar_subquery()
                )
            )
            .scalar() or 0
        )

        return {
            "total_count": total_count,
            "average_rating": round(float(avg_rating), 2),
            "rating_counts": rating_counts,
            "monthly_feedback": monthly_data,
            "average_comment_count": round(float(avg_comment_count), 2)
        }
