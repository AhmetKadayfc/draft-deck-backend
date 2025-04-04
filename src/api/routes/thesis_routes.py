from flask import Blueprint, request, jsonify, g, send_file
from flask_cors import cross_origin
from marshmallow import ValidationError
import io

from application.use_cases.thesis.submit_thesis_use_case import SubmitThesisUseCase
from application.dtos.thesis_dto import ThesisCreateDTO, ThesisUpdateDTO, ThesisStatusUpdateDTO
from api.middleware.auth_middleware import authenticate
from api.middleware.rbac_middleware import (
    require_student, require_advisor, thesis_owner_or_advisor
)
from domain.exceptions.domain_exceptions import (
    ValidationException, EntityNotFoundException, FileStorageException
)
from domain.value_objects.status import ThesisStatus
from api.schemas.request.thesis_schemas import (
    ThesisCreateSchema, ThesisUpdateSchema, ThesisStatusUpdateSchema
)


def create_thesis_routes(
    submit_thesis_use_case: SubmitThesisUseCase,
    thesis_repository,
    user_repository,
    storage_service,
    auth_service
):
    """Factory function to create thesis routes"""
    thesis_bp = Blueprint("thesis", __name__, url_prefix="/api/theses")

    @thesis_bp.route("", methods=["POST"])
    @cross_origin()
    @authenticate(auth_service)
    @require_student()
    def create_thesis():
        """Create a new thesis"""
        try:
            # Parse and validate input using schema
            schema = ThesisCreateSchema()

            # Check if multipart form data (file upload)
            if request.content_type and 'multipart/form-data' in request.content_type:
                data = schema.load(request.form)
                file = request.files.get('file')
            else:
                data = schema.load(request.json)
                file = None

            # Create DTO
            thesis_dto = ThesisCreateDTO(
                title=data["title"],
                thesis_type=data["thesis_type"],
                description=data.get("description"),
                metadata=data.get("metadata", {})
            )

            # Get current user from g object (set by middleware)
            student_id = g.user.id

            # Execute use case
            if file:
                result = submit_thesis_use_case.execute(
                    dto=thesis_dto,
                    student_id=student_id,
                    file_data=file.stream,
                    file_name=file.filename
                )
            else:
                result = submit_thesis_use_case.execute(
                    dto=thesis_dto,
                    student_id=student_id
                )

            # Return response
            return jsonify({
                "message": "Thesis created successfully",
                "thesis": {
                    "id": str(result.id),
                    "title": result.title,
                    "status": result.status,
                    "thesis_type": result.thesis_type,
                    "created_at": result.created_at.isoformat() if result.created_at else None
                }
            }), 201

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except ValidationException as e:
            return jsonify({"error": "Validation error", "message": str(e)}), 400

        except FileStorageException as e:
            return jsonify({"error": "File upload error", "message": str(e)}), 400

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @thesis_bp.route("", methods=["GET"])
    @cross_origin()
    @authenticate(auth_service)
    def get_theses():
        """Get theses based on role and query parameters"""
        try:
            # Get query parameters
            limit = int(request.args.get("limit", 20))
            offset = int(request.args.get("offset", 0))
            status = request.args.get("status")
            thesis_type = request.args.get("type")
            search_query = request.args.get("query")

            # Get current user role
            user = g.user

            # Filter theses based on role
            if user.role.value == "student":
                # Students can only see their own theses
                theses = thesis_repository.get_by_student(
                    user.id, limit, offset)
            elif user.role.value == "advisor":
                # Advisors can see theses assigned to them
                theses = thesis_repository.get_by_advisor(
                    user.id, limit, offset)
            else:  # Admin
                # Admins can see all theses
                theses = thesis_repository.get_all(limit, offset)

            # Apply additional filtering if needed
            if status:
                try:
                    status_enum = ThesisStatus(status)
                    theses = [t for t in theses if t.status == status_enum]
                except ValueError:
                    pass

            if thesis_type:
                theses = [
                    t for t in theses if t.thesis_type.value == thesis_type]

            if search_query:
                theses = [t for t in theses if
                          search_query.lower() in t.title.lower() or
                          (t.description and search_query.lower() in t.description.lower())]

            # Format response
            result = []
            for thesis in theses:
                # Get student name
                student = user_repository.get_by_id(thesis.student_id)
                student_name = f"{student.first_name} {student.last_name}" if student else "Unknown"

                # Get advisor name if assigned
                advisor_name = None
                if thesis.advisor_id:
                    advisor = user_repository.get_by_id(thesis.advisor_id)
                    advisor_name = f"{advisor.first_name} {advisor.last_name}" if advisor else "Unknown"

                # Generate download URL if file exists
                download_url = None
                if thesis.file_path:
                    download_url = f"/api/theses/{thesis.id}/download"

                result.append({
                    "id": str(thesis.id),
                    "title": thesis.title,
                    "student_id": str(thesis.student_id),
                    "student_name": student_name,
                    "advisor_id": str(thesis.advisor_id) if thesis.advisor_id else None,
                    "advisor_name": advisor_name,
                    "thesis_type": thesis.thesis_type.value,
                    "status": thesis.status.value,
                    "version": thesis.version,
                    "has_file": bool(thesis.file_path),
                    "file_name": thesis.file_name,
                    "download_url": download_url,
                    "submitted_at": thesis.submitted_at.isoformat() if thesis.submitted_at else None,
                    "created_at": thesis.created_at.isoformat() if thesis.created_at else None,
                    "updated_at": thesis.updated_at.isoformat() if thesis.updated_at else None
                })

            # Return response
            return jsonify({
                "theses": result,
                "count": len(result),
                "limit": limit,
                "offset": offset
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @thesis_bp.route("/<thesis_id>", methods=["GET"])
    @cross_origin()
    @authenticate(auth_service)
    @thesis_owner_or_advisor(thesis_repository)
    def get_thesis(thesis_id):
        """Get a specific thesis"""
        try:
            # Thesis is already available in g.thesis (set by middleware)
            thesis = g.thesis

            # Get student name
            student = user_repository.get_by_id(thesis.student_id)
            student_name = f"{student.first_name} {student.last_name}" if student else "Unknown"

            # Get advisor name if assigned
            advisor_name = None
            if thesis.advisor_id:
                advisor = user_repository.get_by_id(thesis.advisor_id)
                advisor_name = f"{advisor.first_name} {advisor.last_name}" if advisor else "Unknown"

            # Generate download URL if file exists
            download_url = None
            if thesis.file_path:
                download_url = f"/api/theses/{thesis.id}/download"

            # Return response
            return jsonify({
                "id": str(thesis.id),
                "title": thesis.title,
                "student_id": str(thesis.student_id),
                "student_name": student_name,
                "advisor_id": str(thesis.advisor_id) if thesis.advisor_id else None,
                "advisor_name": advisor_name,
                "thesis_type": thesis.thesis_type.value,
                "status": thesis.status.value,
                "version": thesis.version,
                "description": thesis.description,
                "has_file": bool(thesis.file_path),
                "file_name": thesis.file_name,
                "file_size": thesis.file_size,
                "file_type": thesis.file_type,
                "download_url": download_url,
                "submitted_at": thesis.submitted_at.isoformat() if thesis.submitted_at else None,
                "approved_at": thesis.approved_at.isoformat() if thesis.approved_at else None,
                "rejected_at": thesis.rejected_at.isoformat() if thesis.rejected_at else None,
                "created_at": thesis.created_at.isoformat() if thesis.created_at else None,
                "updated_at": thesis.updated_at.isoformat() if thesis.updated_at else None,
                "metadata": thesis.metadata or {}
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @thesis_bp.route("/<thesis_id>", methods=["PUT"])
    @cross_origin()
    @authenticate(auth_service)
    @thesis_owner_or_advisor(thesis_repository)
    def update_thesis(thesis_id):
        """Update a thesis"""
        try:
            # Thesis is already available in g.thesis (set by middleware)
            thesis = g.thesis

            # Check if user is student (only students can update content)
            is_student_owner = str(g.user.id) == str(thesis.student_id)
            if not is_student_owner and request.content_type and 'multipart/form-data' in request.content_type:
                return jsonify({
                    "error": "Permission denied",
                    "message": "Only students can update thesis content and files"
                }), 403

            # Only allow updates for drafts or theses that need revision
            if thesis.status not in [ThesisStatus.DRAFT, ThesisStatus.NEEDS_REVISION]:
                return jsonify({
                    "error": "Invalid state",
                    "message": f"Cannot update thesis in {thesis.status.value} status"
                }), 400

            # Parse and validate input using schema
            schema = ThesisUpdateSchema()

            # Check if multipart form data (file upload)
            if request.content_type and 'multipart/form-data' in request.content_type:
                data = schema.load(request.form)
                file = request.files.get('file')
            else:
                data = schema.load(request.json)
                file = None

            # Update thesis fields
            if "title" in data:
                thesis.title = data["title"]

            if "description" in data:
                thesis.description = data["description"]

            if "metadata" in data:
                thesis.metadata = data["metadata"]

            # Upload new file if provided
            if file:
                file_info = storage_service.upload_file(
                    file_data=file.stream,
                    file_name=file.filename,
                    user_id=thesis.student_id,
                    thesis_id=thesis.id
                )

                thesis.update_file_info(
                    file_path=file_info["file_path"],
                    file_name=file_info["file_name"],
                    file_size=file_info["file_size"],
                    file_type=file_info["file_type"]
                )

            # Save changes
            updated_thesis = thesis_repository.update(thesis)

            # Return response
            return jsonify({
                "message": "Thesis updated successfully",
                "thesis": {
                    "id": str(updated_thesis.id),
                    "title": updated_thesis.title,
                    "status": updated_thesis.status.value,
                    "updated_at": updated_thesis.updated_at.isoformat() if updated_thesis.updated_at else None
                }
            }), 200

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except ValidationException as e:
            return jsonify({"error": "Validation error", "message": str(e)}), 400

        except FileStorageException as e:
            return jsonify({"error": "File upload error", "message": str(e)}), 400

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @thesis_bp.route("/<thesis_id>/status", methods=["PUT"])
    @cross_origin()
    @authenticate(auth_service)
    @thesis_owner_or_advisor(thesis_repository)
    def update_thesis_status(thesis_id):
        """Update thesis status"""
        try:
            # Thesis is already available in g.thesis (set by middleware)
            thesis = g.thesis

            # Parse and validate input using schema
            schema = ThesisStatusUpdateSchema()
            data = schema.load(request.json)

            # Create DTO
            status_dto = ThesisStatusUpdateDTO(
                status=data["status"]
            )

            # Get current user role
            is_student = g.user.role.value == "student"
            is_advisor = g.user.role.value == "advisor" or g.user.role.value == "admin"

            # Get old status for later use
            old_status = thesis.status.value

            # Validate status transition based on role
            try:
                new_status = ThesisStatus(status_dto.status)

                # Students can only submit drafts
                if is_student:
                    if thesis.status != ThesisStatus.DRAFT and new_status != ThesisStatus.SUBMITTED:
                        return jsonify({
                            "error": "Invalid status transition",
                            "message": "Students can only submit draft theses"
                        }), 400

                # Update status
                thesis.update_status(new_status)

                # Save changes
                updated_thesis = thesis_repository.update(thesis)

                # Return response
                return jsonify({
                    "message": "Thesis status updated successfully",
                    "thesis": {
                        "id": str(updated_thesis.id),
                        "title": updated_thesis.title,
                        "old_status": old_status,
                        "new_status": updated_thesis.status.value,
                        "updated_at": updated_thesis.updated_at.isoformat() if updated_thesis.updated_at else None
                    }
                }), 200

            except ValueError:
                return jsonify({
                    "error": "Invalid status",
                    "message": f"Status must be one of: {', '.join(ThesisStatus.values())}"
                }), 400

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except ValidationException as e:
            return jsonify({"error": "Validation error", "message": str(e)}), 400

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @thesis_bp.route("/<thesis_id>/download", methods=["GET"])
    @cross_origin()
    @authenticate(auth_service)
    @thesis_owner_or_advisor(thesis_repository)
    def download_thesis(thesis_id):
        """Download thesis file"""
        try:
            # Thesis is already available in g.thesis (set by middleware)
            thesis = g.thesis

            # Check if thesis has a file
            if not thesis.file_path:
                return jsonify({
                    "error": "Not found",
                    "message": "This thesis does not have a file"
                }), 404

            # Get file from storage
            file_data = storage_service.get_file(thesis.file_path)

            if not file_data:
                return jsonify({
                    "error": "Not found",
                    "message": "File not found"
                }), 404

            # Send file
            return send_file(
                file_data,
                download_name=thesis.file_name,
                mimetype=thesis.file_type or "application/octet-stream",
                as_attachment=True
            )

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @thesis_bp.route("/<thesis_id>/assign", methods=["POST"])
    @cross_origin()
    @authenticate(auth_service)
    @require_advisor()
    def assign_advisor(thesis_id):
        """Assign an advisor to a thesis"""
        try:
            # Get thesis
            thesis = thesis_repository.get_by_id(thesis_id)

            if not thesis:
                return jsonify({
                    "error": "Not found",
                    "message": "Thesis not found"
                }), 404

            # Check if thesis already has an advisor
            if thesis.advisor_id:
                return jsonify({
                    "error": "Already assigned",
                    "message": "This thesis already has an advisor assigned"
                }), 400

            # Assign current user as advisor
            thesis.assign_advisor(g.user.id)

            # Save changes
            updated_thesis = thesis_repository.update(thesis)

            # Return response
            return jsonify({
                "message": "Thesis assigned successfully",
                "thesis": {
                    "id": str(updated_thesis.id),
                    "title": updated_thesis.title,
                    "advisor_id": str(updated_thesis.advisor_id),
                    "updated_at": updated_thesis.updated_at.isoformat() if updated_thesis.updated_at else None
                }
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    return thesis_bp
