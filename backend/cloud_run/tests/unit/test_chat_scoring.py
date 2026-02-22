import unittest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from backend.cloud_run.routes.chat import chat_bp

class TestChatScoring(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(chat_bp)
        self.app.encryption_service = Mock()
        # Mock encryption to return ENCRYPTED_ prefix for testing
        def mock_encrypt(eval_data):
            return {k: f"ENCRYPTED_{v}" for k, v in eval_data.items()}
        self.app.encryption_service.encrypt_clinical_evaluation.side_effect = mock_encrypt
        self.app.config['TESTING'] = True
        import os
        os.environ['DISABLE_AUTH_FOR_TESTING'] = 'true'
        os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project'
        self.client = self.app.test_client()

    @patch('backend.cloud_run.routes.chat.get_current_user_id')
    @patch('backend.cloud_run.routes.chat.get_firestore_db')
    @patch('backend.cloud_run.routes.chat.fetch_active_script')
    @patch('backend.cloud_run.routes.chat.GenerativeModel')
    def test_chat_emergency_stop_suicidal(self, mock_model, mock_fetch_script, mock_db, mock_user_id):
        """Test that D3 >= 4.0 triggers an emergency stop."""
        mock_user_id.return_value = 'test-user'
        
        # Mock Firestore
        mock_ref = MagicMock()
        mock_db.return_value.collection.return_value.document.return_value = mock_ref
        
        # Mock session data with suicidal ideation
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'progress_map': {'suicidal_ideation_screen': 'Yes'}
        }
        mock_ref.get.return_value = mock_doc
        
        # Send message that would trigger scoring update
        response = self.client.post('/api/v1/chat/message', 
                                  json={'content': '[INTAKE_DATA: suicidal_ideation_screen=Yes]', 'session_id': 'sess-123'},
                                  headers={'Authorization': 'Bearer test-token'})
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['emergency_stop'])
        self.assertIn("concerned about your safety", data['response'])
        
        # Ensure Gemini was NOT called
        mock_model.assert_not_called()

    @patch('backend.cloud_run.routes.chat.get_current_user_id')
    @patch('backend.cloud_run.routes.chat.get_firestore_db')
    @patch('backend.cloud_run.routes.chat.fetch_active_script')
    @patch('backend.cloud_run.routes.chat.GenerativeModel')
    def test_chat_scoring_encryption(self, mock_model, mock_fetch_script, mock_db, mock_user_id):
        """Test that clinical evaluation is encrypted and stored."""
        mock_user_id.return_value = 'test-user'
        
        # Mock Firestore
        mock_ref = MagicMock()
        mock_db.return_value.collection.return_value.document.return_value = mock_ref
        
        # Mock session data (moderate risk)
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'progress_map': {'D1_Q5A': 8} # D1 = 3.2
        }
        mock_ref.get.return_value = mock_doc
        
        # Mock Script and Gemini
        mock_fetch_script.return_value = MagicMock()
        mock_instance = mock_model.return_value
        mock_chat = mock_instance.start_chat.return_value
        mock_chat.send_message.return_value = MagicMock(text="Hello")
        
        # Send message
        response = self.client.post('/api/v1/chat/message', 
                                  json={'content': '[INTAKE_DATA: D1_Q5A=8]', 'session_id': 'sess-456'})
        
        self.assertEqual(response.status_code, 200)
        
        # Verify update called with clinical_evaluation
        update_calls = mock_ref.update.call_args_list
        eval_call = [call for call in update_calls if 'clinical_evaluation' in call[0][0]]
        self.assertTrue(len(eval_call) > 0)
        
        encrypted_eval = eval_call[0][0][0]['clinical_evaluation']
        self.assertTrue(encrypted_eval['scores'].startswith('ENCRYPTED_'))
        self.assertTrue(encrypted_eval['level_of_care'].startswith('ENCRYPTED_'))

if __name__ == '__main__':
    unittest.main()
