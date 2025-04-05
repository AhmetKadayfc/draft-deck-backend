import random
import string
from typing import Optional

from src.application.interfaces.repositories.user_repository import UserRepository
from src.application.interfaces.services.notification_service import NotificationService
from src.domain.exceptions.domain_exceptions import ValidationException
from src.domain.value_objects.status import NotificationType


class ResendVerificationUseCase:
    """Use case for resending email verification code"""

    def __init__(
        self, 
        user_repository: UserRepository,
        notification_service: Optional[NotificationService] = None
    ):
        self.user_repository = user_repository
        self.notification_service = notification_service

    def _generate_verification_code(self, length: int = 5) -> str:
        """Generate a random numeric verification code"""
        return ''.join(random.choices(string.digits, k=length))

    def execute(self, email: str) -> bool:
        """
        Resend verification code to user's email
        
        Args:
            email: Email address to send verification code
            
        Returns:
            Boolean indicating success of operation
            
        Raises:
            ValidationException: If validation fails
        """
        # Get user by email
        user = self.user_repository.get_by_email(email)
        
        if not user:
            # For security reasons, don't reveal if email doesn't exist
            return True
        
        # Check if email is already verified
        if user.email_verified:
            return True
        
        # Generate new verification code
        verification_code = self._generate_verification_code()
        
        # Set the verification code with 24-hour expiry
        user.set_verification_code(verification_code, 24)
        
        # Update user in repository
        self.user_repository.update(user)
        
        # Send email verification notification if notification service is available
        if self.notification_service:
            self.notification_service.send_notification(
                user_id=user.id,
                notification_type=NotificationType.EMAIL_VERIFICATION,
                data={
                    "name": f"{user.first_name}",
                    "verification_code": verification_code
                },
                send_email=True
            )
        
        return True 