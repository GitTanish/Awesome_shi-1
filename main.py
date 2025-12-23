import os
from dotenv import load_dotenv
load_dotenv()
from core.models import RouteIntent
from core.router import router_chain
from workers.chains import coding_chain, execute_research_chain



def run_app():
    print("Groq-Powered R&D Agent Online (v0.1)")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input(">> You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        try:
            # PHASE 1: ROUTING (The Brain)
            # --------------------------------
            print("   -> Classifying intent...")
            raw_intent = router_chain.invoke({"input": user_input}).strip()
            
            # Validation: Ensure the Router didn't hallucinate a fake category
            try:
                intent = RouteIntent(raw_intent)
            except ValueError:
                intent = RouteIntent.CASUAL # Fallback safe mode

            print(f"   -> Route Detected: {intent.value}")

            # PHASE 2: EXECUTION (The Muscle)
            # --------------------------------
            if intent == RouteIntent.CODE:
                print("   -> Engaging Python Engineer...")
                result = coding_chain.invoke({"topic": user_input})
                print(f"\n{result}\n")

            elif intent == RouteIntent.RESEARCH:
                print("   -> Engaging Research Analyst (Chained Process)...")
                result = execute_research_chain(user_input)
                print(f"\nReport:\n{result}\n")

            elif intent == RouteIntent.CASUAL:
                print("\nI am a specialized R&D Agent. Please ask me to code or research something.\n")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run_app()