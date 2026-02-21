# reviewer.py
import json
from utils.analyzer import StaticAnalyzer
from utils.vector_store import VectorStore
from utils.sandbox import validate_code_safety # Our new utility
from schemas import ReviewResponse
from prompts import SYSTEM_PROMPT, AUDITOR_PROMPT

v_store = VectorStore()

async def analyze_code(code: str, language: str) -> ReviewResponse:
    from main import client
    
    # STEP 1: Pre-processing (Static Analysis + RAG)
    static_data = StaticAnalyzer.run_analysis(code)
    context = v_store.query_context(code)
    
    # STEP 2: Agent 1 - Initial Review
    initial_payload = f"CODE:\n{code}\n\nSTATIC ANALYSIS:\n{static_data}\n\nCONTEXT:\n{context}"
    resp1 = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": initial_payload}],
        response_format={"type": "json_object"}
    )
    draft_content = resp1.choices[0].message.content
    draft_json = json.loads(draft_content)

    # STEP 3: Sandbox Validation (The "Smoke Test")
    fixed_candidate = draft_json.get("fixed_code", "")
    sandbox_result = validate_code_safety(fixed_candidate)

    # STEP 4: Agent 2 - The Judge (Reflection & Audit)
    final_payload = (
        f"STATIC ANALYSIS DATA: {static_data}\n"
        f"SANDBOX RESULTS: {sandbox_result}\n"
        f"DRAFT TO JUDGE: {draft_content}"
    )
    
    resp2 = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": AUDITOR_PROMPT}, {"role": "user", "content": final_payload}],
        response_format={"type": "json_object"}
    )
    
    return ReviewResponse.model_validate_json(resp2.choices[0].message.content)