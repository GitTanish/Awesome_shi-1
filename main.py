import os
import json
from dotenv import load_dotenv

load_dotenv()

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
    print("🚀 Groq-Powered Agent (v0.3 - Autonomous Tools) Online")
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

            print(f"Intent: {intent.value}")

            # 2. EXECUTION (Swapped to new chains)
            if intent == RouteIntent.CODE:
                # NEW: Check if the user specifically asked to SAVE a file
                if "save" in user_input.lower() or "file" in user_input.lower():
                    print("🤖 Mode: Autonomous Developer (Tool Use)")
                    response_msg = autonomous_dev_chain.invoke({"request": user_input})
                    result = execute_tool_calls(response_msg)
                    print(f"\\n✅ Final Result: {result}")
                else:
                    print("Engaging Reflective Coder (Loop)...")
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