from typing import TypedDict, Optional, List, Dict


# Simplified State definition
class AgentState(TypedDict):
    agent_name: Optional[str]
    domain: Optional[str]
    goal: Optional[str]
    subtasks: Optional[List[str]]
    current_subtask_index: Optional[int]
    follow_up_answers: Optional[Dict[str, str]]
    tools_to_use: Optional[Dict[str, str]]
    file_requirements: Optional[List[str]]
    ui_components: Optional[List[str]]
    conditional_logic: Optional[List[str]]
    final_code: Optional[str]
    explanation: Optional[str]
    user_skill_level: Optional[str]  # Added to track user skill level
 