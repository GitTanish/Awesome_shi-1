import os
import subprocess
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.pydantic_v1 import BaseModel, Field # <--- NEW IMPORT

# Initialize Search Engine
search_engine = DuckDuckGoSearchRun()

# --- INPUT SCHEMAS (The Safety Molds) ---
class FileInput(BaseModel):
    filename: str = Field(description="Name of the file (e.g., 'script.py')")
    content: str = Field(description="Code or text to write to the file")

class ReadInput(BaseModel):
    filename: str = Field(description="Name of the file to read")

class SearchInput(BaseModel):
    query: str = Field(description="The search query to run on DuckDuckGo")

# --- TOOLS ---

@tool("save_file", args_schema=FileInput) # <--- Bind the Schema
def save_file(filename: str, content: str):
    """
    Saves content to a file in 'agent_workspace'. 
    Overwrites if exists. 
    """
    try:
        OUTPUT_DIR = "agent_workspace"
        file_path = os.path.join(OUTPUT_DIR, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File successfully saved to: {file_path}"
    except Exception as e:
        return f"Error saving file: {str(e)}"

@tool("read_file", args_schema=ReadInput)
def read_file(filename: str):
    """Reads a file from 'agent_workspace'."""
    try:
        OUTPUT_DIR = "agent_workspace"
        file_path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(file_path):
            return "Error: File does not exist."
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool("execute_python_file", args_schema=ReadInput) # Re-use ReadInput since it just needs filename
def execute_python_file(filename: str):
    """
    Runs a Python script inside 'agent_workspace'.
    Returns STDOUT or STDERR.
    """
    try:
        OUTPUT_DIR = "agent_workspace"
        file_path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(file_path):
            return "Error: File does not exist."
            
        script_dir = os.path.dirname(file_path)
        result = subprocess.run(
            ["python", os.path.basename(file_path)], 
            cwd=script_dir,
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            return f"✅ Execution Success:\n{result.stdout}"
        else:
            return f"❌ Execution Error:\n{result.stderr}"
    except Exception as e:
        return f"System Error: {str(e)}"

@tool("web_search", args_schema=SearchInput)
def web_search(query: str):
    """
    Searches the internet for documentation or error fixes.
    """
    try:
        # Using invoke instead of run (Modern LangChain)
        return search_engine.invoke(query)
    except Exception as e:
        return f"Error searching: {str(e)}"

agent_tools = [save_file, read_file, execute_python_file, web_search]