from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.user import User
from src.domain.value_objects.status import UserRole


class UserRepository(ABC):
    """Interface for user repository operations"""

    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user"""
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID"""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        pass

    @abstractmethod
    def get_by_student_id(self, student_id: str) -> Optional[User]:
        """Get a user by student ID"""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Update a user"""
        pass

    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        """Delete a user"""
        pass

    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        pass

    @abstractmethod
    def get_by_role(self, role: UserRole, limit: int = 100, offset: int = 0) -> List[User]:
        """Get users by role with pagination"""
        pass

    @abstractmethod
    def get_advisors_by_department(self, department: str) -> List[User]:
        """Get all advisors in a department"""
        pass
