from app.utils.constants import llm_invoke

def suggest_enhanced_tools(subtask: str, answers: str, subtask_index: int) -> str:
    """Suggest appropriate tools with explanations"""
    prompt = f"""Suggest 2-3 most appropriate tools for this subtask:
 
Subtask #{subtask_index + 1}: "{subtask}"
Requirements: "{answers}"
 
Choose from: pandas, numpy, requests, openai, langchain, streamlit, sqlite3, plotly,
re (regex), json, csv, openpyxl, pillow, scikit-learn, tensorflow, pytorch
 
Format:
**Tool Name** - Brief explanation of why it's needed for this subtask
"""
   
    return llm_invoke(prompt, max_tokens=200)
