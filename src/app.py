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
# from .application.use_cases.feedback.export_feedback_use_case import ExportFeedbackUseCase
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

    # Initialize database
    init_db()

    # Setup migrations
    migrate = Migrate(app, db_session)

    # Setup repositories
    user_repository = UserRepositoryImpl(db_session)
    thesis_repository = ThesisRepositoryImpl(db_session)
    feedback_repository = FeedbackRepositoryImpl(db_session)

    # Setup password hashing service
    class PasswordHashService:
        def hash(self, password):
            return generate_password_hash(password)
        
        def verify(self, password, password_hash):
            return check_password_hash(password_hash, password)

    password_service = PasswordHashService()

    # Setup services
    jwt_service = JwtService(user_repository, password_service)
    storage_service = CloudinaryStorageService()
    pdf_service = PdfService(storage_service)
    notification_service = EmailNotificationService(
        user_repository=user_repository,
        thesis_repository=thesis_repository,
        feedback_repository=feedback_repository
    )

    # Setup use cases
    login_use_case = LoginUseCase(user_repository, jwt_service)
    register_use_case = RegisterUseCase(user_repository, jwt_service, notification_service)
    submit_thesis_use_case = SubmitThesisUseCase(
        thesis_repository, user_repository, storage_service, notification_service
    )
    provide_feedback_use_case = ProvideFeedbackUseCase(
        feedback_repository, thesis_repository, user_repository, notification_service
    )

    # Register routes
    app.register_blueprint(
        create_auth_routes(login_use_case, register_use_case, jwt_service)
    )
    app.register_blueprint(
        create_thesis_routes(
            submit_thesis_use_case, thesis_repository, user_repository, storage_service, jwt_service
        )
    )
    app.register_blueprint(
        create_feedback_routes(
            provide_feedback_use_case, feedback_repository, thesis_repository, 
            user_repository, pdf_service, jwt_service
        )
    )
    app.register_blueprint(
        create_admin_routes(
            user_repository, thesis_repository, feedback_repository, jwt_service
        )
    )

    # Register error handlers
    register_error_handlers(app)

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
        db_session.remove()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 5000))
    )
