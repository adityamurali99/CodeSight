import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
# One single source of truth for the AI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))