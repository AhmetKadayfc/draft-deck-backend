from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
from uuid import UUID

from domain.entities.user import User


class AuthService(ABC):
    """Interface for authentication service operations"""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        pass

    @abstractmethod
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        pass

    @abstractmethod
    def create_access_token(self, user_id: UUID, additional_claims: Optional[Dict] = None) -> str:
        """Create a JWT access token"""
        pass

    @abstractmethod
    def create_refresh_token(self, user_id: UUID) -> str:
        """Create a JWT refresh token"""
        pass

    @abstractmethod
    def verify_token(self, token: str) -> Tuple[bool, Dict]:
        """Verify a JWT token and return claims if valid"""
        pass

    @abstractmethod
    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from a token"""
        pass

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create a new access token from a refresh token"""
        pass

    @abstractmethod
    def revoke_token(self, token: str) -> bool:
        """Revoke a token (add to blacklist)"""
        pass

    @abstractmethod
    def generate_password_reset_token(self, user_email: str) -> Optional[str]:
        """Generate a password reset token"""
        pass

    @abstractmethod
    def verify_password_reset_token(self, token: str) -> Optional[str]:
        """Verify a password reset token and return the associated email"""
        pass
