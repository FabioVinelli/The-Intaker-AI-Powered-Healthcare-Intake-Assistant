import unittest
import sys
import os

# Ensure we can import the package
# We need to add the project root to sys.path
# Current file: services/scoring_engine/tests/test_golden_set.py
# Root is 3 levels up: ../../../
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from services.scoring_engine import score_transcript, calculate_severity, Dimension

class TestGoldenSet(unittest.TestCase):
    
    def test_case_1_withdrawal(self):
        """Test Case 1: Input 'I am shaking and throwing up.' -> Assert D1 >= 2."""
        text = "I am shaking and throwing up."
        result = score_transcript(text)
        d1_score = result['scores'][Dimension.D1.value]
        
        self.assertGreaterEqual(d1_score, 2, "D1 score should be >= 2 for shaking/throwing up")
        
    def test_case_2_homelessness_barriers(self):
        """Test Case 2: Input 'I live in my car.' -> Assert D6 >= 3."""
        text = "I live in my car."
        result = score_transcript(text)
        d6_score = result['scores'][Dimension.D6.value]
        
        # Note: We mapped "live in my car" to D6 per prompt instructions
        self.assertGreaterEqual(d6_score, 3, "D6 score should be >= 3 for homelessness")
        
    def test_suicidal_ideation(self):
        """Test explicit high risk trigger: Suicidal."""
        text = "I am feeling suicidal and might kill myself."
        result = score_transcript(text)
        d3_score = result['scores'][Dimension.D3.value]
        loc = result['level_of_care']
        
        self.assertEqual(d3_score, 4, "Suicidal intent should be score 4")
        self.assertIn("Residential", loc, "Score 4 should trigger Residential/Inpatient")
        
    def test_medical_risk(self):
        """Test medical keywords."""
        text = "I have diabetes and it is unstable."
        result = score_transcript(text)
        d2_score = result['scores'][Dimension.D2.value]
        
        self.assertEqual(d2_score, 4, "Unstable medical condition should be score 4")

    def test_clean_case(self):
        """Test no keywords."""
        text = "I am fine. I have a job and a house."
        result = score_transcript(text)
        # Should be all zeros? 
        # 'job' might not trigger positive keywords, 'house' neither if we only scan for negative strings.
        # This confirms 'default' is 0.
        for dim, score in result['scores'].items():
            self.assertEqual(score, 0)
        self.assertIn("Level 1.0", result['level_of_care'])

if __name__ == '__main__':
    unittest.main()
