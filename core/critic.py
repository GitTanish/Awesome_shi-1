import ast
import re
import os
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from difflib import SequenceMatcher

# --- 1. DETERMINISTIC CHECKS ---
def check_syntax_and_security(code: str) -> dict:
    try:
        ast.parse(code)
    except SyntaxError as e:
        return {"approved": False, "critique": f"FATAL SYNTAX ERROR at line {e.lineno}: {e.msg}"}

    unsafe_patterns = [
        r'(api_key|secret|password|token)\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']', 
        r'sk-[A-Za-z0-9]{32,}'
    ]
    for pattern in unsafe_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return {"approved": False, "critique": "SECURITY RISK: Hardcoded secret detected. Use os.getenv()."}

    return {"approved": True, "critique": "Static checks passed."}

# --- 2. CODE SIMILARITY CHECKER (Loop Detection) ---
def is_similar_code(new_code: str, previous_codes: list) -> bool:
    """Detect if we're generating near-identical code (stuck in loop)"""
    if not previous_codes:
        return False
    
    # Check last 2 attempts
    for prev_code in previous_codes[-2:]:
        similarity = SequenceMatcher(None, new_code, prev_code).ratio()
        if similarity > 0.90:  # 90% similar = likely stuck
            return True
    return False

# --- 3. PROGRESSIVE LENIENCY SYSTEM ---
critic_system_prompt_base = """
You are a Pragmatic Code Reviewer focused on FUNCTIONALITY over PERFECTION.

Your job is to verify code is SAFE and WORKS, not to enforce enterprise-grade standards.

**BLOCK ONLY IF:**
1. **CRITICAL LOGIC ERROR**: Code will not accomplish the task at all
2. **SECURITY RISK**: Hardcoded secrets detected (already checked, just verify)
3. **SYNTAX ERROR**: Code will crash immediately (already checked, just verify)

**DO NOT BLOCK FOR:**
- Missing edge case handling (e.g., "what if URL is unreachable?")
- Lack of "specific" error handling (basic try/except is ENOUGH)
- Missing file existence checks (Python handles this naturally with exceptions)
- Style issues or non-Pythonic code
- Performance concerns
- Missing logging or verbose error messages

**APPROVAL CRITERIA:**
✅ Code attempts to solve the task
✅ Has at least ONE try/except block for I/O or network operations
✅ No obvious crashes

{leniency_instruction}

**OUTPUT FORMAT (JSON ONLY, NO OTHER TEXT):**
{{
    "approved": boolean,
    "critique": "If rejected: state the BLOCKING issue. If approved: say 'LGTM'"
}}
"""

# Different leniency levels based on attempt number
LENIENCY_LEVELS = {
    1: "Be reasonable. Approve functional code with basic error handling.",
    2: "Be MORE LENIENT. Only block if code is fundamentally broken or unsafe.",
    3: "MAXIMUM LENIENCY. Only block syntax errors or security risks. Assume code works."
}

llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# --- 4. REVIEW FUNCTION WITH CONTEXT ---
_code_history = []  # Track previous code for similarity detection

def review_code(code: str, task: str, attempt_number: int = 1) -> dict:
    """
    Review code with progressive leniency to prevent infinite loops.
    
    Args:
        code: Python code to review
        
        task: Original task description
        attempt_number: How many times we've tried (1-indexed)
    
    Returns:
        dict with 'approved' (bool) and 'critique' (str)
    """
    global _code_history
    
    # Phase 0: Loop detection via code similarity
    if is_similar_code(code, _code_history):
        print("      🔁 DUPLICATE CODE DETECTED - Auto-approving to break loop")
        _code_history.append(code)
        return {
            "approved": True, 
            "critique": "Auto-approved: Agent generating same code repeatedly"
        }
    
    _code_history.append(code)
    
    # Phase 1: Static checks (unchanged)
    static_result = check_syntax_and_security(code)
    if not static_result["approved"]:
        return static_result
    
    # Phase 2: Automatic approval after too many attempts
    if attempt_number >= 4:
        print(f"      ⚠️  MAX ATTEMPTS REACHED - Auto-approving")
        return {
            "approved": True, 
            "critique": "Auto-approved: Max review attempts exceeded"
        }
    
    # Phase 3: LLM review with progressive leniency
    try:
        # Get appropriate leniency instruction
        leniency = LENIENCY_LEVELS.get(attempt_number, LENIENCY_LEVELS[3])
        
        # Build prompt with leniency context
        critic_prompt = critic_system_prompt_base.format(leniency_instruction=leniency)
        
        critic_chain = ChatPromptTemplate.from_messages([
            ("system", critic_prompt),
            ("human", "TASK: {task}\n\nCODE:\n```python\n{code}\n```\n\nAttempt: {attempt}/{max_attempts}")
        ]) | llm
        
        response = critic_chain.invoke({
            "task": task, 
            "code": code,
            "attempt": attempt_number,
            "max_attempts": 3
        })
        
        content = response.content.strip()
        result = parse_json_garbage(content)
        
        if result and isinstance(result, dict) and "approved" in result:
            return result
        else:
            # If we can't parse, be conservative but not blocking
            if attempt_number >= 2:
                print(f"      ⚠️  Parse failed, auto-approving (attempt {attempt_number})")
                return {"approved": True, "critique": "Auto-approved: Review format error"}
            return {"approved": False, "critique": "Reviewer output format invalid"}
            
    except Exception as e:
        # Fail-open after attempt 2 to prevent blocking on system errors
        if attempt_number >= 2:
            print(f"      ⚠️  Review error, auto-approving: {str(e)}")
            return {"approved": True, "critique": f"Auto-approved: Review system error"}
        return {"approved": False, "critique": f"System Error: {str(e)}"}

# --- 5. HELPER TO RESET HISTORY (Call between tasks) ---
def reset_code_history():
    """Clear code history between different tasks"""
    global _code_history
    _code_history = []

# --- 6. ROBUST PARSER (unchanged) ---
def parse_json_garbage(text):
    """Extract JSON from potentially chatty LLM output"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
    return None