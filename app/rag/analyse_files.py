# import json
# from typing import Dict, List
# from app.utils.constants import llm_invoke

# def analyze_file_requirements(answers: Dict[str, str]) -> List[str]:
#     """Analyze answers to determine file upload requirements"""
#     prompt = f"""Analyze these user requirements and identify what files need to be uploaded:
 
# Requirements: {json.dumps(answers, indent=2)}
 
# Common file types:
# - CSV files for data
# - TXT files for policies/rules
# - JSON files for configuration
# - XLSX files for spreadsheets
# - Image files for analysis
 
# Return ONLY a simple list of required files (one per line):
# """
   
#     response = llm_invoke(prompt, max_tokens=200)
#     files = []
#     for line in response.split('\n'):
#         line = line.strip()
#         if line and not line.startswith('Requirements:'):
#             files.append(line)
#     return files
 

# import json

# from typing import Dict, List

# from app.utils.constants import llm_invoke

# def analyze_file_requirements(answers: Dict[str, str]) -> List[str]:

#     '''Analyse uploaded files:'''
#     prompt = f"""Analyze these user requirements. Do NOT provide any suggestions or advice. Simply read the files and write out some of the data from each given file.Return ONLY a simple list of required files (one per line):"""
#     response = llm_invoke(prompt, max_tokens=200)

#     files = []

#     for line in response.split('\n'):

#         line = line.strip()

#         if line and not line.startswith('Requirements:'):

#             files.append(line)

#     return files
import json
import os
from typing import Dict, List, Union
import PyPDF2
import io
import streamlit as st
from app.utils.constants import llm_invoke

def extract_pdf_text(uploaded_file) -> str:
    """Extract text content from PDF file"""
    try:
        # Handle both file path and Streamlit UploadedFile
        if hasattr(uploaded_file, 'read'):
            # Streamlit UploadedFile object
            pdf_bytes = uploaded_file.read()
            pdf_file = io.BytesIO(pdf_bytes)
        else:
            # File path string
            with open(uploaded_file, 'rb') as file:
                pdf_file = io.BytesIO(file.read())
        
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_file_data(uploaded_files) -> str:
    """Extract and return actual data from uploaded files"""
    extracted_data = []
    
    for file in uploaded_files:
        file_name = getattr(file, 'name', str(file))
        file_data = f"\n**File: {file_name}**\n"
        
        try:
            if file_name.lower().endswith('.pdf'):
                content = extract_pdf_text(file)
                file_data += f"Content:\n{content}\n"
            
            elif file_name.lower().endswith(('.csv', '.txt')):
                if hasattr(file, 'read'):
                    content = file.read().decode('utf-8')
                else:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                file_data += f"Content:\n{content}\n"
            
            elif file_name.lower().endswith(('.json')):
                if hasattr(file, 'read'):
                    content = file.read().decode('utf-8')
                else:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                try:
                    json_data = json.loads(content)
                    file_data += f"JSON Data:\n{json.dumps(json_data, indent=2)}\n"
                except:
                    file_data += f"Raw Content:\n{content}\n"
            
            else:
                file_data += "File type not supported for text extraction\n"
                
        except Exception as e:
            file_data += f"Error reading file: {str(e)}\n"
        
        extracted_data.append(file_data)
    
    return "\n".join(extracted_data)

def analyze_file_requirements(answers: Dict[str, str], uploaded_files=None) -> List[str]:
    """Read files and write out the actual data from each given file"""
    
    if uploaded_files:
        # Extract actual file content
        file_content = extract_file_data(uploaded_files)
        
        prompt = f"""Read these files and write out some of the data from each given file. Do NOT provide any suggestions or advice.

User Requirements: {json.dumps(answers, indent=2)}

File Contents:
{file_content}

Based on the file contents, extract and list the key data points found (one per line):
"""
    else:
        prompt = f"""Analyze these user requirements. Do NOT provide any suggestions or advice.

Simply read the files and write out some of the data from each given file.

Requirements: {json.dumps(answers, indent=2)}

Return ONLY a simple list of required files (one per line):
"""
    
    response = llm_invoke(prompt, max_tokens=500)
    
    files = []
    for line in response.split('\n'):
        line = line.strip()
        if line and not line.startswith('Requirements:') and not line.startswith('User Requirements:'):
            files.append(line)
    
    return files
