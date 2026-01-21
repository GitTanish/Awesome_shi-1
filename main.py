import os
import sys
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables FIRST
load_dotenv()

from core.models import RouteIntent
from core.router import router_chain

# --- IMPORTS ---
from workers.chains import (
    coding_chain, 
    execute_research_chain, 
    planner_chain,       # The Architect
    autonomous_dev_chain # The Builder
)
from workers.tools import agent_tools

sys.stdout.reconfigure(encoding='utf-8')

# Helper to execute tools
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
            # print(f"      🛠️ Tool: {tool_name}") # Uncomment for verbose debugging
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
            # The router now uses the robust adapter we built
            raw_intent = router_chain.invoke({"input": user_input})
            print(f"   🐛 DEBUG: Router returned -> '{raw_intent}'")
            
            try:
                intent = RouteIntent(raw_intent)
            except ValueError:
                intent = RouteIntent.CASUAL
            
            print(f"   🚦 Intent: {intent.value}")

            # 2. EXECUTION
            if intent == RouteIntent.CODE:
                
                # A. COMPLEX PROJECTS (The Architect)
                if any(word in user_input.lower() for word in ["project", "build", "create app"]):
                    print("   🏗️ Mode: The Architect (Planning Project)")
                    
                    # 1. Plan
                    plan = planner_chain.invoke({"request": user_input})
                    print(f"      Plan Approved: {len(plan['steps'])} steps.")
                    
                    # 2. Execute Step-by-Step
                    for i, step in enumerate(plan['steps']):
                        print(f"\n      Step {i+1}: {step}")
                        
                        # Self-Healing Loop for THIS step
                        current_request = step
                        max_retries = 3
                        for attempt in range(max_retries):
                            ai_msg = autonomous_dev_chain.invoke({"request": current_request})
                            tool_output = execute_tool_calls(ai_msg)
                            
                            if tool_output:
                                if "❌ Execution Error" in tool_output:
                                    print(f"         ⚠️ Error detected (Attempt {attempt+1}/{max_retries})")
                                    current_request = f"Fix this error: {tool_output}. Goal: {step}. Use 'web_search' if needed."
                                else:
                                    print(f"         ✅ Step Success.")
                                    break
                            else:
                                break
                    
                    print("\n   ✨ Project Built Successfully.")

                # B. SINGLE TASK (Self-Healing Mode) <-- THIS IS THE UPGRADE
                elif "save" in user_input.lower() or "file" in user_input.lower() or "script" in user_input.lower():
                    print("   🤖 Mode: Autonomous Developer (Single Task)")
                    
                    current_request = user_input
                    max_retries = 3
                    
                    for attempt in range(max_retries):
                        print(f"      🔄 Iteration {attempt+1}/{max_retries}...")
                        
                        # 1. Think & Act
                        ai_msg = autonomous_dev_chain.invoke({"request": current_request})
                        
                        # 2. Execute Tools
                        tool_output = execute_tool_calls(ai_msg)
                        
                        # 3. Analyze Result
                        if tool_output:
                            if "❌ Execution Error" in tool_output:
                                print(f"         ⚠️ Runtime Error detected!")
                                # FEEDBACK LOOP: Tell the agent it failed and to use its brain (search)
                                current_request = (
                                    f"The previous code failed:\n{tool_output}\n"
                                    f"Original Goal: {user_input}\n"
                                    f"CRITICAL: Use 'web_search' if you don't know how to fix this."
                                )
                            else:
                                print(f"         ✅ Success:\n{tool_output}")
                                break # Exit loop on success
                        else:
                            print(f"      ℹ️  Agent Message: {ai_msg.content}")
                            break

                # C. SIMPLE CODE SNIPPETS
                else:
                    print("   ⚡ Mode: Simple Coder (No Tools)")
                    print(coding_chain.invoke({"topic": user_input}))

            elif intent == RouteIntent.RESEARCH:
                print("   🔎 Mode: Researcher")
                print(execute_research_chain(user_input))

            elif intent == RouteIntent.CASUAL:
                print("   👋 I am a specialized R&D Agent.")

        except Exception as e:
            print(f"   ❌ System Error: {e}")

if __name__ == "__main__":
    run_app()