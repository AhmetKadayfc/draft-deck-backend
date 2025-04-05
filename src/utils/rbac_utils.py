from typing import Dict, List, Set, Optional, Callable
from functools import wraps
from flask import request, g, jsonify

from src.domain.value_objects.status import UserRole


# Define permissions as a set of actions
PERMISSIONS = {
    # Student permissions
    UserRole.STUDENT.value: {
        "thesis:create",
        "thesis:read_own",
        "thesis:update_own",
        "thesis:submit_own",
        "thesis:delete_own",
        "thesis:download_own",
        "feedback:read_own",
        "profile:read_own",
        "profile:update_own",
    },

    # Advisor permissions
    UserRole.ADVISOR.value: {
        "thesis:read_assigned",
        "thesis:read_department",
        "thesis:assign_self",
        "thesis:update_status",
        "thesis:download_assigned",
        "feedback:create",
        "feedback:read_own",
        "feedback:update_own",
        "feedback:delete_own",
        "profile:read_own",
        "profile:update_own",
    },

    # Admin permissions (has all permissions)
    UserRole.ADMIN.value: {
        "thesis:create",
        "thesis:read_any",
        "thesis:update_any",
        "thesis:delete_any",
        "thesis:submit_any",
        "thesis:download_any",
        "thesis:assign_any",
        "thesis:update_status",
        "feedback:create",
        "feedback:read_any",
        "feedback:update_any",
        "feedback:delete_any",
        "user:create",
        "user:read_any",
        "user:update_any",
        "user:delete_any",
        "profile:read_any",
        "profile:update_any",
    }
}


def has_permission(permission: str) -> bool:
    """
    Check if the current user has a specific permission
    
    Args:
        permission: Permission to check
        
    Returns:
        True if user has permission, False otherwise
    """
    # Check if user is authenticated
    if not hasattr(g, 'user'):
        return False

    # Get user role
    role = g.user.role.value

    # Check if user has the permission
    return permission in PERMISSIONS.get(role, set())


def require_permission(permission: str, get_resource_id: Optional[Callable] = None):
    """
    Decorator to check if user has a specific permission
    
    Args:
        permission: Permission to check
        get_resource_id: Optional function to get resource ID for ownership checks
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                return jsonify({
                    "error": "Authentication required",
                    "message": "You must be logged in to access this resource"
                }), 401

            # Get user role
            role = g.user.role.value

            # Admin always has access
            if role == UserRole.ADMIN.value:
                return func(*args, **kwargs)

            # Check permission based on role
            if permission not in PERMISSIONS.get(role, set()):
                return jsonify({
                    "error": "Permission denied",
                    "message": "You do not have permission to access this resource"
                }), 403

            # If permission is for "own" resources, check ownership
            if permission.endswith("_own") and get_resource_id:
                resource_id = get_resource_id(request, kwargs)
                if str(g.user.id) != str(resource_id):
                    return jsonify({
                        "error": "Permission denied",
                        "message": "You can only access your own resources"
                    }), 403

            # If permission is for "assigned" resources, check assignment
            if permission.endswith("_assigned") and get_resource_id and hasattr(g, 'thesis'):
                if not g.thesis.advisor_id or str(g.user.id) != str(g.thesis.advisor_id):
                    return jsonify({
                        "error": "Permission denied",
                        "message": "You can only access theses assigned to you"
                    }), 403

            # Permission granted, proceed to the route
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_user_permissions(role: UserRole) -> List[str]:
    """
    Get a list of permissions for a specific role
    
    Args:
        role: User role
        
    Returns:
        List of permissions
    """
    return list(PERMISSIONS.get(role.value, set()))
