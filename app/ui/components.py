import json
from typing import Dict, List
from app.utils.constants import llm_invoke

def identify_ui_components(goal: str, subtasks: List[str], answers: Dict[str, str]) -> List[str]:
    """Identify required UI components based on requirements"""
    prompt = f"""Based on this goal and requirements, identify the UI components needed:
 
Goal: "{goal}"
Subtasks: {subtasks}
Requirements: {json.dumps(answers, indent=2)}
 
Consider:
- Input forms (text, numbers, dates, etc.)
- File uploaders
- Data displays (tables, charts, json)
- Progress indicators
- Result sections
- Error messages
- Reset/restart functionality
 
Return ONLY a list of components (one per line):
"""
   
    response = llm_invoke(prompt, max_tokens=250)
    components = []
    for line in response.split('\n'):
        line = line.strip()
        if line and not line.startswith(('Goal:', 'Subtasks:', 'Requirements:')):
            components.append(line)
    return components
 