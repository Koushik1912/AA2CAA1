from app.agents.state import AgentState
from app.rag.analyse_files import analyze_file_requirements
from app.ui.components import identify_ui_components


from app.agents.state import AgentState
from app.rag.analyse_files import analyze_file_requirements
from app.ui.components import identify_ui_components


def generate_production_code(state: AgentState) -> str:
    """
    Code generator agent.
    Generates a minimal, ready-to-run Python script with:
      - File agent for processing uploaded/mentioned files
      - Subtask execution
      - Workflow orchestration
    """

    subtasks = state.get("subtasks", [])
    answers = state.get("follow_up_answers", {})
    agent_name = state.get("agent_name", "MultiAgent")
    goal = state.get("goal", "")

    # Collect files from input + subtasks answers
    file_reqs = analyze_file_requirements(answers, goal)
    file_reqs = [
        f for f in file_reqs
        if "." in f and not f.strip().startswith("<") and " " not in f.strip()
    ]

    state_fields = [f"    step_{i+1}_result: Optional[Any]" for i in range(len(subtasks))]
    additional_fields = [
        "    user_input: Optional[str]",
        "    follow_up_answers: Optional[dict]",
        "    validation_messages: Optional[List[str]]",
        "    error_occurred: Optional[bool]",
        "    files: Optional[dict]",
    ]

    agent_functions = []
    for i, subtask in enumerate(subtasks):
        fn = f"""def agent_step_{i+1}(state: AgentState) -> AgentState:
    \"\"\"Handles: {subtask}\"\"\"
    messages = state.get("validation_messages", [])
    try:
        input_data = state.get("{'step_'+str(i)+'_result' if i > 0 else 'user_input'}", "")
        files = state.get("files", {{}})
        prompt = f\"\"\" 
        Subtask: {subtask}
        Overall Goal: {goal}
        Step {i+1}/{len(subtasks)}
        Input: {{input_data}}
        Files Available: {{list(files.keys())}}
        Requirements: {{state.get("follow_up_answers", {{}}).get("{subtask}", "No specific requirements")}}
        \"\"\"
        result = llm_invoke(prompt)
        messages.append("✅ Step {i+1} done: {subtask}")
        return {{**state, "step_{i+1}_result": result, "validation_messages": messages}}
    except Exception as e:
        messages.append(f"❌ Error in step {i+1}: {{e}}")
        return {{**state, "error_occurred": True, "validation_messages": messages}}
"""
        agent_functions.append(fn)

    workflow_edges = []
    for i in range(len(subtasks) - 1):
        workflow_edges.append(f'    wf.add_edge("step_{i+1}", "step_{i+2}")')

    final_code = f'''"""
Auto-generated agent script
Agent: {agent_name}
Goal: {goal}
"""

from typing import TypedDict, Optional, List, Any
from langgraph.graph import StateGraph, END
from together import Together

def get_together_client():
    return Together(api_key="your_api_key_here")

client = get_together_client()

def llm_invoke(prompt: str, max_tokens: int = 1024) -> str:
    try:
        resp = client.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.2
        )
        return resp.choices[0].text.strip()
    except Exception as e:
        return f"Error: {{e}}"

# File Agent
def file_agent(state: AgentState) -> AgentState:
    import pandas as pd, sqlite3, json, os
    messages = state.get("validation_messages", [])
    files = {{}}

    uploaded_files = []
    if state.get("user_input"):
        uploaded_files.extend([tok for tok in state["user_input"].split() if "." in tok])
    if state.get("follow_up_answers"):
        for ans in state["follow_up_answers"].values():
            if isinstance(ans, str):
                uploaded_files.extend([tok for tok in ans.split() if "." in tok])

    for file_path in uploaded_files:
        ext = os.path.splitext(file_path)[-1].lower()
        var_name = os.path.basename(file_path).replace(".", "_").replace(" ", "_").lower()
        try:
            if ext == ".csv":
                files[var_name] = pd.read_csv(file_path)
            elif ext in [".xlsx", ".xls"]:
                files[var_name] = pd.read_excel(file_path)
            elif ext in [".sqlite", ".db"]:
                conn = sqlite3.connect(file_path)
                files[var_name] = conn
            elif ext == ".sql":
                with open(file_path, "r") as f:
                    sql_script = f.read()
                conn = sqlite3.connect(":memory:")
                conn.executescript(sql_script)
                files[var_name] = conn
            elif ext == ".json":
                with open(file_path, "r") as f:
                    files[var_name] = json.load(f)
            elif ext in [".txt", ".md"]:
                with open(file_path, "r") as f:
                    files[var_name] = f.read()
            else:
                files[var_name] = None
            messages.append(f"📂 Loaded file: {{file_path}}")
        except Exception as e:
            messages.append(f"❌ Error loading {{file_path}}: {{e}}")

    return {{**state, "files": files, "validation_messages": messages}}

class AgentState(TypedDict):
{chr(10).join(additional_fields)}
{chr(10).join(state_fields)}

{chr(10).join(agent_functions)}

def create_workflow():
    wf = StateGraph(AgentState)
    wf.add_node("file_agent", file_agent)
{chr(10).join([f'    wf.add_node("step_{i+1}", agent_step_{i+1})' for i in range(len(subtasks))])}
    wf.set_entry_point("file_agent")
    wf.add_edge("file_agent", "step_1")
{chr(10).join(workflow_edges)}
    wf.add_edge("step_{len(subtasks)}", END)
    return wf.compile()

if __name__ == "__main__":
    state = AgentState(
        user_input="<<< PUT USER INPUT HERE >>>",
        follow_up_answers={answers},
        validation_messages=[],
        error_occurred=False,
        files={{}}{''.join([f", step_{i+1}_result=None" for i in range(len(subtasks))])}
    )
    wf = create_workflow()
    result = wf.invoke(state)
    print("\\n=== Workflow Finished ===")
    for msg in result.get("validation_messages", []):
        print(msg)
    for i in range({len(subtasks)}):
        print(f"Step {{i+1}} result:", result.get(f"step_{{i+1}}_result"))
'''

    return final_code
