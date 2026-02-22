from backend.logic.scoring_engine import ASAMScoringEngine

def test_scoring():
    engine = ASAMScoringEngine()
    
    # Mock progress map
    progress = {
        "D1_Q5A": 7.5, # 7.5 / 2.5 = 3.0
        "history_severe_withdrawal": "No",
        "biomedical_condition_treatment_status": "stable",
        "biomedical_conditions": "Yes", # D2 = 2.0
        "suicidal_ideation_screen": "No",
        "phq2_depression_q1_q2": "Yes", # D3 = 3.0
        "change_importance_score": 8,
        "change_confidence_score": 8,
        "past_change_attempts": "Tried meetings", # D4 = 1.0
        "environment_safety_triggers": "Yes",
        "social_support_system": "Yes", # D5 = 1.0
        "treatment_barriers": "No",
        "patient_strengths_resources": "Family support" # D6 = 1.0 - 1.0 = 0.0
    }
    
    scores = engine.calculate_dimension_scores(progress)
    print(f"Scores: {scores}")
    
    # Expected: D1=3.0, D2=2.0, D3=3.0, D4=1.0, D5=1.0, D6=0.0
    assert scores["D1"] == 3.0
    assert scores["D2"] == 2.0
    assert scores["D3"] == 3.0
    assert scores["D4"] == 1.0
    assert scores["D5"] == 1.0
    assert scores["D6"] == 0.0
    
    loc = engine.determine_level_of_care(scores)
    print(f"Level of Care: {loc}")
    
    # Overall risk calculation:
    # medical = max(3, 2) * 0.3 = 0.9
    # psych = 3 * 0.3 = 0.9
    # substance = 1 * 0.2 = 0.2
    # env = 1 * 0.15 = 0.15
    # barriers = 0 * 0.15 = 0.0
    # total = 0.9 + 0.9 + 0.2 + 0.15 + 0 = 2.15
    # 2.15 < 2.5 -> Level 1.0
    assert loc == "Level 1.0: Outpatient Therapy"
    
    # Test escalation
    progress["suicidal_ideation_screen"] = "Yes"
    scores_esc = engine.calculate_dimension_scores(progress)
    assert scores_esc["D3"] == 4.0
    loc_esc = engine.determine_level_of_care(scores_esc)
    assert loc_esc == "Level 3.7: Residential/Inpatient"
    print("All tests passed!")

if __name__ == "__main__":
    test_scoring()
