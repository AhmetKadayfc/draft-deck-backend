from typing import List, Optional
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from application.interfaces.repositories.user_repository import UserRepository
from domain.entities.user import User
from domain.value_objects.status import UserRole
from infrastructure.database.models.user_model import UserModel
from domain.exceptions.domain_exceptions import EntityNotFoundException, ValidationException


class UserRepositoryImpl(UserRepository):
    """SQLAlchemy implementation of UserRepository"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, user: User) -> User:
        """Create a new user"""
        try:
            user_model = UserModel.from_entity(user)
            self.session.add(user_model)
            self.session.commit()

            # Refresh to get any database-generated values
            self.session.refresh(user_model)

            return user_model.to_entity()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValidationException(f"Failed to create user: {str(e)}")

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID"""
        user_model = self.session.query(UserModel).filter(
            UserModel.id == str(user_id)).first()

        if not user_model:
            return None

        return user_model.to_entity()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        user_model = self.session.query(UserModel).filter(
            UserModel.email == email).first()

        if not user_model:
            return None

        return user_model.to_entity()

    def get_by_student_id(self, student_id: str) -> Optional[User]:
        """Get a user by student ID"""
        user_model = self.session.query(UserModel).filter(
            UserModel.student_id == student_id).first()

        if not user_model:
            return None

        return user_model.to_entity()

    def update(self, user: User) -> User:
        """Update a user"""
        user_model = self.session.query(UserModel).filter(
            UserModel.id == str(user.id)).first()

        if not user_model:
            raise EntityNotFoundException("User", user.id)

        try:
            # Update all fields from entity
            user_model.email = user.email
            user_model.first_name = user.first_name
            user_model.last_name = user.last_name
            user_model.role = user.role.value
            user_model.department = user.department
            user_model.student_id = user.student_id
            user_model.is_active = user.is_active
            # Don't update password_hash unless it changed
            if user.password_hash and user.password_hash != user_model.password_hash:
                user_model.password_hash = user.password_hash

            self.session.commit()
            self.session.refresh(user_model)

            return user_model.to_entity()
        except SQLAlchemyError as e:
            self.session.rollback()
            raise ValidationException(f"Failed to update user: {str(e)}")

    def delete(self, user_id: UUID) -> bool:
        """Delete a user"""
        user_model = self.session.query(UserModel).filter(
            UserModel.id == str(user_id)).first()

        if not user_model:
            return False

        try:
            self.session.delete(user_model)
            self.session.commit()
            return True
        except SQLAlchemyError:
            self.session.rollback()
            return False

    def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        user_models = self.session.query(
            UserModel).limit(limit).offset(offset).all()

        return [model.to_entity() for model in user_models]

    def get_by_role(self, role: UserRole, limit: int = 100, offset: int = 0) -> List[User]:
        """Get users by role with pagination"""
        user_models = self.session.query(UserModel).filter(
            UserModel.role == role.value
        ).limit(limit).offset(offset).all()

        return [model.to_entity() for model in user_models]

    def get_advisors_by_department(self, department: str) -> List[User]:
        """Get all advisors in a department"""
        user_models = self.session.query(UserModel).filter(
            UserModel.role == UserRole.ADVISOR.value,
            UserModel.department == department,
            UserModel.is_active == True
        ).all()

        return [model.to_entity() for model in user_models]
