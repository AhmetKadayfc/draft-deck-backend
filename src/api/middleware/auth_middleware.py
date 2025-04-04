from functools import wraps
from flask import request, jsonify, g
import os

from application.interfaces.services.auth_service import AuthService


def get_token_from_header():
    """Extract bearer token from the Authorization header"""
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    parts = auth_header.split()

    if parts[0].lower() != "bearer" or len(parts) != 2:
        return None

    return parts[1]


def authenticate(auth_service: AuthService):
    """Middleware for authenticating requests"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get token from header
            token = get_token_from_header()

            if not token:
                return jsonify({
                    "error": "Authentication required",
                    "message": "Please provide a valid authorization token"
                }), 401

            # Verify token
            is_valid, payload = auth_service.verify_token(token)

            if not is_valid:
                return jsonify({
                    "error": "Invalid authentication token",
                    "message": payload.get("error", "Token validation failed")
                }), 401

            # Get user from token
            user = auth_service.get_user_from_token(token)

            if not user:
                return jsonify({
                    "error": "Invalid user",
                    "message": "User not found or inactive"
                }), 401

            if not user.is_active:
                return jsonify({
                    "error": "Account inactive",
                    "message": "Your account is inactive"
                }), 403

            # Store user in Flask's g object for use in the route
            g.user = user
            g.token = token

            # Continue to the route
            return func(*args, **kwargs)

        return wrapper

    return decorator


def optional_auth(auth_service: AuthService):
    """
    Middleware for optional authentication
    Attempts to authenticate but continues even if authentication fails
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get token from header
            token = get_token_from_header()

            if token:
                # Verify token
                is_valid, payload = auth_service.verify_token(token)

                if is_valid:
                    # Get user from token
                    user = auth_service.get_user_from_token(token)

                    if user and user.is_active:
                        # Store user in Flask's g object
                        g.user = user
                        g.token = token

            # Continue to the route
            return func(*args, **kwargs)

        return wrapper

    return decorator


def refresh_auth(auth_service: AuthService):
    """Middleware for handling refresh token requests"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get token from header
            token = get_token_from_header()

            if not token:
                return jsonify({
                    "error": "Authentication required",
                    "message": "Please provide a valid refresh token"
                }), 401

            # Verify token
            is_valid, payload = auth_service.verify_token(token)

            if not is_valid:
                return jsonify({
                    "error": "Invalid refresh token",
                    "message": payload.get("error", "Token validation failed")
                }), 401

            # Check token type
            if payload.get("type") != "refresh":
                return jsonify({
                    "error": "Invalid token type",
                    "message": "Expected refresh token"
                }), 401

            # Store token in Flask's g object
            g.refresh_token = token

            # Continue to the route
            return func(*args, **kwargs)

        return wrapper

    return decorator
