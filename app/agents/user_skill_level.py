from typing import TypedDict, Optional, List, Dict, Any
import json
from app.utils.constants import llm_invoke


def determine_user_skill_level(goal: str) -> Dict[str, str]:
    """Analyze the goal to determine user's technical skill level with detailed reasoning"""
    prompt = f"""Analyze this goal description to determine the user's technical skill level:
 
Goal: "{goal}"
 
Consider these factors:
1. Technical terminology used
2. Complexity of requirements
3. Specificity of implementation details
4. Expected sophistication of solution
 
Classify as:
- BEGINNER: Simple, non-technical language, general requests, minimal technical details
- INTERMEDIATE: Some technical aspects, specific functional needs, basic implementation details
- ADVANCED: Precise technical terms, complex requirements, detailed implementation specifics
 
Return your analysis in this exact JSON format:
{{
    "skill_level": "beginner|intermediate|advanced",
    "reason": "detailed explanation of your classification"
}}
"""
    response = llm_invoke(prompt, max_tokens=300)
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        return {"skill_level": "intermediate", "reason": "Unable to determine - defaulting to intermediate"}
   