import json
from utils.analyzer import StaticAnalyzer
from utils.sandbox import validate_code_safety
from schemas import ReviewResponse
from prompts import SYSTEM_PROMPT, AUDITOR_PROMPT
from utils.factory import client

async def analyze_code(diff_text: str, graph: object) -> ReviewResponse:
    print("🚀 BACKGROUND TASK: analyze_code started", flush=True)
    
    # --- 1. SMART CONTENT DETECTION ---
    # Check if input is a Git Diff (GitHub) or Raw Code (VS Code)
    is_diff = diff_text.startswith("diff --git") or "@@" in diff_text

    if is_diff:
        print("DEBUG: Processing as GitHub Diff", flush=True)
        lines = diff_text.split('\n')
        clean_lines = []
        for line in lines:
            stripped_line = line.strip()
            # Extract only the added lines (+)
            if stripped_line.startswith('+') and not stripped_line.startswith('+++'):
                # Preserve indentation by finding the first '+'
                clean_lines.append(line[line.find('+')+1:]) 
        clean_code = "\n".join(clean_lines).strip()
    else:
        print("DEBUG: Processing as Raw VS Code text", flush=True)
        # No diff markers found, treat the entire payload as the target code
        clean_code = diff_text.strip()

    # --- 2. VALIDATION ---
    if not clean_code:
        return ReviewResponse(
            thought_process="Analysis skipped: No valid code content detected in the input.",
            findings=[],
            summary="No new code detected for analysis.",
            fixed_code=""
        )

    print(f"DEBUG: FINAL CLEAN CODE (first 100 chars):\n{clean_code[:100]}", flush=True)

    # --- 3. CONTEXT & ANALYSIS ---
    dependency_context = graph.get_context(clean_code, hops=2)
    impact_context = graph.get_impact_analysis(clean_code, hops=1)
    static_data = StaticAnalyzer.run_analysis(clean_code)
    
    # Agent 1: Reviewer
    payload = (
        f"### TARGET CODE:\n{clean_code}\n\n"
        f"### STATIC ANALYSIS:\n{static_data if static_data else 'No static analysis issues found.'}\n\n"
        f"### REPOSITORY CONTEXT:\nDependencies: {dependency_context}\nImpact: {impact_context}"
    )
    
    resp1 = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT}, 
            {"role": "user", "content": payload}
        ],
        response_format={"type": "json_object"}
    )
    draft = json.loads(resp1.choices[0].message.content)

    # Agent 2: Auditor
    sandbox = validate_code_safety(draft.get("fixed_code", ""))
    final_payload = f"DATA: {static_data}\nSANDBOX: {sandbox}\nDRAFT: {draft}"
    
    resp2 = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": AUDITOR_PROMPT}, 
            {"role": "user", "content": final_payload}
        ],
        response_format={"type": "json_object"}
    )
    
    # --- 4. RETURN STRUCTURED RESPONSE ---
    return ReviewResponse.model_validate_json(resp2.choices[0].message.content)