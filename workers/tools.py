import os
import subprocess
from langchain_core.tools import tool

# @tool decorator tells LangChain: "This function is available for the LLM"
@tool
def save_file(filename: str, content: str):
    """
    Saves the given content to a file. 
    ALWAYS use this tool when the user asks to write code to a file.
    If the file exists, it will be overwritten.
    """
    try:
        # Simple security sandbox: specific folder for agent outputs
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
    Reads the content of a file. Use this to inspect code before fixing it.
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
    Returns the STDOUT (output) or STDERR (errors).
    """
    try:
        OUTPUT_DIR = "agent_workspace"
        file_path = os.path.join(OUTPUT_DIR, filename)
        
        if not os.path.exists(file_path):
            return "Error: File does not exist. Save it first."
            
        script_dir = os.path.dirname(file_path)
        # Security: Run with a timeout so infinite loops don't freeze your agent
        # capture_output=True grabs what would have printed to the terminal
        result = subprocess.run(
            ["python", os.path.basename(file_path)], 
            cwd=script_dir,
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        # Return the actual output or the crash log
        if result.returncode == 0:
            return f"✅ Execution Success:\n{result.stdout}"
        else:
            return f"❌ Execution Error:\n{result.stderr}"

    except Exception as e:
        return f"System Error: {str(e)}"

# Export the list of tools
agent_tools = [save_file, read_file, execute_python_file]
