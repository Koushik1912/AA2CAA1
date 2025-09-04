from app.agents.state import AgentState
from typing import Dict, Any

def explain_code(state: AgentState) -> Dict[str, str]:
    """Generate comprehensive code explanation and documentation"""
    
    # Get context from state
    subtasks = state.get('subtasks', [])
    goal = state.get('goal', '')
    agent_name = state.get('agent_name', 'MultiAgent')
    domain = state.get('domain', '')
    answers = state.get('follow_up_answers', {})
    file_analysis = state.get('file_analysis', [])
    
    # Generate overview
    overview = f"""
    This is a {agent_name} system designed to {goal.lower()}.
    
    The application is built using Streamlit for the user interface and LangGraph for workflow orchestration.
    It implements a multi-step agent workflow with {len(subtasks)} main processing steps.
    
    Key Features:
    - Interactive web interface with file upload capabilities
    - Multi-step workflow processing with error handling
    - Session state management and persistence
    - Real-time progress tracking and validation
    - SQLite database integration for data storage
    """
    
    # Generate architecture explanation
    architecture = f"""
    System Architecture:
    
    1. Frontend Layer (Streamlit):
       - User interface components
       - File upload and preview functionality
       - Progress tracking and status indicators
       - Interactive forms and controls
    
    2. Agent Layer (LangGraph):
       - {len(subtasks)} specialized agent functions
       - State management between processing steps
       - Conditional workflow routing
       - Error handling and recovery
    
    3. Data Layer:
       - SQLite database for persistent storage
       - Session state management
       - File processing and validation
       - Results caching and retrieval
    
    4. Integration Layer:
       - Together AI API for language model processing
       - File system operations
       - Database connections and queries
    """
    
    # Generate dependencies explanation
    dependencies = """
    Core Dependencies:
    
    - streamlit: Web application framework for the user interface
    - langgraph: Graph-based workflow orchestration
    - together: AI model API client for language processing
    - pandas: Data manipulation and analysis
    - sqlite3: Database operations and storage
    - json: Data serialization and configuration
    - typing: Type hints and annotations
    
    Optional Dependencies (based on file types):
    - openpyxl: Excel file processing
    - python-docx: Word document handling
    - PIL/Pillow: Image processing capabilities
    """
    
    # Generate components explanation
    components = f"""
    Core Components:
    
    1. AgentState (TypedDict):
       - Manages workflow state across all processing steps
       - Stores user input, validation messages, and results
       - Tracks completion status and error conditions
    
    2. Agent Functions ({len(subtasks)} functions):
    """
    
    for i, subtask in enumerate(subtasks, 1):
        components += f"""
       - agent_step_{i}: {subtask}
         * Processes step-specific requirements
         * Validates input data and handles errors
         * Returns structured results for next step
    """
    
    components += """
    3. Conditional Logic Functions:
       - Determine workflow routing between steps
       - Handle error conditions and recovery
       - Manage completion and termination states
    
    4. UI Components:
       - File upload interfaces with type validation
       - Progress tracking with visual indicators
       - Results display with expandable sections
       - Session management and reset functionality
    
    5. Database Components:
       - SQLite schema initialization
       - CRUD operations for data persistence
       - Session state backup and recovery
    """
    
    # Generate workflow explanation
    workflow_steps = []
    for i, subtask in enumerate(subtasks, 1):
        workflow_steps.append(f"Step {i}: {subtask}")
    
    workflow = f"""
    Workflow Process:
    
    Initialization:
    1. Load Streamlit interface and initialize session state
    2. Create LangGraph workflow with defined agent nodes
    3. Initialize database connections and required tables
    4. Set up file upload handlers and validation
    
    Processing Flow:
    {chr(10).join(workflow_steps)}
    
    Each step includes:
    - Input validation and preprocessing
    - AI-powered processing using Together API
    - Result validation and error handling
    - State updates and progress tracking
    - Conditional routing to next step or termination
    
    Error Handling:
    - Comprehensive try-catch blocks in each agent function
    - Graceful degradation with informative error messages
    - State preservation during error conditions
    - User-friendly error reporting and recovery options
    
    State Management:
    - Persistent session state across page refreshes
    - SQLite backup of critical workflow data
    - Progress tracking with visual indicators
    - Results caching for performance optimization
    """
    
    # Generate usage examples
    examples = f"""
    Usage Examples:
    
    1. Basic Workflow Execution:
       ```python
       # Initialize the workflow
       workflow = create_workflow()
       
       # Set up initial state
       initial_state = AgentState(
           user_input="Your input data here",
           validation_messages=[],
           workflow_complete=False,
           error_occurred=False
       )
       
       # Execute the workflow
       result = workflow.invoke(initial_state)
       ```
    
    2. File Upload Integration:
       ```python
       # Handle uploaded files
       uploaded_file = st.file_uploader("Choose file", type=['csv', 'txt'])
       if uploaded_file:
           # Process different file types
           if uploaded_file.name.endswith('.csv'):
               data = pd.read_csv(uploaded_file)
               st.session_state.file_data = data
       ```
    
    3. Database Operations:
       ```python
       # Initialize database
       conn = init_db()
       
       # Insert data
       insert_invoice(conn, product_name, category, vendor, 
                     quantity, actual_price, selling_price, invoice_date)
       
       # Retrieve data
       all_invoices = fetch_all_invoices(conn)
       ```
    
    4. Custom Agent Function:
       ```python
       def custom_agent_step(state: AgentState) -> AgentState:
           try:
               # Get input data
               input_data = state.get('user_input', '')
               
               # Process with AI
               prompt = f"Process this data: {{input_data}}"
               result = llm_invoke(prompt)
               
               # Update state
               return {{
                   **state,
                   "step_result": result,
                   "validation_messages": ["✅ Step completed"]
               }}
           except Exception as e:
               return {{
                   **state,
                   "error_occurred": True,
                   "validation_messages": [f"❌ Error: {{str(e)}}"]
               }}
       ```
    
    5. Streamlit Interface Setup:
       ```python
       # Main application entry point
       def app_main():
           st.title("🤖 {agent_name}")
           
           # File uploads
           uploaded_files = st.file_uploader("Choose files", 
                                           accept_multiple_files=True)
           
           # Input form
           with st.form("main_form"):
               user_input = st.text_area("Enter input:")
               submit = st.form_submit_button("Process")
           
           # Execute workflow
           if submit and user_input:
               workflow = create_workflow()
               result = workflow.invoke(initial_state)
       ```
    """
    
    return {
        "overview": overview.strip(),
        "architecture": architecture.strip(),
        "dependencies": dependencies.strip(),
        "components": components.strip(),
        "workflow": workflow.strip(),
        "examples": examples.strip()
    }