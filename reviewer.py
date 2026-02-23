import json
from utils.analyzer import StaticAnalyzer
from utils.sandbox import validate_code_safety
from schemas import ReviewResponse
from prompts import SYSTEM_PROMPT, AUDITOR_PROMPT

async def analyze_code(diff_text: str, graph: object) -> ReviewResponse:
    from main import client
    
    clean_code = "\n".join([l[1:] for l in diff_text.split('\n') if l.startswith('+') and not l.startswith('+++')])
    
    # Deterministic Context Retrieval
    dependency_context = graph.get_context(clean_code, hops=2)
    impact_context = graph.get_impact_analysis(clean_code, hops=1)
    static_data = StaticAnalyzer.run_analysis(clean_code)
    
    # Agent 1: Review
    payload = (
        f"CODE:\n{clean_code}\n\n"
        f"STATIC ANALYSIS:\n{static_data}\n\n"
        f"DEPENDENCIES:\n{dependency_context}\n\n"
        f"POTENTIAL IMPACT:\n{impact_context}"
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