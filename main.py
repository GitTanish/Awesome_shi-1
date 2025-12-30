import os
from dotenv import load_dotenv

load_dotenv()

from core.models import RouteIntent
from core.router import router_chain

# --- IMPORT SWAP ---
# OLD (Chapter 1):
# from workers.chains import coding_chain, research_chain

# NEW (Chapter 3 & 4):
from workers.another_chains import parallel_research_chain, reflective_coding_chain
# -------------------

def run_app():
    print("Groq-Powered Agent (v0.2 - Parallel & Reflective) Online")
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
                print("Engaging Reflective Coder (Loop)...")
                result = reflective_coding_chain(user_input)
                print(f"\nFinal Code:\n{result}")

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