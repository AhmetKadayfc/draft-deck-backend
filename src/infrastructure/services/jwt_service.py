import os
import jwt
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from uuid import UUID
import json

from src.application.interfaces.services.auth_service import AuthService
from src.application.interfaces.repositories.user_repository import UserRepository
from src.domain.entities.user import User


class JwtService(AuthService):
    """JWT implementation of the authentication service"""

    def __init__(self, user_repository: UserRepository, password_hash_service):
        self.user_repository = user_repository
        self.password_hash_service = password_hash_service
        self.secret_key = os.getenv(
            "JWT_SECRET_KEY", "default-secret-key-change-me")
        self.access_token_expires = int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))  # 1 hour
        self.refresh_token_expires = int(
            os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))  # 30 days
        self.algorithm = "HS256"
        self.blacklisted_tokens = set()  # In production, use Redis or database

    def hash_password(self, password: str) -> str:
        """Hash a password using passlib"""
        return self.password_hash_service.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return self.password_hash_service.verify(password, password_hash)

    def create_access_token(self, user_id: UUID, additional_claims: Optional[Dict] = None) -> str:
        """Create a JWT access token"""
        return self._create_token(
            user_id=user_id,
            token_type="access",
            expires_delta=timedelta(seconds=self.access_token_expires),
            additional_claims=additional_claims
        )

    def create_refresh_token(self, user_id: UUID) -> str:
        """Create a JWT refresh token"""
        return self._create_token(
            user_id=user_id,
            token_type="refresh",
            expires_delta=timedelta(seconds=self.refresh_token_expires)
        )

    def _create_token(self, user_id: UUID, token_type: str, expires_delta: timedelta,
                      additional_claims: Optional[Dict] = None) -> str:
        """Helper to create JWT tokens"""
        now = datetime.utcnow()

        payload = {
            "sub": str(user_id),
            "type": token_type,
            "iat": now,
            "exp": now + expires_delta
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Tuple[bool, Dict]:
        """Verify a JWT token and return claims if valid"""
        try:
            if token in self.blacklisted_tokens:
                return False, {"error": "Token has been revoked"}

            payload = jwt.decode(token, self.secret_key,
                                 algorithms=[self.algorithm])

            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
                return False, {"error": "Token has expired"}

            return True, payload

        except jwt.PyJWTError as e:
            return False, {"error": str(e)}

    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from a token"""
        is_valid, payload = self.verify_token(token)

        if not is_valid:
            return None

        user_id = UUID(payload["sub"])
        return self.user_repository.get_by_id(user_id)

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create a new access token from a refresh token"""
        is_valid, payload = self.verify_token(refresh_token)

        if not is_valid:
            return None

        # Check token type
        if payload.get("type") != "refresh":
            return None

        # Refresh token valid, create new access token
        user_id = UUID(payload["sub"])

        # Get additional claims from user (role, email)
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return None

        additional_claims = {
            "role": user.role.value,
            "email": user.email
        }

        return self.create_access_token(user_id, additional_claims=additional_claims)

    def revoke_token(self, token: str) -> bool:
        """Revoke a token (add to blacklist)"""
        is_valid, payload = self.verify_token(token)

        if not is_valid:
            return False

        # Add to blacklist
        self.blacklisted_tokens.add(token)
        return True

    def generate_password_reset_token(self, user_email: str) -> Optional[str]:
        """Generate a password reset code and store in user record"""
        user = self.user_repository.get_by_email(user_email)

        if not user:
            return None
            
        # Generate a 5-digit reset code
        reset_code = self._generate_reset_code()
        
        # Store the reset code in the user record
        user.set_password_reset_code(reset_code, 24)  # 24 hour expiry
        
        # Update the user in the repository
        self.user_repository.update(user)

        return reset_code
        
    def _generate_reset_code(self, length: int = 5) -> str:
        """Generate a random numeric reset code"""
        return ''.join(random.choices(string.digits, k=length))

    def verify_password_reset_token(self, email: str, reset_code: str) -> bool:
        """Verify a password reset code for the specified email"""
        user = self.user_repository.get_by_email(email)

        if not user:
            return False

        # Verify the reset code
        return user.verify_password_reset_code(reset_code)
