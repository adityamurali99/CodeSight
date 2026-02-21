import os
import hmac
import hashlib
import logging
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Header
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Initialize Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-suite")

# Initialize OpenAI Client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Local Imports
from reviewer import analyze_code, v_store
from utils.github_client import GitHubClient

app = FastAPI(title="Augmented AI Code Reviewer")
github = GitHubClient()

# Configuration
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

# --- UTILS ---

async de verify_signature(request: Request, signature: str):
    """Verifies the HMAC signature from GitHub."""
    if not signature:
        raise HTTPException(status_code=401, detail="X-Hub-Signature-256 missing")
    
    payload = await request.body()
    expected_hash = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # signature is format 'sha256=xxxx'
    actual_hash = signature.split('=')[-1]
    
    if not hmac.compare_digest(expected_hash, actual_hash):
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")

async def process_review_task(repo_name: str, pr_number: int, diff_url: str):
    """
    Background worker that handles the heavy lifting:
    Fetch Diff -> AI Analysis -> GitHub Comment.
    """
    try:
        logger.info(f"Task Started: Reviewing {repo_name} PR #{pr_number}")
        
        # 1. Fetch the code changes (the diff)
        diff_text = await github.get_diff(diff_url)
        if not diff_text:
            logger.error("No diff content found.")
            return

        # 2. Execute Augmented AI Analysis (Static Analysis + RAG + Judge)
        # Note: We pass the diff as the code context
        review_result = await analyze_code(diff_text, "python")

        # 3. Format the Markdown Comment
        comment_body = (
            f"## 🤖 AI Code Reviewer\n\n"
            f"### 📋 Summary\n{review_result.summary}\n\n"
            f"### 🧠 Analysis & Logic\n> {review_result.thought_process}\n\n"
            f"### ✅ Suggested Improvement\n"
            f"```python\n{review_result.fixed_code}\n```\n\n"
            f"--- \n*Self-correction audit passed. Feedback grounded in Pylint/Radon data.*"
        )

        # 4. Post back to GitHub PR
        await github.post_comment(repo_name, pr_number, comment_body)
        
    except Exception as e:
        logger.error(f"Error in background task: {str(e)}")

# --- ENDPOINTS ---

@app.on_event("startup")
async def startup_event():
    """Indexes the local repository for RAG context on boot."""
    repo_path = os.getcwd()
    logger.info(f"--- Indexing Repository: {repo_path} ---")
    v_store.index_repository(repo_path)
    logger.info("--- Vector Store Ready ---")

@app.post("/webhook")
async def github_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None)
):
    """Receives and verifies GitHub webhooks, then queues review tasks."""
    # 1. Verify Request Authenticity
    await verify_signature(request, x_hub_signature_256)

    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    # 2. Filter for specific PR actions
    if event_type == "pull_request":
        action = payload.get("action")
        if action in ["opened", "synchronize"]:
            repo_name = payload["repository"]["full_name"]
            pr_number = payload["pull_request"]["number"]
            diff_url = payload["pull_request"]["diff_url"]

            # 3. Offload to Background Worker
            background_tasks.add_task(
                process_review_task, 
                repo_name, 
                pr_number, 
                diff_url
            )
            
            return {"status": "accepted", "details": f"Review queued for PR #{pr_number}"}

    return {"status": "ignored", "details": "Event type or action not supported"}