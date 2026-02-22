
import os
import logging
from typing import Dict, Any
from google import genai
from dotenv import load_dotenv

# Load environment variables (relevant if running standalone or testing)
load_dotenv()

logger = logging.getLogger("treatment-planner")

def create_plan_from_scores(scores: Dict[Any, int], loc: str) -> str:
    """
    Generates a compassionate, 1-page treatment plan summary using Gemini Flash.
    
    Args:
        scores: Dictionary of ASAM Dimension scores (Dimension Enum -> int)
        loc: Level of Care string
        
    Returns:
        Markdown string containing the treatment plan.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not found. Using MOCK PLAN for testing.")
        return f"""# Treatment Plan (MOCK)
**Based on ASAM Scores:** {scores}
**Level of Care:** {loc}

## Drivers
- Identified withdrawal symptoms (Tremors).
- High risk indicators.

## Goals
1. Stabilize physical symptoms.
2. Ensure safety.

## Action Items
- Admit to {loc}.
- Monitor vitals.
"""

    try:
        client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
        
        # Format scores for the prompt (Handle Enum keys if present)
        scores_text = "\n".join([f"{str(k)}: {v}" for k, v in scores.items()])
        
        prompt = f"""
You are a clinical assistant. transform these ASAM scores [DATA] into a compassionate, 1-page treatment plan summary. 
Structure: Drivers -> Goals -> Action Items.

[DATA]
ASAM Dimension Scores:
{scores_text}

Recommended Level of Care:
{loc}
"""
        
        # Use Gemini Flash for speed and cost effectiveness
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp", # Using Flash as requested
                contents=prompt
            )
            if response and response.text:
                return response.text
            return "Error: Empty response from plan generator."
        except Exception as api_error:
            logger.warning(f"Gemini API Error (likely quota): {api_error}. Returning FALLBACK plan.")
            return f"""# Treatment Plan (FALLBACK)
**Based on ASAM Scores:** (See JSON data)
**Level of Care:** {loc}

## Drivers
- Clinical indications found in transcript.
- Immediate safety or medical concerns addressed.

## Goals
1. Stabilize acute symptoms.
2. Engage in {loc} services.

## Action Items
- Complete administrative intake.
- Schedule nurse assessment.
- (Generated via fallback due to API constraints)
"""
            
    except Exception as e:
        logger.error(f"Plan generation failed: {e}")
        return f"Error: Plan generation failed due to {str(e)}"
