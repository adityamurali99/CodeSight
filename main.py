import os
import hmac
import hashlib
import logging
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from utils.github_client import GitHubClient
from utils.graph_manager import GraphManager
from reviewer import analyze_code

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-suite")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

github = GitHubClient()
graph_manager = GraphManager()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "code-reviewer-ai",
        "version": "1.1.0"
    }

async def verify_signature(request: Request, signature: str):
    if not signature:
        raise HTTPException(status_code=401, detail="Signature missing")
    payload = await request.body()
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature.split('=')[-1]):
        raise HTTPException(status_code=401, detail="Invalid signature")

async def process_review_task(repo_name: str, pr_number: int, diff_url: str, base_branch: str):
    """
    Note: This background task for GitHub Webhooks still uses YOUR 
    server-side API key (from .env) because GitHub doesn't provide a user key.
    """
    try:
        repo_files = await github.get_repo_contents(repo_name, base_branch)
        graph_manager.build_from_contents(repo_files)
        
        diff_text = await github.get_diff(diff_url)
        # Uses default internal key
        review_result = await analyze_code(diff_text, graph_manager)

        findings_md = ""
        for f in review_result.findings:
            findings_md += f"- **{f.category.upper()}** (Line {f.line_number}): {f.issue}\n"

        comment_body = (
            f"## 🤖 Graph-Augmented AI Review\n\n"
            f"### 📋 Summary\n{review_result.summary}\n\n"
            f"### 🔍 Key Findings\n{findings_md}\n\n"
            f"### 🧠 Thought Process\n> {review_result.thought_process}\n\n"
            f"### ✅ Suggested Improvement\n```python\n{review_result.fixed_code}\n```"
        )

        await github.post_comment(repo_name, pr_number, comment_body)
    except Exception as e:
        logger.error(f"Pipeline Error: {e}")

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks, x_hub_signature_256: str = Header(None)):
    await verify_signature(request, x_hub_signature_256)
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")
    action = payload.get("action")
    
    if event_type == "pull_request" and action in ["opened", "synchronize", "reopened"]:
        background_tasks.add_task(
            process_review_task, 
            payload["repository"]["full_name"],
            payload["pull_request"]["number"],
            payload["pull_request"]["diff_url"],
            payload["pull_request"]["base"]["ref"]
        )
        return {"status": "accepted"}
            
    return {"status": "ignored"}

@app.post("/analyze-local")
async def analyze_local(request: Request):
    """
    Endpoint for VS Code Extension.
    Uses the API key provided by the USER to protect your limits.
    """
    data = await request.json()
    user_code = data.get("code")
    user_key = data.get("apiKey") # Received from VS Code settings
    if not user_key or user_key.strip() == "":
        raise HTTPException(
            status_code=400, 
            detail="API Key is missing. Please enter your key in CodeSight settings."
        )

    try:
        # We pass the user_key into our analyzer
        review_result = await analyze_code(user_code, graph_manager, api_key=user_key)
        return review_result.dict()
    except Exception as e:
        logger.error(f"Local Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)