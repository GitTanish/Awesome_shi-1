import os
import sys
import json
from dotenv import load_dotenv

# 1. LOAD ENV FIRST (Crucial Fix)
load_dotenv()

# 2. NOW IMPORT MODULES (They need the env vars)
from core.memory import memory
from core.critic import review_code, reset_code_history 
from core.models import RouteIntent
from core.router import router_chain
from workers.chains import coding_chain, planner_chain, autonomous_dev_chain
from workers.tools import agent_tools

sys.stdout.reconfigure(encoding='utf-8')

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
    print("Groq-Powered Architect Online (v5.0 - With Critic)")
    
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
                reset_code_history() # <--- Fresh start for new task
                
                current_request = user_input
                max_steps = 10
                action_history = []
                
                for step in range(max_steps):
                    print(f"\n   🔄 Step {step+1}/{max_steps}...")

                    # Memory
                    context = memory.search_memory(current_request)
                    augmented_request = current_request
                    if context:
                        print(f"      🧠 Recalled: {str(context)[:100]}...")
                        augmented_request += f"\n\n[MEMORY]: I found relevant past info: {context}"
                    
                    # Brain
                    ai_response_str = autonomous_dev_chain.invoke({"request": augmented_request})
                    tool_name, tool_args = execute_json_tool_call(ai_response_str)
                    
                    if not tool_name:
                        print("      ⚠️ Invalid JSON. Retrying...")
                        current_request += "\nSYSTEM: Invalid JSON. Fix format."
                        continue

                    # Loop Check
                    current_action_signature = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
                    if action_history.count(current_action_signature) >= 2:
                        print("      🔴 FATAL LOOP DETECTED. Terminating.")
                        break
                    action_history.append(current_action_signature)

                    # Execute
                    print(f"      🛠️  Tool: {tool_name}")
                    print(f"      📂 Args: {str(tool_args)[:100]}...")
                    
                    # --- CRITIC INTERCEPTION (The Gate) ---
                    if tool_name == "save_file":
                        filename = tool_args.get("filename", "")
                        content = tool_args.get("content", "")

                        # A. Hard Stop for Data
                        if any(filename.endswith(ext) for ext in DATA_EXTENSIONS):
                            # Execute the save first
                            next((t for t in agent_tools if t.name == tool_name)).invoke(tool_args)
                            print(f"      🏁 DATA FILE CREATED ({filename}). TASK COMPLETE.")
                            memory.save_memory(f"Task: {user_input}. Status: Success (Data File).")
                            break

                        # B. Review for Code
                        if any(filename.endswith(ext) for ext in CODE_EXTENSIONS):
                            # CALCULATE ATTEMPT NUMBER (step starts at 0, so step+1 is current attempt)
                            current_attempt = step + 1 
                            
                            print(f"      🔍 Reviewing code: {filename} (Attempt {current_attempt})...")
                            
                            # PASS ATTEMPT NUMBER TO CRITIC
                            review = review_code(content, current_request, attempt_number=current_attempt)
                            
                            if not review["approved"]:
                                print(f"      ❌ Code Review FAILED: {review['critique']}")
                                current_request += f"\n\nSYSTEM: Code review FAILED. Reason: {review['critique']}. Fix the code and save again."
                                continue 

                            print(f"      ✅ Code Review Passed: {review['critique']}")

                            # --- AUTO-EXECUTION (The Architect's Acceleration) ---
                            # 1. Save the file explicitly (since we bypass the loop's standard execution)
                            save_tool = next((t for t in agent_tools if t.name == "save_file"), None)
                            save_tool.invoke(tool_args)
                            print(f"      💾 File saved: {filename}")

                            # 2. Run it immediately
                            print(f"      🚀 Auto-Executing {filename}...")
                            exec_tool = next((t for t in agent_tools if t.name == "execute_python_file"), None)
                            exec_result = exec_tool.invoke({"filename": filename})
                            print(f"      ✅ Execution Result: {str(exec_result)[:200]}...")
                            
                            # 3. Environmental Checks
                            env_errors = ["getaddrinfo failed", "network is unreachable", "connection refused"]
                            if any(e in str(exec_result).lower() for e in env_errors):
                                print("      🔴 CRITICAL: NETWORK ERROR DETECTED.")
                                print("      ⚠️  The Agent cannot fix your internet connection.")
                                memory.save_memory(f"Task: {user_input}. Status: Failed (Network Error).")
                                break # <--- KILL SWITCH
                                
                            # 4. Success Check
                            if "Error" not in str(exec_result):
                                print("      🎉 Task Completed Successfully.")
                                memory.save_memory(f"Task: {user_input}. Status: Success.")
                                break
                                
                            # 5. Failure Loop Feedback
                            current_request += f"\n\nSYSTEM: Code saved and ran, but failed execution:\n{exec_result}\nFix the code."
                            continue

                    # Execution (only if passed review)
                    selected_tool = next((t for t in agent_tools if t.name == tool_name), None)
                    if selected_tool:
                        tool_output = selected_tool.invoke(tool_args)
                        print(f"      ✅ Result: {str(tool_output)[:100]}...")
                    else:
                        tool_output = f"Error: Tool {tool_name} not found."

                    if tool_name == "task_complete":
                        print("      ✅ Task Completed.")
                        memory.save_memory(f"Task: {user_input}. Status: Success.")
                        break

                    # Feedback
                    if "Error" in str(tool_output) or "❌" in str(tool_output):
                         current_request += f"\n\nSYSTEM: Tool '{tool_name}' failed: {tool_output}. Fix it."
                    else:
                         next_prompt = "What is the next step?"
                         if tool_name == "save_file":
                             # Explicit instruction to run the approved code
                             next_prompt = "Code passed review and is saved. You MUST now call 'execute_python_file' to verify runtime behavior."
                         
                         current_request += f"\n\nSYSTEM: Tool '{tool_name}' succeeded. {next_prompt}"

            elif intent == RouteIntent.CASUAL:
                print("   👋 I am a specialized R&D Agent.")

        except Exception as e:
            print(f"   ❌ Main Loop Error: {e}")

if __name__ == "__main__":
    run_app()