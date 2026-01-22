import os
import subprocess
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

# Initialize Search Engine
search_engine = DuckDuckGoSearchRun()

# --- TOOLS (Docstring-Driven / No Pydantic Dependencies) ---

@tool
def save_file(filename: str, content: str):
    """
    Saves content to a file in the agent_workspace directory.
    
    Args:
        filename: The name of the file (e.g., 'script.py').
        content: The actual code or text to write.
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

@tool
def read_file(filename: str):
    """
    Reads the content of a file from the agent_workspace.
    
    Args:
        filename: The name of the file to read.
    """
    try:
        OUTPUT_DIR = "agent_workspace"
        file_path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(file_path):
            return "Error: File does not exist."
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def execute_python_file(filename: str):
    """
    Runs a Python script that is already saved in the workspace.
    
    Args:
        filename: The name of the script to run (e.g., 'script.py').
    """
    try:
        OUTPUT_DIR = "agent_workspace"
        file_path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(file_path):
            return "Error: File does not exist."
            
        script_dir = os.path.dirname(file_path)
        # Timeout prevents infinite loops
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

@tool
def web_search(query: str):
    """
    Searches the internet for information.
    
    Args:
        query: The search term (e.g., 'python install yfinance error').
    """
    try:
        # Using invoke instead of run (Modern LangChain)
        return search_engine.invoke(query)
    except Exception as e:
        return f"Error searching: {str(e)}"

# Export
agent_tools = [save_file, read_file, execute_python_file, web_search]