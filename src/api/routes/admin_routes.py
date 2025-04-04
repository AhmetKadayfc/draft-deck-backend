from flask import Blueprint, request, jsonify, g
from flask_cors import cross_origin
from uuid import UUID

from src.api.middleware.auth_middleware import authenticate
from src.api.middleware.rbac_middleware import require_admin
from src.domain.value_objects.status import UserRole


def create_admin_routes(
    user_repository,
    thesis_repository,
    feedback_repository,
    auth_service
):
    """Factory function to create admin routes"""
    admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

    @admin_bp.route("/users", methods=["GET"])
    @cross_origin()
    @authenticate(auth_service)
    @require_admin()
    def get_users():
        """Get all users (admin only)"""
        try:
            # Get query parameters
            limit = int(request.args.get("limit", 100))
            offset = int(request.args.get("offset", 0))
            role = request.args.get("role")

            # Get users based on role filter
            if role and role in UserRole.values():
                users = user_repository.get_by_role(
                    UserRole(role), limit, offset)
            else:
                users = user_repository.get_all(limit, offset)

            # Format response
            result = []
            for user in users:
                result.append({
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
                })

            # Return response
            return jsonify({
                "users": result,
                "count": len(result),
                "limit": limit,
                "offset": offset
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @admin_bp.route("/users/<user_id>", methods=["PUT"])
    @cross_origin()
    @authenticate(auth_service)
    @require_admin()
    def update_user(user_id):
        """Update a user (admin only)"""
        try:
            # Get user
            user = user_repository.get_by_id(UUID(user_id))

            if not user:
                return jsonify({
                    "error": "Not found",
                    "message": "User not found"
                }), 404

            # Get request data
            data = request.json

            # Update fields
            if "first_name" in data:
                user.first_name = data["first_name"]

            if "last_name" in data:
                user.last_name = data["last_name"]

            if "department" in data:
                user.department = data["department"]

            if "student_id" in data and user.role == UserRole.STUDENT:
                user.student_id = data["student_id"]

            if "is_active" in data:
                if data["is_active"]:
                    user.activate()
                else:
                    user.deactivate()

            if "role" in data and data["role"] in UserRole.values():
                user.role = UserRole(data["role"])

            # Save changes
            updated_user = user_repository.update(user)

            # Return response
            return jsonify({
                "message": "User updated successfully",
                "user": {
                    "id": str(updated_user.id),
                    "email": updated_user.email,
                    "role": updated_user.role.value,
                    "is_active": updated_user.is_active,
                    "updated_at": updated_user.updated_at.isoformat() if updated_user.updated_at else None
                }
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @admin_bp.route("/stats", methods=["GET"])
    @cross_origin()
    @authenticate(auth_service)
    @require_admin()
    def get_stats():
        """Get system statistics (admin only)"""
        try:
            # Get user statistics
            total_users = len(user_repository.get_all(1000))
            students = len(user_repository.get_by_role(UserRole.STUDENT, 1000))
            advisors = len(user_repository.get_by_role(UserRole.ADVISOR, 1000))

            # Get thesis statistics
            thesis_stats = thesis_repository.get_stats()

            # Return response
            return jsonify({
                "users": {
                    "total": total_users,
                    "students": students,
                    "advisors": advisors,
                    "admins": total_users - students - advisors
                },
                "theses": thesis_stats
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    return admin_bp
