import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

from core.models import RouteIntent
from core.router import router_chain
from workers.chains import coding_chain, planner_chain, autonomous_dev_chain
from workers.tools import agent_tools # We still need the functions

sys.stdout.reconfigure(encoding='utf-8')

# --- THE MANUAL PARSER ---
def execute_json_tool_call(json_str):
    try:
        # 1. Clean the output (sometimes models add markdown ```json blocks)
        clean_json = json_str.replace("```json", "").replace("```", "").strip()
        
        # 2. Parse JSON
        tool_data = json.loads(clean_json)
        tool_name = tool_data.get("tool")
        tool_args = tool_data.get("args")
        
        print(f"      🛠️ Tool Call: {tool_name}") # Debug print
        
        # 3. Find and Run Tool
        # We manually match the string name to the function in agent_tools
        selected_tool = next((t for t in agent_tools if t.name == tool_name), None)
        
        if selected_tool:
            return selected_tool.invoke(tool_args)
        else:
            return f"Error: Tool '{tool_name}' not found."
            
    except json.JSONDecodeError:
        return f"Error: Agent output invalid JSON.\nRaw output: {json_str}"
    except Exception as e:
        return f"System Error executing tool: {e}"

def run_app():
    print("Groq-Powered Architect Online (Explicit Mode)")
    
    while True:
        user_input = input("\n>> You: ")
        if user_input.lower() in ["exit", "q"]: break

        try:
            # 1. ROUTING
            raw_intent = router_chain.invoke({"input": user_input})
            print(f"   🐛 DEBUG: Router returned -> '{raw_intent}'")
            
            try:
                intent = RouteIntent(raw_intent)
            except ValueError:
                intent = RouteIntent.CASUAL
            
            print(f"   🚦 Intent: {intent.value}")

            # 2. EXECUTION
            if intent == RouteIntent.CODE:
                
                # A. PROJECT MODE (Architect)
                if any(word in user_input.lower() for word in ["project", "build", "create app"]):
                    print("   🏗️ Mode: The Architect")
                    # ... (Architect logic same as before, but using execute_json_tool_call inside loop)
                    # Let's focus on Single Task first to verify the fix.
                    print("   (Architect mode paused for testing Single Task)")

                # B. SINGLE TASK (Persistent Loop)
                else:
                    print("   Mode: Autonomous Developer")
                    current_request = user_input
                    max_retries = 5 # Give it more turns to think -> code -> run -> fix
                    
                    for attempt in range(max_retries):
                        print(f"      Iteration {attempt+1}/{max_retries}...")
                        
                        # 1. Ask Brain
                        ai_response_str = autonomous_dev_chain.invoke({"request": current_request})
                        
                        # 2. Parse
                        try:
                            clean_json = ai_response_str.replace("```json", "").replace("```", "").strip()
                            tool_data = json.loads(clean_json)
                            tool_name = tool_data.get("tool")
                            tool_args = tool_data.get("args") or {}
                        except json.JSONDecodeError:
                            print(f"      JSON Error. Retrying...")
                            current_request += f"\nSYSTEM: Your last output was invalid JSON. Try again."
                            continue

                        # 3. Check for Termination
                        if tool_name == "task_complete":
                            print("      Task Completed.")
                            break
                        
                        # 4. Execute Real Tool
                        print(f"      Tool Call: {tool_name}")
                        
                        # Find the tool function
                        selected_tool = next((t for t in agent_tools if t.name == tool_name), None)
                        
                        if selected_tool:
                            tool_output = selected_tool.invoke(tool_args)
                        else:
                            tool_output = f"Error: Tool {tool_name} not found."
                        
                        # 5. FEEDBACK LOOP (The Critical Fix)
                        # We append the result to the request so the agent knows what happened.
                        if "Error" in tool_output or "❌" in tool_output:
                             print(f"         Output: {tool_output[:100]}...") 
                             current_request += f"\n\nSYSTEM: Tool '{tool_name}' failed: {tool_output}. Fix it."
                        else:
                             print(f"         Output: {tool_output[:100]}...")
                             
                             # --- SMART HINTING (The Fix) ---
                             # We guide the agent based on what it just did.
                             next_prompt = "What is the next step?"
                             
                             if tool_name == "save_file":
                                 next_prompt = "File saved. STOP EDITING. You must now call 'execute_python_file' immediately to test the code."
                             elif tool_name == "web_search":
                                 # NUANCED LOGIC:
                                 # 1. Acknowledge the search.
                                 # 2. Remind about the pip limitation.
                                 # 3. Suggest Standard Libs.
                                 # 4. Allow graceful failure.
                                 next_prompt = (
                                     "Search complete. CRITICAL CONTEXT: You do not have access to a terminal to run 'pip install'. "
                                     "STRATEGY: Write a Python script using STANDARD LIBRARIES (like 'urllib', 'json', 're') to fetch the data directly from a URL. "
                                     "If this is impossible, save a file named 'report.txt' explaining why."
                                 )
                             
                             current_request += f"\n\nSYSTEM: Tool '{tool_name}' succeeded. {next_prompt}"
            
            elif intent == RouteIntent.CASUAL:
                print("   👋 I am a specialized R&D Agent.")

        except Exception as e:
            print(f"   ❌ Main Loop Error: {e}")

if __name__ == "__main__":
    run_app()