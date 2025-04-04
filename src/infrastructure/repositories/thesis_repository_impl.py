from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy import desc, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.application.interfaces.repositories.thesis_repository import ThesisRepository
from src.domain.entities.thesis import Thesis
from src.domain.value_objects.status import ThesisStatus, ThesisType
from src.infrastructure.database.models.thesis_model import ThesisModel
from src.domain.exceptions.domain_exceptions import EntityNotFoundException, ValidationException


class ThesisRepositoryImpl(ThesisRepository):
    """SQLAlchemy implementation of ThesisRepository"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, thesis: Thesis) -> Thesis:
        """Create a new thesis"""
        try:
            thesis_model = ThesisModel.from_entity(thesis)
            self.session.add(thesis_model)
            self.session.commit()

            # Refresh to get any database-generated values
            self.session.refresh(thesis_model)

            return thesis_model.to_entity()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValidationException(f"Failed to create thesis: {str(e)}")

    def get_by_id(self, thesis_id: UUID) -> Optional[Thesis]:
        """Get a thesis by ID"""
        thesis_model = self.session.query(ThesisModel).filter(
            ThesisModel.id == str(thesis_id)).first()

        if not thesis_model:
            return None

        return thesis_model.to_entity()

    def update(self, thesis: Thesis) -> Thesis:
        """Update a thesis"""
        thesis_model = self.session.query(ThesisModel).filter(
            ThesisModel.id == str(thesis.id)).first()

        if not thesis_model:
            raise EntityNotFoundException("Thesis", thesis.id)

        try:
            # Update all fields from entity
            thesis_model.title = thesis.title
            thesis_model.student_id = str(thesis.student_id)
            thesis_model.advisor_id = str(
                thesis.advisor_id) if thesis.advisor_id else None
            thesis_model.thesis_type = thesis.thesis_type.value
            thesis_model.status = thesis.status.value
            thesis_model.version = thesis.version
            thesis_model.description = thesis.description
            thesis_model.file_path = thesis.file_path
            thesis_model.file_name = thesis.file_name
            thesis_model.file_size = thesis.file_size
            thesis_model.file_type = thesis.file_type
            thesis_model.submitted_at = thesis.submitted_at
            thesis_model.approved_at = thesis.approved_at
            thesis_model.rejected_at = thesis.rejected_at
            thesis_model.metadata = thesis.metadata

            self.session.commit()
            self.session.refresh(thesis_model)

            return thesis_model.to_entity()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValidationException(f"Failed to update thesis: {str(e)}")

    def delete(self, thesis_id: UUID) -> bool:
        """Delete a thesis"""
        thesis_model = self.session.query(ThesisModel).filter(
            ThesisModel.id == str(thesis_id)).first()

        if not thesis_model:
            return False

        try:
            self.session.delete(thesis_model)
            self.session.commit()
            return True
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Get all theses with pagination"""
        thesis_models = (
            self.session.query(ThesisModel)
            .order_by(desc(ThesisModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [model.to_entity() for model in thesis_models]

    def get_by_student(self, student_id: UUID, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Get theses by student ID with pagination"""
        thesis_models = (
            self.session.query(ThesisModel)
            .filter(ThesisModel.student_id == str(student_id))
            .order_by(desc(ThesisModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [model.to_entity() for model in thesis_models]

    def get_by_advisor(self, advisor_id: UUID, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Get theses by advisor ID with pagination"""
        thesis_models = (
            self.session.query(ThesisModel)
            .filter(ThesisModel.advisor_id == str(advisor_id))
            .order_by(desc(ThesisModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [model.to_entity() for model in thesis_models]

    def get_by_status(self, status: ThesisStatus, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Get theses by status with pagination"""
        thesis_models = (
            self.session.query(ThesisModel)
            .filter(ThesisModel.status == status.value)
            .order_by(desc(ThesisModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [model.to_entity() for model in thesis_models]

    def get_by_type(self, thesis_type: ThesisType, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Get theses by type with pagination"""
        thesis_models = (
            self.session.query(ThesisModel)
            .filter(ThesisModel.thesis_type == thesis_type.value)
            .order_by(desc(ThesisModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [model.to_entity() for model in thesis_models]

    def search(self, query: str, limit: int = 100, offset: int = 0) -> List[Thesis]:
        """Search theses by title or description"""
        query_term = f"%{query}%"
        thesis_models = (
            self.session.query(ThesisModel)
            .filter(or_(
                ThesisModel.title.ilike(query_term),
                ThesisModel.description.ilike(query_term)
            ))
            .order_by(desc(ThesisModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [model.to_entity() for model in thesis_models]

    def get_versions(self, thesis_id: UUID) -> List[Thesis]:
        """Get all versions of a thesis"""
        # Get the original thesis to find its title and student
        original_thesis = self.session.query(ThesisModel).filter(
            ThesisModel.id == str(thesis_id)).first()

        if not original_thesis:
            return []

        # Find all theses with the same title and student (likely versions)
        thesis_models = (
            self.session.query(ThesisModel)
            .filter(
                ThesisModel.title == original_thesis.title,
                ThesisModel.student_id == original_thesis.student_id
            )
            .order_by(ThesisModel.version)
            .all()
        )

        return [model.to_entity() for model in thesis_models]

    def get_stats(self) -> Dict:
        """Get thesis statistics"""
        # Total theses count
        total_count = self.session.query(func.count(ThesisModel.id)).scalar()

        # Count by status
        status_counts = {}
        for status in ThesisStatus:
            count = (
                self.session.query(func.count(ThesisModel.id))
                .filter(ThesisModel.status == status.value)
                .scalar()
            )
            status_counts[status.value] = count

        # Count by type
        type_counts = {}
        for thesis_type in ThesisType:
            count = (
                self.session.query(func.count(ThesisModel.id))
                .filter(ThesisModel.thesis_type == thesis_type.value)
                .scalar()
            )
            type_counts[thesis_type.value] = count

        # Submissions per month (last 6 months)
        # This is a simplified approach - in a real app, you'd want to use proper time functions
        submissions_per_month = (
            self.session.query(
                func.year(ThesisModel.created_at).label('year'),
                func.month(ThesisModel.created_at).label('month'),
                func.count(ThesisModel.id).label('count')
            )
            .filter(ThesisModel.status != ThesisStatus.DRAFT.value)
            .group_by('year', 'month')
            .order_by(desc('year'), desc('month'))
            .limit(6)
            .all()
        )

        monthly_data = [
            {"year": year, "month": month, "count": count}
            for year, month, count in submissions_per_month
        ]

        return {
            "total_count": total_count,
            "status_counts": status_counts,
            "type_counts": type_counts,
            "monthly_submissions": monthly_data
        }
