from typing import Optional

from application.dtos.user_dto import UserCreateDTO, UserResponseDTO
from application.interfaces.repositories.user_repository import UserRepository
from application.interfaces.services.auth_service import AuthService
from application.interfaces.services.notification_service import NotificationService
from domain.entities.user import User
from domain.exceptions.domain_exceptions import ValidationException
from domain.value_objects.status import UserRole, NotificationType


class RegisterUseCase:
    """Use case for user registration"""

    def __init__(
        self,
        user_repository: UserRepository,
        auth_service: AuthService,
        notification_service: Optional[NotificationService] = None
    ):
        self.user_repository = user_repository
        self.auth_service = auth_service
        self.notification_service = notification_service

    def execute(self, dto: UserCreateDTO) -> UserResponseDTO:
        """
        Register a new user
        
        Args:
            dto: User creation data
            
        Returns:
            UserResponseDTO with created user data
            
        Raises:
            ValidationException: If validation fails
        """
        # Check if email already exists
        existing_user = self.user_repository.get_by_email(dto.email)
        if existing_user:
            raise ValidationException("Email is already registered")

        # Check if student ID already exists (for students)
        if dto.role == UserRole.STUDENT and dto.student_id:
            existing_student = self.user_repository.get_by_student_id(
                dto.student_id)
            if existing_student:
                raise ValidationException("Student ID is already registered")

        # Hash password
        password_hash = self.auth_service.hash_password(dto.password)

        # Create user entity
        user = User(
            email=dto.email,
            first_name=dto.first_name,
            last_name=dto.last_name,
            role=dto.role,
            password_hash=password_hash,
            department=dto.department,
            student_id=dto.student_id
        )

        # Save user
        created_user = self.user_repository.create(user)

        # Send welcome notification if notification service is available
        if self.notification_service:
            self.notification_service.send_notification(
                user_id=created_user.id,
                notification_type=NotificationType.NEW_SUBMISSION,
                data={
                    "message": f"Welcome to the Thesis Management System, {created_user.first_name}!"
                },
                send_email=True
            )

        # Return response
        return UserResponseDTO.from_entity(created_user)
