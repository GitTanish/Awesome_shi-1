'''
We break the research task into Analyze $\rightarrow$ Summarize. The output of step 1 becomes the input of step 2. This forces the model to "think" before it "speaks."
'''
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# smart brain (larger model for complex reasoning and coding)
llm_worker = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# Worker A: CODER
coding_prompt = ChatPromptTemplate.from_template(
"""
    Role: Python Engineer.
    Task: Write a script for: {topic}
    
    Constraints: 
    - Type hints required.
    - No markdown text, JUST code.
    - Use standard libraries.
    """    
)
coding_chain = coding_prompt | llm_worker | StrOutputParser()

# Worker B: RESEARCHER (Prompt Chaining)
# Link 1: Analysis
analysis_prompt = ChatPromptTemplate.from_template(
"Analyze '{topic}'. List 3 technical pros and 3 cons. Be brief."    
)

# LINK 2: writer
summary_prompt = ChatPromptTemplate.from_template(
"Synthesize this analysis into a 3-sentence executive summary:\n\n{analysis}"
)

def execute_research_chain(topic: str):
    """
    Manually chains the steps together: Input -> Analysis -> Summary
    """
    # Step 1: Analyze
    chain_1 = analysis_prompt | llm_worker | StrOutputParser()
    analysis_result = chain_1.invoke({"topic": topic})
    
    # Step 2: Summarize (The output of Step 1 is passed here)
    chain_2 = summary_prompt | llm_worker | StrOutputParser()
    final_result = chain_2.invoke({"analysis": analysis_result})
    
    return final_result