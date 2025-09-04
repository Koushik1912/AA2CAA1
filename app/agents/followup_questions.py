from app.utils.constants import llm_invoke
from typing import List, Dict, Any
import re
import logging
import streamlit as st
import sqlite3
import pandas as pd
import json
import os
from io import StringIO

logger = logging.getLogger(__name__)

def handle_errors():
    """Decorator for error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                return kwargs.get('default', {})
        return wrapper
    return decorator

def format_db_display(db_config):
    """Format database configuration display string properly"""
    if not db_config or not isinstance(db_config, dict):
        return "No database configured"
    
    db_type = db_config.get('type', '').lower().strip()
    
    # Skip if no type or explicitly none
    if not db_type or db_type == 'none':
        return "No database configured"
    
    if db_type == 'sqlite':
        database = db_config.get('database', '').strip()
        if database:
            return f"SQLite: {database}"
        else:
            return "SQLite: (no file specified)"
    
    elif db_type in ['mysql', 'postgresql']:
        user = db_config.get('user', '').strip()
        host = db_config.get('host', '').strip()
        port = db_config.get('port', '').strip()
        database = db_config.get('database', '').strip()
        
        # Check if we have complete configuration
        if all([user, host, port, database]):
            return f"{db_type.upper()}: {user}@{host}:{port}/{database}"
        else:
            return f"{db_type.upper()}: (incomplete configuration)"
    
    return f"Unknown DB ({db_type})"

def get_skill_based_question_template(skill_level: str) -> str:
    """Return appropriate question templates based on user skill level"""
    templates = {
        "beginner": (
            "Ask simple, non-technical questions focused on:\n"
            "- What the system should do in plain language\n"
            "- Basic inputs and expected outputs\n"
            "- Simple examples of desired behavior\n"
            "Avoid technical jargon and focus on user goals"
        ),
        "intermediate": (
            "Ask balanced questions that cover:\n"
            "- Functional requirements\n"
            "- Basic technical considerations\n"
            "- Expected behavior in different scenarios\n"
            "- Simple validation rules\n"
            "Use some technical terms but explain when needed"
        ),
        "advanced": (
            "Ask detailed technical questions about:\n"
            "- Specific implementation requirements\n"
            "- Technical constraints and edge cases\n"
            "- Performance considerations\n"
            "- Integration requirements\n"
            "- Advanced error handling\n"
            "Use precise technical terminology"
        ),
    }
    
    return templates.get(skill_level.lower(), templates["intermediate"])

def get_default_questions(skill_level: str) -> List[str]:
    """Return exactly 5 default questions based on skill level"""
    defaults = {
        "beginner": [
            "What is the primary use case or problem you're trying to solve?",
            "Who will be using this system and how?",
            "What should the system do when it works correctly?",
            "Do you have any constraints in terms of time, resources, or environment?",
            "How will you measure success for this project?"
        ],
        "intermediate": [
            "What are the core functional requirements and success criteria?",
            "What technologies, frameworks, or architectural patterns do you prefer?",
            "What are the main constraints, limitations, or non-functional requirements?",
            "Who are the target users and what are their key needs?",
            "What performance, scalability, or integration requirements exist?"
        ],
        "advanced": [
            "What are the detailed technical specifications and architectural requirements?",
            "What design patterns, frameworks, and implementation constraints should be followed?",
            "What are the specific performance, security, compliance, and scalability requirements?",
            "How should monitoring, logging, error handling, and deployment be implemented?",
            "What are the integration points, API requirements, and data flow specifications?"
        ]
    }
    
    return defaults.get(skill_level.lower(), defaults["intermediate"])

def init_followup_db():
    """Initialize SQLite database for follow-up questions and files"""
    conn = sqlite3.connect('followup_data.db')
    cursor = conn.cursor()
    
    # Create followup_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS followup_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            objective TEXT,
            skill_level TEXT,
            questions TEXT,
            answers TEXT,
            refined_objective TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create uploaded_files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            filename TEXT,
            file_type TEXT,
            file_size INTEGER,
            file_content TEXT,
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES followup_sessions (session_id)
        )
    ''')
    
    conn.commit()
    return conn

def save_followup_session(session_id: str, objective: str, skill_level: str,
                         questions: List[str], answers: Dict[int, str] = None,
                         refined_objective: str = None):
    """Save follow-up session to database"""
    conn = init_followup_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO followup_sessions
            (session_id, objective, skill_level, questions, answers, refined_objective)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            objective,
            skill_level,
            json.dumps(questions),
            json.dumps(answers) if answers else None,
            refined_objective
        ))
        conn.commit()
        logger.info(f"Saved follow-up session: {session_id}")
    except Exception as e:
        logger.error(f"Error saving follow-up session: {e}")
    finally:
        conn.close()

def save_uploaded_file(session_id: str, file_data: Dict[str, Any]):
    """Save uploaded file information to database"""
    conn = init_followup_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO uploaded_files
            (session_id, filename, file_type, file_size, file_content)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session_id,
            file_data['filename'],
            file_data['file_type'],
            file_data['file_size'],
            file_data['content'][:10000]  # Limit content size
        ))
        conn.commit()
        logger.info(f"Saved uploaded file: {file_data['filename']}")
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
    finally:
        conn.close()

def process_uploaded_file(uploaded_file):
    """Process uploaded file and return structured data"""
    if uploaded_file is None:
        return None
    
    file_data = {
        'filename': uploaded_file.name,
        'file_type': uploaded_file.type,
        'file_size': uploaded_file.size,
        'content': ''
    }
    
    try:
        if uploaded_file.type == 'text/csv':
            # Process CSV file
            df = pd.read_csv(uploaded_file)
            file_data['content'] = df.to_string(index=False)
            file_data['processed_data'] = df.to_dict('records')
        elif uploaded_file.type == 'application/json':
            # Process JSON file
            content = uploaded_file.read().decode('utf-8')
            file_data['content'] = content
            file_data['processed_data'] = json.loads(content)
        elif uploaded_file.type == 'text/plain':
            # Process text file
            content = uploaded_file.read().decode('utf-8')
            file_data['content'] = content
        elif uploaded_file.name.endswith('.xlsx'):
            # Process Excel file
            df = pd.read_excel(uploaded_file)
            file_data['content'] = df.to_string(index=False)
            file_data['processed_data'] = df.to_dict('records')
        else:
            # Generic file processing
            try:
                content = uploaded_file.read().decode('utf-8')
                file_data['content'] = content
            except:
                file_data['content'] = f"Binary file: {uploaded_file.name}"
                
        return file_data
        
    except Exception as e:
        logger.error(f"Error processing file {uploaded_file.name}: {e}")
        file_data['content'] = f"Error processing file: {str(e)}"
        return file_data

def generate_followup_questions_with_files(objective: str, skill_level: str = "intermediate",
                                          uploaded_files: List[Dict] = None) -> List[str]:
    """Generate follow-up questions considering uploaded files"""
    file_context = ""
    if uploaded_files:
        file_info = []
        for file_data in uploaded_files:
            file_info.append(f"- {file_data['filename']} ({file_data['file_type']}): {file_data['content'][:200]}...")
        file_context = f"\n\nUPLOADED FILES:\n" + "\n".join(file_info)
    
    skill_template = get_skill_based_question_template(skill_level)
    
    prompt = f"""
Based on this user objective: "{objective}"

User skill level: {skill_level}

{file_context}

{skill_template}

Generate EXACTLY 5 thoughtful follow-up questions that consider both the objective and any uploaded files. The questions should:

1. **Clarify Scope**: What specific aspects or boundaries should be considered?
2. **Understand Context**: What environment, constraints, or requirements exist?
3. **File Integration**: How should the uploaded files be used in the solution?
4. **Define Success**: How will success be measured or what is the desired outcome?
5. **Technical Requirements**: What technologies, approaches, or styles are preferred?

Format your response as exactly 5 numbered questions:

1. [Question 1]
2. [Question 2]
3. [Question 3]
4. [Question 4]
5. [Question 5]

Make each question specific, actionable, and directly relevant to achieving the objective with the available data.
"""

    try:
        response = llm_invoke(prompt)
        questions = []
        
        for line in response.split('\n'):
            line = line.strip()
            if line and re.match(r'^\d+\.', line):
                question = re.sub(r'^\d+\.\s*', '', line).strip()
                if question and len(question) > 10:
                    if not question.endswith('?'):
                        question += '?'
                    questions.append(question)
        
        # Ensure exactly 5 questions
        if len(questions) < 5:
            fallback_questions = get_default_questions(skill_level)
            questions.extend(fallback_questions[len(questions):])
            
        return questions[:5]
        
    except Exception as e:
        logger.error(f"Error generating questions with files: {e}")
        return get_default_questions(skill_level)

def create_user_database_connection(db_config: Dict):
    """Create connection to user-specified database"""
    try:
        if db_config['type'] == 'sqlite':
            conn = sqlite3.connect(db_config['database'])
            return conn
        elif db_config['type'] == 'postgresql':
            import psycopg2
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            return conn
        elif db_config['type'] == 'mysql':
            import mysql.connector
            conn = mysql.connector.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['user'],
                password=db_config['password'],
                database=db_config['database']
            )
            return conn
    except Exception as e:
        st.error(f"Failed to connect to {db_config['type']} database: {e}")
        return None

def test_database_connections(db_configs: List[Dict]):
    """Test all user-configured database connections"""
    connection_results = []
    
    for i, db_config in enumerate(db_configs):
        if db_config.get('database') or db_config.get('host'):
            st.write(f"Testing Database Connection {i+1}...")
            conn = create_user_database_connection(db_config)
            
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")  # Simple test query
                    st.success(f"✅ Connected to {db_config['type']} database successfully!")
                    connection_results.append({'config': db_config, 'status': 'success', 'connection': conn})
                except Exception as e:
                    st.error(f"❌ Connection test failed: {e}")
                    connection_results.append({'config': db_config, 'status': 'failed', 'error': str(e)})
                finally:
                    conn.close()
            else:
                connection_results.append({'config': db_config, 'status': 'failed', 'error': 'Could not establish connection'})
    
    return connection_results

def setup_user_database_tables(db_configs: List[Dict]):
    """Create tables in user-configured databases"""
    for db_config in db_configs:
        conn = create_user_database_connection(db_config)
        if conn:
            try:
                cursor = conn.cursor()
                
                # Create a sample table based on the question context
                create_table_sql = """
                    CREATE TABLE IF NOT EXISTS workflow_data (
                        id INTEGER PRIMARY KEY,
                        session_id TEXT,
                        question_index INTEGER,
                        answer_data TEXT,
                        file_content TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                cursor.execute(create_table_sql)
                conn.commit()
                st.success(f"✅ Tables created in {db_config['type']} database")
            except Exception as e:
                st.error(f"❌ Error creating tables: {e}")
            finally:
                conn.close()

def render_followup_questions_with_upload(objective: str, skill_level: str = "intermediate",
                                        session_id: str = None):
    """Enhanced follow-up questions interface with collapsible file upload and DB setup"""
    
    if not session_id:
        session_id = f"session_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    
    processed_files = []
    
    # Generate questions
    questions = generate_followup_questions_with_files(objective, skill_level, processed_files)
    save_followup_session(session_id, objective, skill_level, questions)
    
    # Display questions with answer, file upload, and database config
    st.write("Please answer these questions to help us better understand your requirements:")
    
    # Create a form for all questions and answers
    with st.form(f"followup_questions_form_{session_id}"):
        answers = []
        uploaded_files_data = []
        db_configs = []
        
        # Iterate through questions
        for i, question in enumerate(questions):
            st.write(f"**Question {i+1}:** {question}")
            
            # Text Answer
            answer = st.text_area(
                f"Your answer:",
                key=f"followup_answer_{session_id}_{i}",
                height=120,
                placeholder="Type your answer here..."
            )
            answers.append(answer)
            
            # Create expandable sections for optional features
            col1, col2 = st.columns(2)
            
            # --- Column 1: File upload in expander ---
            with col1:
                with st.expander("📎 Upload Files (Optional)", expanded=False):
                    st.markdown("**Upload relevant files for this question**")
                    uploaded_files_per_question = st.file_uploader(
                        "Choose files",
                        key=f"file_uploader_{session_id}_{i}",
                        type=['csv', 'txt', 'json', 'pdf', 'docx', 'jpg', 'jpeg', 'png', 'xlsx'],
                        help="Upload files that are relevant to this specific question",
                        accept_multiple_files=True
                    )
                    
                    # Process uploaded files for this question
                    question_files = []
                    if uploaded_files_per_question:
                        for uploaded_file in uploaded_files_per_question:
                            try:
                                file_data = process_uploaded_file(uploaded_file)
                                if file_data:
                                    file_info = {
                                        'question_index': i,
                                        'question_text': question,
                                        'filename': uploaded_file.name,
                                        'file_type': uploaded_file.type,
                                        'content': file_data['content'],
                                        'file_size': file_data['file_size']
                                    }
                                    question_files.append(file_info)
                                    st.success(f"✅ Processed: {uploaded_file.name}")
                            except Exception as e:
                                st.error(f"Error processing file {uploaded_file.name}: {str(e)}")
                    
                    uploaded_files_data.extend(question_files)
            
            # --- Column 2: Database Setup exactly like the image ---
            # --- Column 2: Database Setup exactly like the image ---
            with col2:
                with st.expander("🗄️ Database Setup (Optional)", expanded=False):
                    # Database type selection with clean styling
                    db_type = st.selectbox(
                        "Database Type",
                        ["None", "sqlite", "mysql", "postgresql"],
                        key=f"db_type_{session_id}_{i}",
                        help="Select database type for this question"
                    )
                    
                    # Initialize db_config with basic structure
                    db_config = {'type': db_type.lower(), 'question_index': i}
                    
                    # Handle database configuration based on type - exactly like your image
                    if db_type.lower() == "sqlite":
                        db_file = st.text_input(
                            "SQLite DB File",
                            value="",  # Empty default value
                            placeholder="Db_name.db",
                            key=f"sqlite_file_{session_id}_{i}",
                            help="Path to SQLite database file"
                        )

                        
                        # Update config if file path is provided
                        if db_file and db_file.strip():
                            db_config.update({
                                'database': db_file.strip(),
                                'connection_string': f"sqlite:///{db_file.strip()}"
                            })
                    
                    elif db_type.lower() in ["mysql", "postgresql"]:
                        # Connection details for MySQL/PostgreSQL - compact layout
                        st.markdown(f"**{db_type.upper()} Connection:**")
                        
                        # Use columns for compact layout
                        col_left, col_right = st.columns(2)
                        
                        with col_left:
                            host = st.text_input("Host", key=f"db_host_{session_id}_{i}", 
                                            placeholder="localhost")
                            user = st.text_input("User", key=f"db_user_{session_id}_{i}", 
                                            placeholder="username")
                        
                        with col_right:
                            port = st.text_input("Port", key=f"db_port_{session_id}_{i}", 
                                            placeholder="3306" if db_type.lower() == "mysql" else "5432")
                            password = st.text_input("Pass", key=f"db_pass_{session_id}_{i}", 
                                                type="password", placeholder="password")
                        
                        dbname = st.text_input("Database", key=f"db_name_{session_id}_{i}", 
                                            placeholder="database_name")
                        
                        # Update config with all fields
                        db_config.update({
                            'host': host.strip() if host else '',
                            'port': port.strip() if port else '',
                            'user': user.strip() if user else '',
                            'password': password.strip() if password else '',
                            'database': dbname.strip() if dbname else ''
                        })
                        
                        # Add connection string if we have all required fields
                        if all([host and host.strip(), user and user.strip(), 
                            port and port.strip(), dbname and dbname.strip()]):
                            db_config['connection_string'] = f"{db_type.lower()}://{user.strip()}:{password}@{host.strip()}:{port.strip()}/{dbname.strip()}"
                    
                    db_configs.append(db_config)

            st.divider()
        
        # Submit button
        submit_answers = st.form_submit_button(
            "🔄 Submit All Answers",
            use_container_width=True,
            type="primary"
        )
        
        if submit_answers:
            try:
                # Filter out empty answers
                filtered_answers = {k: v for k, v in enumerate(answers) if v.strip()}
                
                # Process and save all data
                if filtered_answers or uploaded_files_data or any(db.get('database') or db.get('host') for db in db_configs if db.get('type', '').lower() != 'none'):
                    # Combine all files (general + question-specific)
                    all_files = processed_files + uploaded_files_data
                    
                    # Generate refined objective with all context
                    refined_objective = process_followup_answers_with_files(
                        objective, questions, filtered_answers, skill_level, all_files
                    )
                    
                    # Extract valid database configurations
                    valid_db_configs = []
                    for i, db_config in enumerate(db_configs):
                        db_type = db_config.get('type', '').lower()
                        
                        # Skip None or empty database types
                        if db_type == 'none' or not db_type:
                            continue
                        
                        # Check if database configuration is complete
                        if db_type == 'sqlite' and db_config.get('database'):
                            valid_db_configs.append(db_config)
                            st.info(f"✅ Database config {i+1}: SQLite - {db_config['database']}")
                        elif db_type in ['mysql', 'postgresql'] and db_config.get('host'):
                            valid_db_configs.append(db_config)
                            st.info(f"✅ Database config {i+1}: {db_type.upper()} - {db_config.get('host')}")
                    
                    # Save session with enhanced data
                    enhanced_session_data = {
                        'session_id': session_id,
                        'objective': objective,
                        'refined_objective': refined_objective,
                        'skill_level': skill_level,
                        'questions': questions,
                        'answers': filtered_answers,
                        'uploaded_files': all_files,
                        'database_configs': valid_db_configs
                    }
                    
                    save_followup_session(session_id, objective, skill_level, questions,
                                        filtered_answers, refined_objective)
                    
                    # Display results
                    st.success("✅ Answers submitted successfully!")
                    
                    with st.expander("🎯 View Refined Objective", expanded=True):
                        st.write(refined_objective)
                    
                    # Show database configurations summary
                    if valid_db_configs:
                        with st.expander("🗄️ Database Configurations"):
                            connection_results = test_database_connections(valid_db_configs)
                            successful_configs = [r['config'] for r in connection_results if r['status'] == 'success']
                            
                            if successful_configs:
                                if st.button("🔧 Create Required Tables"):
                                    setup_user_database_tables(successful_configs)
                            
                            # Store connection results
                            enhanced_session_data['database_connections'] = connection_results
                    
                    # Show question-specific files summary
                    if uploaded_files_data:
                        with st.expander("📎 Question-Specific Files"):
                            for file_info in uploaded_files_data:
                                st.write(f"**Q{file_info['question_index']+1}**: {file_info['filename']} ({file_info['file_type']})")
                    
                    if all_files:
                        with st.expander("📊 File Integration Plan"):
                            file_integration = generate_file_integration_plan(all_files, refined_objective)
                            st.write(file_integration)
                    
                    return {
                        'session_id': session_id,
                        'original_objective': objective,
                        'refined_objective': refined_objective,
                        'questions': questions,
                        'answers': filtered_answers,
                        'uploaded_files': processed_files,
                        'question_specific_files': uploaded_files_data,
                        'database_configs': valid_db_configs,
                        'skill_level': skill_level
                    }
                
                else:
                    st.warning("⚠️ Please answer at least one question to proceed. File uploads and database configurations are optional.")
                    
            except Exception as e:
                st.error(f"❌ Error submitting answers: {str(e)}")
                logger.error(f"Follow-up submission error: {e}")
        
        return None

def process_followup_answers_with_files(original_objective: str, questions: List[str],
                                      answers: Dict[int, str], skill_level: str,
                                      uploaded_files: List[Dict] = None) -> str:
    """Process follow-up answers with file context to create refined objective"""
    
    qa_pairs = []
    for i, question in enumerate(questions):
        answer = answers.get(i, "").strip()
        if answer:
            qa_pairs.append(f"Q: {question}\nA: {answer}")
    
    if not qa_pairs:
        return original_objective
    
    qa_text = "\n\n".join(qa_pairs)
    
    file_context = ""
    if uploaded_files:
        file_info = []
        for file_data in uploaded_files:
            file_info.append(f"File: {file_data['filename']} - {file_data['content'][:300]}...")
        file_context = f"\n\nUPLOADED FILES CONTEXT:\n" + "\n".join(file_info)
    
    prompt = f"""Based on the original objective, user answers, and uploaded files, create a comprehensive refined objective.

ORIGINAL OBJECTIVE: {original_objective}

USER SKILL LEVEL: {skill_level}

DETAILED Q&A SESSION:
{qa_text}

{file_context}

Create a refined objective that:
1. Incorporates all key insights from user answers and file context
2. Is significantly more specific and actionable than the original
3. Includes how uploaded files should be integrated into the solution
4. Addresses technical constraints, preferences, and success criteria
5. Is structured appropriately for a {skill_level} level implementation

REFINED OBJECTIVE:"""

    try:
        refined = llm_invoke(prompt)
        return refined.strip() if refined.strip() else original_objective
    except Exception as e:
        logger.error(f"Error processing follow-up answers with files: {e}")
        return original_objective

def generate_file_integration_plan(uploaded_files: List[Dict], refined_objective: str) -> str:
    """Generate a plan for how uploaded files should be integrated"""
    
    file_summary = []
    for file_data in uploaded_files:
        file_summary.append(f"- {file_data['filename']}: {file_data['content'][:200]}...")
    
    prompt = f"""Based on the refined objective and uploaded files, create an integration plan.

REFINED OBJECTIVE: {refined_objective}

UPLOADED FILES:
{chr(10).join(file_summary)}

Create a specific plan for how each file should be used in the solution:
1. Data processing requirements
2. Integration points in the workflow
3. Expected outputs from each file
4. Any data transformations needed

INTEGRATION PLAN:"""

    try:
        plan = llm_invoke(prompt)
        return plan.strip()
    except Exception as e:
        logger.error(f"Error generating integration plan: {e}")
        return "File integration plan could not be generated automatically. Please specify how files should be used."
