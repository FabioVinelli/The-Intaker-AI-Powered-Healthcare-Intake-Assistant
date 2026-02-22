import math
from typing import Dict, List, Any

class ASAMScoringEngine:
    """
    Implements the ASAM 4th Edition scoring logic as defined in 
    Full_ASAM_Script_logic_scores_placement.txt
    """
    
    # Weights as defined in the technical project documentation 
    WEIGHTS = {
        "medical_risk": 0.3,         # Dimensions 1 & 2
        "psychological_risk": 0.3,   # Dimension 3
        "substance_use_risk": 0.2,   # Dimension 4
        "recovery_env_risk": 0.15,   # Dimension 5
        "barriers_risk": 0.15        # Dimension 6
    }

    @staticmethod
    def calculate_dimension_scores(progress_map: Dict[str, Any]) -> Dict[str, float]:
        """Calculates 0-4 risk scores for each ASAM dimension [cite: 31, 35, 118]"""
        scores = {f"D{i}": 0.0 for i in range(1, 7)}
        
        # Dimension 1: Intoxication & Withdrawal [cite: 9, 238, 201]
        intox_val = progress_map.get("D1_Q5A", 0)
        # Normalize 0-10 self-report to 0-4 scale if numeric
        try:
            intox_score = float(intox_val) / 2.5
        except (ValueError, TypeError):
            intox_score = 0.0
            
        # Check for critical intoxication (EP004 logic)
        if progress_map.get("critical_intoxication") == "Yes":
            intox_score = 4.0

        withdrawal_score = 0.0
        if progress_map.get("history_severe_withdrawal") == "Yes" or progress_map.get("critical_withdrawal") == "Yes":
            withdrawal_score = 4.0
        elif progress_map.get("withdrawal_symptoms_self_report"):
            # Simple heuristic for severe symptoms if reported
            withdrawal_score = 3.0
            
        scores["D1"] = max(intox_score, withdrawal_score, float(progress_map.get("D1_score", 0)))

        # Dimension 2: Biomedical [cite: 36, 248, 292]
        d2_risk = 0.0
        if progress_map.get("biomedical_condition_treatment_status") == "unstable":
            d2_risk = 4.0
        elif progress_map.get("biomedical_conditions") == "Yes":
            d2_risk = 2.0 # Moderate default if conditions exist
            
        if progress_map.get("pregnancy_status") == "Yes":
            d2_risk = min(4.0, d2_risk + 1.0)
            
        scores["D2"] = max(d2_risk, float(progress_map.get("D2_score", 0)))
        
        # Dimension 3: EBC (Mental Health) [cite: 53, 264, 401]
        d3_risk = 0.0
        if progress_map.get("suicidal_ideation_screen") == "Yes" or progress_map.get("psychosis_screen") == "Yes":
            d3_risk = 4.0
        elif progress_map.get("phq2_depression_q1_q2") == "Yes" or progress_map.get("trauma_history_screen") == "Yes":
            d3_risk = 3.0
        
        if progress_map.get("cognitive_functioning_screen") == "Yes":
            d3_risk = min(4.0, d3_risk + 1.0)
            
        scores["D3"] = max(d3_risk, float(progress_map.get("D3_score", 0)))

        # Dimension 4: Readiness to Change [cite: 471-480]
        importance = float(progress_map.get("change_importance_score", 0))
        confidence = float(progress_map.get("change_confidence_score", 0))
        
        if importance > 7 and confidence > 7 and progress_map.get("past_change_attempts"):
            d4_risk = 1.0
        elif importance > 5:
            d4_risk = 2.0
        else:
            d4_risk = 4.0 # Low readiness
            
        if progress_map.get("risky_behaviors_substance_use") == "Yes":
            d4_risk = min(4.0, d4_risk + 1.0)
            
        scores["D4"] = d4_risk

        # Dimension 5: Recovery Environment [cite: 550-559]
        safety = progress_map.get("environment_safety_triggers")
        support = progress_map.get("social_support_system")
        
        if safety == "unsafe_imminent_danger" or (safety == "No" and support == "No"):
            d5_risk = 4.0
        elif safety == "No" or support == "No" or progress_map.get("life_stressors_recovery") == "Yes":
            d5_risk = 3.0
        elif safety == "Yes" and support == "Yes":
            d5_risk = 1.0
        else:
            d5_risk = 2.0
            
        scores["D5"] = d5_risk

        # Dimension 6: Barriers and Preferences [cite: 632-633]
        barriers = progress_map.get("treatment_barriers")
        if barriers == "Yes": # Simple check if barriers endorsed
            d6_risk = 3.0
        else:
            d6_risk = 1.0
            
        if progress_map.get("patient_strengths_resources"):
            d6_risk = max(0.0, d6_risk - 1.0)
            
        scores["D6"] = d6_risk
        
        return scores

    def determine_level_of_care(self, scores: Dict[str, float]) -> str:
        """Determines placement using the overall risk score logic [cite: 209]"""
        # Weighted aggregate score 
        overall_risk = (
            (max(scores["D1"], scores["D2"]) * self.WEIGHTS["medical_risk"]) +
            (scores["D3"] * self.WEIGHTS["psychological_risk"]) +
            (scores["D4"] * self.WEIGHTS["substance_use_risk"]) +
            (scores["D5"] * self.WEIGHTS["recovery_env_risk"]) +
            (scores["D6"] * self.WEIGHTS["barriers_risk"])
        )

        # ASAM Placement Logic [cite: 118, 209, 210]
        if overall_risk >= 3.5 or max(scores.values()) >= 4:
            return "Level 3.7: Residential/Inpatient"
        elif overall_risk >= 3.0:
            return "Level 2.5: High-Intensity Outpatient"
        elif overall_risk >= 2.5:
            return "Level 2.1: Intensive Outpatient"
        else:
            return "Level 1.0: Outpatient Therapy"
