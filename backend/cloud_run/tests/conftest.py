"""
Pytest configuration and fixtures for The Intaker Flask API tests.
Provides reusable test fixtures for database mocking, authentication, and app testing.
"""

import os
import pytest
from unittest.mock import Mock, MagicMock
import sys
from datetime import datetime

# Add the parent directory to the path so we can import our app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app
from google.cloud import firestore


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    
    # Set test environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-unit-tests'
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project-id'
    os.environ['FIRESTORE_DATABASE'] = 'test-db'
    os.environ['GOOGLE_CLIENT_ID'] = 'test-client-id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'test-client-secret'
    
    # Set rate limiting to high values for testing
    os.environ['RATELIMIT_DEFAULT'] = '1000 per minute'
    os.environ['RATELIMIT_PHI_ACCESS'] = '1000 per minute'
    os.environ['RATELIMIT_HEALTH'] = '1000 per minute'
    
    # Create the app with test configuration
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Create application context
    with app.app_context():
        yield app


@pytest.fixture
def fresh_app():
    """Create a fresh Flask application for tests that need to add routes dynamically."""
    
    # Set test environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-unit-tests'
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project-id'
    os.environ['FIRESTORE_DATABASE'] = 'test-db'
    os.environ['GOOGLE_CLIENT_ID'] = 'test-client-id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'test-client-secret'
    
    # Set rate limiting to high values for testing
    os.environ['RATELIMIT_DEFAULT'] = '1000 per minute'
    os.environ['RATELIMIT_PHI_ACCESS'] = '1000 per minute'
    os.environ['RATELIMIT_HEALTH'] = '1000 per minute'
    
    # Create the app with test configuration
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the Flask application."""
    return app.test_cli_runner()


@pytest.fixture
def mock_firestore_client():
    """Create a mock Firestore client for testing."""
    mock_client = Mock()
    mock_db = Mock()
    mock_client.db = mock_db
    return mock_client


@pytest.fixture
def mock_firestore_document_storage(mock_firestore_client):
    """Create a mock FirestoreDocumentStorage instance."""
    from cloud_functions.document_processing.firestore_integration import FirestoreDocumentStorage
    
    # Create a mock instance
    mock_storage = Mock(spec=FirestoreDocumentStorage)
    mock_storage.db = mock_firestore_client.db
    
    # Mock the audit logging methods
    mock_storage.log_manual_audit_event = Mock()
    mock_storage.log_phi_access_attempt = Mock()
    
    return mock_storage


@pytest.fixture
def sample_patient_data():
    """Provide sample patient data for testing (non-PHI only)."""
    return [
        {
            'patient_id': 'patient_001',
            'registration_date': datetime(2024, 1, 15),
            'document_count': 3,
            'last_document_upload': datetime(2024, 1, 20),
            'status': 'active',
            '_version': 1,
            '_created_at': datetime(2024, 1, 15),
            '_updated_at': datetime(2024, 1, 20)
        },
        {
            'patient_id': 'patient_002',
            'registration_date': datetime(2024, 1, 16),
            'document_count': 1,
            'last_document_upload': datetime(2024, 1, 16),
            'status': 'pending',
            '_version': 1,
            '_created_at': datetime(2024, 1, 16),
            '_updated_at': datetime(2024, 1, 16)
        },
        {
            'patient_id': 'patient_003',
            'registration_date': datetime(2024, 1, 17),
            'document_count': 5,
            'last_document_upload': datetime(2024, 1, 22),
            'status': 'completed',
            '_version': 2,
            '_created_at': datetime(2024, 1, 17),
            '_updated_at': datetime(2024, 1, 22)
        }
    ]


@pytest.fixture
def mock_firestore_documents(sample_patient_data):
    """Create mock Firestore document objects from sample data."""
    mock_docs = []
    for data in sample_patient_data:
        mock_doc = Mock()
        mock_doc.to_dict.return_value = data
        mock_doc.exists = True
        mock_docs.append(mock_doc)
    return mock_docs


@pytest.fixture
def auth_headers():
    """Provide mock authentication headers for testing."""
    # In a real implementation, this would be a valid JWT token
    # For testing, we'll use a mock token that our auth decorator can recognize
    return {
        'Authorization': 'Bearer test-jwt-token-for-unit-tests',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def mock_jwt_decode():
    """Mock JWT decoding for authentication testing."""
    return {
        'sub': 'test-user-id',
        'email': 'test@example.com',
        'aud': 'test-client-id',
        'iss': 'https://securetoken.google.com/test-project-id',
        'exp': 9999999999,  # Far future expiry
        'iat': 1000000000,   # Past issued time
        'firebase': {
            'identities': {
                'email': ['test@example.com']
            },
            'sign_in_provider': 'password'
        }
    }


@pytest.fixture
def mock_get_current_user_id():
    """Mock the get_current_user_id function to return a test user ID."""
    return 'test-user-id'


@pytest.fixture(autouse=True)
def mock_firestore_globally(monkeypatch, mock_firestore_document_storage):
    """Automatically mock Firestore for all tests."""
    
    # Mock the get_firestore_client function in routes
    def mock_get_firestore_client():
        return mock_firestore_document_storage
    
    # Apply the mock to all route modules that use Firestore
    monkeypatch.setattr('routes.patients.get_firestore_client', mock_get_firestore_client)
    monkeypatch.setattr('routes.documents.get_firestore_client', mock_get_firestore_client)
    
    return mock_firestore_document_storage


@pytest.fixture(autouse=True) 
def mock_auth_globally(monkeypatch, mock_jwt_decode, mock_get_current_user_id):
    """Automatically mock authentication for all tests."""
    
    # Mock Google OAuth2 token verification
    def mock_verify_oauth2_token(token, request, audience):
        if token == 'test-jwt-token-for-unit-tests':
            return {
                'sub': 'test-user-id',
                'email': 'test@example.com',
                'name': 'Test User',
                'picture': 'https://example.com/avatar.jpg',
                'email_verified': True,
                'iss': 'https://accounts.google.com',
                'aud': 'test-client-id',
                'exp': 9999999999,
                'iat': 1000000000
            }
        raise ValueError('Invalid token')
    
    # Mock get_current_user_id function
    def mock_user_id_func():
        return mock_get_current_user_id
    
    # Apply mocks to the correct modules
    monkeypatch.setattr('google.oauth2.id_token.verify_oauth2_token', mock_verify_oauth2_token)
    monkeypatch.setattr('auth.get_current_user_id', mock_user_id_func)
    
    # Mock the Firestore client initialization to avoid real connections
    def mock_firestore_client():
        return Mock()
    
    monkeypatch.setattr('google.cloud.firestore.Client', mock_firestore_client) 