import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, jsonify, g
from src.api.middleware.auth_middleware import authenticate, get_token_from_header

class TestAuthMiddleware(unittest.TestCase):
    """Test the authentication middleware"""

    def setUp(self):
        # Create a test Flask app
        self.app = Flask(__name__)
        self.client = self.app.test_client()
        
        # Mock the AuthService
        self.auth_service_patcher = patch('src.infrastructure.services.jwt_service.JwtService')
        self.mock_auth_service = self.auth_service_patcher.start()
        
        # Configure the test route
        @self.app.route('/test')
        @authenticate(self.mock_auth_service.return_value)
        def test_route():
            # This route should only be accessible with a valid token
            return jsonify({"success": True, "user_id": str(g.user.id)})
            
    def tearDown(self):
        self.auth_service_patcher.stop()
        
    def test_authentication_success(self):
        """Test successful authentication"""
        # Configure mock
        mock_instance = self.mock_auth_service.return_value
        
        # Mock verify_token to return True and payload
        mock_instance.verify_token.return_value = (True, {"sub": "test-user-id", "type": "access"})
        
        # Mock get_user_from_token to return a user
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.is_active = True
        mock_instance.get_user_from_token.return_value = mock_user
        
        # Make request with token
        response = self.client.get('/test', headers={'Authorization': 'Bearer test-token'})
        
        # Check that the request was successful
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user_id'], "test-user-id")
        
        # Verify mock calls
        mock_instance.verify_token.assert_called_once_with('test-token')
        mock_instance.get_user_from_token.assert_called_once_with('test-token')
        
    def test_authentication_failure_no_token(self):
        """Test authentication failure when no token is provided"""
        # Make request without token
        response = self.client.get('/test')
        
        # Check that the request was rejected
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['error'], "Authentication required")
        
    def test_authentication_failure_invalid_token(self):
        """Test authentication failure when an invalid token is provided"""
        # Configure mock
        mock_instance = self.mock_auth_service.return_value
        
        # Mock verify_token to return False
        mock_instance.verify_token.return_value = (False, {"error": "Invalid token"})
        
        # Make request with invalid token
        response = self.client.get('/test', headers={'Authorization': 'Bearer invalid-token'})
        
        # Check that the request was rejected
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['error'], "Invalid authentication token")
        
    def test_authentication_failure_no_user(self):
        """Test authentication failure when no user is found for the token"""
        # Configure mock
        mock_instance = self.mock_auth_service.return_value
        
        # Mock verify_token to return True
        mock_instance.verify_token.return_value = (True, {"sub": "test-user-id", "type": "access"})
        
        # Mock get_user_from_token to return None
        mock_instance.get_user_from_token.return_value = None
        
        # Make request with token for non-existent user
        response = self.client.get('/test', headers={'Authorization': 'Bearer test-token'})
        
        # Check that the request was rejected
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['error'], "Invalid user")
        
    def test_authentication_failure_inactive_user(self):
        """Test authentication failure when the user is inactive"""
        # Configure mock
        mock_instance = self.mock_auth_service.return_value
        
        # Mock verify_token to return True
        mock_instance.verify_token.return_value = (True, {"sub": "test-user-id", "type": "access"})
        
        # Mock get_user_from_token to return an inactive user
        mock_user = MagicMock()
        mock_user.id = "test-user-id"
        mock_user.is_active = False
        mock_instance.get_user_from_token.return_value = mock_user
        
        # Make request with token for inactive user
        response = self.client.get('/test', headers={'Authorization': 'Bearer test-token'})
        
        # Check that the request was rejected
        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertEqual(data['error'], "Account inactive")
        
    def test_get_token_from_header(self):
        """Test extraction of token from Authorization header"""
        with self.app.test_request_context(headers={'Authorization': 'Bearer test-token'}):
            token = get_token_from_header()
            self.assertEqual(token, 'test-token')
            
    def test_get_token_from_header_no_auth(self):
        """Test extraction of token when no Authorization header is present"""
        with self.app.test_request_context():
            token = get_token_from_header()
            self.assertIsNone(token)
            
    def test_get_token_from_header_invalid_format(self):
        """Test extraction of token when Authorization header has invalid format"""
        with self.app.test_request_context(headers={'Authorization': 'Basic test-token'}):
            token = get_token_from_header()
            self.assertIsNone(token)
            
        with self.app.test_request_context(headers={'Authorization': 'Bearer'}):
            token = get_token_from_header()
            self.assertIsNone(token)


if __name__ == '__main__':
    unittest.main() 