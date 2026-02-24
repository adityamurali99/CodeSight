import os
import hmac
import hashlib
import logging
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Header
from dotenv import load_dotenv
from utils.factory import client

from utils.github_client import GitHubClient
from utils.graph_manager import GraphManager
from reviewer import analyze_code

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-suite")

app = FastAPI()
github = GitHubClient()
graph_manager = GraphManager()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")


@app.get("/health")
async def health_check():
    """
    Standard health check for cloud providers (Railway, Render, AWS).
    Returns 200 OK if the service is running.
    """
    return {
        "status": "healthy",
        "service": "code-reviewer-ai",
        "version": "1.0.0"
    }

async def verify_signature(request: Request, signature: str):
    if not signature:
        raise HTTPException(status_code=401, detail="Signature missing")
    payload = await request.body()
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature.split('=')[-1]):
        raise HTTPException(status_code=401, detail="Invalid signature")

async def process_review_task(repo_name: str, pr_number: int, diff_url: str, base_branch: str):
    try:
        repo_files = await github.get_repo_contents(repo_name, base_branch)
        graph_manager.build_from_contents(repo_files)
        
        diff_text = await github.get_diff(diff_url)
        review_result = await analyze_code(diff_text, graph_manager)

        comment_body = (
            f"## 🤖 Graph-Augmented AI Review\n\n"
            f"### 📋 Summary\n{review_result.summary}\n\n"
            f"### 🧠 Impact Analysis\n> {review_result.thought_process}\n\n"
            f"### ✅ Suggested Improvement\n```python\n{review_result.fixed_code}\n```"
        )
        await github.post_comment(repo_name, pr_number, comment_body)
    except Exception as e:
        logger.error(f"Pipeline Error: {e}")

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks, x_hub_signature_256: str = Header(None)):
    await verify_signature(request, x_hub_signature_256)
    payload = await request.json()
    
    if request.headers.get("X-GitHub-Event") == "pull_request":
        if payload.get("action") in ["opened", "synchronize"]:
            background_tasks.add_task(
                process_review_task, 
                payload["repository"]["full_name"],
                payload["pull_request"]["number"],
                payload["pull_request"]["diff_url"],
                payload["pull_request"]["base"]["ref"]
            )
            return {"status": "accepted"}
    return {"status": "ignored"}