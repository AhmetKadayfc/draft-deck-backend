from typing import Optional, Tuple
from uuid import UUID

from src.application.dtos.user_dto import UserResponseDTO
from src.application.interfaces.repositories.user_repository import UserRepository
from src.domain.exceptions.domain_exceptions import ValidationException


class VerifyEmailUseCase:
    """Use case for verifying user email"""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def execute(self, email: str, verification_code: str) -> Tuple[bool, Optional[UserResponseDTO]]:
        """
        Verify a user's email using verification code
        
        Args:
            email: Email address to verify
            verification_code: Verification code sent to the user
            
        Returns:
            Tuple with verification result and user data (if successful)
            
        Raises:
            ValidationException: If validation fails
        """
        # Get user by email
        user = self.user_repository.get_by_email(email)
        
        if not user:
            raise ValidationException("Email not found")
        
        # Check if email is already verified
        if user.email_verified:
            return True, UserResponseDTO.from_entity(user)
        
        # Verify email with the provided code
        if user.verify_email(verification_code):
            # Update user in repository
            updated_user = self.user_repository.update(user)
            return True, UserResponseDTO.from_entity(updated_user)
        
        return False, None 