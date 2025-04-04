from flask import Blueprint, request, jsonify, g
from flask_cors import cross_origin
from marshmallow import ValidationError

from application.use_cases.auth.login_use_case import LoginUseCase
from application.use_cases.auth.register_use_case import RegisterUseCase
from application.dtos.user_dto import LoginDTO, UserCreateDTO
from api.middleware.auth_middleware import authenticate, refresh_auth
from domain.exceptions.domain_exceptions import ValidationException
from api.schemas.request.auth_schemas import (
    LoginSchema, RegisterSchema, PasswordResetRequestSchema, PasswordResetSchema
)


def create_auth_routes(
    login_use_case: LoginUseCase,
    register_use_case: RegisterUseCase,
    auth_service
):
    """Factory function to create authentication routes"""
    auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

    @auth_bp.route("/register", methods=["POST"])
    @cross_origin()
    def register():
        """Register a new user"""
        # Validate request data
        try:
            # Parse and validate input using schema
            schema = RegisterSchema()
            data = schema.load(request.json)

            # Create DTO
            user_dto = UserCreateDTO(
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                password=data["password"],
                role=data["role"],
                department=data.get("department"),
                student_id=data.get("student_id")
            )

            # Execute use case
            result = register_use_case.execute(user_dto)

            # Return response
            return jsonify({
                "message": "User registered successfully",
                "user": {
                    "id": str(result.id),
                    "email": result.email,
                    "first_name": result.first_name,
                    "last_name": result.last_name,
                    "role": result.role
                }
            }), 201

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except ValidationException as e:
            return jsonify({"error": "Validation error", "message": str(e)}), 400

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @auth_bp.route("/login", methods=["POST"])
    @cross_origin()
    def login():
        """Login a user"""
        # Validate request data
        try:
            # Parse and validate input using schema
            schema = LoginSchema()
            data = schema.load(request.json)

            # Create DTO
            login_dto = LoginDTO(
                email=data["email"],
                password=data["password"]
            )

            # Execute use case
            result = login_use_case.execute(login_dto)

            if not result:
                return jsonify({
                    "error": "Authentication failed",
                    "message": "Invalid email or password"
                }), 401

            # Return response
            return jsonify({
                "access_token": result.access_token,
                "refresh_token": result.refresh_token,
                "token_type": result.token_type,
                "expires_in": result.expires_in,
                "user": {
                    "id": str(result.user.id),
                    "email": result.user.email,
                    "first_name": result.user.first_name,
                    "last_name": result.user.last_name,
                    "role": result.user.role
                }
            }), 200

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except ValidationException as e:
            return jsonify({"error": "Authentication failed", "message": str(e)}), 401

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @auth_bp.route("/refresh", methods=["POST"])
    @cross_origin()
    @refresh_auth(auth_service)
    def refresh_token():
        """Refresh access token using refresh token"""
        try:
            # Get refresh token from g object (set by middleware)
            refresh_token = g.refresh_token

            # Generate new access token
            new_access_token = auth_service.refresh_access_token(refresh_token)

            if not new_access_token:
                return jsonify({
                    "error": "Invalid refresh token",
                    "message": "Could not refresh access token"
                }), 401

            # Return response
            return jsonify({
                "access_token": new_access_token,
                "token_type": "bearer"
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @auth_bp.route("/logout", methods=["POST"])
    @cross_origin()
    @authenticate(auth_service)
    def logout():
        """Logout a user by revoking their token"""
        try:
            # Get token from g object (set by middleware)
            token = g.token

            # Revoke token
            auth_service.revoke_token(token)

            # Return response
            return jsonify({
                "message": "Logged out successfully"
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @auth_bp.route("/password-reset/request", methods=["POST"])
    @cross_origin()
    def request_password_reset():
        """Request password reset"""
        try:
            # Parse and validate input using schema
            schema = PasswordResetRequestSchema()
            data = schema.load(request.json)

            # Generate reset token
            reset_token = auth_service.generate_password_reset_token(
                data["email"])

            # Even if email doesn't exist, return success to prevent user enumeration
            return jsonify({
                "message": "If the email exists, a password reset link has been sent"
            }), 200

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @auth_bp.route("/password-reset/confirm", methods=["POST"])
    @cross_origin()
    def confirm_password_reset():
        """Confirm password reset"""
        try:
            # Parse and validate input using schema
            schema = PasswordResetSchema()
            data = schema.load(request.json)

            # Verify reset token
            email = auth_service.verify_password_reset_token(data["token"])

            if not email:
                return jsonify({
                    "error": "Invalid token",
                    "message": "Password reset token is invalid or expired"
                }), 400

            # Get user by email
            user = auth_service.user_repository.get_by_email(email)

            if not user:
                return jsonify({
                    "error": "User not found",
                    "message": "User does not exist"
                }), 404

            # Update password
            user.password_hash = auth_service.hash_password(
                data["new_password"])
            auth_service.user_repository.update(user)

            # Return response
            return jsonify({
                "message": "Password has been reset successfully"
            }), 200

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @auth_bp.route("/me", methods=["GET"])
    @cross_origin()
    @authenticate(auth_service)
    def get_current_user():
        """Get current user profile"""
        try:
            # Get user from g object (set by middleware)
            user = g.user

            # Return response
            return jsonify({
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "department": user.department,
                "student_id": user.student_id,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    return auth_bp
