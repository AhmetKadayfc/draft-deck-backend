from typing import Optional

from application.dtos.user_dto import LoginDTO, TokenResponseDTO, UserResponseDTO
from application.interfaces.repositories.user_repository import UserRepository
from application.interfaces.services.auth_service import AuthService
from domain.exceptions.domain_exceptions import ValidationException


class LoginUseCase:
    """Use case for user authentication"""

    def __init__(self, user_repository: UserRepository, auth_service: AuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service

    def execute(self, dto: LoginDTO) -> Optional[TokenResponseDTO]:
        """
        Authenticate a user and return tokens
        
        Args:
            dto: Login credentials
            
        Returns:
            TokenResponseDTO with access and refresh tokens if successful
            
        Raises:
            ValidationException: If credentials are invalid
        """
        # Validate input
        if not dto.email or not dto.password:
            raise ValidationException("Email and password are required")

        # Get user by email
        user = self.user_repository.get_by_email(dto.email)

        # Check if user exists and is active
        if not user:
            raise ValidationException("Invalid email or password")

        if not user.is_active:
            raise ValidationException("Account is inactive")

        # Verify password
        if not self.auth_service.verify_password(dto.password, user.password_hash):
            raise ValidationException("Invalid email or password")

        # Generate tokens
        additional_claims = {
            "role": user.role.value,
            "email": user.email
        }

        access_token = self.auth_service.create_access_token(
            user.id, additional_claims=additional_claims
        )
        refresh_token = self.auth_service.create_refresh_token(user.id)

        # Create response
        user_dto = UserResponseDTO.from_entity(user)

        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_dto
        )
