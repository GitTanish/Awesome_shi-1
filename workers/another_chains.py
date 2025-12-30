from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda

# ==========================================
# CONFIGURATION
# ==========================================
FAST_MODEL = "llama-3.1-8b-instant"
SMART_MODEL = "llama-3.3-70b-versatile"

llm_fast = ChatGroq(model=FAST_MODEL, temperature=0)
llm_smart = ChatGroq(model=SMART_MODEL, temperature=0)

# ==========================================
# CHAPTER 3: PARALLELIZATION (Robust Version)
# ==========================================

# 1. PLANNER (Splitter)
# We make the prompt stricter to enforce the q1/q2/q3 format
query_splitter_prompt = ChatPromptTemplate.from_template(
    """
    You are a Research Planner. Break down this topic: '{topic}' into 3 distinct search queries.
    
    Return a STRICT JSON object with NO other text. Use exactly these keys:
    {{
      "q1": "First sub-question (Technical)",
      "q2": "Second sub-question (Market/Usage)",
      "q3": "Third sub-question (Risks/Alternatives)"
    }}
    """
)
query_splitter = query_splitter_prompt | llm_fast | JsonOutputParser()

# 2. WORKER (Research Agent)
sub_research_prompt = ChatPromptTemplate.from_template(
    "Analyze this specific aspect briefly: {question}"
)
sub_research_chain = sub_research_prompt | llm_fast | StrOutputParser()

# --- HELPER FUNCTIONS FOR ROBUST EXTRACTION ---
# These handle cases where the model returns "sub-questions": ["..."] instead of "q1" keys
def get_q1(data):
    if "q1" in data: return {"question": data["q1"]}
    if "sub-questions" in data and len(data["sub-questions"]) > 0: return {"question": data["sub-questions"][0]}
    return {"question": f"Aspect 1 of {data.get('title', 'topic')}"}

def get_q2(data):
    if "q2" in data: return {"question": data["q2"]}
    if "sub-questions" in data and len(data["sub-questions"]) > 1: return {"question": data["sub-questions"][1]}
    return {"question": f"Aspect 2 of {data.get('title', 'topic')}"}

def get_q3(data):
    if "q3" in data: return {"question": data["q3"]}
    if "sub-questions" in data and len(data["sub-questions"]) > 2: return {"question": data["sub-questions"][2]}
    return {"question": f"Aspect 3 of {data.get('title', 'topic')}"}

# 3. PARALLEL ENGINE
# We use RunnableLambda to wrap our safety functions
research_branch = RunnableParallel(
    branch1=RunnableLambda(get_q1) | sub_research_chain,
    branch2=RunnableLambda(get_q2) | sub_research_chain,
    branch3=RunnableLambda(get_q3) | sub_research_chain,
)

# 4. AGGREGATOR
aggregator_prompt = ChatPromptTemplate.from_template(
    """
    Synthesize these 3 research reports into one cohesive executive summary.
    
    Report 1: {branch1}
    Report 2: {branch2}
    Report 3: {branch3}
    
    Format with clear headers.
    """
)
aggregator_chain = aggregator_prompt | llm_smart | StrOutputParser()

# THE CHAIN
parallel_research_chain = (
    query_splitter 
    | research_branch 
    | aggregator_chain
)

# ==========================================
# CHAPTER 4: REFLECTION (The Coder)
# ==========================================

gen_prompt = ChatPromptTemplate.from_template(
    "Write a Python script for: {request}. Return ONLY the code block."
)
generator = gen_prompt | llm_smart | StrOutputParser()

critic_prompt = ChatPromptTemplate.from_template(
    """
    Review this Python code for:
    1. SYNTAX errors.
    2. SECURITY vulnerabilities (SQL Injection, Remote Code Execution).
    3. LOGIC bugs.
    
    Code:
    {code}
    
    If you see 'f"SELECT...' or 'f"DELETE...' with variables, FLAG IT as SQL Injection immediately.
    
    If it is good, return 'APPROVED'.
    If it has bugs, return 'FIX_REQUIRED: <explanation>'.
    """
)
critic = critic_prompt | llm_fast | StrOutputParser()

fix_prompt = ChatPromptTemplate.from_template(
    """
    Fix this code based on feedback: {feedback}
    Original Request: {request}
    Code: {code}
    Return ONLY the fixed code.
    """
)
fixer = fix_prompt | llm_smart | StrOutputParser()

def reflective_coding_chain(request: str):
    print(f"   Drafting code for: {request}...")
    code = generator.invoke({"request": request})
    
    for attempt in range(2):
        print(f"   Reviewing code (Cycle {attempt+1})...")
        critique = critic.invoke({"code": code})
        
        if "APPROVED" in critique:
            print("   Code approved.")
            return code
        else:
            print(f"   Critique: {critique}")
            print("   Fixing code...")
            code = fixer.invoke({
                "request": request,
                "code": code,
                "feedback": critique
            })
            
    return code