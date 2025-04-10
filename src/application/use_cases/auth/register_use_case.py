from typing import Optional
import random
import string

from src.application.dtos.user_dto import UserCreateDTO, UserResponseDTO
from src.application.interfaces.repositories.user_repository import UserRepository
from src.application.interfaces.services.auth_service import AuthService
from src.application.interfaces.services.notification_service import NotificationService
from src.domain.entities.user import User
from src.domain.exceptions.domain_exceptions import ValidationException
from src.domain.value_objects.status import UserRole, NotificationType


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

    def _generate_verification_code(self, length: int = 5) -> str:
        """Generate a random numeric verification code"""
        return ''.join(random.choices(string.digits, k=length))

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

        # Generate verification code
        verification_code = self._generate_verification_code()

        # Create user entity
        user = User(
            email=dto.email,
            first_name=dto.first_name,
            last_name=dto.last_name,
            role=dto.role,
            password_hash=password_hash,
            department=dto.department,
            student_id=dto.student_id,
            email_verified=False
        )
        
        # Set the verification code with 24-hour expiry
        user.set_verification_code(verification_code, 24)

        # Save user
        created_user = self.user_repository.create(user)

        # Send email verification notification if notification service is available
        if self.notification_service:
            self.notification_service.send_notification(
                user_id=created_user.id,
                notification_type=NotificationType.EMAIL_VERIFICATION,
                data={
                    "name": f"{created_user.first_name}",
                    "verification_code": verification_code
                },
                send_email=True
            )

        # Return response
        return UserResponseDTO.from_entity(created_user)
