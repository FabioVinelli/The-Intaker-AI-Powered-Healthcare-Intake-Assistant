from .asam_schema import Dimension, Severity

# Scoring Rules derived from "The Intaker - Comprehensive Documentation" and "Full_ASAM_Script"
# Maps keywords/phrases to (Dimension, Severity Score)
SCORING_RULES = {
    # D1 - Intoxication/Withdrawal
    "shaking": (Dimension.D1, 2),
    "tremors": (Dimension.D1, 2),
    "sweating": (Dimension.D1, 2),
    "nausea": (Dimension.D1, 2),
    "vomiting": (Dimension.D1, 2),
    "throwing up": (Dimension.D1, 2),
    "seizure": (Dimension.D1, 4),
    "seizures": (Dimension.D1, 4),
    "hallucinations": (Dimension.D1, 4),
    "hallucinating": (Dimension.D1, 4),
    "delirium": (Dimension.D1, 4),
    "blackout": (Dimension.D1, 3),
    
    # D2 - Biomedical
    "diabetes": (Dimension.D2, 2),
    "heart disease": (Dimension.D2, 2),
    "liver": (Dimension.D2, 3),
    "pregnant": (Dimension.D2, 3), # High risk potential
    "infection": (Dimension.D2, 2),
    "chronic pain": (Dimension.D2, 2),
    "unstable": (Dimension.D2, 4), # Generic medical
    
    # D3 - Emotional/Behavioral
    "suicidal": (Dimension.D3, 4),
    "suicide": (Dimension.D3, 4),
    "kill myself": (Dimension.D3, 4),
    "hurt myself": (Dimension.D3, 3),
    "better off dead": (Dimension.D3, 3),
    "depressed": (Dimension.D3, 2),
    "anxiety": (Dimension.D3, 2),
    "panic": (Dimension.D3, 2),
    "voices": (Dimension.D3, 4),
    "hearing voices": (Dimension.D3, 4),
    "psychosis": (Dimension.D3, 4),
    
    # D4 - Readiness (Keywords for low readiness/high risk)
    "don't want help": (Dimension.D4, 4),
    "forced": (Dimension.D4, 3),
    "court ordered": (Dimension.D4, 2), # Often correlates with lower internal motivation initially
    "not ready": (Dimension.D4, 3),
    "denial": (Dimension.D4, 4),
    
    # D5 - Relapse/Environment 
    "unsafe": (Dimension.D5, 4),
    "danger": (Dimension.D5, 4),
    "violence": (Dimension.D5, 4),
    "abusive": (Dimension.D5, 4),
    "triggers": (Dimension.D5, 2),
    
    # D6 - Barriers (and Housing in this schema per prompt example)
    "homeless": (Dimension.D6, 3),
    "live in my car": (Dimension.D6, 3),
    "no money": (Dimension.D6, 3),
    "financial": (Dimension.D6, 2),
    "transportation": (Dimension.D6, 2),
    "no job": (Dimension.D6, 2),
}

def calculate_severity(transcript: str) -> dict[Dimension, int]:
    """
    Deterministically maps transcript text to ASAM Dimension Scores (0-4).
    """
    # Initialize all dimensions to 0 (None)
    scores = {d: 0 for d in Dimension}
    
    transcript_lower = transcript.lower()
    
    # Check for keywords and update max score for that dimension
    for phrase, (dim, score) in SCORING_RULES.items():
        if phrase in transcript_lower:
            if score > scores[dim]:
                scores[dim] = score
                
    return scores
