from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database connection
from .infrastructure.database.connection import init_db, db_session

# Import repositories
from .infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from .infrastructure.repositories.thesis_repository_impl import ThesisRepositoryImpl
from .infrastructure.repositories.feedback_repository_impl import FeedbackRepositoryImpl

# Import services
from .infrastructure.services.jwt_service import JwtService
from .infrastructure.services.cloudinary_service import CloudinaryStorageService
from .infrastructure.services.pdf_service import PdfService
from .infrastructure.services.email_service import EmailNotificationService

# Import use cases
from .application.use_cases.auth.login_use_case import LoginUseCase
from .application.use_cases.auth.register_use_case import RegisterUseCase
from .application.use_cases.thesis.submit_thesis_use_case import SubmitThesisUseCase
from .application.use_cases.thesis.get_thesis_use_case import GetThesisUseCase
from .application.use_cases.feedback.export_feedback_use_case import ExportFeedbackUseCase
from .application.use_cases.feedback.provide_feedback_use_case import ProvideFeedbackUseCase

# Import routes
from .api.routes.auth_routes import create_auth_routes
from .api.routes.thesis_routes import create_thesis_routes
from .api.routes.feedback_routes import create_feedback_routes
from .api.routes.admin_routes import create_admin_routes

# Import error handlers
from .api.error_handlers import register_error_handlers


def create_app(testing=False):
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Configure app
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default-secret-key-change-this")
    app.config["DEBUG"] = os.getenv("DEBUG", "False").lower() in ["true", "1", "yes"]
    app.config["TESTING"] = testing

    # Setup CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Root route for API health check
    @app.route("/", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "ok",
            "message": "Draft Deck API is running",
            "version": "0.0.1"
        })

    # Clean up database session after each request
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        pass
        # db_session.remove()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 5000))
    )
