from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.domain.exceptions.domain_exceptions import (
    DomainException, ValidationException, EntityNotFoundException,
    AuthorizationException, ThesisAlreadySubmittedException,
    InvalidStatusTransitionException, FileStorageException
)


def register_error_handlers(app):
    """Register custom error handlers for the application"""

    @app.errorhandler(ValidationException)
    def handle_validation_exception(e):
        return jsonify({
            "error": "Validation error",
            "message": str(e)
        }), 400

    @app.errorhandler(EntityNotFoundException)
    def handle_entity_not_found(e):
        return jsonify({
            "error": "Not found",
            "message": str(e)
        }), 404

    @app.errorhandler(AuthorizationException)
    def handle_authorization_exception(e):
        return jsonify({
            "error": "Permission denied",
            "message": str(e)
        }), 403

    @app.errorhandler(ThesisAlreadySubmittedException)
    def handle_thesis_already_submitted(e):
        return jsonify({
            "error": "Invalid operation",
            "message": str(e)
        }), 400

    @app.errorhandler(InvalidStatusTransitionException)
    def handle_invalid_status_transition(e):
        return jsonify({
            "error": "Invalid operation",
            "message": str(e)
        }), 400

    @app.errorhandler(FileStorageException)
    def handle_file_storage_exception(e):
        return jsonify({
            "error": "File error",
            "message": str(e)
        }), 400

    @app.errorhandler(DomainException)
    def handle_domain_exception(e):
        return jsonify({
            "error": "Application error",
            "message": str(e)
        }), 400

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({
            "error": e.name,
            "message": e.description
        }), e.code

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        # In production, you would log this error
        return jsonify({
            "error": "Server error",
            "message": "An unexpected error occurred"
        }), 500
