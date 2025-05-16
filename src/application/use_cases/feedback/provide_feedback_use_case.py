from typing import Optional
from uuid import UUID

from src.application.dtos.feedback_dto import FeedbackCreateDTO, FeedbackResponseDTO
from src.application.interfaces.repositories.feedback_repository import FeedbackRepository
from src.application.interfaces.repositories.thesis_repository import ThesisRepository
from src.application.interfaces.repositories.user_repository import UserRepository
from src.application.interfaces.services.notification_service import NotificationService
from src.domain.entities.feedback import Feedback, FeedbackComment
from src.domain.exceptions.domain_exceptions import ValidationException, EntityNotFoundException
from src.domain.value_objects.status import UserRole, ThesisStatus, NotificationType


class ProvideFeedbackUseCase:
    """Use case for providing feedback on a thesis"""

    def __init__(
        self,
        feedback_repository: FeedbackRepository,
        thesis_repository: ThesisRepository,
        user_repository: UserRepository,
        notification_service: Optional[NotificationService] = None
    ):
        self.feedback_repository = feedback_repository
        self.thesis_repository = thesis_repository
        self.user_repository = user_repository
        self.notification_service = notification_service

    def execute(self, dto: FeedbackCreateDTO, advisor_id: UUID) -> FeedbackResponseDTO:
        """
        Provide feedback on a thesis
        
        Args:
            dto: Feedback creation data
            advisor_id: ID of the advisor providing feedback
            
        Returns:
            FeedbackResponseDTO with created feedback data
            
        Raises:
            ValidationException: If validation fails
            EntityNotFoundException: If thesis or advisor not found
        """
        # Validate advisor exists and has advisor role
        advisor = self.user_repository.get_by_id(advisor_id)
        if not advisor:
            raise EntityNotFoundException("User", advisor_id)

        if advisor.role != UserRole.ADVISOR:
            raise ValidationException("Only advisors can provide feedback")

        # Validate thesis exists
        thesis = self.thesis_repository.get_by_id(dto.thesis_id)
        if not thesis:
            raise EntityNotFoundException("Thesis", dto.thesis_id)

        # Ensure thesis is in a valid state for feedback
        if thesis.status not in [ThesisStatus.SUBMITTED, ThesisStatus.UNDER_REVIEW]:
            raise ValidationException(
                f"Cannot provide feedback on thesis with status '{thesis.status.value}'")

        # Check if advisor is assigned to this thesis
        if thesis.advisor_id and thesis.advisor_id != advisor_id:
            raise ValidationException("You are not assigned to this thesis")

        # If no advisor is assigned, assign this advisor
        if not thesis.advisor_id:
            thesis.assign_advisor(advisor_id)
            self.thesis_repository.update(thesis)

        # Update thesis status to under review if it's currently submitted
        if thesis.status == ThesisStatus.SUBMITTED:
            thesis.update_status(ThesisStatus.UNDER_REVIEW)
            self.thesis_repository.update(thesis)

        # Create feedback entity
        feedback = Feedback(
            thesis_id=dto.thesis_id,
            advisor_id=advisor_id,
            overall_comments=dto.overall_comments,
            rating=dto.rating,
            recommendations=dto.recommendations
        )

        # Add comments if provided
        for comment_dto in dto.comments:
            feedback.add_comment(
                content=comment_dto.content,
                page=comment_dto.page,
                position_x=comment_dto.position_x,
                position_y=comment_dto.position_y
            )

        # Save feedback
        created_feedback = self.feedback_repository.create(feedback)

        # Send notification if notification service is available
        if self.notification_service:
            self.notification_service.notify_feedback_provided(
                thesis_id=thesis.id,
                feedback_id=created_feedback.id
            )

        # Get advisor and thesis info for response
        advisor_name = advisor.full_name()
        thesis_title = str(thesis.title) if thesis.title else None

        # Return response
        return FeedbackResponseDTO.from_entity(
            created_feedback,
            thesis_title=thesis_title,
            advisor_name=advisor_name
        )
