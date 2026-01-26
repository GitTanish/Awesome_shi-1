import os
import sys
import json
from dotenv import load_dotenv
from core.memory import memory

load_dotenv()

from core.models import RouteIntent
from core.router import router_chain
from workers.chains import coding_chain, planner_chain, autonomous_dev_chain
from workers.tools import agent_tools

sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
CODE_EXTENSIONS = {'.py', '.sh', '.bat', '.js', '.ts', '.go', '.rs'}
DATA_EXTENSIONS = {'.txt', '.md', '.json', '.csv', '.xml', '.html', '.css', '.yaml', '.yml', '.env'}

def execute_json_tool_call(json_str):
    try:
        clean_json = json_str.replace("```json", "").replace("```", "").strip()
        tool_data = json.loads(clean_json)
        tool_name = tool_data.get("tool")
        tool_args = tool_data.get("args")
        return tool_name, tool_args
    except json.JSONDecodeError:
        return None, None
    except Exception:
        return None, None

def run_app():
    print("Groq-Powered Architect Online (v4.0 - Deterministic)")
    
    while True:
        user_input = input("\n>> You: ")
        if user_input.lower() in ["exit", "q"]: break

        try:
            # 1. ROUTING
            raw_intent = router_chain.invoke({"input": user_input})
            try:
                intent = RouteIntent(raw_intent)
            except ValueError:
                intent = RouteIntent.CASUAL
            
            print(f"   🚦 Intent: {intent.value}")

            if intent == RouteIntent.CODE:
                print("   🤖 Mode: Autonomous Developer")
                current_request = user_input
                
                # ARCHITECTURAL STATE
                max_steps = 10  # It's an action budget, not retries
                action_history = [] # List of (tool_name, args_str)
                
                for step in range(max_steps):
                    print(f"\n   🔄 Step {step+1}/{max_steps}...")

                    # 1. Memory Recall
                    context = memory.search_memory(current_request)
                    augmented_request = current_request
                    if context:
                        print(f"      🧠 Recalled: {str(context)[:100]}...")
                        augmented_request += f"\n\n[MEMORY]: I found relevant past info: {context}"
                    
                    # 2. Invoke Brain
                    ai_response_str = autonomous_dev_chain.invoke({"request": augmented_request})
                    
                    # 3. Parse (But Don't Run Yet)
                    tool_name, tool_args = execute_json_tool_call(ai_response_str)
                    
                    if not tool_name:
                        print("      ⚠️ Invalid JSON from Agent. Retrying...")
                        current_request += "\nSYSTEM: Invalid JSON. Fix format."
                        continue

                    # 4. PROACTIVE LOOP DETECTION (The Fix)
                    # We serialize args to check for exact duplicates
                    current_action_signature = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
                    
                    if action_history.count(current_action_signature) >= 2:
                        print("      🔴 FATAL LOOP DETECTED. History repeats 3 times.")
                        print("      🛑 SYSTEM FORCED TERMINATION.")
                        memory.save_memory(f"Task: {user_input}. Status: Failed (Loop).")
                        break
                    
                    action_history.append(current_action_signature)

                    # 5. EXECUTE REAL TOOL
                    print(f"      🛠️  Tool: {tool_name}")
                    print(f"      📂 Args: {str(tool_args)[:100]}...")
                    
                    selected_tool = next((t for t in agent_tools if t.name == tool_name), None)
                    if selected_tool:
                        tool_output = selected_tool.invoke(tool_args)
                        print(f"      ✅ Result: {str(tool_output)[:100]}...")
                    else:
                        tool_output = f"Error: Tool {tool_name} not found."

                    # 6. DETERMINISTIC TERMINATION (The Architect's Rule)
                    # If it's a data file, we don't ask the agent. We just end it.
                    if tool_name == "save_file":
                        filename = tool_args.get("filename", "")
                        if any(filename.endswith(ext) for ext in DATA_EXTENSIONS):
                            print(f"      🏁 DATA FILE CREATED ({filename}). TASK COMPLETE.")
                            memory.save_memory(f"Task: {user_input}. Status: Success (Data File).")
                            break # <--- HARD BREAK

                    # 7. EXPLICIT COMPLETION
                    if tool_name == "task_complete":
                        print("      ✅ Task Completed.")
                        memory.save_memory(f"Task: {user_input}. Status: Success.")
                        break

                    # 8. FEEDBACK GENERATION
                    if "Error" in str(tool_output) or "❌" in str(tool_output):
                         current_request += f"\n\nSYSTEM: Tool '{tool_name}' failed: {tool_output}. Fix it."
                    else:
                         # Smart Hinting for Code
                         next_prompt = "What is the next step?"
                         if tool_name == "save_file" and any(tool_args.get("filename", "").endswith(ext) for ext in CODE_EXTENSIONS):
                             next_prompt = "Code saved. You MUST now verify it with 'execute_python_file'."
                         
                         current_request += f"\n\nSYSTEM: Tool '{tool_name}' succeeded. {next_prompt}"

            elif intent == RouteIntent.CASUAL:
                print("   👋 I am a specialized R&D Agent.")

        except Exception as e:
            print(f"   ❌ Main Loop Error: {e}")

if __name__ == "__main__":
    run_app()