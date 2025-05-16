from flask import Blueprint, request, jsonify, g, send_file
from flask_cors import cross_origin
from marshmallow import ValidationError
from uuid import UUID
import io

from src.application.use_cases.feedback.provide_feedback_use_case import ProvideFeedbackUseCase
from src.application.dtos.feedback_dto import FeedbackCreateDTO, FeedbackUpdateDTO, FeedbackExportDTO
from src.api.middleware.auth_middleware import authenticate
from src.api.middleware.rbac_middleware import (
    require_advisor, thesis_owner_or_advisor
)
from src.domain.exceptions.domain_exceptions import ValidationException, EntityNotFoundException
from src.api.schemas.request.feedback_schemas import (
    FeedbackCreateSchema, FeedbackUpdateSchema, FeedbackExportSchema
)


def create_feedback_routes(
    provide_feedback_use_case: ProvideFeedbackUseCase,
    feedback_repository,
    thesis_repository,
    user_repository,
    pdf_service,
    auth_service
):
    """Factory function to create feedback routes"""
    feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")

    @feedback_bp.route("", methods=["POST"])
    @cross_origin()
    @authenticate(auth_service)
    @require_advisor()
    def create_feedback():
        """Create new feedback for a thesis"""
        try:
            # Parse and validate input using schema
            schema = FeedbackCreateSchema()
            data = schema.load(request.json)

            # Extract comments from request data
            comments = []
            for comment_data in data.get("comments", []):
                comments.append({
                    "content": comment_data["content"],
                    "page": comment_data.get("page"),
                    "position_x": comment_data.get("position_x"),
                    "position_y": comment_data.get("position_y")
                })

            # Create DTO
            # Ensure thesis_id is a proper UUID object
            thesis_id = data["thesis_id"]
            # If thesis_id is already a UUID object, use it directly; otherwise convert from string
            if not isinstance(thesis_id, UUID):
                thesis_id = UUID(thesis_id)
                
            feedback_dto = FeedbackCreateDTO(
                thesis_id=thesis_id,
                overall_comments=data["overall_comments"],
                rating=data.get("rating"),
                recommendations=data.get("recommendations"),
                comments=comments
            )

            # Get current user ID (advisor)
            advisor_id = g.user.id

            # Execute use case
            result = provide_feedback_use_case.execute(
                feedback_dto, advisor_id)

            # Return response
            return jsonify({
                "message": "Feedback provided successfully",
                "feedback": {
                    "id": str(result.id),
                    "thesis_id": str(result.thesis_id),
                    "thesis_title": result.thesis_title,
                    "advisor_id": str(result.advisor_id),
                    "advisor_name": result.advisor_name,
                    "created_at": result.created_at.isoformat() if result.created_at else None
                }
            }), 201

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except ValidationException as e:
            return jsonify({"error": "Validation error", "message": str(e)}), 400

        except EntityNotFoundException as e:
            return jsonify({"error": "Not found", "message": str(e)}), 404

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @feedback_bp.route("/thesis/<thesis_id>", methods=["GET"])
    @cross_origin()
    @authenticate(auth_service)
    @thesis_owner_or_advisor(thesis_repository)
    def get_thesis_feedback(thesis_id):
        """Get all feedback for a thesis"""
        try:
            # Get thesis from g object (set by middleware)
            thesis = g.thesis

            # Get all feedback for the thesis
            feedback_list = feedback_repository.get_by_thesis(thesis.id)

            # Format response
            result = []
            for feedback in feedback_list:
                # Get advisor name
                advisor = user_repository.get_by_id(feedback.advisor_id)
                advisor_name = f"{advisor.first_name} {advisor.last_name}" if advisor else "Unknown"

                # Format comments
                comments = []
                for comment in feedback.comments:
                    comments.append({
                        "id": str(comment.id),
                        "content": comment.content,
                        "page": comment.page,
                        "position_x": comment.position_x,
                        "position_y": comment.position_y,
                        "created_at": comment.created_at.isoformat() if comment.created_at else None
                    })

                result.append({
                    "id": str(feedback.id),
                    "thesis_id": str(feedback.thesis_id),
                    "thesis_title": thesis.title,
                    "advisor_id": str(feedback.advisor_id),
                    "advisor_name": advisor_name,
                    "overall_comments": feedback.overall_comments,
                    "rating": feedback.rating,
                    "recommendations": feedback.recommendations,
                    "comments": comments,
                    "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
                    "updated_at": feedback.updated_at.isoformat() if feedback.updated_at else None
                })

            # Return response
            return jsonify({
                "thesis_id": str(thesis.id),
                "thesis_title": thesis.title,
                "feedback": result,
                "count": len(result)
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @feedback_bp.route("/<feedback_id>", methods=["GET"])
    @cross_origin()
    @authenticate(auth_service)
    def get_feedback(feedback_id):
        """Get specific feedback by ID"""
        try:
            # Get feedback
            feedback = feedback_repository.get_by_id(UUID(feedback_id))

            if not feedback:
                return jsonify({
                    "error": "Not found",
                    "message": "Feedback not found"
                }), 404

            # Get thesis
            thesis = thesis_repository.get_by_id(feedback.thesis_id)

            if not thesis:
                return jsonify({
                    "error": "Not found",
                    "message": "Associated thesis not found"
                }), 404

            # Check permission - must be student owner or advisor
            user_id = g.user.id
            is_student_owner = str(user_id) == str(thesis.student_id)
            is_feedback_advisor = str(user_id) == str(feedback.advisor_id)
            is_admin = g.user.role.value == "admin"

            if not (is_student_owner or is_feedback_advisor or is_admin):
                return jsonify({
                    "error": "Permission denied",
                    "message": "You do not have permission to view this feedback"
                }), 403

            # Get advisor name
            advisor = user_repository.get_by_id(feedback.advisor_id)
            advisor_name = f"{advisor.first_name} {advisor.last_name}" if advisor else "Unknown"

            # Format comments
            comments = []
            for comment in feedback.comments:
                comments.append({
                    "id": str(comment.id),
                    "content": comment.content,
                    "page": comment.page,
                    "position_x": comment.position_x,
                    "position_y": comment.position_y,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None
                })

            # Return response
            return jsonify({
                "id": str(feedback.id),
                "thesis_id": str(feedback.thesis_id),
                "thesis_title": thesis.title,
                "advisor_id": str(feedback.advisor_id),
                "advisor_name": advisor_name,
                "overall_comments": feedback.overall_comments,
                "rating": feedback.rating,
                "recommendations": feedback.recommendations,
                "comments": comments,
                "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
                "updated_at": feedback.updated_at.isoformat() if feedback.updated_at else None
            }), 200

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @feedback_bp.route("/<feedback_id>", methods=["PUT"])
    @cross_origin()
    @authenticate(auth_service)
    @require_advisor()
    def update_feedback(feedback_id):
        """Update feedback"""
        try:
            # Get feedback
            feedback = feedback_repository.get_by_id(UUID(feedback_id))

            if not feedback:
                return jsonify({
                    "error": "Not found",
                    "message": "Feedback not found"
                }), 404

            # Check if user is the advisor who provided the feedback
            if str(g.user.id) != str(feedback.advisor_id) and g.user.role.value != "admin":
                return jsonify({
                    "error": "Permission denied",
                    "message": "You can only update your own feedback"
                }), 403

            # Parse and validate input using schema
            schema = FeedbackUpdateSchema()
            data = schema.load(request.json)

            # Update feedback fields
            if "overall_comments" in data:
                feedback.overall_comments = data["overall_comments"]

            if "rating" in data:
                feedback.rating = data["rating"]

            if "recommendations" in data:
                feedback.recommendations = data["recommendations"]

            # Process comments if provided
            if "comments" in data:
                # Clear existing comments
                feedback.comments = []

                # Add new comments
                for comment_data in data["comments"]:
                    feedback.add_comment(
                        content=comment_data["content"],
                        page=comment_data.get("page"),
                        position_x=comment_data.get("position_x"),
                        position_y=comment_data.get("position_y")
                    )

            # Save changes
            updated_feedback = feedback_repository.update(feedback)

            # Return response
            return jsonify({
                "message": "Feedback updated successfully",
                "feedback": {
                    "id": str(updated_feedback.id),
                    "thesis_id": str(updated_feedback.thesis_id),
                    "updated_at": updated_feedback.updated_at.isoformat() if updated_feedback.updated_at else None
                }
            }), 200

        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.messages}), 400

        except ValidationException as e:
            return jsonify({"error": "Validation error", "message": str(e)}), 400

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    @feedback_bp.route("/<feedback_id>/export", methods=["GET"])
    @cross_origin()
    @authenticate(auth_service)
    def export_feedback(feedback_id):
        """Export feedback as PDF"""
        try:
            # Convert feedback_id to UUID
            feedback_id = UUID(feedback_id)
            
            # Get feedback
            feedback = feedback_repository.get_by_id(feedback_id)

            if not feedback:
                return jsonify({
                    "error": "Not found",
                    "message": "Feedback not found"
                }), 404

            # Get thesis
            thesis = thesis_repository.get_by_id(feedback.thesis_id)

            if not thesis:
                return jsonify({
                    "error": "Not found",
                    "message": "Associated thesis not found"
                }), 404

            # Check permission - must be student owner or advisor
            user_id = g.user.id
            is_student_owner = str(user_id) == str(thesis.student_id)
            is_feedback_advisor = str(user_id) == str(feedback.advisor_id)
            is_admin = g.user.role.value == "admin"

            if not (is_student_owner or is_feedback_advisor or is_admin):
                return jsonify({
                    "error": "Permission denied",
                    "message": "You do not have permission to export this feedback"
                }), 403

            # Get student and advisor
            student = user_repository.get_by_id(thesis.student_id)
            advisor = user_repository.get_by_id(feedback.advisor_id)

            if not student or not advisor:
                return jsonify({
                    "error": "Not found",
                    "message": "Student or advisor not found"
                }), 404

            # Get query parameters
            include_inline_comments = request.args.get(
                "inline", "true").lower() == "true"
            include_original_document = request.args.get(
                "original", "false").lower() == "true"

            # Generate PDF
            pdf_buffer = pdf_service.generate_feedback_report(
                feedback=feedback,
                thesis=thesis,
                student=student,
                advisor=advisor,
                include_inline_comments=include_inline_comments,
                include_original_document=include_original_document
            )

            # Create a filename using string representations of data
            # Ensure thesis.title is a proper string even if it's a UUID object
            title_str = str(thesis.title) if thesis.title else "Untitled"
            # Handle UUID objects by converting to string first
            safe_title = title_str.replace(' ', '_')
            filename = f"Feedback_{safe_title}_{feedback.created_at.strftime('%Y-%m-%d')}.pdf"
            
            # Send file
            return send_file(
                pdf_buffer,
                download_name=filename,
                mimetype="application/pdf",
                as_attachment=True
            )

        except Exception as e:
            return jsonify({"error": "Server error", "message": str(e)}), 500

    return feedback_bp
