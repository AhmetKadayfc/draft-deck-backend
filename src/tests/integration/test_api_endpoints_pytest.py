import json
import pytest


# Helper functions for making authenticated requests
def make_student_request(client, method, url, data=None, content_type='application/json'):
    headers = {'Authorization': 'Bearer student_token'}
    if data and content_type == 'application/json':
        data = json.dumps(data)
    return getattr(client, method)(url, data=data, headers=headers, content_type=content_type)


def make_advisor_request(client, method, url, data=None, content_type='application/json'):
    headers = {'Authorization': 'Bearer advisor_token'}
    if data and content_type == 'application/json':
        data = json.dumps(data)
    return getattr(client, method)(url, data=data, headers=headers, content_type=content_type)


def make_admin_request(client, method, url, data=None, content_type='application/json'):
    headers = {'Authorization': 'Bearer admin_token'}
    if data and content_type == 'application/json':
        data = json.dumps(data)
    return getattr(client, method)(url, data=data, headers=headers, content_type=content_type)


# ------------------- TEST AUTH ROUTES -------------------
def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert data['message'] == 'Draft Deck API is running'


def test_register(client, mock_repositories):
    """Test user registration endpoint"""
    # Test data
    data = {
        'email': 'newstudent@example.com',
        'first_name': 'New',
        'last_name': 'Student',
        'password': 'SecurePassword123!',
        'role': 'student',
        'department': 'Computer Science',
        'student_id': '12345'
    }
    
    response = client.post('/api/auth/register', 
                           data=json.dumps(data), 
                           content_type='application/json')
    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert 'user' in response_data
    assert 'message' in response_data


def test_login(client, mock_services, mock_users):
    """Test login endpoint"""
    # Test data
    data = {
        'email': 'student@example.com',
        'password': 'password123'
    }
    
    response = client.post('/api/auth/login', 
                           data=json.dumps(data), 
                           content_type='application/json')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'access_token' in response_data
    assert 'refresh_token' in response_data
    assert 'user' in response_data


def test_refresh_token(client, mock_services):
    """Test token refresh endpoint"""
    # Test data
    headers = {'Authorization': 'Bearer fake_refresh_token'}
    
    response = client.post('/api/auth/refresh', headers=headers)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'access_token' in response_data
    assert response_data['token_type'] == 'bearer'


def test_logout(client, mock_services):
    """Test logout endpoint"""
    response = make_student_request(client, 'post', '/api/auth/logout')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data['message'] == 'Logged out successfully'


def test_password_reset_request(client, mock_repositories, mock_services):
    """Test password reset request endpoint"""
    data = {
        'email': 'student@example.com'
    }
    
    response = client.post('/api/auth/password-reset/request', 
                           data=json.dumps(data), 
                           content_type='application/json')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data


def test_password_reset_confirm(client, mock_repositories, mock_services):
    """Test password reset confirmation endpoint"""
    data = {
        'email': 'student@example.com',
        'reset_code': '123456'
    }
    
    response = client.post('/api/auth/password-reset/confirm', 
                           data=json.dumps(data), 
                           content_type='application/json')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'valid' in response_data


def test_password_reset_complete(client, mock_repositories, mock_services):
    """Test password reset completion endpoint"""
    data = {
        'email': 'student@example.com',
        'reset_code': '123456',
        'new_password': 'NewSecurePassword123!'
    }
    
    response = client.post('/api/auth/password-reset/complete', 
                           data=json.dumps(data), 
                           content_type='application/json')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data


def test_get_current_user(client, mock_services, mock_users):
    """Test get current user endpoint"""
    response = make_student_request(client, 'get', '/api/auth/me')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'user' in response_data


def test_verify_email(client, mock_repositories):
    """Test email verification endpoint"""
    data = {
        'email': 'student@example.com',
        'verification_code': '123456'
    }
    
    response = client.post('/api/auth/verify-email', 
                           data=json.dumps(data), 
                           content_type='application/json')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data


def test_resend_verification(client, mock_repositories):
    """Test resend verification email endpoint"""
    data = {
        'email': 'student@example.com'
    }
    
    response = client.post('/api/auth/resend-verification', 
                          data=json.dumps(data), 
                          content_type='application/json')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data


# ------------------- TEST THESIS ROUTES -------------------
def test_create_thesis(client, mock_repositories, mock_services, mock_ids):
    """Test thesis creation endpoint"""
    data = {
        'title': 'New Test Thesis',
        'thesis_type': 'masters',
        'description': 'This is a test thesis',
        'metadata': {'keywords': ['test', 'api']}
    }
    
    response = make_student_request(client, 'post', '/api/theses', data=data)
    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert 'thesis' in response_data
    assert 'message' in response_data


def test_get_theses(client, mock_repositories, mock_services):
    """Test get theses endpoint"""
    response = make_student_request(client, 'get', '/api/theses')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'theses' in response_data
    assert 'count' in response_data


def test_get_thesis(client, mock_repositories, mock_services, mock_ids):
    """Test get specific thesis endpoint"""
    response = make_student_request(client, 'get', f'/api/theses/{mock_ids["thesis_id"]}')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert str(response_data['id']) == str(mock_ids["thesis_id"])


def test_update_thesis(client, mock_repositories, mock_services, mock_ids):
    """Test thesis update endpoint"""
    data = {
        'title': 'Updated Thesis Title',
        'description': 'Updated thesis description'
    }
    
    response = make_student_request(client, 'put', f'/api/theses/{mock_ids["thesis_id"]}', data=data)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'thesis' in response_data


def test_update_thesis_status(client, mock_repositories, mock_services, mock_ids):
    """Test thesis status update endpoint"""
    data = {
        'status': 'submitted',
        'comments': 'Submitting thesis for review'
    }
    
    response = make_student_request(client, 'put', f'/api/theses/{mock_ids["thesis_id"]}/status', data=data)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'thesis' in response_data


def test_download_thesis(client, mock_repositories, mock_services, mock_ids):
    """Test thesis download endpoint"""
    response = make_student_request(client, 'get', f'/api/theses/{mock_ids["thesis_id"]}/download')
    assert response.status_code == 200
    assert 'application/pdf' in response.headers['Content-Type']


def test_assign_advisor(client, mock_repositories, mock_services, mock_ids):
    """Test advisor assignment endpoint"""
    response = make_advisor_request(client, 'post', f'/api/theses/{mock_ids["thesis_id"]}/assign')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'thesis' in response_data


# ------------------- TEST FEEDBACK ROUTES -------------------
def test_create_feedback(client, mock_repositories, mock_services, mock_ids):
    """Test feedback creation endpoint"""
    data = {
        'thesis_id': str(mock_ids["thesis_id"]),
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
    
    response = make_advisor_request(client, 'post', '/api/feedback', data=data)
    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert 'feedback' in response_data
    assert 'message' in response_data


def test_get_thesis_feedback(client, mock_repositories, mock_services, mock_ids):
    """Test get thesis feedback endpoint"""
    response = make_student_request(client, 'get', f'/api/feedback/thesis/{mock_ids["thesis_id"]}')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'feedback' in response_data
    assert 'thesis_id' in response_data
    assert 'thesis_title' in response_data


def test_get_feedback(client, mock_repositories, mock_services, mock_ids):
    """Test get specific feedback endpoint"""
    response = make_student_request(client, 'get', f'/api/feedback/{mock_ids["feedback_id"]}')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert str(response_data['id']) == str(mock_ids["feedback_id"])


def test_update_feedback(client, mock_repositories, mock_services, mock_ids):
    """Test feedback update endpoint"""
    data = {
        'overall_comments': 'Updated feedback comments',
        'rating': 5,
        'recommendations': 'Updated recommendations'
    }
    
    response = make_advisor_request(client, 'put', f'/api/feedback/{mock_ids["feedback_id"]}', data=data)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'feedback' in response_data


def test_export_feedback(client, mock_repositories, mock_services, mock_ids):
    """Test feedback export endpoint"""
    response = make_student_request(client, 'get', f'/api/feedback/{mock_ids["feedback_id"]}/export')
    assert response.status_code == 200
    assert 'application/pdf' in response.headers['Content-Type']


# ------------------- TEST ADMIN ROUTES -------------------
def test_get_users(client, mock_repositories, mock_services):
    """Test admin get users endpoint"""
    response = make_admin_request(client, 'get', '/api/admin/users')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'users' in response_data
    assert 'count' in response_data


def test_update_user(client, mock_repositories, mock_services, mock_ids):
    """Test admin update user endpoint"""
    data = {
        'first_name': 'Updated',
        'last_name': 'Name',
        'department': 'Updated Department',
        'is_active': True,
        'role': 'student'
    }
    
    response = make_admin_request(client, 'put', f'/api/admin/users/{mock_ids["student_id"]}', data=data)
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'message' in response_data
    assert 'user' in response_data


def test_get_stats(client, mock_repositories, mock_services):
    """Test admin stats endpoint"""
    response = make_admin_request(client, 'get', '/api/admin/stats')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert 'users' in response_data
    assert 'theses' in response_data 