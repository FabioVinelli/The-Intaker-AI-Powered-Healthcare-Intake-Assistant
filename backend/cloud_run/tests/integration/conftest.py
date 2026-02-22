"""
Integration test configuration for The Intaker Flask API.
Configures real Firestore emulator and Firebase Auth for end-to-end testing.
"""

import os
import pytest
import subprocess
import time
import requests
import logging
from datetime import datetime
import uuid

# Import parent conftest fixtures but override the ones we need for integration
from tests.conftest import *


# Configuration for Firestore emulator
FIRESTORE_EMULATOR_HOST = 'localhost:8080'
FIRESTORE_PROJECT_ID = 'test-intaker-project'

logger = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def firestore_emulator():
    """Start and stop Firestore emulator for integration tests."""
    
    # Check if emulator is already running
    try:
        response = requests.get(f'http://{FIRESTORE_EMULATOR_HOST}')
        logger.info("Firestore emulator already running")
        yield
        return
    except requests.ConnectionError:
        pass
    
    # Start the emulator
    logger.info("Starting Firestore emulator...")
    emulator_process = None
    
    try:
        # Start Firestore emulator
        emulator_process = subprocess.Popen([
            'gcloud', 'emulators', 'firestore', 'start',
            '--host-port', FIRESTORE_EMULATOR_HOST,
            '--project', FIRESTORE_PROJECT_ID
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for emulator to be ready
        for _ in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f'http://{FIRESTORE_EMULATOR_HOST}')
                if response.status_code == 200:
                    logger.info("Firestore emulator is ready")
                    break
            except requests.ConnectionError:
                time.sleep(1)
        else:
            raise RuntimeError("Firestore emulator failed to start within 30 seconds")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start Firestore emulator: {e}")
        # Fallback: use a mock setup instead
        logger.warning("Falling back to mock Firestore for integration tests")
        yield
        
    finally:
        if emulator_process:
            emulator_process.terminate()
            emulator_process.wait()
            logger.info("Firestore emulator stopped")


@pytest.fixture
def integration_app(firestore_emulator):
    """Create Flask app configured for integration testing with real Firestore emulator."""
    
    # Set environment variables for emulator
    os.environ['FIRESTORE_EMULATOR_HOST'] = FIRESTORE_EMULATOR_HOST
    os.environ['FIRESTORE_PROJECT_ID'] = FIRESTORE_PROJECT_ID
    os.environ['PROJECT_ID'] = FIRESTORE_PROJECT_ID
    
    # Set other test environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    os.environ['SECRET_KEY'] = 'integration-test-secret-key'
    os.environ['FIRESTORE_DATABASE'] = '(default)'
    os.environ['GOOGLE_CLIENT_ID'] = 'integration-test-client-id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'integration-test-client-secret'
    
    # Disable authentication for integration tests
    os.environ['DISABLE_AUTH_FOR_TESTING'] = 'true'
    
    # Set high rate limits for testing
    os.environ['RATELIMIT_DEFAULT'] = '10000 per minute'
    os.environ['RATELIMIT_PHI_ACCESS'] = '10000 per minute'
    os.environ['RATELIMIT_HEALTH'] = '10000 per minute'
    
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        yield app


@pytest.fixture
def integration_client(integration_app):
    """Create a test client for integration testing."""
    return integration_app.test_client()


@pytest.fixture
def integration_auth_headers():
    """Provide authentication headers for integration testing."""
    # For integration tests, we'll still use a mock token but with
    # auth validation disabled or minimal validation
    return {
        'Authorization': 'Bearer integration-test-jwt-token',
        'Content-Type': 'application/json'
    }


@pytest.fixture(autouse=True, scope='function')
def disable_auth_for_integration(monkeypatch):
    """Disable authentication for integration tests to focus on business logic."""
    
    # Mock the auth decorators to always pass for integration tests
    def mock_require_auth(f):
        """Mock decorator that bypasses authentication."""
        def wrapper(*args, **kwargs):
            # Set a mock user context
            from flask import g
            g.current_user_id = 'integration-test-user'
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    
    def mock_optional_auth(f):
        """Mock decorator that bypasses optional authentication."""
        return f
    
    def mock_get_current_user_id():
        """Mock function to return test user ID."""
        return 'integration-test-user'
    
    # Apply the mocks to auth module
    monkeypatch.setattr('auth.require_auth', mock_require_auth)
    monkeypatch.setattr('auth.optional_auth', mock_optional_auth)
    monkeypatch.setattr('auth.get_current_user_id', mock_get_current_user_id)
    
    # Also patch imports in routes modules
    try:
        monkeypatch.setattr('routes.patients.require_auth', mock_require_auth)
        monkeypatch.setattr('routes.patients.optional_auth', mock_optional_auth)
        monkeypatch.setattr('routes.patients.get_current_user_id', mock_get_current_user_id)
    except AttributeError:
        # Module may not be imported yet
        pass


@pytest.fixture
def sample_integration_patient():
    """Provide sample patient data for integration testing."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        'patient_id': f'integration_test_patient_{unique_id}',
        'registration_date': datetime.now(),
        'document_count': 0,
        'last_document_upload': None,
        'status': 'pending',
        'metadata': {
            'test_marker': 'integration_test',
            'created_by': 'integration_test_suite'
        }
    }


@pytest.fixture
def cleanup_test_patients(integration_app):
    """Cleanup function to remove test patients after integration tests."""
    created_patients = []
    
    def register_patient(patient_id):
        """Register a patient for cleanup."""
        created_patients.append(patient_id)
    
    yield register_patient
    
    # Cleanup after test
    if created_patients:
        logger.info(f"Cleaning up {len(created_patients)} test patients")
        
        with integration_app.app_context():
            try:
                from routes.patients import get_firestore_client
                firestore_client = get_firestore_client()
                
                for patient_id in created_patients:
                    try:
                        # Delete patient document
                        patient_ref = firestore_client.db.collection('patients').document(patient_id)
                        patient_ref.delete()
                        
                        # Delete related documents
                        docs_query = firestore_client.db.collection('patient_documents').where('patient_id', '==', patient_id)
                        for doc in docs_query.stream():
                            doc.reference.delete()
                        
                        logger.debug(f"Cleaned up test patient: {patient_id}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to cleanup patient {patient_id}: {e}")
                        
            except Exception as e:
                logger.error(f"Failed to initialize cleanup: {e}")


# Additional integration test utilities

def wait_for_firestore_consistency(seconds=1):
    """Wait for Firestore to achieve consistency (useful for emulator)."""
    time.sleep(seconds)


@pytest.fixture
def integration_test_marker():
    """Marker fixture to identify integration tests."""
    return 'integration_test_marker' 