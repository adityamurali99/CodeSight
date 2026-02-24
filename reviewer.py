import json
from utils.analyzer import StaticAnalyzer
from utils.sandbox import validate_code_safety
from schemas import ReviewResponse
from prompts import SYSTEM_PROMPT, AUDITOR_PROMPT
from utils.factory import client

async def analyze_code(diff_text: str, graph: object) -> ReviewResponse:
    try:
        # your existing code here
        print("Starting AI analysis...", flush=True)
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}", flush=True)

    lines = diff_text.split('\n')
    clean_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        # Ensure it's an addition but NOT the file header
        if stripped_line.startswith('+') and not stripped_line.startswith('+++'):
            # Use lstrip to remove only the '+' but keep the indentation
            # Note: line[1:] is usually safer for indentation than stripped_line
            clean_lines.append(line[line.find('+')+1:]) 
            
    clean_code = "\n".join(clean_lines).strip()
    
    if not clean_code.strip():
        return ReviewResponse(
            thought_process="Analysis skipped: The provided diff contained no valid code additions.",
            findings=[],  # Matches List[ReviewFinding]
            summary="No new code detected in this diff.",
            fixed_code=""
        )

    # --- Keep the rest of your logic as is ---
    dependency_context = graph.get_context(clean_code, hops=2)
    impact_context = graph.get_impact_analysis(clean_code, hops=1)
    static_data = StaticAnalyzer.run_analysis(clean_code)
    
    # Agent 1: Review
    payload = (
        f"### TARGET CODE:\n{clean_code}\n\n"
        f"### STATIC ANALYSIS:\n{static_data if static_data else 'No static analysis issues found.'}\n\n"
        f"### REPOSITORY CONTEXT:\nDependencies: {dependency_context}\nImpact: {impact_context}"
    )
    
    resp1 = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": payload}],
        response_format={"type": "json_object"}
    )
    draft = json.loads(resp1.choices[0].message.content)

    # Agent 2: Audit
    sandbox = validate_code_safety(draft.get("fixed_code", ""))
    final_payload = f"DATA: {static_data}\nSANDBOX: {sandbox}\nDRAFT: {draft}"
    
    resp2 = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": AUDITOR_PROMPT}, {"role": "user", "content": final_payload}],
        response_format={"type": "json_object"}
    )
    
    return ReviewResponse.model_validate_json(resp2.choices[0].message.content)