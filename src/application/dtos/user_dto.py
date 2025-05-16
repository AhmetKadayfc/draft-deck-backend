from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from src.domain.value_objects.status import UserRole


@dataclass
class UserCreateDTO:
    """DTO for user creation"""
    email: str
    first_name: str
    last_name: str
    password: str
    role: UserRole
    department: Optional[str] = None
    student_id: Optional[str] = None


@dataclass
class UserUpdateDTO:
    """DTO for user update"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    student_id: Optional[str] = None


@dataclass
class UserResponseDTO:
    """DTO for user response"""
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    department: Optional[str] = None
    student_id: Optional[str] = None
    is_active: bool = True
    email_verified: bool = False
    created_at: datetime = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_entity(cls, user):
        """Create DTO from User entity"""
        return cls(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            department=user.department,
            student_id=user.student_id,
            is_active=user.is_active,
            email_verified=user.email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )


@dataclass
class LoginDTO:
    """DTO for login credentials"""
    email: str
    password: str


@dataclass
class TokenResponseDTO:
    """DTO for authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 14400  # 1 hour by default
    user: Optional[UserResponseDTO] = None


@dataclass
class PasswordResetRequestDTO:
    """DTO for password reset request"""
    email: str


@dataclass
class PasswordResetDTO:
    """DTO for password reset"""
    token: str
    new_password: str
