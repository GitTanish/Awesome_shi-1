from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. configuration
# if llama 3.1 disappears, you only change this one line.
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# 2. the robust system-human structure
# we DO NOT import RouteIntent. we explicitly state the contract here.
# this ensures this file is self-contained.
route_prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are a precise classification system.
    Classify the user input into EXACTLY one of these categories:
    
    1. CODE
    - Writing scripts, debugging, "save this", "build a project".
    
    2. RESEARCH
    - Explaining concepts, "how does X work", searching web.
    
    3. CASUAL
    - Greetings, small talk, "hi".
    
    Return ONLY the category name. No punctuation.
    """),
    ("human", "{input}")
])

# 3. the chain (with the safety adapter)
# THE ADAPTER (The "Engineering Solution")
def parse_intent(text):
    # 1. Normalize: "  Code. " -> "CODE."
    text = text.strip().upper()
    
    # 2. Match: Look for the signal in the noise
    if "CODE" in text: return "CODE"
    if "RESEARCH" in text: return "RESEARCH"
    
    # 3. Fallback: If unsure, be safe
    return "CASUAL"

router_chain = (
    route_prompt 
    | llm 
    | StrOutputParser() 
    | parse_intent # <--- Applies the logic above automatically
)