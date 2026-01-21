from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain_core.utils.function_calling import convert_to_openai_function
from workers.tools import agent_tools

# ==========================================
# CONFIGURATION
# ==========================================
FAST_MODEL = "llama-3.1-8b-instant"
SMART_MODEL = "llama-3.3-70b-versatile"

llm_fast = ChatGroq(model=FAST_MODEL, temperature=0)
llm_smart = ChatGroq(model=SMART_MODEL, temperature=0)

# ==========================================
# CHAPTER 3: PARALLELIZATION (Research)
# ==========================================
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

sub_research_prompt = ChatPromptTemplate.from_template(
    "Analyze this specific aspect briefly: {question}"
)
sub_research_chain = sub_research_prompt | llm_fast | StrOutputParser()

def get_q1(data): return {"question": data.get("q1", "Aspect 1")}
def get_q2(data): return {"question": data.get("q2", "Aspect 2")}
def get_q3(data): return {"question": data.get("q3", "Aspect 3")}

research_branch = RunnableParallel(
    branch1=RunnableLambda(get_q1) | sub_research_chain,
    branch2=RunnableLambda(get_q2) | sub_research_chain,
    branch3=RunnableLambda(get_q3) | sub_research_chain,
)

aggregator_prompt = ChatPromptTemplate.from_template(
    """
    Synthesize these 3 research reports into one cohesive executive summary.
    Report 1: {branch1}
    Report 2: {branch2}
    Report 3: {branch3}
    """
)
aggregator_chain = aggregator_prompt | llm_smart | StrOutputParser()

parallel_research_chain = (query_splitter | research_branch | aggregator_chain)

# ==========================================
# CHAPTER 4: REFLECTION (Simple Coding)
# ==========================================
gen_prompt = ChatPromptTemplate.from_template("Write a Python script for: {request}. Return ONLY the code block.")
generator = gen_prompt | llm_smart | StrOutputParser()

critic_prompt = ChatPromptTemplate.from_template(
    """
    Review this Python code for bugs and security (SQL Injection, etc).
    Code: {code}
    If good, return 'APPROVED'. If bad, return 'FIX_REQUIRED: <reason>'.
    """
)
critic = critic_prompt | llm_fast | StrOutputParser()

fix_prompt = ChatPromptTemplate.from_template("Fix this code: {code}\nFeedback: {feedback}\nReturn ONLY fixed code.")
fixer = fix_prompt | llm_smart | StrOutputParser()

def reflective_coding_chain(request: str):
    print(f"   Drafting code for: {request}...")
    code = generator.invoke({"request": request})
    for attempt in range(2):
        print(f"   Reviewing code (Cycle {attempt+1})...")
        critique = critic.invoke({"code": code})
        if "APPROVED" in critique:
            return code
        else:
            print(f"   Critique: {critique}")
            code = fixer.invoke({"request": request, "code": code, "feedback": critique})
    return code

# Also define a simple coding chain for fallback
coding_chain = generator

# ==========================================
# CHAPTER 5 & 6: THE ARCHITECT & BUILDER
# ==========================================

# 1. THE ARCHITECT (Planner)
planner_prompt = ChatPromptTemplate.from_template(
    """
    You are a Technical Architect.
    Goal: {request}
    
    Break this goal down into a step-by-step checklist.
    CRITICAL RULES:
    1. DO NOT create separate "Create folder" steps. The tool handles that.
    2. ALWAYS use the full relative path (e.g., 'project_name/main.py') for every file.
    3. The list must be strictly sequential.


    Return a STRICT JSON object with a "steps" key containing a list of strings:
    {{
      "steps": [
        "Create and write 'project_name/main.py' with core logic",
        "Create and write 'project_name/utils.py' with helper functions",
        "Run 'project_name/main.py' to verify"
      ]
    }}
    """
)
planner_chain = planner_prompt | llm_fast | JsonOutputParser()

# 2. THE BUILDER (Tool User)
llm_with_tools = llm_smart.bind_tools(agent_tools)

# ... (imports and other chains remain the same) ...

# 2. THE BUILDER (Tool User)
# Ensure you are using the Smart Model (70b) for this!
# If you are using 8b here, CHANGE IT to 70b-versatile or similar.
llm_with_tools = llm_smart.bind_tools(agent_tools)

tool_prompt = ChatPromptTemplate.from_template(
    """
    You are an Autonomous Developer.
    Goal: {request}

    Rules:
    1. If you need to write code, use 'save_file' then 'execute_python_file'.
    2. If the code crashes, ANALYZE the error.
    3. If the error implies a missing library or unknown method, use 'web_search'.
    4. FIX the code and retry.
    
    Do NOT output XML or Markdown for tool calls. Just call the function directly.
    """
)

autonomous_dev_chain = tool_prompt | llm_with_tools

# For Chapter 2 compatibility (Research routing fallback)
def execute_research_chain(topic):
    return parallel_research_chain.invoke({"topic": topic})