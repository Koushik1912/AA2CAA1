# from app.agents.state import AgentState
# from app.utils.constants import llm_invoke

# def apply_reasoning(state: AgentState) -> AgentState:
#         """Enhanced reasoning with structured approach"""
#         state = state.copy()
        
#         # Use refined objective if available
#         objective_to_reason = state.get('refine_objective', state.get('objective', ''))
        
#         prompt = f"""
#         Apply systematic reasoning to solve this objective:
        
#         **Objective**: {objective_to_reason}
#         **Sub-tasks**: {chr(10).join([f"• {task}" for task in state.get('sub_tasks', [])])}
#         **Context**: {state.get('input_analysis', '')}
        
#         Provide structured reasoning covering:
#         1. **Problem Decomposition**: How the sub-tasks address the objective
#         2. **Logical Flow**: Sequential reasoning and dependencies
#         3. **Key Considerations**: Important factors to keep in mind
#         4. **Risk Assessment**: Potential challenges and mitigation strategies
#         5. **Success Metrics**: How to evaluate the solution
#         6. **Alternative Approaches**: Other ways to tackle this problem
        
#         Focus on practical, actionable insights.
#         """
        
#         # state["reasoning"] = llm_invoke.invoke(prompt, max_tokens=1500)
#         state["current_step"] = AgentState.REASONING.value
#         return state