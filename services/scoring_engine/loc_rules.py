from typing import Dict, Optional
from .asam_schema import Dimension

def determine_loc(scores: Dict[Dimension, int]) -> str:
    """
    Determines Level of Care based on ASAM Dimension Scores.
    Source Logic: Full_ASAM_Script_logic_scores_placement.txt
    
    Pseudocode from source:
      if overall_risk_score >= 3.5: Level 3.7 (Residential/Inpatient)
      elif overall_risk_score >= 3.0: Level 2.5 (High-Intensity Outpatient)
      elif overall_risk_score >= 2.5: Level 2.1 (Intensive Outpatient)
      else: Level 1.0 (Outpatient Therapy)
      
    Interpretation for Integer Scores:
      - Score 4 satisfies >= 3.5 -> Level 3.7
      - Score 3 satisfies >= 3.0 -> Level 2.5
      - Score 2:
        - Strictly < 2.5, which would map to Level 1.0.
        - However, clinical standard usually places Score 2 (Moderate Risk) in IOP (Level 2.1).
        - AND User Prompt says "If max(scores) <= 1, suggest Outpatient", implying Score 2 should be > Level 1.
        - Therefore, we map Score 2 to Level 2.1 to align with Prompt constraints + Clinical prudence.
      - Score 0-1 -> Level 1.0
    """
    if not scores:
        return "Level 1.0 (Outpatient Therapy)"

    # Calculate overall risk as the maximum single dimension score
    # (Standard ASAM Multidimensional Assessment typically places based on highest severity need)
    overall_risk_score = max(scores.values())
    
    if overall_risk_score >= 4:
        # Meets >= 3.5 criteria
        return "Level 3.7 (Residential/Inpatient)"
    
    elif overall_risk_score >= 3:
        # Meets >= 3.0 criteria
        return "Level 2.5 (High-Intensity Outpatient)"
        
    elif overall_risk_score >= 2:
        # Adjusted to meet User Prompt constraint (<=1 is Outpatient)
        return "Level 2.1 (Intensive Outpatient)"
        
    else:
        # Scores 0, 1
        return "Level 1.0 (Outpatient Therapy)"
