from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.models import RouteIntent

# fast brain
# temp =0 because, classification must be deterministic
llm_router = ChatGroq(model="llama3.2", temperature=0)

# sys prompt
system_prompt = f"""
You are a precise classifier. 
Classify the user input into EXACTLY one of these categories:
{RouteIntent.list_options()}

Rules:
1. If the user asks for code, functions, or implementation -> Return '{RouteIntent.CODE.value}'
2. If the user asks for explanation, history, or how-to -> Return '{RouteIntent.RESEARCH.value}'
3. For greetings or other chatter -> Return '{RouteIntent.CASUAL.value}'

OUTPUT ONLY THE CATEGORY NAME. NO OTHER TEXT.
"""
# Prompt template
route_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])

# The chain (prompt -> llm -> string parser)
router_chain = route_prompt | llm_router | StrOutputParser()