from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

route_prompt = ChatPromptTemplate.from_messages([
    ("system", """
    You are a classifier. Determine the user's intent.
    
    Categories:
    1. CODE: Writing scripts, fixing bugs, running code, saving files, or building projects.
    2. RESEARCH: Pure information gathering, explaining concepts, or summarizing history.
    3. CASUAL: Greetings and small talk.
    
    CRITICAL RULE: If the user asks to write code, run a script, or fix an error, the intent is ALWAYS 'CODE', even if they also mention "searching" or "researching" libraries.
    
    Return ONLY one word: CODE, RESEARCH, or CASUAL.
    """),
    ("human", "{input}")
])

# The Adapter Function (Keeps it safe)
def parse_intent(text):
    text = text.strip().upper()
    if "CODE" in text: return "CODE"
    if "RESEARCH" in text: return "RESEARCH"
    return "CASUAL"

router_chain = (
    route_prompt 
    | llm 
    | StrOutputParser() 
    | parse_intent 
)