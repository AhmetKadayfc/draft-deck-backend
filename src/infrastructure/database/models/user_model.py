import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.mysql import CHAR

from src.infrastructure.database.connection import Base
from src.domain.value_objects.status import UserRole


class UserModel(Base):
    """SQLAlchemy model for users"""
    __tablename__ = "users"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole.STUDENT.value, UserRole.ADVISOR.value, UserRole.ADMIN.value),
                  nullable=False, default=UserRole.STUDENT.value)
    department = Column(String(100), nullable=True)
    student_id = Column(String(50), unique=True, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    def to_entity(self):
        """Convert model to domain entity"""
        from src.domain.entities.user import User

        return User(
            id=uuid.UUID(self.id),
            email=self.email,
            first_name=self.first_name,
            last_name=self.last_name,
            role=UserRole(self.role),
            password_hash=self.password_hash,
            department=self.department,
            student_id=self.student_id,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

    @classmethod
    def from_entity(cls, user):
        """Create model from domain entity"""
        return cls(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            password_hash=user.password_hash,
            department=user.department,
            student_id=user.student_id,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
