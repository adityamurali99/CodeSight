from pydantic import BaseModel
from typing import List, Optional

class CodeSnippet(BaseModel):
    code: str
    language: str = "python"

class ReviewFinding(BaseModel):
    category: str
    line_number: Optional[int] = None
    issue: str
    suggestion: str

class ReviewResponse(BaseModel):
    thought_process: str
    findings: List[ReviewFinding]
    summary: str
    fixed_code: str 