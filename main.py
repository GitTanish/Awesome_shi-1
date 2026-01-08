import os
import json
from dotenv import load_dotenv

load_dotenv()
import sys
# Force UTF-8 encoding for Windows consoles to support emojis like 🚀
sys.stdout.reconfigure(encoding='utf-8')

from core.models import RouteIntent
from core.router import router_chain

# --- IMPORT SWAP ---
# OLD (Chapter 1):
# from workers.chains import coding_chain, research_chain

# NEW (Chapter 3 & 4):
from workers.another_chains import parallel_research_chain, reflective_coding_chain, autonomous_dev_chain
from workers.tools import agent_tools
# -------------------

# Helper to execute tools
def execute_tool_calls(ai_message):
    """
    Checks if the AI wants to call a tool, and if so, runs it.
    """
    # 1. Check if there are tool calls in the response
    if not ai_message.tool_calls:
        print("ℹ️  Agent decided NOT to use tools. Returning text.")
        return ai_message.content

    results = []
    # 2. Iterate through requested tools
    for tool_call in ai_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        print(f"🛠️  Agent is calling tool: {tool_name} with args: {tool_args}")
        
        # 3. Find the matching function
        selected_tool = next((t for t in agent_tools if t.name == tool_name), None)
        
        if selected_tool:
            # 4. Run the function
            output = selected_tool.invoke(tool_args)
            print(f"   ↳ Tool Output: {output}")
            results.append(output)
            
    return "\\n".join(results)

def run_app():
    print("🚀 Groq-Powered Agent (v0.4 - Self-Healing) Online")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("\n>> You: ")
        if user_input.lower() in ["exit", "q"]: break

        try:
            # 1. ROUTING (Chapter 2 - Still active!)
            raw_intent = router_chain.invoke({"input": user_input}).strip()
            try:
                intent = RouteIntent(raw_intent)
            except ValueError:
                intent = RouteIntent.CASUAL

            print(f"🚦 Intent: {intent.value}")

            # 2. EXECUTION (Swapped to new chains)
            if intent == RouteIntent.CODE:
                # CHECK FOR AUTONOMOUS MODE
                if "save" in user_input.lower() or "file" in user_input.lower():
                    print("🤖 Mode: Autonomous Developer (Self-Healing)")
                    
                    # --- THE SELF-HEALING LOOP ---
                    current_request = user_input
                    max_retries = 3
                    
                    for attempt in range(max_retries):
                        print(f"   🔄 Iteration {attempt + 1}/{max_retries}...")
                        
                        # A. Ask the Brain
                        ai_msg = autonomous_dev_chain.invoke({"request": current_request})
                        
                        # B. Check for Tool Calls
                        if not ai_msg.tool_calls:
                            print("   ℹ️  Agent finished (no more tools needed).")
                            print(f"\nFinal Reply: {ai_msg.content}")
                            break
                        
                        # C. Execute Tools (The Hands)
                        tool_output = execute_tool_calls(ai_msg)
                        
                        # D. The "Eye": Check if it worked
                        if "❌ Execution Error" in tool_output:
                            print(f"   ⚠️ Runtime Error detected!")
                            # KEY TRICK: We update the request to force a fix
                            current_request = (
                                f"The previous code failed with this error:\\n{tool_output}\\n"
                                f"Original Goal: {user_input}\\n"
                                f"Please FIX the code, SAVE it again, and RUN it."
                            )
                        elif "✅ Execution Success" in tool_output:
                            print(f"\\n✅ Task Completed Successfully:\\n{tool_output}")
                            break
                        else:
                            # If it just saved but didn't run, we assume success or let it continue
                            print(f"   ↳ Output: {tool_output}")
                    
                    else:
                        print("❌ Max retries reached. I couldn't fix the bug.")
                    # -----------------------------

                else:
                    print("⚡ Mode: Reflective Coder (No File I/O)")
                    result = reflective_coding_chain(user_input)
                    print(f"\\nFinal Code:\\n{result}")

            elif intent == RouteIntent.RESEARCH:
                print("Engaging Parallel Researcher (Split -> Merge)...")
                result = parallel_research_chain.invoke({"topic": user_input})
                print(f"\nResearch Report:\n{result}")

            elif intent == RouteIntent.CASUAL:
                print("I am a specialized R&D Agent.")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_app()