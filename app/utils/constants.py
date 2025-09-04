import streamlit as st
from typing import TypedDict, Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ✅ SINGLE CLIENT - OpenAI Only
CLIENT = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    # base_url="http://10.10.9.79:8000/v1",
    # model_name="DeepSeek-R1-Distill-Llama-8B",  # or "gpt-3.5-turbo" for cheaper/faster
    temperature=0.7,
    max_tokens=2048  # Set default max_tokens
)

def llm_invoke(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """Single LLM invocation - OpenAI only"""
    response = CLIENT.invoke(prompt)
    return response.content.strip()

def human_assistant(question: str, context: str) -> str:
    """Provide helpful explanations to users"""
    prompt = f"""You're a helpful assistant explaining AI development concepts.

Context: {context}
User Question: "{question}"

Provide a clear, concise answer (1-3 sentences) using simple language when possible:
"""
    return llm_invoke(prompt)

def llm_for_subtasks(prompt: str) -> str:
    """Wrapper function for LLM calls specifically for subtask generation"""
    try:
        response = CLIENT.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        return f"Error generating subtasks: {str(e)}"

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") 
        
    def invoke(self, prompt: str, max_tokens: int = 200) -> str:
        """Invoke LLM with proper error handling"""
        try:
            # Replace this with your actual LLM client
            # Example for OpenAI:
            # from openai import OpenAI
            # client = OpenAI(api_key=self.api_key)
            # response = client.chat.completions.create(
            #     model="gpt-3.5-turbo",
            #     messages=[{"role": "user", "content": prompt}],
            #     max_tokens=max_tokens,
            #     temperature=0.2
            # )
            # return response.choices[0].message.content
            
            # For now, let's use a mock response that shows the structure works
            if "modify" in prompt.lower() or "update" in prompt.lower():
                return """1. Define requirements and data sources
2. Design system architecture  
3. Implement core functionality
4. Add security validation
5. Deploy and test system"""
            else:
                return "Mock LLM response for: " + prompt[:50] + "..."
                
        except Exception as e:
            print(f"LLM Error: {e}")
            return ""

# Create global instance
llm_service = LLMService()
##########################################################################
##################################################
# import streamlit as st
# from typing import TypedDict, Optional, List, Dict, Any
# from langgraph.graph import StateGraph, END
# from together import Together
# import json
# import time
# import os
# from huggingface_hub import InferenceClient
# from dotenv import load_dotenv

# load_dotenv()


# CLIENT = InferenceClient(
#     provider="novita",
#     api_key=os.environ["HF_TOKEN"]
# )

# def llm_invoke(prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
#     client = CLIENT
#     if not client:
#         return "Error: client not initialized"
    
#     try:
#         with st.spinner("Generating response..."):
#             response = client.chat.completions.create(
#                 model="meta-llama/Llama-3.1-8B-Instruct",   # or your model
#                 messages=[{"role": "user", "content": "Your prompt here"}],
#                 max_tokens=max_tokens,
#                 temperature=temperature
#             )
#             return response.choices[0].message.content.strip()
#     except Exception as e:
#         return f"Error: {str(e)}"

# def human_assistant(question: str, context: str) -> str:
#     """Provide helpful explanations to users"""
#     prompt = f"""You're a helpful assistant explaining AI development concepts.
 
# Context: {context}
 
# User Question: "{question}"
 
# Provide a clear, concise answer (1-3 sentences) using simple language when possible:
# """
#     return llm_invoke(prompt, max_tokens=300)

# def llm_for_subtasks(prompt: str, max_tokens: int = 300):
#     """Wrapper function for LLM calls specifically for subtask generation"""
#     client = CLIENT

#     try:
#         # If using OpenAI
#         response = client.chat.completions.create(
#             model="mistralai/Mixtral-8x7B-Instruct-v0.1",  # or your preferred model
#             messages=[{"role": "user", "content": prompt}],
#             max_tokens=max_tokens,
#             temperature=0.2
#         )
#         return response.choices[0].message.content
        
#         # If using Together AI (as shown in your code.py)
#         # response = client.completions.create(
#         #     model="mistralai/Mixtral-8x7B-Instruct-v0.1",
#         #     prompt=prompt,
#         #     max_tokens=max_tokens,
#         #     temperature=0.2
#         # )
#         # return response.choices[0].text.strip()
        
#     except Exception as e:
#         return f"Error generating subtasks: {str(e)}"
