
import streamlit as st
import re
from app.utils.constants import llm_invoke

def process_complex_subtask_modification(current_tasks: list, user_request: str) -> list:
    """Enhanced conversational subtask modification"""
    
    # Enhanced conversational prompt for LLM
    prompt = f"""You are an intelligent assistant responsible for modifying a list of subtasks based on user instructions.

The user may express their wishes in natural language, in various forms.

Possible commands include adding, removing, editing, or reordering subtasks.

Examples of natural requests:
- "Add a new step: Implement security audit after step 3"
- "Remove step 2"
- "Please change step 1 to focus on data validation"  
- "Insert a new subtask between steps 4 and 5: Conduct code review"
- "I want to include streamlit visualization at the end"
- "Can you add data testing before the final step?"
- "Delete the last step"
your task : if the user ask to add the step , then always Read the user's input, understand their intent ,add the step in existing subtasks and return the updated list by adding the step in existing subtasks
your task : if the user ask to remove the step , then always Read the user's input, understand their intent remove the step in existing subtasks and return the updated list by removing the step in existing subtasks
your task : if the user ask to modify the step , then always Read the user's input, understand their intent modify the step in existing subtasks and return the updated list by modifying the step in existing subtasks
Your task: Read the user's input, understand their intent, and return ONLY the updated numbered list of subtasks.

Current subtasks:
{chr(10).join([f"{i+1}. {task}" for i, task in enumerate(current_tasks)])}

User request: {user_request}

Return only the updated numbered subtask list:"""

    try:
        response = llm_invoke(prompt, max_tokens=500, temperature=0.6)
        
        # Parse the response to extract subtasks
        updated_tasks = []
        for line in response.split('\n'):
            line = line.strip()
            if re.match(r'^\d+\.\s', line):
                task = re.sub(r'^\d+\.\s*', '', line).strip()
                if task:
                    updated_tasks.append(task)

        if updated_tasks and len(updated_tasks) > 0:
            if "remove" in user_request.lower():
                if len(updated_tasks) < len(current_tasks):
                    st.success(f"✅ Removed tasks: {len(current_tasks)} → {len(updated_tasks)} tasks")
                    return updated_tasks
                else:
                    st.warning("Remove operation didn't reduce task count")
                    return current_tasks
            else:
                # For other operations, allow same or different count
                if updated_tasks != current_tasks:
                    st.success(f"✅ Updated subtasks based on your request!")
                    return updated_tasks
                else:
                    st.warning("No changes detected in the updated list")
                    return current_tasks
        else:
            st.error("Could not parse updated tasks from LLM response")
            return current_tasks
            
    except Exception as e:
        st.error(f"Error processing request: {str(e)}")
        return current_tasks
    #         st.success(f"✅ Updated subtasks based on your request!")
    #         return updated_tasks
    #     else:
    #         st.warning("Could not understand the request. Try being more specific.")
    #         return current_tasks
            
    # except Exception as e:
    #     st.error(f"Error processing request: {str(e)}")
    #     return current_tasks



def render_subtasks_for_review(subtasks: list, goal: str, key_prefix="subtask_review"):
    """Simple working subtask editor"""
    
    st.subheader("🔍 Generated Subtasks")
    for idx, task in enumerate(subtasks):
        st.write(f"{idx+1}. {task}")

    # Three buttons
    col1, col2, col3 = st.columns(3)
    
    edit_clicked = col1.button("✏️ Edit", key=f"{key_prefix}_edit", use_container_width=True)
    # regen_clicked = col2.button("🔄 Regenerate", key=f"{key_prefix}_regen", use_container_width=True)
    continue_clicked = col3.button("✅ Continue", key=f"{key_prefix}_continue", use_container_width=True)

    edit_key = f"{key_prefix}_editing"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False
    # Edit mode
    if edit_clicked:
        st.session_state[edit_key] = True

    # Edit form
    if st.session_state[edit_key]:
        st.markdown("---")
        
        with st.form(f"{key_prefix}_edit_form", clear_on_submit=False):
            st.subheader("🤖 Modify Subtasks")
            
            modification_text = st.text_area(
                "What changes do you want?",
                placeholder="Examples:\n- Remove step 3\n- Add security check after step 2\n- Make step 1 more specific",
                height=100,
                key=f"{key_prefix}_input"
            
            )
            
            col_submit, col_cancel = st.columns([1, 1])
            with process_complex_subtask_modification:
                apply_clicked = st.form_submit_button("🚀 Apply Changes", type="primary")
            
            with col_cancel:
                cancel_clicked = st.form_submit_button("❌ Cancel")
            
            # Handle form submission
            if apply_clicked:
                if modification_text and modification_text.strip():
                    st.write("**🔄 Processing your request...**")
                    updated_tasks = process_complex_subtask_modification(subtasks, modification_text)
                    
                    # Check if tasks actually changed
                    if updated_tasks != subtasks:
                        st.session_state[edit_key] = False
                        st.balloons()
                        return {"action": "save", "subtasks": updated_tasks}
                    else:
                        st.error("❌ **NO CHANGES APPLIED**")
                else:
                    st.error("Please enter what you want to change")
            
            if cancel_clicked:
                st.session_state[edit_key] = False
                st.rerun()
    
        
    return None            

def classify_into_subtasks(objective: str) -> list:
    """Generate initial subtasks based on user objective"""
    
    uploaded_files = st.session_state.get('uploaded_files', [])
    file_context = ""
    
    if uploaded_files:
        file_info = []
        for file_data in uploaded_files:
            file_info.append(f"- {file_data.name}: {file_data.read().decode()[:300]}...")
        file_context = f"\n\nUPLOADED FILES CONTEXT:\n" + "\n".join(file_info)

    prompt = f"""You are an expert project manager. Break down this objective into exactly 4-5 specific, actionable subtasks.

PROJECT OBJECTIVE: {objective}

{file_context}

REQUIREMENTS:
- Each subtask should be specific and implementable
- Use clear, technical language appropriate for the domain  
- Focus on concrete development/implementation steps
- Maintain logical sequence and dependencies
- Return as a clean numbered list

SUBTASKS FOR THIS OBJECTIVE:"""

    try:
        # 🔍 DEBUG: Print the prompt being sent
        # st.write("**DEBUG - Prompt sent to LLM:**")
        st.text(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        
        response = llm_invoke(prompt, max_tokens=800, temperature=0.2)  # Increased tokens
        
        # 🔍 DEBUG: Print raw LLM response  
        # st.write("**DEBUG - Raw LLM Response:**")
        st.text(f"Response length: {len(response) if response else 0}")
        st.text(response if response else "EMPTY RESPONSE!")
        
        if not response or len(response.strip()) < 10:
            st.error("❌ LLM returned empty or very short response!")
            return _get_domain_specific_fallback(objective)

        # Parse numbered list
        tasks = []
        for line in response.split('\n'):
            line = line.strip()
            if line and re.match(r'^\d+\.\s', line):
                task = re.sub(r'^\d+\.\s*', '', line).strip()
                if task and len(task) > 10:
                    tasks.append(task)

        if len(tasks) >= 3:
            st.success(f"✅ Generated {len(tasks)} custom subtasks")
            return tasks[:5]
        else:
            st.warning("⚠️ LLM generated too few tasks, using fallback")
            return _get_domain_specific_fallback(objective)
            
    except Exception as e:
        st.error(f"❌ Error generating subtasks: {e}")
        return _get_domain_specific_fallback(objective)

# def classify_into_subtasks(objective: str) -> list:
#     """Generate initial subtasks based on user objective"""
#     uploaded_files = st.session_state.get('uploaded_files', [])
    
#     file_context = ""
#     if uploaded_files:
#         file_info = []
#         for file_data in uploaded_files:
#             file_info.append(f"- {file_data.name}: {file_data.read().decode()[:300]}...")
#         file_context = f"\n\nUPLOADED FILES CONTEXT:\n" + "\n".join(file_info)
    
#     prompt = f"""You are an expert project manager. Break down this objective into exactly 4-5 specific, actionable subtasks.

# PROJECT OBJECTIVE: {objective}
# {file_context}

# REQUIREMENTS:
# - understand the domain and context from the objective
# - Consider any uploaded files for context and then generate the subtask based on objective and uploaded files
# - Each subtask should be specific and implementable
# - Use clear, technical language appropriate for the domain
# - Focus on concrete development/implementation steps
# - Maintain logical sequence and dependencies
# - Return as a clean numbered list

# EXAMPLE FORMAT:
# 1. Analyze requirements and define system specifications
# 2. Design architecture and data models
# 3. Implement core functionality and business logic
# 4. Create user interface and interaction components
# 5. Deploy, test and optimize the system

# SUBTASKS FOR THIS OBJECTIVE:"""

#     try:
#         response = llm_invoke(prompt, max_tokens=500, temperature=0.2)
        
#         if not response:
#             return []
        
#         # Parse numbered list
#         tasks = []
#         for line in response.split('\n'):
#             line = line.strip()
#             if line and re.match(r'^\d+\.\s', line):
#                 task = re.sub(r'^\d+\.\s*', '', line).strip()
#                 if task and len(task) > 10:
#                     tasks.append(task)
        
#         # Return 4-5 quality tasks
#         if len(tasks) >= 3:
#             return tasks[:5]
#         else:
#             # Domain-specific fallback based on objective
#             return _get_domain_specific_fallback(objective)
            
#     except Exception as e:
#         print(f"Error generating subtasks: {e}")
#         return _get_domain_specific_fallback(objective)

def _get_domain_specific_fallback(objective: str) -> list:
    """Generate domain-specific fallback subtasks"""
    obj_lower = objective.lower()
    
    if any(term in obj_lower for term in ['invoice', 'payment', 'financial', 'revenue', 'vendor']):
        return [
            "Analyze invoice processing requirements and data sources",
            "Design database schema for vendors, payments, and products", 
            "Implement invoice parsing and data extraction logic",
            "Create reporting dashboard and analytics features",
            "Deploy system with automated workflows and notifications"
        ]
    elif any(term in obj_lower for term in ['ai', 'ml', 'agent', 'model']):
        return [
            "Define AI/ML requirements and data sources",
            "Design system architecture and agent workflow",
            "Implement core AI/ML processing logic", 
            "Create user interface and interaction layer",
            "Deploy, test and optimize the system"
        ]
    else:
        return [
            "Analyze project requirements and scope",
            "Design system architecture and data flow",
            "Implement core functionality and features",
            "Add testing, validation and error handling", 
            "Deploy, document and optimize the system"
        ]
