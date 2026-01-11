import os
import json
import sys
from dotenv import load_dotenv

# Load environment variables FIRST before importing components that use them
load_dotenv()

from core.models import RouteIntent
from core.router import router_chain

# --- UPDATE IMPORTS ---
from workers.chains import (
    coding_chain, 
    execute_research_chain, 
    planner_chain,       # <--- NEW: The Architect
    autonomous_dev_chain # <--- NEW: The Builder
)
from workers.tools import agent_tools

sys.stdout.reconfigure(encoding='utf-8')

# Helper to execute tools (This stays the same)
def execute_tool_calls(ai_message):
    if not ai_message.tool_calls:
        return None
    
    results = []
    for tool_call in ai_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # Find the tool
        selected_tool = next((t for t in agent_tools if t.name == tool_name), None)
        
        if selected_tool:
            # print(f"      Running Tool: {tool_name}") # Optional: less noise
            output = selected_tool.invoke(tool_args)
            results.append(output)
            
    return "\n".join(results)

def run_app():
    print("Groq-Powered Architect Online")
    
    while True:
        user_input = input("\n>> You: ")
        if user_input.lower() in ["exit", "q"]: break

        try:
            # 1. ROUTING
            raw_intent = router_chain.invoke({"input": user_input}).strip()
            try:
                intent = RouteIntent(raw_intent)
            except ValueError:
                intent = RouteIntent.CASUAL
            
            print(f" Intent: {intent.value}")

            # 2. EXECUTION
            if intent == RouteIntent.CODE:
                
                # --- NEW LOGIC: DETECT COMPLEX PROJECTS ---
                if any(word in user_input.lower() for word in ["project", "build", "create app"]):
                    print(" Mode: The Architect (Planning Project)")
                    
                    # A. CALL THE PLANNER (Chapter 6)
                    # This uses the fast model to make the checklist
                    plan = planner_chain.invoke({"request": user_input})
                    print(f"    Plan Approved: {len(plan['steps'])} steps.")
                    
                    # B. EXECUTE THE PLAN (Chapter 5 Loop)
                    for i, step in enumerate(plan['steps']):
                        print(f"\n    Step {i+1}: {step}")
                        
                        # Self-Healing Loop for THIS specific step
                        current_request = step
                        max_retries = 3
                        for attempt in range(max_retries):
                            ai_msg = autonomous_dev_chain.invoke({"request": current_request})
                            tool_output = execute_tool_calls(ai_msg)
                            
                            if tool_output:
                                if "Execution Error" in tool_output: # Error detected
                                    print(f"       Error. Retrying ({attempt+1}/{max_retries})...")
                                    current_request = f"Fix this error: {tool_output}. Goal: {step}"
                                else:
                                    print(f"       Success.")
                                    break # Step complete
                            else:
                                # No tools used, maybe just a comment
                                break
                    
                    print("\n Project Built Successfully.")

                # --- OLD LOGIC: SINGLE FILE TASKS ---
                elif "save" in user_input.lower() or "file" in user_input.lower():
                    print(" Mode: Autonomous Developer (Single Task)")
                    # ... (Your existing self-healing loop for single files goes here) ...
                    ai_msg = autonomous_dev_chain.invoke({"request": user_input})
                    print(execute_tool_calls(ai_msg))

                else:
                    print(" Mode: Simple Coder (No Tools)")
                    print(coding_chain.invoke({"topic": user_input}))

            elif intent == RouteIntent.RESEARCH:
                print(" Mode: Researcher")
                print(execute_research_chain(user_input))

            elif intent == RouteIntent.CASUAL:
                print(" I am a specialized R&D Agent.")

        except Exception as e:
            print(f" Error: {e}")

if __name__ == "__main__":
    run_app()