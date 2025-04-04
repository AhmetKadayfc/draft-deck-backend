from functools import wraps
from flask import request, jsonify, g
from typing import List, Union, Callable

from src.domain.value_objects.status import UserRole


def require_role(allowed_roles: Union[UserRole, List[UserRole]]):
    """
    Middleware for role-based access control
    
    Args:
        allowed_roles: Single role or list of roles allowed to access the route
    """
    if not isinstance(allowed_roles, list):
        allowed_roles = [allowed_roles]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if user is in Flask's g object (set by auth middleware)
            if not hasattr(g, 'user'):
                return jsonify({
                    "error": "Authentication required",
                    "message": "You must be logged in to access this resource"
                }), 401

            # Check if user has an allowed role
            if g.user.role not in allowed_roles:
                return jsonify({
                    "error": "Permission denied",
                    "message": "You do not have permission to access this resource"
                }), 403

            # Continue to the route
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_student():
    """Middleware requiring student role"""
    return require_role(UserRole.STUDENT)


def require_advisor():
    """Middleware requiring advisor role"""
    return require_role(UserRole.ADVISOR)


def require_admin():
    """Middleware requiring admin role"""
    return require_role(UserRole.ADMIN)


def require_student_or_advisor():
    """Middleware requiring student or advisor role"""
    return require_role([UserRole.STUDENT, UserRole.ADVISOR])


def require_advisor_or_admin():
    """Middleware requiring advisor or admin role"""
    return require_role([UserRole.ADVISOR, UserRole.ADMIN])


def is_resource_owner(resource_owner_id: str):
    """
    Middleware to check if user is the owner of a resource
    
    Args:
        resource_owner_id: Function that extracts owner ID from request
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if user is in Flask's g object (set by auth middleware)
            if not hasattr(g, 'user'):
                return jsonify({
                    "error": "Authentication required",
                    "message": "You must be logged in to access this resource"
                }), 401

            # Get owner ID using the provided function
            owner_id = resource_owner_id(request, kwargs)

            # Check if user is the owner
            if str(g.user.id) != str(owner_id):
                # If not owner, check if admin (admins can access any resource)
                if g.user.role != UserRole.ADMIN:
                    return jsonify({
                        "error": "Permission denied",
                        "message": "You do not have permission to access this resource"
                    }), 403

            # Continue to the route
            return func(*args, **kwargs)

        return wrapper

    return decorator


def thesis_owner_or_advisor(thesis_repository):
    """
    Middleware to check if user is the thesis owner or assigned advisor
    
    Args:
        thesis_repository: Repository for accessing thesis data
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if user is in Flask's g object (set by auth middleware)
            if not hasattr(g, 'user'):
                return jsonify({
                    "error": "Authentication required",
                    "message": "You must be logged in to access this resource"
                }), 401

            # Get thesis ID from route parameters
            thesis_id = kwargs.get('thesis_id')

            if not thesis_id:
                return jsonify({
                    "error": "Invalid request",
                    "message": "Thesis ID is required"
                }), 400

            # Get thesis
            thesis = thesis_repository.get_by_id(thesis_id)

            if not thesis:
                return jsonify({
                    "error": "Not found",
                    "message": "Thesis not found"
                }), 404

            # Check if user is student owner, assigned advisor, or admin
            is_owner = str(g.user.id) == str(thesis.student_id)
            is_advisor = thesis.advisor_id and str(
                g.user.id) == str(thesis.advisor_id)
            is_admin = g.user.role == UserRole.ADMIN

            if not (is_owner or is_advisor or is_admin):
                return jsonify({
                    "error": "Permission denied",
                    "message": "You do not have permission to access this thesis"
                }), 403

            # Store thesis in Flask's g object for use in the route
            g.thesis = thesis

            # Continue to the route
            return func(*args, **kwargs)
        return wrapper

    return decorator
