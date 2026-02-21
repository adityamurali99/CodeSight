import hmac
import hashlib
import os
import json
import logging
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Header
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
logger = logging.getLogger("webhook-receiver")

# CONFIG
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

async def verify_signature(request: Request, signature: str):
    """Verifies that the payload comes from GitHub."""
    if not signature:
        raise HTTPException(status_code=401, detail="Signature missing")
    
    # GitHub sends signature as 'sha256=hash'
    hash_type, signature_hash = signature.split('=')
    if hash_type != 'sha256':
        raise HTTPException(status_code=400, detail="Invalid hash type")

    payload = await request.body()
    expected_hash = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, signature_hash):
        raise HTTPException(status_code=401, detail="Invalid signature")

def process_review_task(repo_name: str, pr_number: int, diff_url: str):
    """
    Placeholder for the heavy lifting. 
    This runs in the background after the 200 OK is sent.
    """
    logger.info(f"Starting analysis for {repo_name} PR #{pr_number}")
    # Integration with analyze_code logic goes here
    pass

@app.post("/webhook")
async def github_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None)
):
    # 1. Security Handshake
    await verify_signature(request, x_hub_signature_256)

    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    # 2. Filter for Pull Request events
    if event_type == "pull_request":
        action = payload.get("action")
        if action in ["opened", "synchronize"]:
            # 3. Extraction
            repo_info = {
                "repo_full_name": payload["repository"]["full_name"],
                "pr_number": payload["pull_request"]["number"],
                "diff_url": payload["pull_request"]["diff_url"]
            }
            
            # 4. Immediate Handover to Background
            background_tasks.add_task(
                process_review_task, 
                repo_info["repo_full_name"], 
                repo_info["pr_number"], 
                repo_info["diff_url"]
            )
            
            return {"status": "accepted", "message": "Review task queued"}

    return {"status": "ignored", "message": "Event not relevant"}