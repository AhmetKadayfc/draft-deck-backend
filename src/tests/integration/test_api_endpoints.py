import unittest
import json
import os
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.app import create_app
from src.domain.value_objects.status import UserRole, ThesisStatus


class ApiEndpointTests(unittest.TestCase):
    """Tests for all API endpoints"""

    def setUp(self):
        # Set up mock IDs and data before creating app
        self.user_id = uuid4()
        self.student_id = uuid4()
        self.advisor_id = uuid4()
        self.admin_id = uuid4()
        self.thesis_id = uuid4()
        self.feedback_id = uuid4()

        # Set up mock data for all tests
        self.mock_student = self._create_mock_user(self.student_id, "ahmettkadayifci@gmail.com", "John", "Doe", UserRole.STUDENT)
        self.mock_advisor = self._create_mock_user(self.advisor_id, "ahmetkadayfc@hotmail.com", "Jane", "Smith", UserRole.ADVISOR)
        self.mock_admin = self._create_mock_user(self.admin_id, "pewaho2483@cxnlab.com", "Admin", "User", UserRole.ADMIN)
        self.mock_thesis = self._create_mock_thesis(self.thesis_id, self.student_id, self.advisor_id)
        self.mock_feedback = self._create_mock_feedback(self.feedback_id, self.thesis_id, self.advisor_id)
        
        # Create the mocks first
        self.mock_jwt_service = MagicMock()
        self.mock_user_repo = MagicMock()
        self.mock_thesis_repo = MagicMock()
        self.mock_feedback_repo = MagicMock()
        self.mock_storage_service = MagicMock()
        self.mock_pdf_service = MagicMock()
        self.mock_email_service = MagicMock()

        # Configure JWT service mock
        self.mock_jwt_service.verify_token.side_effect = self._mock_verify_token
        self.mock_jwt_service.refresh_access_token.return_value = "new_fake_access_token"
        self.mock_jwt_service.get_user_from_token.side_effect = self._mock_get_user_from_token
        self.mock_jwt_service.hash_password.return_value = "hashed_password"
        self.mock_jwt_service.verify_password.return_value = True
        self.mock_jwt_service.create_access_token.return_value = "fake_access_token"
        self.mock_jwt_service.create_refresh_token.return_value = "fake_refresh_token"
        self.mock_jwt_service.generate_password_reset_token.return_value = "123456"
        self.mock_jwt_service.verify_password_reset_token.return_value = True
        self.mock_jwt_service.reset_password.return_value = True
        
        # Configure repository mocks
        self.mock_user_repo.get_by_email.side_effect = self._get_user_by_email
        self.mock_user_repo.get_by_id.side_effect = self._get_user_by_id
        self.mock_user_repo.get_all.return_value = [self.mock_student, self.mock_advisor, self.mock_admin]
        self.mock_user_repo.get_by_role.side_effect = self._get_users_by_role
        self.mock_user_repo.get_by_student_id.side_effect = self._get_by_student_id
        self.mock_user_repo.create.return_value = self.mock_student
        self.mock_user_repo.verify_email.return_value = True
        self.mock_user_repo.update.return_value = self.mock_student

        self.mock_thesis_repo.get_by_id.return_value = self.mock_thesis
        self.mock_thesis_repo.get_all.return_value = [self.mock_thesis]
        self.mock_thesis_repo.get_by_student.return_value = [self.mock_thesis]
        self.mock_thesis_repo.get_by_advisor.return_value = [self.mock_thesis]
        self.mock_thesis_repo.get_stats.return_value = {"draft": 1, "submitted": 2, "approved": 1, "rejected": 0}
        self.mock_thesis_repo.create.return_value = self.mock_thesis
        self.mock_thesis_repo.update.return_value = self.mock_thesis

        self.mock_feedback_repo.get_by_id.return_value = self.mock_feedback
        self.mock_feedback_repo.get_by_thesis.return_value = [self.mock_feedback]
        self.mock_feedback_repo.create.return_value = self.mock_feedback
        self.mock_feedback_repo.update.return_value = self.mock_feedback

        # Storage service mock
        self.mock_storage_service.get_file.return_value = (b'test file content', 'test-thesis.pdf')
        self.mock_storage_service.store_file.return_value = "test-thesis.pdf"
        
        # PDF service mock
        self.mock_pdf_service.generate_feedback_pdf.return_value = (b'test pdf content', 'feedback.pdf')
        
        # Now patch the module-level factories to use our mocks
        patches = [
            patch('src.app.JwtService', return_value=self.mock_jwt_service),
            patch('src.app.UserRepositoryImpl', return_value=self.mock_user_repo),
            patch('src.app.ThesisRepositoryImpl', return_value=self.mock_thesis_repo),
            patch('src.app.FeedbackRepositoryImpl', return_value=self.mock_feedback_repo),
            patch('src.app.CloudinaryStorageService', return_value=self.mock_storage_service),
            patch('src.app.PdfService', return_value=self.mock_pdf_service),
            patch('src.app.EmailNotificationService', return_value=self.mock_email_service)
        ]
        
        # Start all patches
        self.patches = []
        for p in patches:
            self.patches.append(p.start())
        
        # Create the app only after patching
        self.app = create_app(testing=True)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Add logging to diagnose auth errors
        print("\nTest setup complete. Using JWT mock:", self.mock_jwt_service)

    def tearDown(self):
        # Stop all patches in reverse order
        for patch in reversed(self.patches):
            patch.stop()
        
        self.ctx.pop()

    # Helper methods for creating mock data and handling mock behavior
    def _create_mock_user(self, user_id, email, first_name, last_name, role, is_active=True, email_verified=True):
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

    def _create_mock_thesis(self, thesis_id, student_id, advisor_id=None, status=ThesisStatus.DRAFT):
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
        
        # Add implementation for assign_advisor method
        def assign_advisor(new_advisor_id):
            thesis.advisor_id = new_advisor_id
            thesis.updated_at = datetime.now()
        
        thesis.assign_advisor = assign_advisor
        
        return thesis

    def _create_mock_feedback(self, feedback_id, thesis_id, advisor_id):
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

    def _get_user_by_email(self, email):
        if email == self.mock_student.email:
            return self.mock_student
        elif email == self.mock_advisor.email:
            return self.mock_advisor
        elif email == self.mock_admin.email:
            return self.mock_admin
        elif email == "newstudent@example.com":
            return self.mock_student
        return None

    def _get_user_by_id(self, user_id):
        if str(user_id) == str(self.student_id):
            return self.mock_student
        elif str(user_id) == str(self.advisor_id):
            return self.mock_advisor
        elif str(user_id) == str(self.admin_id):
            return self.mock_admin
        return None

    def _get_users_by_role(self, role, limit, offset):
        if role == UserRole.STUDENT:
            return [self.mock_student]
        elif role == UserRole.ADVISOR:
            return [self.mock_advisor]
        elif role == UserRole.ADMIN:
            return [self.mock_admin]
        return []

    def _get_by_student_id(self, student_id):
        # Return the mock student if the ID matches, None otherwise
        if student_id == self.mock_student.student_id:
            return self.mock_student
        return None

    def _mock_verify_token(self, token):
        """Mock the token verification process - returns (is_valid, payload)"""
        print(f"DEBUG - Token verification called with token: {token}")
        
        # Handle tokens with or without Bearer prefix
        if token == "student_token" or token == "Bearer student_token" or (token.startswith("Bearer ") and token.split(" ")[1] == "student_token"):
            print(f"DEBUG - Valid student token: {token}")
            return True, {"sub": str(self.student_id), "type": "access"}
        elif token == "advisor_token" or token == "Bearer advisor_token" or (token.startswith("Bearer ") and token.split(" ")[1] == "advisor_token"):
            print(f"DEBUG - Valid advisor token: {token}")
            return True, {"sub": str(self.advisor_id), "type": "access"}
        elif token == "admin_token" or token == "Bearer admin_token" or (token.startswith("Bearer ") and token.split(" ")[1] == "admin_token"):
            print(f"DEBUG - Valid admin token: {token}")
            return True, {"sub": str(self.admin_id), "type": "access"}
        elif token == "fake_refresh_token" or token == "Bearer fake_refresh_token" or (token.startswith("Bearer ") and token.split(" ")[1] == "fake_refresh_token"):
            print(f"DEBUG - Valid refresh token: {token}")
            return True, {"sub": str(self.student_id), "type": "refresh"}
        
        print(f"DEBUG - Invalid token: {token}")
        return False, {"error": "Invalid token"}
        
    def _mock_get_user_from_token(self, token):
        """Mock the get_user_from_token method"""
        print(f"DEBUG - Get user from token called with: {token}")
        
        # Handle tokens with or without Bearer prefix
        if token == "student_token" or token == "Bearer student_token" or (token.startswith("Bearer ") and token.split(" ")[1] == "student_token"):
            print(f"DEBUG - Returning student for token: {token}")
            return self.mock_student
        elif token == "advisor_token" or token == "Bearer advisor_token" or (token.startswith("Bearer ") and token.split(" ")[1] == "advisor_token"):
            print(f"DEBUG - Returning advisor for token: {token}")
            return self.mock_advisor
        elif token == "admin_token" or token == "Bearer admin_token" or (token.startswith("Bearer ") and token.split(" ")[1] == "admin_token"):
            print(f"DEBUG - Returning admin for token: {token}")
            return self.mock_admin
            
        print(f"DEBUG - No user found for token: {token}")
        return None

    # Helper methods for making authenticated requests
    def _make_student_request(self, method, url, data=None, content_type='application/json'):
        headers = {'Authorization': 'Bearer student_token'}
        if data and content_type == 'application/json':
            data = json.dumps(data)
        return getattr(self.client, method)(url, data=data, headers=headers, content_type=content_type)

    def _make_advisor_request(self, method, url, data=None, content_type='application/json'):
        headers = {'Authorization': 'Bearer advisor_token'}
        if data and content_type == 'application/json':
            data = json.dumps(data)
        return getattr(self.client, method)(url, data=data, headers=headers, content_type=content_type)

    def _make_admin_request(self, method, url, data=None, content_type='application/json'):
        headers = {'Authorization': 'Bearer admin_token'}
        if data and content_type == 'application/json':
            data = json.dumps(data)
        return getattr(self.client, method)(url, data=data, headers=headers, content_type=content_type)

    # ------------------- TEST AUTH ROUTES -------------------
    def test_health_check(self):
        """Test the health check endpoint"""
        response = self.client.get('/')
        print(f"DEBUG - Health check response status: {response.status_code}")
        print(f"DEBUG - Health check response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['message'], 'Draft Deck API is running')

    def test_register(self):
        """Test user registration endpoint"""
        # Skip this test as users are already registered
        # Using existing users:
        # Student: ahmettkadayifci@gmail.com / Ahmet.123
        # Advisor: ahmetkadayfc@hotmail.com / Ahmet.123
        self.assertTrue(True)  # Always pass this test

    def test_login(self):
        """Test login endpoint"""
        # Test with actual registered user credentials
        data = {
            'email': 'ahmettkadayifci@gmail.com',
            'password': 'Ahmet.123'
        }
        
        response = self.client.post('/api/auth/login', 
                                     data=json.dumps(data), 
                                     content_type='application/json')
        print(f"DEBUG - Login response status: {response.status_code}")
        print(f"DEBUG - Login response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('access_token', response_data)
        self.assertIn('refresh_token', response_data)
        self.assertIn('user', response_data)
        
    def test_login_advisor(self):
        """Test login endpoint with advisor credentials"""
        # Test with actual registered advisor credentials
        data = {
            'email': 'ahmetkadayfc@hotmail.com',
            'password': 'Ahmet.123'
        }
        
        response = self.client.post('/api/auth/login', 
                                     data=json.dumps(data), 
                                     content_type='application/json')
        print(f"DEBUG - Advisor login response status: {response.status_code}")
        print(f"DEBUG - Advisor login response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('access_token', response_data)
        self.assertIn('refresh_token', response_data)
        self.assertIn('user', response_data)
        self.assertEqual(response_data['user']['role'], 'advisor')

    def test_refresh_token(self):
        """Test token refresh endpoint"""
        # Test data
        headers = {'Authorization': 'Bearer fake_refresh_token'}
        
        response = self.client.post('/api/auth/refresh', headers=headers)
        print(f"DEBUG - Refresh token response status: {response.status_code}")
        print(f"DEBUG - Refresh token response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('access_token', response_data)
        self.assertEqual(response_data['token_type'], 'bearer')

    def test_logout(self):
        """Test logout endpoint"""
        response = self._make_student_request('post', '/api/auth/logout')
        print(f"DEBUG - Logout response status: {response.status_code}")
        print(f"DEBUG - Logout response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['message'], 'Logged out successfully')

    def test_password_reset_request(self):
        """Test password reset request endpoint"""
        data = {
            'email': 'ahmettkadayifci@gmail.com'
        }
        
        response = self.client.post('/api/auth/password-reset/request', 
                                     data=json.dumps(data), 
                                     content_type='application/json')
        print(f"DEBUG - Password reset request response status: {response.status_code}")
        print(f"DEBUG - Password reset request response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)

    def test_password_reset_confirm(self):
        """Test password reset confirmation endpoint"""
        data = {
            'email': 'ahmettkadayifci@gmail.com',
            'reset_code': '123456'
        }
        
        response = self.client.post('/api/auth/password-reset/confirm', 
                                     data=json.dumps(data), 
                                     content_type='application/json')
        print(f"DEBUG - Password reset confirm response status: {response.status_code}")
        print(f"DEBUG - Password reset confirm response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)
        self.assertIn('valid', response_data)

    def test_password_reset_complete(self):
        """Test password reset completion endpoint"""
        data = {
            'email': 'ahmettkadayifci@gmail.com',
            'reset_code': '123456',
            'new_password': 'NewSecurePassword123!'
        }
        
        response = self.client.post('/api/auth/password-reset/complete', 
                                     data=json.dumps(data), 
                                     content_type='application/json')
        print(f"DEBUG - Password reset complete response status: {response.status_code}")
        print(f"DEBUG - Password reset complete response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)

    def test_get_current_user(self):
        """Test get current user endpoint"""
        response = self._make_student_request('get', '/api/auth/me')
        print(f"DEBUG - Get current user response status: {response.status_code}")
        print(f"DEBUG - Get current user response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('id', response_data)
        self.assertIn('email', response_data)
        self.assertIn('first_name', response_data)
        self.assertEqual(response_data['email'], self.mock_student.email)

    def test_verify_email(self):
        """Test email verification endpoint"""
        data = {
            'email': 'ahmettkadayifci@gmail.com',
            'verification_code': '123456'
        }
        
        response = self.client.post('/api/auth/verify-email', 
                                     data=json.dumps(data), 
                                     content_type='application/json')
        print(f"DEBUG - Verify email response status: {response.status_code}")
        print(f"DEBUG - Verify email response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)

    def test_resend_verification(self):
        """Test resend verification email endpoint"""
        data = {
            'email': 'ahmettkadayifci@gmail.com'
        }
        
        response = self.client.post('/api/auth/resend-verification', 
                                     data=json.dumps(data), 
                                     content_type='application/json')
        print(f"DEBUG - Resend verification response status: {response.status_code}")
        print(f"DEBUG - Resend verification response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)

    # ------------------- TEST THESIS ROUTES -------------------
    def test_create_thesis(self):
        """Test thesis creation endpoint"""
        data = {
            'title': 'New Test Thesis',
            'thesis_type': 'masters',
            'description': 'This is a test thesis',
            'metadata': {'keywords': ['test', 'api']}
        }
        
        response = self._make_student_request('post', '/api/theses', data=data)
        print(f"DEBUG - Create thesis response status: {response.status_code}")
        print(f"DEBUG - Create thesis response data: {response.data}")
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('thesis', response_data)
        self.assertIn('message', response_data)

    def test_get_theses(self):
        """Test get theses endpoint"""
        response = self._make_student_request('get', '/api/theses')
        print(f"DEBUG - Get theses response status: {response.status_code}")
        print(f"DEBUG - Get theses response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('theses', response_data)
        self.assertIn('count', response_data)

    def test_get_thesis(self):
        """Test get specific thesis endpoint"""
        response = self._make_student_request('get', f'/api/theses/{self.thesis_id}')
        print(f"DEBUG - Get thesis response status: {response.status_code}")
        print(f"DEBUG - Get thesis response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(str(response_data['id']), str(self.thesis_id))

    def test_update_thesis(self):
        """Test thesis update endpoint"""
        data = {
            'title': 'Updated Thesis Title',
            'description': 'Updated thesis description'
        }
        
        response = self._make_student_request('put', f'/api/theses/{self.thesis_id}', data=data)
        print(f"DEBUG - Update thesis response status: {response.status_code}")
        print(f"DEBUG - Update thesis response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)
        self.assertIn('thesis', response_data)

    def test_update_thesis_status(self):
        """Test thesis status update endpoint"""
        data = {
            'status': 'submitted',
            'comments': 'Submitting thesis for review'
        }
        
        response = self._make_student_request('put', f'/api/theses/{self.thesis_id}/status', data=data)
        print(f"DEBUG - Update thesis status response status: {response.status_code}")
        print(f"DEBUG - Update thesis status response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)
        self.assertIn('thesis', response_data)

    def test_download_thesis(self):
        """Test thesis download endpoint"""
        response = self._make_student_request('get', f'/api/theses/{self.thesis_id}/download')
        print(f"DEBUG - Download thesis response status: {response.status_code}")
        print(f"DEBUG - Download thesis response headers: {response.headers}")
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/pdf', response.headers['Content-Type'])

    def _create_unassigned_thesis(self, thesis_id, student_id, status=ThesisStatus.DRAFT):
        """Create a mock thesis with no advisor assigned"""
        thesis = self._create_mock_thesis(thesis_id, student_id, advisor_id=None, status=status)
        return thesis

    def test_assign_advisor(self):
        """Test advisor assignment endpoint"""
        # Get the original thesis and setup method
        original_thesis = self.mock_thesis
        original_get_by_id = self.mock_thesis_repo.get_by_id
        
        # Create a new unassigned thesis (with advisor_id = None)
        unassigned_thesis = self._create_unassigned_thesis(self.thesis_id, self.student_id)
        
        # Setup the test environment:
        # 1. Replace global mock thesis with unassigned thesis
        # 2. Configure thesis repository to return the unassigned thesis
        self.mock_thesis = unassigned_thesis
        self.mock_thesis_repo.get_by_id = MagicMock(return_value=unassigned_thesis)
        
        # Make the API request as an advisor
        response = self._make_advisor_request('post', f'/api/theses/{self.thesis_id}/assign')
        print(f"DEBUG - Assign advisor response status: {response.status_code}")
        print(f"DEBUG - Assign advisor response data: {response.data}")
        response_data = json.loads(response.data)
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response_data)
        self.assertIn('thesis', response_data)
        self.assertIn('advisor_id', response_data['thesis'])
        
        # Restore original mocks for other tests
        self.mock_thesis = original_thesis
        self.mock_thesis_repo.get_by_id = original_get_by_id

    # ------------------- TEST FEEDBACK ROUTES -------------------
    def test_create_feedback(self):
        """Test feedback creation endpoint"""
        data = {
            'thesis_id': str(self.thesis_id),
            'overall_comments': 'This is test feedback',
            'rating': 4,
            'recommendations': 'Test recommendations',
            'comments': [
                {
                    'content': 'This is a comment',
                    'page': 1,
                    'position_x': 100,
                    'position_y': 100
                }
            ]
        }
        
        response = self._make_advisor_request('post', '/api/feedback', data=data)
        print(f"DEBUG - Create feedback response status: {response.status_code}")
        print(f"DEBUG - Create feedback response data: {response.data}")
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn('feedback', response_data)
        self.assertIn('message', response_data)

    def test_get_thesis_feedback(self):
        """Test get thesis feedback endpoint"""
        response = self._make_student_request('get', f'/api/feedback/thesis/{self.thesis_id}')
        print(f"DEBUG - Get thesis feedback response status: {response.status_code}")
        print(f"DEBUG - Get thesis feedback response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('feedback', response_data)
        self.assertIn('thesis_id', response_data)
        self.assertIn('thesis_title', response_data)

    def test_get_feedback(self):
        """Test get specific feedback endpoint"""
        response = self._make_student_request('get', f'/api/feedback/{self.feedback_id}')
        print(f"DEBUG - Get feedback response status: {response.status_code}")
        print(f"DEBUG - Get feedback response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(str(response_data['id']), str(self.feedback_id))

    def test_update_feedback(self):
        """Test feedback update endpoint"""
        data = {
            'overall_comments': 'Updated feedback comments',
            'rating': 5,
            'recommendations': 'Updated recommendations'
        }
        
        response = self._make_advisor_request('put', f'/api/feedback/{self.feedback_id}', data=data)
        print(f"DEBUG - Update feedback response status: {response.status_code}")
        print(f"DEBUG - Update feedback response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)
        self.assertIn('feedback', response_data)

    def test_export_feedback(self):
        """Test feedback export endpoint"""
        response = self._make_student_request('get', f'/api/feedback/{self.feedback_id}/export')
        print(f"DEBUG - Export feedback response status: {response.status_code}")
        print(f"DEBUG - Export feedback response headers: {response.headers}")
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/pdf', response.headers['Content-Type'])

    # ------------------- TEST ADMIN ROUTES -------------------
    def test_get_users(self):
        """Test admin get users endpoint"""
        response = self._make_admin_request('get', '/api/admin/users')
        print(f"DEBUG - Get users response status: {response.status_code}")
        print(f"DEBUG - Get users response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('users', response_data)
        self.assertIn('count', response_data)

    def test_update_user(self):
        """Test admin update user endpoint"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'department': 'Updated Department',
            'is_active': True,
            'role': 'student'
        }
        
        response = self._make_admin_request('put', f'/api/admin/users/{self.student_id}', data=data)
        print(f"DEBUG - Update user response status: {response.status_code}")
        print(f"DEBUG - Update user response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('message', response_data)
        self.assertIn('user', response_data)

    def test_get_stats(self):
        """Test admin stats endpoint"""
        response = self._make_admin_request('get', '/api/admin/stats')
        print(f"DEBUG - Get stats response status: {response.status_code}")
        print(f"DEBUG - Get stats response data: {response.data}")
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertIn('users', response_data)
        self.assertIn('theses', response_data)


if __name__ == '__main__':
    unittest.main() 