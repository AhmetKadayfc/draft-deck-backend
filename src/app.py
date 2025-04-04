from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_app(testing=False):
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Configure app
    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY", "default-secret-key-change-this")
    app.config["DEBUG"] = os.getenv("DEBUG", "False").lower() in [
        "true", "1", "yes"]
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
