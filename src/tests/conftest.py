import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime

from src.app import create_app
from src.domain.value_objects.status import UserRole, ThesisStatus


@pytest.fixture
def app():
    """Create and return a Flask app for testing"""
    app = create_app(testing=True)
    return app


@pytest.fixture
def client(app):
    """Create and return a test client for the app"""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Push an application context for the tests"""
    with app.app_context():
        yield


@pytest.fixture
def mock_ids():
    """Generate and return UUIDs for testing"""
    return {
        'user_id': uuid4(),
        'student_id': uuid4(),
        'advisor_id': uuid4(),
        'admin_id': uuid4(),
        'thesis_id': uuid4(),
        'feedback_id': uuid4(),
    }


@pytest.fixture
def mock_users(mock_ids):
    """Create mock user objects for testing"""
    mock_student = _create_mock_user(
        mock_ids['student_id'], 
        "student@example.com", 
        "John", 
        "Doe", 
        UserRole.STUDENT
    )
    
    mock_advisor = _create_mock_user(
        mock_ids['advisor_id'], 
        "advisor@example.com", 
        "Jane", 
        "Smith", 
        UserRole.ADVISOR
    )
    
    mock_admin = _create_mock_user(
        mock_ids['admin_id'], 
        "admin@example.com", 
        "Admin", 
        "User", 
        UserRole.ADMIN
    )
    
    return {
        'student': mock_student,
        'advisor': mock_advisor,
        'admin': mock_admin
    }


@pytest.fixture
def mock_thesis(mock_ids):
    """Create a mock thesis object for testing"""
    return _create_mock_thesis(
        mock_ids['thesis_id'],
        mock_ids['student_id'],
        mock_ids['advisor_id']
    )


@pytest.fixture
def mock_feedback(mock_ids):
    """Create a mock feedback object for testing"""
    return _create_mock_feedback(
        mock_ids['feedback_id'],
        mock_ids['thesis_id'],
        mock_ids['advisor_id']
    )


@pytest.fixture
def mock_repositories(mock_users, mock_thesis, mock_feedback, mock_ids):
    """Set up mock repositories for testing"""
    with patch('src.infrastructure.repositories.user_repository_impl.UserRepositoryImpl') as mock_user_repo, \
         patch('src.infrastructure.repositories.thesis_repository_impl.ThesisRepositoryImpl') as mock_thesis_repo, \
         patch('src.infrastructure.repositories.feedback_repository_impl.FeedbackRepositoryImpl') as mock_feedback_repo:
        
        # Configure user repository
        instance = mock_user_repo.return_value
        instance.get_by_email.side_effect = lambda email: next(
            (user for user in mock_users.values() if user.email == email), None
        )
        instance.get_by_id.side_effect = lambda user_id: next(
            (user for user in mock_users.values() if str(user.id) == str(user_id)), None
        )
        instance.get_all.return_value = list(mock_users.values())
        instance.get_by_role.side_effect = lambda role, limit, offset: [
            user for user in mock_users.values() if user.role == role
        ]
        instance.create.return_value = mock_users['student']
        
        # Configure thesis repository
        instance = mock_thesis_repo.return_value
        instance.get_by_id.return_value = mock_thesis
        instance.get_all.return_value = [mock_thesis]
        instance.get_by_student.return_value = [mock_thesis]
        instance.get_by_advisor.return_value = [mock_thesis]
        instance.get_stats.return_value = {"draft": 1, "submitted": 2, "approved": 1, "rejected": 0}
        instance.create.return_value = mock_thesis
        instance.update.return_value = mock_thesis
        
        # Configure feedback repository
        instance = mock_feedback_repo.return_value
        instance.get_by_id.return_value = mock_feedback
        instance.get_by_thesis.return_value = [mock_feedback]
        instance.create.return_value = mock_feedback
        instance.update.return_value = mock_feedback
        
        yield {
            'user_repo': mock_user_repo,
            'thesis_repo': mock_thesis_repo,
            'feedback_repo': mock_feedback_repo
        }


@pytest.fixture
def mock_services(mock_users, mock_ids):
    """Set up mock services for testing"""
    with patch('src.infrastructure.services.jwt_service.JwtService') as mock_jwt_service, \
         patch('src.infrastructure.services.cloudinary_service.CloudinaryStorageService') as mock_storage_service, \
         patch('src.infrastructure.services.pdf_service.PdfService') as mock_pdf_service, \
         patch('src.infrastructure.services.email_service.EmailNotificationService') as mock_email_service:
        
        # Configure JWT service
        instance = mock_jwt_service.return_value
        instance.generate_tokens.return_value = {
            "access_token": "fake_access_token", 
            "refresh_token": "fake_refresh_token", 
            "token_type": "bearer", 
            "expires_in": 3600
        }
        instance.verify_token.side_effect = lambda token: (
            (True, {"sub": str(mock_ids['student_id']), "type": "access"}) 
            if token == "student_token" or token == "Bearer student_token"
            else (True, {"sub": str(mock_ids['advisor_id']), "type": "access"}) 
            if token == "advisor_token" or token == "Bearer advisor_token"
            else (True, {"sub": str(mock_ids['admin_id']), "type": "access"}) 
            if token == "admin_token" or token == "Bearer admin_token" 
            else (True, {"sub": str(mock_ids['student_id']), "type": "refresh"}) 
            if token == "fake_refresh_token" or token == "Bearer fake_refresh_token"
            else (False, {"error": "Invalid token"})
        )
        
        instance.get_user_from_token.side_effect = lambda token: (
            mock_users['student'] 
            if token == "student_token" or (token.startswith("Bearer ") and token.split(" ")[1] == "student_token")
            else mock_users['advisor'] 
            if token == "advisor_token" or (token.startswith("Bearer ") and token.split(" ")[1] == "advisor_token")
            else mock_users['admin'] 
            if token == "admin_token" or (token.startswith("Bearer ") and token.split(" ")[1] == "admin_token")
            else None
        )
        
        instance.refresh_access_token.return_value = "new_fake_access_token"
        instance.authenticate.return_value = (
            mock_users['student'], 
            "fake_access_token", 
            "fake_refresh_token", 
            "bearer", 
            3600
        )
        instance.verify_password_reset_token.return_value = True
        instance.reset_password.return_value = True
        
        # Configure Storage service
        instance = mock_storage_service.return_value
        instance.get_file.return_value = (b'test file content', 'test-thesis.pdf')
        instance.store_file.return_value = "test-thesis.pdf"
        
        # Configure PDF service
        instance = mock_pdf_service.return_value
        instance.generate_feedback_pdf.return_value = (b'test pdf content', 'feedback.pdf')
        
        yield {
            'jwt_service': mock_jwt_service,
            'storage_service': mock_storage_service,
            'pdf_service': mock_pdf_service,
            'email_service': mock_email_service
        }


# Helper functions
def _create_mock_user(user_id, email, first_name, last_name, role, is_active=True, email_verified=True):
    """Create a mock user object"""
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.first_name = first_name
    user.last_name = last_name
    user.role = role
    user.is_active = is_active
    user.email_verified = email_verified
    user.department = "Computer Science" if role == UserRole.STUDENT or role == UserRole.ADVISOR else None
    user.student_id = "12345" if role == UserRole.STUDENT else None
    user.created_at = datetime.now()
    user.updated_at = datetime.now()
    return user


def _create_mock_thesis(thesis_id, student_id, advisor_id=None, status=ThesisStatus.DRAFT):
    """Create a mock thesis object"""
    thesis = MagicMock()
    thesis.id = thesis_id
    thesis.title = "Test Thesis"
    thesis.thesis_type = MagicMock()
    thesis.thesis_type.value = "masters"
    thesis.student_id = student_id
    thesis.advisor_id = advisor_id
    thesis.description = "This is a test thesis description"
    thesis.status = status
    thesis.file_path = "test-thesis.pdf" if status != ThesisStatus.DRAFT else None
    thesis.file_name = "test-thesis.pdf" if status != ThesisStatus.DRAFT else None
    thesis.file_size = 1024 if status != ThesisStatus.DRAFT else None
    thesis.file_type = "application/pdf" if status != ThesisStatus.DRAFT else None
    thesis.version = 1
    thesis.metadata = {"keywords": ["test", "api"]}
    thesis.created_at = datetime.now()
    thesis.updated_at = datetime.now()
    thesis.submitted_at = datetime.now() if status != ThesisStatus.DRAFT else None
    thesis.approved_at = datetime.now() if status == ThesisStatus.APPROVED else None
    thesis.rejected_at = None
    return thesis


def _create_mock_feedback(feedback_id, thesis_id, advisor_id):
    """Create a mock feedback object"""
    comment = MagicMock()
    comment.id = uuid4()
    comment.content = "This is a comment"
    comment.page = 1
    comment.position_x = 100
    comment.position_y = 100
    comment.created_at = datetime.now()

    feedback = MagicMock()
    feedback.id = feedback_id
    feedback.thesis_id = thesis_id
    feedback.advisor_id = advisor_id
    feedback.overall_comments = "This is overall feedback"
    feedback.rating = 4
    feedback.recommendations = "These are my recommendations"
    feedback.comments = [comment]
    feedback.created_at = datetime.now()
    feedback.updated_at = datetime.now()
    return feedback 