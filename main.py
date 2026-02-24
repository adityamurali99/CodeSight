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

async def process_review_task(repo_name, pr_number, diff_url, base_ref):
    # FORCE A LOG IMMEDIATELY
    print(f"DEBUG: Starting task for PR {pr_number}", flush=True)
    try:
        # Comment out the complex stuff for ONE test run
        # static_data = StaticAnalyzer.run_analysis(clean_code) 
        
        # Just print the payload size
        print(f"DEBUG: Task is alive for {repo_name}", flush=True)
        
        # Call your analysis
        # ... rest of code
    except Exception as e:
        print(f"ERROR IN TASK: {str(e)}", flush=True)


@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks, x_hub_signature_256: str = Header(None)):
    await verify_signature(request, x_hub_signature_256)
    payload = await request.json()
    
    event_type = request.headers.get("X-GitHub-Event")
    action = payload.get("action")
    
    print(f"Received {event_type} with action: {action}")

    #check comment  
    if event_type == "pull_request":
        if action in ["opened", "synchronize", "reopened"]:
            background_tasks.add_task(
                process_review_task, 
                payload["repository"]["full_name"],
                payload["pull_request"]["number"],
                payload["pull_request"]["diff_url"],
                payload["pull_request"]["base"]["ref"]
            )
            return {"status": "accepted"}
            
    return {"status": "ignored", "reason": f"Action {action} on {event_type} not tracked"}