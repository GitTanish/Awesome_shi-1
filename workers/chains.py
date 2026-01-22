import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- CONFIGURATION ---
llm_fast = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
llm_smart = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# --- 1. SIMPLE CODER ---
coding_chain = (
    ChatPromptTemplate.from_template("Write Python code for: {topic}. Return ONLY the code.")
    | llm_fast 
    | StrOutputParser()
)

# --- 2. THE BUILDER (Explicit JSON Mode) ---
tool_definitions = """
AVAILABLE TOOLS:
1. save_file(filename: str, content: str) - Save code.
2. read_file(filename: str) - Read a file.
3. execute_python_file(filename: str) - Run a script.
4. web_search(query: str) - Search for answers.
5. task_complete() - Call this ONLY when the user's entire goal is achieved.
"""

tool_prompt = ChatPromptTemplate.from_template(
    """
    You are an Autonomous Developer.
    Goal: {request}
    
    {tools}
    
    INSTRUCTIONS:
    1. Output ONLY a valid JSON object in this format:
       {{ "tool": "tool_name", "args": {{ "arg_name": "value" }} }}
    2. If you need to search, use 'web_search'.
    3. If you write code, you MUST run it using 'execute_python_file' to verify it works.
    4. If the code crashes, use 'web_search' to find a fix, then rewrite the file.
    5. When the code runs successfully and prints the answer, output {{ "tool": "task_complete", "args": {{}} }}.
    
    Output nothing else. Just the JSON.
    """
)

# Note: We do NOT use bind_tools here. We want raw text output.
autonomous_dev_chain = tool_prompt.partial(tools=tool_definitions) | llm_smart | StrOutputParser()

# --- 3. THE PLANNER ---
planner_prompt = ChatPromptTemplate.from_template(
    """
    You are a Software Architect.
    User Request: {request}
    Return a JSON object with a list of steps: {{ "steps": ["step 1", "step 2"] }}
    """
)
planner_chain = planner_prompt | llm_fast | StrOutputParser()

# --- 4. RESEARCHER ---
# For now, let's keep researcher simple since we are focusing on the Builder.
def execute_research_chain(topic):
    return "Research mode temporarily disabled for refactor."