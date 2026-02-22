from .scorer import calculate_severity
from .loc_rules import determine_loc
from .asam_schema import Dimension, Severity

def score_transcript(transcript: str) -> dict:
    """
    Analyzes a version of the conversation transcript and returns 
    ASAM Dimension scores and a Level of Care recommendation.
    """
    # 1. Calculate Severity Scores per Dimension
    scores_map = calculate_severity(transcript)
    
    # 2. Determine Level of Care
    loc = determine_loc(scores_map)
    
    # 3. Format Output
    return {
        "scores": {dim.value: score for dim, score in scores_map.items()},
        "level_of_care": loc
    }
