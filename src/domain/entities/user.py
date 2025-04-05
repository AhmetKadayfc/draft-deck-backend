from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from ..value_objects.status import UserRole
from ..exceptions.domain_exceptions import ValidationException


@dataclass
class User:
    """User entity for the thesis management system"""
    email: str
    first_name: str
    last_name: str
    role: UserRole
    id: UUID = field(default_factory=uuid4)
    password_hash: Optional[str] = None
    department: Optional[str] = None
    student_id: Optional[str] = None
    is_active: bool = True
    email_verified: bool = False
    verification_code: Optional[str] = None
    verification_code_expiry: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate user data"""
        if not self.email:
            raise ValidationException("Email is required")

        if not self.first_name:
            raise ValidationException("First name is required")

        if not self.last_name:
            raise ValidationException("Last name is required")

        if self.role not in [UserRole.STUDENT, UserRole.ADVISOR, UserRole.ADMIN]:
            raise ValidationException("Invalid user role")

        if self.role == UserRole.STUDENT and not self.student_id:
            raise ValidationException(
                "Student ID is required for student users")

    def update(self,
               first_name: Optional[str] = None,
               last_name: Optional[str] = None,
               department: Optional[str] = None,
               student_id: Optional[str] = None):
        """Update user properties"""
        if first_name:
            self.first_name = first_name

        if last_name:
            self.last_name = last_name

        if department:
            self.department = department

        if student_id and self.role == UserRole.STUDENT:
            self.student_id = student_id

        self.updated_at = datetime.utcnow()
        self._validate()

    def deactivate(self):
        """Deactivate user account"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self):
        """Activate user account"""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"

    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role"""
        return self.role == role

    def verify_email(self, code: str) -> bool:
        """Verify email with provided verification code"""
        if not self.verification_code or not self.verification_code_expiry:
            return False
        
        # Check if code is valid and not expired
        if (self.verification_code == code and 
            self.verification_code_expiry > datetime.utcnow()):
            self.email_verified = True
            self.verification_code = None
            self.verification_code_expiry = None
            self.updated_at = datetime.utcnow()
            return True
        
        return False
        
    def set_verification_code(self, code: str, expiry_hours: int = 24):
        """Set a new verification code with expiry"""
        self.verification_code = code
        self.verification_code_expiry = datetime.utcnow().replace(microsecond=0) + timedelta(hours=expiry_hours)
        self.email_verified = False
        self.updated_at = datetime.utcnow()
