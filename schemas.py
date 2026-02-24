from pydantic import BaseModel
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class CodeSnippet(BaseModel):
    code: str
    language: str = "python"

class ReviewFinding(BaseModel):
    category: str = Field("General", alias="type")
    line_number: int = Field(1, alias="line") 
    issue: str
    suggestion: Optional[str] = Field(None, alias="fix")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore"
    )

class ReviewResponse(BaseModel):
    thought_process: str
    findings: List[ReviewFinding]
    summary: str
    fixed_code: str 