from flask import Blueprint, request, jsonify, g
from flask_cors import cross_origin
from marshmallow import ValidationError

from src.application.use_cases.auth.login_use_case import LoginUseCase
from src.application.use_cases.auth.register_use_case import RegisterUseCase
from src.application.use_cases.auth.verify_email_use_case import VerifyEmailUseCase
from src.application.use_cases.auth.resend_verification_use_case import ResendVerificationUseCase
from src.application.dtos.user_dto import LoginDTO, UserCreateDTO
from src.api.middleware.auth_middleware import authenticate, refresh_auth
from src.domain.exceptions.domain_exceptions import ValidationException
from src.domain.value_objects.status import NotificationType, UserRole
from src.api.schemas.request.auth_schemas import (
    LoginSchema, RegisterSchema, PasswordResetRequestSchema, PasswordResetConfirmSchema,
    PasswordResetCompleteSchema, EmailVerificationSchema
)


def create_auth_routes(
    login_use_case: LoginUseCase,
    register_use_case: RegisterUseCase,
    auth_service,
    verify_email_use_case: VerifyEmailUseCase = None,
    resend_verification_use_case: ResendVerificationUseCase = None
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

            # Convert role string to UserRole enum
            role_str = data["role"].lower()
            try:
                # Try direct conversion
                role = UserRole(role_str)
            except ValueError:
                # Fallback to manual mapping for case variations or custom handling
                if role_str == "student":
                    role = UserRole.STUDENT
                elif role_str == "advisor":
                    role = UserRole.ADVISOR
                elif role_str == "admin":
                    role = UserRole.ADMIN
                else:
                    raise ValidationException(f"Invalid role: {role_str}")

            # Create DTO
            user_dto = UserCreateDTO(
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                password=data["password"],
                role=role,
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
                
            # Check if email is verified
            if not result.user.email_verified:
                return jsonify({
                    "error": "Email not verified",
                    "message": "Please verify your email before logging in",
                    "user_id": str(result.user.id),
                    "email": result.user.email
                }), 403

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

            # Generate reset code
            reset_code = auth_service.generate_password_reset_token(data["email"])
            
            # If email exists and code was generated, send email with reset code
            if reset_code and auth_service.user_repository.get_by_email(data["email"]):
                user = auth_service.user_repository.get_by_email(data["email"])
                
                # Send email with reset code if notification service is available
                if hasattr(register_use_case, 'notification_service') and register_use_case.notification_service:
                    register_use_case.notification_service.send_notification(
                        user_id=user.id,
                        notification_type=NotificationType.PASSWORD_RESET,
                        data={
                            "name": f"{user.first_name}",
                            "reset_code": reset_code
                        },
                        send_email=True
                    )

            # Even if email doesn't exist, return success to prevent user enumeration
            return jsonify({
                "message": "If the email exists, a password reset code has been sent"
            }), 200

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @auth_bp.route("/password-reset/confirm", methods=["POST"])
    @cross_origin()
    def confirm_password_reset():
        """Confirm password reset code"""
        try:
            # Parse and validate input using schema
            schema = PasswordResetConfirmSchema()
            data = schema.load(request.json)

            # Get user by email
            user = auth_service.user_repository.get_by_email(data["email"])

            if not user:
                return jsonify({
                    "error": "Invalid email",
                    "message": "Email not found"
                }), 404

            # Verify reset code
            if not auth_service.verify_password_reset_token(data["email"], data["code"]):
                return jsonify({
                    "error": "Invalid reset code",
                    "message": "Password reset code is invalid or expired"
                }), 400

            # Return success
            return jsonify({
                "message": "Reset code verified successfully",
                "email": data["email"]
            }), 200

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500
            
    @auth_bp.route("/password-reset/complete", methods=["POST"])
    @cross_origin()
    def complete_password_reset():
        """Complete password reset with new password"""
        try:
            # Parse and validate input using schema
            schema = PasswordResetCompleteSchema()
            data = schema.load(request.json)

            # Get user by email
            user = auth_service.user_repository.get_by_email(data["email"])

            if not user:
                return jsonify({
                    "error": "Invalid email",
                    "message": "Email not found"
                }), 404

            # Verify reset code
            if not auth_service.verify_password_reset_token(data["email"], data["code"]):
                return jsonify({
                    "error": "Invalid reset code",
                    "message": "Password reset code is invalid or expired"
                }), 400

            # Update password and clear reset code
            user.password_hash = auth_service.hash_password(data["new_password"])
            user.verification_code = None
            user.verification_code_expiry = None
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
                "email_verified": user.email_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @auth_bp.route("/verify-email", methods=["POST"])
    @cross_origin()
    def verify_email():
        """Verify user email with verification code"""
        try:
            # Parse and validate input using schema
            schema = EmailVerificationSchema()
            data = schema.load(request.json)

            if verify_email_use_case:
                # Use the dedicated use case if available
                success, user = verify_email_use_case.execute(
                    email=data["email"],
                    verification_code=data["code"]
                )
                
                if success:
                    return jsonify({
                        "message": "Email verified successfully",
                        "user": {
                            "id": str(user.id),
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "email_verified": user.email_verified,
                            "role": user.role
                        }
                    }), 200
                else:
                    return jsonify({
                        "error": "Invalid verification code",
                        "message": "The code is invalid or has expired"
                    }), 400
            else:
                # Fallback to direct repository access if use case not provided
                # Get user by email
                user = auth_service.user_repository.get_by_email(data["email"])

                if not user:
                    return jsonify({
                        "error": "Invalid email",
                        "message": "Email not found"
                    }), 404

                # Verify email with code
                if user.verify_email(data["code"]):
                    # Update user in repository
                    auth_service.user_repository.update(user)
                    
                    return jsonify({
                        "message": "Email verified successfully",
                        "user": {
                            "id": str(user.id),
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "email_verified": user.email_verified,
                            "role": user.role
                        }
                    }), 200
                else:
                    return jsonify({
                        "error": "Invalid verification code",
                        "message": "The code is invalid or has expired"
                    }), 400

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except ValidationException as e:
            return jsonify({"error": "Validation error", "message": str(e)}), 400

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @auth_bp.route("/resend-verification", methods=["POST"])
    @cross_origin()
    def resend_verification():
        """Resend email verification code"""
        try:
            # Parse and validate input properly
            if isinstance(request.json, str):
                # If request.json is a string, try to extract email from it
                email = request.json.strip()
            elif isinstance(request.json, dict):
                # If request.json is a dictionary, use get method
                email = request.json.get("email")
            else:
                email = None
                
            if not email:
                return jsonify({
                    "error": "Email required",
                    "message": "Please provide an email address"
                }), 400

            if resend_verification_use_case:
                # Use the dedicated use case if available
                success = resend_verification_use_case.execute(email=email)
                
                return jsonify({
                    "message": "If the email exists, a verification code has been sent"
                }), 200
            else:
                # Fallback to direct repository access if use case not provided
                # Get user by email
                user = auth_service.user_repository.get_by_email(email)

                if not user:
                    # For security reasons, don't reveal if email exists
                    return jsonify({
                        "message": "If the email exists, a verification code has been sent"
                    }), 200

                if user.email_verified:
                    return jsonify({
                        "message": "Email is already verified"
                    }), 200

                # Generate new verification code
                verification_code = register_use_case._generate_verification_code()
                user.set_verification_code(verification_code, 24)
                
                # Update user in repository
                auth_service.user_repository.update(user)
                
                # Send verification email
                if register_use_case.notification_service:
                    register_use_case.notification_service.send_notification(
                        user_id=user.id,
                        notification_type=NotificationType.EMAIL_VERIFICATION,
                        data={
                            "name": f"{user.first_name}",
                            "verification_code": verification_code
                        },
                        send_email=True
                    )
                
                return jsonify({
                    "message": "Verification code has been sent"
                }), 200

        except ValidationException as e:
            return jsonify({"error": "Validation error", "message": str(e)}), 400

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    return auth_bp
