import streamlit as st
import os
import streamlit as st
import os
import sqlite3
import pandas as pd
import json
import base64
from app.agents.user_skill_level import determine_user_skill_level
from app.agents.code import generate_production_code
from app.agents.subtasks import (
    classify_into_subtasks, 
    render_subtasks_for_review, 
    process_complex_subtask_modification
)
from app.agents.followup_questions import (
    render_followup_questions_with_upload,
    init_followup_db
)
from app.rag.analyse_files import analyze_file_requirements
from app.agents.explain_code import explain_code
from app.agents.api_service import APIService
# from app.agents.reasoning import apply_reasoning

# Custom CSS for modern UI with logo
def load_custom_css():
    st.markdown("""
    <style>
    /* Fixed logo in top-right corner */
    .fixed-logo {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 999999;
        padding: 6px 8px;
        border-radius: 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        
        display: flex;
        align-items: center;
        gap: 20px;
        min-width: 180px;
        max-width: 260px;
    }
    
    .fixed-logo img {
        height: 40px !important;
        width: auto !important;
        max-width: 1000px !important;
        object-fit: contain !important;
        
    }
    
    .logo-text {
        font-weight: bold;
        font-size: 36px;
        color: #4285f4;
        white-space: nowrap;
    }
    
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #4285f4 0%, #34a853 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #4285f4;
    }
    
    .upload-area {
        border: 2px dashed #dadce0;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        background: #fafbfc;
        margin: 1rem 0;
    }
    
    .workflow-button {
        background: linear-gradient(45deg, #4285f4, #34a853);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 25px;
        width: 100%;
        font-size: 16px;
        font-weight: bold;
        margin: 1rem 0;
    }
    
    .mode-selector {
        background: white;
        border: 2px solid #dadce0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .status-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    
    .active { background-color: #ea4335; }
    .inactive { background-color: #dadce0; }
    
    .api-config-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #4285f4;
    }
    </style>
    """, unsafe_allow_html=True)

def render_fixed_logo():
    """Render logo in top-right corner"""
    logo_paths = ["logo.png"]
    logo_found = False
    
    for logo_path in logo_paths:
        if os.path.exists(logo_path):
            try:
                import base64
                with open(logo_path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode()
                
                st.markdown(f"""
                    <div class="fixed-logo">
                        <img src="data:image/png;base64,{logo_data}" alt="Logo">
                    </div>
                """, unsafe_allow_html=True)
                logo_found = True
                break
            except:
                continue
    
    if not logo_found:
        st.markdown("""
            <div class="fixed-logo">
                <div class="logo-text">AAxon AI</div>
            </div>
        """, unsafe_allow_html=True)

# Initialize database functions (keeping your existing ones)
def initialize_session_database():
    """Initialize database for session management"""
    conn = sqlite3.connect('main_sessions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS main_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            stage INTEGER,
            agent_name TEXT,
            goal TEXT,
            refined_goal TEXT,
            subtasks TEXT,
            skill_level TEXT,
            uploaded_files TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def save_session_state(session_id: str):
    """Save current session state to database"""
    conn = initialize_session_database()
    cursor = conn.cursor()
    try:
        session_data = {
            'session_id': session_id,
            'stage': st.session_state.stage,
            'agent_name': st.session_state.data.get('agent_name', ''),
            'goal': st.session_state.data.get('goal', ''),
            'refined_goal': st.session_state.data.get('refined_goal', ''),
            'subtasks': json.dumps(st.session_state.data.get('subtasks', [])),
            'skill_level': st.session_state.data.get('user_skill_level', ''),
            'uploaded_files': json.dumps(st.session_state.data.get('uploaded_files', []))
        }
        
        cursor.execute('''
            INSERT OR REPLACE INTO main_sessions
            (session_id, stage, agent_name, goal, refined_goal, subtasks, skill_level, uploaded_files)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_data['session_id'],
            session_data['stage'],
            session_data['agent_name'],
            session_data['goal'],
            session_data['refined_goal'],
            session_data['subtasks'],
            session_data['skill_level'],
            session_data['uploaded_files']
        ))
        conn.commit()
        st.success(f"✅ Session saved: {session_id}")
    except Exception as e:
        st.error(f"Error saving session: {e}")
    finally:
        conn.close()

def render_subtasks_for_review(subtasks: list, goal: str, key_prefix="subtask_review"):
    """Generalized subtask editor"""
    
    st.subheader("📋 Generated Subtasks")
    
    # Show current subtasks
    for idx, task in enumerate(subtasks):
        st.write(f"{idx+1}. {task}")

    # Buttons
    col1, col2, col3 = st.columns(3)
    
    edit_clicked = col1.button("✏️ Edit", key=f"{key_prefix}_edit", use_container_width=True)
    regen_clicked = col2.button("🔄 Regenerate", key=f"{key_prefix}_regen", use_container_width=True)
    continue_clicked = col3.button("✅ Continue", key=f"{key_prefix}_continue", use_container_width=True)

    # Initialize edit state
    edit_key = f"{key_prefix}_editing"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    # Toggle edit mode
    if edit_clicked:
        st.session_state[edit_key] = True

    # Edit form
    if st.session_state[edit_key]:
        st.markdown("---")
        
        # Show examples to help users
        with st.expander("💡 **Example Modification Requests**"):
            st.markdown("""
            **Adding tasks:**
            - "Add security review after step 2"
            - "Insert database backup before step 3"
            - "Add testing phase at the end"
            
            **Removing tasks:**
            - "Remove step 3"
            - "Delete the testing step"
            - "Remove any steps about documentation"
            
            **Modifying tasks:**
            - "Make step 1 more specific about requirements gathering"
            - "Change step 2 to focus on API design"
            - "Update deployment step to use Docker"
            
            **Reordering tasks:**
            - "Move testing to be the last step"
            - "Put database design before implementation"
            - "Swap steps 2 and 3"
            """)
        
        with st.form(f"{key_prefix}_edit_form", clear_on_submit=False):
            st.subheader("🤖 Modify Subtasks")
            
            modification_text = st.text_area(
                "What changes do you want to make?",
                placeholder=" ",
                height=100,
                key=f"{key_prefix}_input"
            )
            
            col_apply, col_cancel = st.columns([1, 1])
            
            with col_apply:
                apply_clicked = st.form_submit_button("🚀 Apply Changes", type="primary")
            
            with col_cancel:
                cancel_clicked = st.form_submit_button("❌ Cancel")
            
            # Handle form submission
            if apply_clicked:
                if modification_text and modification_text.strip():
                    st.write("**🔄 Processing your request...**")
                    
                    # Process the modification
                    updated_tasks = process_complex_subtask_modification(subtasks, modification_text)
                    
                    # Check if tasks actually changed
                    if updated_tasks != subtasks:
                        st.session_state[edit_key] = False
                        st.balloons()
                        return {"action": "save", "subtasks": updated_tasks}
                    else:
                        st.error("❌ **NO CHANGES APPLIED** - see debug info above")
                else:
                    st.error("Please enter what you want to change")
            
            if cancel_clicked:
                st.session_state[edit_key] = False
                st.rerun()

    # Handle other buttons
    if regen_clicked:
        st.session_state[edit_key] = False
        return {"action": "regen"}
    elif continue_clicked:
        st.session_state[edit_key] = False
        return {"action": "continue"}
        
    return None

def render_api_design_section():
    """Render API design configuration section"""
    st.subheader("🔌 API Design Configuration")
    
    # Initialize API service if not exists
    if 'api_service' not in st.session_state:
        st.session_state.api_service = APIService()
    
    # API Configuration Section
    with st.expander("⚙️ Configure API Endpoints", expanded=True):
        api_name = st.text_input("API Name", placeholder="e.g., user_api, payment_api")
        base_url = st.text_input("Base URL", placeholder="https://api.example.com")
        api_key = st.text_input("API Key (optional)", type="password", placeholder="Bearer token or API key")
        
        # Additional headers
        st.markdown("**Additional Headers:**")
        headers_json = st.text_area(
            "Headers (JSON format)",
            placeholder='{"Content-Type": "application/json", "Custom-Header": "value"}',
            height=100
        )
        
        if st.button("Add API Configuration"):
            if api_name and base_url:
                try:
                    headers = json.loads(headers_json) if headers_json else {}
                    config = {
                        'base_url': base_url,
                        'api_key': api_key if api_key else None,
                        'headers': headers
                    }
                    st.session_state.api_service.add_api_config(api_name, config)
                    st.success(f"✅ API configuration added for {api_name}")
                except json.JSONDecodeError:
                    st.error("Invalid JSON format in headers")
            else:
                st.error("Please provide API name and base URL")
    
    # Display configured APIs
    if st.session_state.api_service.api_configs:
        st.markdown("**Configured APIs:**")
        for api_name, config in st.session_state.api_service.api_configs.items():
            with st.expander(f"📡 {api_name}"):
                st.write(f"**Base URL:** {config['base_url']}")
                st.write(f"**Has API Key:** {'Yes' if config.get('api_key') else 'No'}")
                if config.get('headers'):
                    st.write("**Headers:**")
                    st.json(config['headers'])
    
    # API Testing Section
    with st.expander("🧪 Test API Endpoints"):
        if st.session_state.api_service.api_configs:
            selected_api = st.selectbox(
                "Select API to test",
                options=list(st.session_state.api_service.api_configs.keys())
            )
            
            endpoint = st.text_input("Endpoint", placeholder="/users, /products, etc.")
            method = st.selectbox("HTTP Method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
            
            if method in ["POST", "PUT", "PATCH"]:
                request_data = st.text_area(
                    "Request Data (JSON)",
                    placeholder='{"key": "value"}',
                    height=100
                )
            else:
                request_params = st.text_area(
                    "Query Parameters (JSON)",
                    placeholder='{"param1": "value1", "param2": "value2"}',
                    height=100
                )
            
            if st.button("🚀 Test API Call"):
                try:
                    data = None
                    params = None
                    
                    if method in ["POST", "PUT", "PATCH"] and request_data:
                        data = json.loads(request_data)
                    elif method == "GET" and request_params:
                        params = json.loads(request_params)
                    
                    # This would be an async call in real implementation
                    with st.spinner("Making API request..."):
                        st.info("API testing functionality would execute here")
                        # result = await st.session_state.api_service.make_request(
                        #     selected_api, endpoint, method, data, params
                        # )
                        st.success("✅ API test completed (mock response)")
                        
                except json.JSONDecodeError:
                    st.error("Invalid JSON format in request data/parameters")
                except Exception as e:
                    st.error(f"API test failed: {str(e)}")
        else:
            st.info("No APIs configured. Add an API configuration above to test endpoints.")
    
    # Generate API Documentation
    with st.expander("📚 Generate API Documentation"):
        if st.button("Generate Documentation"):
            if st.session_state.api_service.api_configs:
                doc_content = "# API Documentation\n\n"
                
                for api_name, config in st.session_state.api_service.api_configs.items():
                    doc_content += f"## {api_name}\n\n"
                    doc_content += f"**Base URL:** `{config['base_url']}`\n\n"
                    
                    if config.get('api_key'):
                        doc_content += "**Authentication:** Bearer Token required\n\n"
                    
                    if config.get('headers'):
                        doc_content += "**Default Headers:**\n```json\n"
                        doc_content += json.dumps(config['headers'], indent=2)
                        doc_content += "\n```\n\n"
                    
                    doc_content += "**Available Endpoints:**\n"
                    doc_content += "- GET /endpoint - Description\n"
                    doc_content += "- POST /endpoint - Description\n"
                    doc_content += "- PUT /endpoint/{id} - Description\n"
                    doc_content += "- DELETE /endpoint/{id} - Description\n\n"
                
                st.markdown(doc_content)
                
                # Download button for documentation
                st.download_button(
                    label="📥 Download Documentation",
                    data=doc_content,
                    file_name="api_documentation.md",
                    mime="text/markdown"
                )
            else:
                st.info("No APIs configured to document.")

def render_sidebar():
    """Render the modern sidebar interface"""
    with st.sidebar:
        # Quick Start Section
        
        st.markdown("### 📁 Upload Files")
        # st.markdown("**Choose files to analyze**")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=['csv', 'txt', 'json', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'pdf'],
            help="Limit 200MB per file • CSV, TXT, JSON, DOCX, JPG, JPEG, PNG, GIF"
        )

        if uploaded_files:
    # Now call your analyze_file_requirements with the uploaded files
            file_analysis_results = analyze_file_requirements(answers={}, uploaded_files=uploaded_files)
            
            # Display the results
            st.write("**File Analysis Results:**")
            for result in file_analysis_results:
                st.write(f"• {result}")
        
        # if uploaded_files:
        #     st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
        #     for file in uploaded_files:
        #         st.write(f"• {file.name}")
        
        # if st.button("Browse files"):
        #     st.info("File browser would open here")
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Clear Workflow Button
        if st.button("🗑️ Clear Workflow"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def main():
    # Set page config
    st.set_page_config(
        page_title="Agentic AI Creator",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_custom_css()
    
    # Render logo in top-right corner
    render_fixed_logo()
    
    # Initialize database
    init_followup_db()
    
    # Session state initialization
    if 'stage' not in st.session_state:
        st.session_state.stage = 1
        st.session_state.data = {}
        st.session_state.session_id = f"session_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.mode = 'workflow'
    
    # Render sidebar
    render_sidebar()
    
    # Main header
    st.markdown("""
        <div class="main-header">
            <h1> Agentic AI to Create Agentic AI</h1>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.stage == 1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 Define Your Objective")
        st.markdown("**What would you like to accomplish?**")
        
        goal = st.text_area(
            "",
            placeholder="Ask Anything",
            height=120,
            help="Press Ctrl+Enter to apply"
        )
        
        if st.button("🚀 Generate Subtasks", key="start_workflow"):
            if goal.strip():
                st.session_state.data.update({
                    'domain': "AI Assistant",
                    'goal': goal.strip()
                })
                
                with st.spinner("🔍 Analyzing your objective..."):
                    skill_analysis = determine_user_skill_level(goal.strip())
                    st.session_state.data['user_skill_level'] = skill_analysis['skill_level']
                    st.session_state.data['skill_reason'] = skill_analysis['reason']
                
                with st.spinner("⚡ Generating subtasks from your objective..."):
                    try:
                        subtasks = classify_into_subtasks(goal.strip())
                        if not subtasks:
                            st.error("Failed to generate subtasks. Please try again.")
                            return
                        st.session_state.data['subtasks'] = subtasks
                        st.success(f"✅ Generated {len(subtasks)} subtasks!")
                    except Exception as e:
                        st.error(f"Error generating subtasks: {e}")
                        return
                
                st.session_state.stage = 2
                st.rerun()
            else:
                st.error("Please describe what you'd like to accomplish")
        
        # st.info("💡 Start by describing your project objective")
        # st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.stage == 2:
        # st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.header("📋 Generated Subtasks")
        
        if 'user_skill_level' in st.session_state.data:
            skill_level = st.session_state.data['user_skill_level'].upper()
            st.success(f"🔍 **Detected Skill Level:** {skill_level}")
        
        # Show original objective
        # Get current subtasks
        subtasks = st.session_state.data.get('subtasks', [])
        goal = st.session_state.data.get('goal', '')
        
        # Use the render_subtasks_for_review function
        result = render_subtasks_for_review(subtasks, goal, "stage2")
            
        # Handle button actions
        if result:
            if result["action"] == "save":
                st.session_state.data['subtasks'] = result["subtasks"]
                # if 'original_subtasks' not in st.session_state.data:
                    # st.session_state.data['original_subtasks'] = subtasks.copy()
                st.success("🎉 Subtasks have been updated!")
                # st.rerun()
                st.write("**Updated Subtasks:**")
                for i, task in enumerate(result["subtasks"], 1):
                    st.write(f"{i}. {task}")
                st.rerun()
            
            # Force rerun to show changes
            
                
            elif result["action"] == "regen":
                with st.spinner("🔄 Regenerating subtasks..."):
                    try:
                        goal = st.session_state.data.get('goal', '')
                        subtasks = classify_into_subtasks(goal)
                        st.session_state.data['subtasks'] = subtasks
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error regenerating subtasks: {e}")
            
            elif result["action"] == "continue":
                # Move to follow-up questions stage
                st.session_state.stage = 3
                st.rerun()
        
        # Back button
        if st.button("🔙 Back to Objective"):
            st.session_state.stage = 1
            st.rerun()
        
        st.info("💡 Edit your subtasks or click Continue to proceed")
        st.markdown('</div>', unsafe_allow_html=True)

    
    elif st.session_state.stage == 3:
        # Follow-up Questions Section
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Follow-up Questions")
        
        result = render_followup_questions_with_upload(
            objective=st.session_state.data.get('goal', ''),
            skill_level=st.session_state.data.get('user_skill_level', 'intermediate'),
            session_id=st.session_state.session_id
        )
        
        if result:
            st.session_state.data.update({
                'refined_goal': result['refined_objective'],
                'followup_answers': result['answers'],
                'uploaded_files': result.get('uploaded_files', []),
                'question_specific_files': result.get('question_specific_files', []),
                'database_configs': result.get('database_configs', [])
            
            })

            
            st.session_state.stage = 4
            st.rerun()
        
        
    elif st.session_state.stage == 4:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 Analysis & Code Generation")

        # Initialize states if not exists
        if 'current_analysis_tab' not in st.session_state:
            st.session_state.current_analysis_tab = 0
        if 'generated_code' not in st.session_state:
            st.session_state.generated_code = None
        if 'code_explanation' not in st.session_state:
            st.session_state.code_explanation = None
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
        if 'tool_suggestions' not in st.session_state:
            st.session_state.tool_suggestions = None

        # Create tabs for different analyses
        tabs = st.tabs([
            "🎯 Objective Analysis",
            "👤 User Skill Level",
            "📋 Subtasks Analysis", 
            "❓ Follow-up Analysis",
            "📁 File Analysis",
            "🔧 Tool Suggestions",
            # "🤔 Reasoning",
            "🔌 API Design",
            "💻 Generated Code",
            "📖 Code Explanation"
        ])

        # Objective Analysis Tab
        with tabs[0]:
            st.subheader("🎯 Project Objective")
            st.markdown("**Original Objective:**")
            st.info(st.session_state.data.get('goal', ''))
            if st.session_state.data.get('refined_goal'):
                st.markdown("**Refined Objective:**")
                st.success(st.session_state.data.get('refined_goal', ''))

        # User Skill Level Tab
        # with tabs[1]:
        #     st.subheader("👤 User Skill Level Analysis")
        #     skill_level = st.session_state.data.get('user_skill_level', 'intermediate').upper()
        #     st.success(f"**Detected Skill Level:** {skill_level}")
        #     if 'skill_reason' in st.session_state.data:
        #         with st.expander("View Analysis"):
        #             st.write(st.session_state.data['skill_reason'])

        # Subtasks Analysis Tab
        with tabs[2]:
            st.subheader("📋 Subtask Breakdown")
            subtasks = st.session_state.data.get('subtasks', [])
            for i, subtask in enumerate(subtasks, 1):
                with st.expander(f"Subtask {i}"):
                    st.markdown(f"**Task:** {subtask}")
                    st.markdown("**Dependencies:**")
                    if i > 1:
                        st.markdown(f"- Depends on Subtask {i-1}")

        # Follow-up Analysis Tab
        with tabs[3]:
            st.subheader("❓ Requirements Analysis")
            if st.session_state.data.get('followup_answers'):
                for q, a in st.session_state.data['followup_answers'].items():
                    with st.expander(f"Q: {q+1}"):
                        st.write(f"**Answer:** {a}")

        # File Analysis Tab
        with tabs[4]:
            st.subheader("📁 File Analysis")
            if not st.session_state.data.get('file_analysis'):
                with st.spinner("Analyzing file requirements..."):
                    file_analysis = analyze_file_requirements(
                        st.session_state.data.get('followup_answers', {})
                    )
                    st.session_state.data['file_analysis'] = file_analysis

            if st.session_state.data.get('uploaded_files'):
                st.markdown("**📤 Uploaded Files:**")
                for file_data in st.session_state.data['uploaded_files']:
                    with st.expander(f"📄 {file_data['filename']}"):
                        st.write(f"Type: {file_data['file_type']}")
                        st.write(f"Size: {file_data.get('file_size', 'N/A')} bytes")

            st.markdown("**📋 Required File Types:**")
            for req in st.session_state.data.get('file_analysis', []):
                st.info(req)

        # Tool Suggestions Tab
        with tabs[5]:
            st.subheader("🔧 Tool Suggestions")
            # if not st.session_state.tool_suggestions:
            #     with st.spinner("Analyzing tool requirements..."):
            #         st.session_state.tool_suggestions = suggest_tools(st.session_state.data)

            if st.session_state.tool_suggestions:
                for tool, purpose in st.session_state.tool_suggestions.items():
                    with st.expander(f"🔨 {tool}"):
                        st.write(purpose)

        # Reasoning Tab
        # with tabs[6]:
        #     st.subheader("🤔 Implementation Reasoning")
        #     if not st.session_state.analysis_results:
        #         with st.spinner("Generating analysis..."):
        #             st.session_state.analysis_results = apply_reasoning(st.session_state.data)

        #     if st.session_state.analysis_results:
        #         for section, content in st.session_state.analysis_results.items():
        #             with st.expander(section):
        #                 st.write(content)

        # API Design Tab
        with tabs[6]:
            render_api_design_section()

        # Generated Code Tab
        with tabs[7]:
            st.subheader("💻 Generated Implementation")
            if not st.session_state.generated_code:
                with st.spinner("⚡ Generating production code..."):
                    enhanced_data = st.session_state.data.copy()
                    if st.session_state.data.get('uploaded_files'):
                        enhanced_data['file_integration_required'] = True
                        enhanced_data['database_required'] = True
                        enhanced_data['file_types'] = [f['file_type'] for f in st.session_state.data['uploaded_files']]
                    st.session_state.generated_code = generate_production_code(enhanced_data)

            if st.session_state.generated_code:
                st.code(st.session_state.generated_code, language='python')
                col1, col2,col3 = st.columns(3)
                with col1:
                    st.download_button(
                        label="📥 Download Code",
                        data=st.session_state.generated_code,
                        file_name=f"{st.session_state.data.get('agent_name', 'multi_agent')}_enhanced.py",
                        mime="text/python",
                        type="primary"
                    )
                with col2:
                    session_export = {
                        'session_id': st.session_state.session_id,
                        'data': st.session_state.data,
                        'generated_code': st.session_state.generated_code
                    }
                    st.download_button(
                        label="📊 Export Session",
                        data=json.dumps(session_export, indent=2),
                        file_name=f"enhanced_session_{st.session_state.session_id}.json",
                        mime="application/json"
                    )
                with col3:
                    st.download_button(
                        label="Deploy",
                        data=st.session_state.generated_code,
                        type="primary")


        # Code Explanation Tab
        with tabs[8]:
            st.subheader("📖 Code Documentation & Explanation")
            if not st.session_state.code_explanation and st.session_state.generated_code:
                with st.spinner("Generating documentation..."):
                    st.session_state.code_explanation = explain_code(st.session_state.data)

            if st.session_state.code_explanation:
                explanation_sections = [
                    ("🎯 Overview", "overview"),
                    ("🏗️ Architecture", "architecture"),
                    ("📦 Dependencies", "dependencies"),
                    ("⚙️ Core Components", "components"),
                    ("🔄 Workflow", "workflow"),
                    ("🚀 Usage Examples", "examples")
                ]
                for section_title, section_key in explanation_sections:
                    with st.expander(section_title):
                        st.write(st.session_state.code_explanation.get(section_key, "Section content loading..."))

# # Navigation between tabs
#         st.markdown("---")
#         col1, col2, col3 = st.columns([1, 2, 1])
#         with col1:
#             if st.button("⬅️ Previous", key="prev_tab"):
#                 if st.session_state.current_analysis_tab > 0:
#                     st.session_state.current_analysis_tab -= 1
#                     st.rerun()
#         with col2:
#             st.markdown(f"**Step {st.session_state.current_analysis_tab + 1} of 10**")
#         with col3:
#             if st.button("Next ➡️", key="next_tab"):
#                 if st.session_state.current_analysis_tab < 9:
#                     st.session_state.current_analysis_tab += 1
#                     st.rerun()

        # Reset button
        with st.container():
            if st.button("🔄 Generate New System", type="secondary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()