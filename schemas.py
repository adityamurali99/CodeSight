from pydantic import BaseModel
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class CodeSnippet(BaseModel):
    code: str
    language: str = "python"

class ReviewFinding(BaseModel):
    # This allows the AI to send 'type' or 'category'
    category: str = Field(..., alias="type")
    
    # This allows 'line', 'line_number', or 'line_no'
    line_number: Optional[int] = Field(None, alias="line")
    
    issue: str
    
    # This allows 'fix', 'suggestion', or 'recommended_fix'
    suggestion: str = Field(..., alias="fix")

    # This config is CRITICAL: it allows the model to be populated 
    # using either the field name OR the alias.
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore" # Prevents crashing if AI adds random extra fields
    )

class ReviewResponse(BaseModel):
    thought_process: str
    findings: List[ReviewFinding]
    summary: str
    fixed_code: str 