import json
import os
from openai import AsyncOpenAI  
from utils.analyzer import StaticAnalyzer
from schemas import ReviewResponse, AuditResponse
from prompts import SYSTEM_PROMPT, AUDITOR_PROMPT

async def analyze_code(diff_text: str, graph: object, api_key: str = None) -> ReviewResponse:
    print("🚀 BACKGROUND TASK: analyze_code started", flush=True)
    
    if api_key is not None:
        current_key = api_key
    else:
        current_key = os.getenv("OPENAI_API_KEY")

    if not current_key or current_key.strip() == "":
        raise ValueError("No valid OpenAI API key provided.")

    client = AsyncOpenAI(api_key=current_key)

    is_diff = diff_text.startswith("diff --git") or "@@" in diff_text

    if is_diff:
        lines = diff_text.split('\n')
        clean_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('+') and not stripped_line.startswith('+++'):
                clean_lines.append(line[1:])  # Fix: was line[line.find('+')+1:], which breaks when '+' not at index 0
        clean_code = "\n".join(clean_lines).strip()
    else:
        clean_code = diff_text.strip()

    if not clean_code:
        return ReviewResponse(
            thought_process="Analysis skipped: No valid code content detected.",
            findings=[],
            summary="No new code detected for analysis.",
            fixed_code=""
        )

    # --- CONTEXT & ANALYSIS ---
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
    final_payload = (
        f"### TARGET CODE:\n{clean_code}\n\n"
        f"### STATIC ANALYSIS:\n{static_data}\n\n"
        f"### REPOSITORY CONTEXT:\nDependencies: {dependency_context}\nImpact: {impact_context}\n\n"
        f"### REVIEWER DRAFT:\n{json.dumps(draft, indent=2)}"
    )

    resp2 = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": AUDITOR_PROMPT}, 
            {"role": "user", "content": final_payload}
        ],
        response_format={"type": "json_object"}
    )

    audit_result = AuditResponse.model_validate_json(resp2.choices[0].message.content)

    return ReviewResponse(
        thought_process=f"[Verdict: {audit_result.verdict}] {draft.get('thought_process', '')}",
        findings=audit_result.final_findings,
        summary=audit_result.summary,
        fixed_code=audit_result.fixed_code
    )