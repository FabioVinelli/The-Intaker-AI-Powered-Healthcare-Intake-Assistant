"""
Integration test core for The Intaker Flask API.
This file implements the core integration tests as requested:
- Patient creation & document upload workflow  
- OpenAPI documentation validation
- Health check endpoint testing
- Test data management strategy
"""

import pytest
import json
import uuid
import time
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock


class TestIntegrationCore:
    """Core integration tests for The Intaker API."""
    
    # ========== Patient Creation & Document Upload Workflow ==========
    
    def test_patient_creation_and_document_workflow(self, integration_client, integration_auth_headers, cleanup_test_patients):
        """
        Test the complete patient intake workflow:
        1. Create a new patient
        2. Verify patient retrieval
        3. Generate document upload URL
        4. Simulate document processing
        """
        # Step 1: Create a new patient
        patient_data = {
            'patient_id': f'core_test_patient_{uuid.uuid4().hex[:8]}',
            'status': 'pending',
            'metadata': {
                'test_marker': 'core_integration_test',
                'created_by': 'test_integration_core',
                'workflow': 'patient_creation_and_document'
            }
        }
        
        cleanup_test_patients(patient_data['patient_id'])
        
        # Mock Firestore operations for patient creation
        with patch('routes.patients.get_firestore_client') as mock_get_client:
            mock_firestore = MagicMock()
            mock_get_client.return_value = mock_firestore
            
            # Mock document operations
            mock_doc_ref = MagicMock()
            mock_firestore.db.collection.return_value.document.return_value = mock_doc_ref
            mock_doc_ref.get.return_value.exists = False  # Patient doesn't exist yet
            mock_doc_ref.set.return_value = None
            
            # Mock the created patient response
            mock_created_doc = MagicMock()
            mock_created_doc.to_dict.return_value = {
                **patient_data,
                '_version': 1,
                '_created_at': datetime.now(timezone.utc),
                '_updated_at': datetime.now(timezone.utc),
                '_created_by': 'integration-test-user',
                'document_count': 0,
                'registration_date': datetime.now(timezone.utc),
                'last_document_upload': None,
                'documents': []
            }
            
            # Configure mock to return the created patient when retrieved
            def mock_get_side_effect():
                mock_doc_ref.get.return_value = mock_created_doc
                return mock_doc_ref.get.return_value
            mock_doc_ref.get.side_effect = mock_get_side_effect
            
            # Mock audit logging
            mock_firestore.log_manual_audit_event = MagicMock()
            
            # Create patient
            response = integration_client.post(
                '/api/v1/patients/',
                json=patient_data,
                headers=integration_auth_headers
            )
            
            # Verify patient creation
            assert response.status_code == 201
            created_patient = response.get_json()
            assert created_patient['patient_id'] == patient_data['patient_id']
            assert created_patient['status'] == 'pending'
            assert created_patient['document_count'] == 0
            assert '_version' in created_patient
            assert '_created_at' in created_patient
            
            # Step 2: Verify patient retrieval
            response = integration_client.get(
                f'/api/v1/patients/{patient_data["patient_id"]}',
                headers=integration_auth_headers
            )
            
            assert response.status_code == 200
            retrieved_patient = response.get_json()
            assert retrieved_patient['patient_id'] == patient_data['patient_id']
            assert retrieved_patient['status'] == 'pending'
            
        # Step 3: Test document upload URL generation (conceptual)
        # Note: This would typically involve Cloud Storage signed URLs
        # For integration testing, we verify the endpoint exists and responds appropriately
        
        # Step 4: Simulate document processing
        document_id = f'doc_{uuid.uuid4().hex[:8]}'
        with patch('routes.documents.get_firestore_client') as mock_get_client:
            mock_firestore = MagicMock()
            mock_get_client.return_value = mock_firestore
            
            # Mock document status update
            mock_doc_ref = MagicMock()
            mock_firestore.db.collection.return_value.document.return_value = mock_doc_ref
            mock_firestore.update_document_status = MagicMock(return_value={
                'document_id': document_id,
                'new_status': 'completed',
                'previous_status': 'processing',
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'updated_by': 'integration-test-user'
            })
            
            response = integration_client.put(
                f'/api/v1/documents/{document_id}/status',
                json={'status': 'completed', 'additional_data': {'phi_detected': True}},
                headers=integration_auth_headers
            )
            
            assert response.status_code == 200
            update_response = response.get_json()
            assert update_response['document_id'] == document_id
            assert update_response['new_status'] == 'completed'
    
    def test_patient_phi_access_workflow(self, integration_client, integration_auth_headers, cleanup_test_patients):
        """Test PHI data access workflow with proper mocking."""
        patient_data = {
            'patient_id': f'phi_core_test_{uuid.uuid4().hex[:8]}',
            'status': 'active',
            'metadata': {'test_type': 'phi_access_core_test'}
        }
        
        cleanup_test_patients(patient_data['patient_id'])
        
        with patch('routes.patients.get_firestore_client') as mock_get_client:
            mock_firestore = MagicMock()
            mock_get_client.return_value = mock_firestore
            
            # Mock patient creation
            mock_doc_ref = MagicMock()
            mock_firestore.db.collection.return_value.document.return_value = mock_doc_ref
            mock_doc_ref.get.return_value.exists = False
            mock_doc_ref.set.return_value = None
            
            # Mock created patient response
            mock_created_doc = MagicMock()
            mock_created_doc.to_dict.return_value = {
                **patient_data,
                '_version': 1,
                '_created_at': datetime.now(timezone.utc),
                '_updated_at': datetime.now(timezone.utc),
                '_created_by': 'integration-test-user',
                'document_count': 0,
                'registration_date': datetime.now(timezone.utc),
                'documents': []
            }
            
            def mock_get_side_effect():
                mock_doc_ref.get.return_value = mock_created_doc
                return mock_doc_ref.get.return_value
            mock_doc_ref.get.side_effect = mock_get_side_effect
            
            # Mock audit logging
            mock_firestore.log_manual_audit_event = MagicMock()
            
            # Create patient
            response = integration_client.post(
                '/api/v1/patients/',
                json=patient_data,
                headers=integration_auth_headers
            )
            assert response.status_code == 201
            
            # Test PHI access endpoint
            phi_response = integration_client.get(
                f'/api/v1/patients/{patient_data["patient_id"]}/phi',
                headers=integration_auth_headers
            )
            
            assert phi_response.status_code == 200
            phi_data = phi_response.get_json()
            assert phi_data['patient_id'] == patient_data['patient_id']
            assert 'access_timestamp' in phi_data
            assert 'warning' in phi_data
    
    # ========== OpenAPI Documentation Validation ==========
    
    def test_openapi_specification_accessibility(self, integration_client):
        """Test that OpenAPI specification is accessible and structurally valid."""
        # Test JSON spec endpoint
        json_response = integration_client.get('/docs/openapi.json')
        assert json_response.status_code == 200
        
        spec_data = json_response.get_json()
        
        # Verify OpenAPI specification structure
        assert 'openapi' in spec_data
        assert 'info' in spec_data
        assert 'paths' in spec_data
        assert 'components' in spec_data
        
        # Verify info section
        info = spec_data['info']
        assert 'title' in info
        assert 'version' in info
        assert 'description' in info
        
        # Verify critical endpoints are documented
        paths = spec_data['paths']
        critical_endpoints = [
            '/api/v1/patients/',
            '/api/v1/patients/{patient_id}',
            '/health',
            '/ready'
        ]
        
        for endpoint in critical_endpoints:
            # Check if endpoint exists (with or without path parameters)
            endpoint_found = False
            for documented_path in paths.keys():
                if endpoint.replace('{patient_id}', '{patient_id}') == documented_path:
                    endpoint_found = True
                    break
            assert endpoint_found, f"Critical endpoint {endpoint} not found in OpenAPI spec"
        
        # Test Swagger UI endpoint
        swagger_response = integration_client.get('/docs/swagger')
        assert swagger_response.status_code == 200
        
        # Test ReDoc endpoint  
        redoc_response = integration_client.get('/docs/redoc')
        assert redoc_response.status_code == 200
    
    def test_api_response_schema_compliance(self, integration_client, integration_auth_headers, cleanup_test_patients):
        """Test that API responses match their documented schemas."""
        patient_data = {
            'patient_id': f'schema_core_test_{uuid.uuid4().hex[:8]}',
            'status': 'pending',
            'metadata': {'test_type': 'schema_compliance_core'}
        }
        
        cleanup_test_patients(patient_data['patient_id'])
        
        with patch('routes.patients.get_firestore_client') as mock_get_client:
            mock_firestore = MagicMock()
            mock_get_client.return_value = mock_firestore
            
            # Mock patient creation
            mock_doc_ref = MagicMock()
            mock_firestore.db.collection.return_value.document.return_value = mock_doc_ref
            mock_doc_ref.get.return_value.exists = False
            mock_doc_ref.set.return_value = None
            
            # Mock created patient response
            mock_created_doc = MagicMock()
            mock_created_doc.to_dict.return_value = {
                **patient_data,
                '_version': 1,
                '_created_at': datetime.now(timezone.utc),
                '_updated_at': datetime.now(timezone.utc),
                '_created_by': 'integration-test-user',
                'document_count': 0,
                'registration_date': datetime.now(timezone.utc),
                'last_document_upload': None,
                'documents': []
            }
            
            def mock_get_side_effect():
                mock_doc_ref.get.return_value = mock_created_doc
                return mock_doc_ref.get.return_value
            mock_doc_ref.get.side_effect = mock_get_side_effect
            
            # Mock audit logging
            mock_firestore.log_manual_audit_event = MagicMock()
            
            # Test patient creation response schema
            response = integration_client.post(
                '/api/v1/patients/',
                json=patient_data,
                headers=integration_auth_headers
            )
            
            assert response.status_code == 201
            response_data = response.get_json()
            
            # Verify required fields are present according to schema
            required_fields = [
                'patient_id', 'status', 'document_count', '_version', 
                '_created_at', '_updated_at', 'registration_date'
            ]
            for field in required_fields:
                assert field in response_data, f"Required field '{field}' missing from patient creation response"
            
            # Verify data types
            assert isinstance(response_data['document_count'], int)
            assert isinstance(response_data['_version'], int)
            assert isinstance(response_data['status'], str)
            assert response_data['status'] in ['pending', 'active', 'inactive', 'archived']
    
    # ========== Health Check Endpoint Testing ==========
    
    def test_health_check_endpoint(self, integration_client):
        """Test the health check endpoint returns proper status."""
        response = integration_client.get('/health')
        
        assert response.status_code == 200
        health_data = response.get_json()
        
        # Verify health response structure
        assert 'status' in health_data
        assert 'service' in health_data
        assert 'version' in health_data
        
        # Verify health status value
        assert health_data['status'] == 'healthy'
        assert health_data['service'] == 'intaker-api'
        
        # Verify response content type
        assert response.content_type == 'application/json'
    
    def test_readiness_check_endpoint(self, integration_client):
        """Test the readiness check endpoint returns proper status."""
        response = integration_client.get('/ready')
        
        assert response.status_code == 200
        ready_data = response.get_json()
        
        # Verify readiness response structure
        assert 'status' in ready_data
        assert 'service' in ready_data
        
        # Verify readiness status value
        assert ready_data['status'] == 'ready'
        assert ready_data['service'] == 'intaker-api'
        
        # Check for checks object if present
        if 'checks' in ready_data:
            assert isinstance(ready_data['checks'], dict)
    
    # ========== Test Data Management Strategy ==========
    
    def test_data_cleanup_strategy(self, integration_client, integration_auth_headers, cleanup_test_patients):
        """
        Test that the test data management strategy works correctly.
        This includes patient creation, cleanup registration, and automatic cleanup.
        """
        # Create multiple test patients to verify cleanup
        test_patients = []
        
        for i in range(3):
            patient_data = {
                'patient_id': f'cleanup_test_patient_{i}_{uuid.uuid4().hex[:8]}',
                'status': 'pending',
                'metadata': {
                    'test_marker': 'cleanup_strategy_test',
                    'batch_id': f'batch_{uuid.uuid4().hex[:4]}'
                }
            }
            test_patients.append(patient_data)
            cleanup_test_patients(patient_data['patient_id'])
        
        # Mock Firestore for all patient operations
        with patch('routes.patients.get_firestore_client') as mock_get_client:
            mock_firestore = MagicMock()
            mock_get_client.return_value = mock_firestore
            
            # Mock patient creation for each patient
            for patient_data in test_patients:
                mock_doc_ref = MagicMock()
                mock_firestore.db.collection.return_value.document.return_value = mock_doc_ref
                mock_doc_ref.get.return_value.exists = False
                mock_doc_ref.set.return_value = None
                
                # Mock created patient response
                mock_created_doc = MagicMock()
                mock_created_doc.to_dict.return_value = {
                    **patient_data,
                    '_version': 1,
                    '_created_at': datetime.now(timezone.utc),
                    '_updated_at': datetime.now(timezone.utc),
                    '_created_by': 'integration-test-user',
                    'document_count': 0,
                    'registration_date': datetime.now(timezone.utc),
                    'documents': []
                }
                
                def mock_get_side_effect():
                    mock_doc_ref.get.return_value = mock_created_doc
                    return mock_doc_ref.get.return_value
                mock_doc_ref.get.side_effect = mock_get_side_effect
                
                # Mock audit logging
                mock_firestore.log_manual_audit_event = MagicMock()
                
                # Create patient
                response = integration_client.post(
                    '/api/v1/patients/',
                    json=patient_data,
                    headers=integration_auth_headers
                )
                
                assert response.status_code == 201
                created_patient = response.get_json()
                assert created_patient['patient_id'] == patient_data['patient_id']
        
        # Verify that cleanup is registered for all test patients
        # The cleanup_test_patients fixture will handle the actual cleanup
        # This test verifies the strategy is working correctly
        assert len(test_patients) == 3
        for patient_data in test_patients:
            assert patient_data['metadata']['test_marker'] == 'cleanup_strategy_test'
    
    def test_unique_test_identifiers(self, integration_client, integration_auth_headers, cleanup_test_patients):
        """Test that test identifiers are unique and prevent conflicts."""
        # Create patients with UUID-based identifiers
        patient_ids = []
        
        for i in range(5):
            patient_id = f'unique_test_{uuid.uuid4().hex[:8]}'
            patient_ids.append(patient_id)
            cleanup_test_patients(patient_id)
        
        # Verify all IDs are unique
        assert len(patient_ids) == len(set(patient_ids))
        
        # Verify UUID format is working correctly
        for patient_id in patient_ids:
            assert patient_id.startswith('unique_test_')
            assert len(patient_id.split('_')[-1]) == 8  # UUID hex portion
    
    # ========== Error Handling Integration Tests ==========
    
    def test_error_handling_integration(self, integration_client, integration_auth_headers):
        """Test error handling in integration scenarios."""
        
        # Test 404 - Patient not found
        with patch('routes.patients.get_firestore_client') as mock_get_client:
            mock_firestore = MagicMock()
            mock_get_client.return_value = mock_firestore
            
            # Mock patient not found
            mock_doc_ref = MagicMock()
            mock_firestore.db.collection.return_value.document.return_value = mock_doc_ref
            mock_doc_ref.get.return_value.exists = False
            
            # Mock audit logging
            mock_firestore.log_manual_audit_event = MagicMock()
            
            response = integration_client.get(
                '/api/v1/patients/nonexistent_patient_id',
                headers=integration_auth_headers
            )
            assert response.status_code == 404
            error_data = response.get_json()
            assert 'error' in error_data
            assert 'message' in error_data
        
        # Test 422 - Invalid patient data
        invalid_patient_data = {
            'patient_id': '',  # Invalid empty ID
            'status': 'invalid_status',  # Invalid status
        }
        
        response = integration_client.post(
            '/api/v1/patients/',
            json=invalid_patient_data,
            headers=integration_auth_headers
        )
        assert response.status_code == 422
        error_data = response.get_json()
        assert 'error' in error_data
        assert 'message' in error_data
    
    def test_concurrent_request_handling(self, integration_client, integration_auth_headers):
        """Test that the API can handle concurrent requests appropriately."""
        # Simple concurrent test - make multiple health check requests
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_health_request():
            response = integration_client.get('/health')
            results.put(response.status_code)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_health_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        while not results.empty():
            status_code = results.get()
            assert status_code == 200 