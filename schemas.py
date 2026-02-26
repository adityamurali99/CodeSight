from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from enum import Enum

class FindingType(str, Enum):
    BUG = "bug"
    STYLE = "style"
    PERFORMANCE = "performance"
    SECURITY = "security"

class Verdict(str, Enum):
    APPROVED = "approved"         
    REVISED = "revised"           
    ESCALATED = "escalated"      

# --- Shared Finding model ---
class ReviewFinding(BaseModel):
    category: FindingType = Field(..., alias="type")
    line_number: int = Field(..., alias="line")
    issue: str = Field(..., description="Specific technical failure, no vague terms")
    suggestion: Optional[str] = Field(None, alias="fix")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore"
    )

class ReviewResponse(BaseModel):
    thought_process: str = Field(..., description="Step-by-step logic trace")
    findings: List[ReviewFinding]
    summary: str = Field(..., description="Two sentences max: critical bugs, then other issues")
    fixed_code: str = Field(..., description="Complete corrected snippet")

class AuditFinding(BaseModel):
    finding_ref: Optional[int] = Field(None, description="Index of the Reviewer finding being evaluated (0-based). Null if this is a net-new finding.")
    judgment: str = Field(..., description="One of: CONFIRMED, REJECTED, ESCALATED")
    reason: str = Field(..., description="Technical justification for the judgment")
    corrected_fix: Optional[str] = Field(None, description="Only populate if judgment is REJECTED or ESCALATED")

class AuditResponse(BaseModel):
    verdict: Verdict = Field(..., description="Overall verdict on the Reviewer's output")
    audit_findings: List[AuditFinding] = Field(..., description="Per-finding judgments from the Auditor")
    missed_bugs: List[ReviewFinding] = Field(default_factory=list, description="Net-new bugs the Reviewer missed entirely")
    final_findings: List[ReviewFinding] = Field(..., description="The authoritative merged finding list after audit")
    summary: str = Field(..., description="One sentence verdict. One sentence on what changed vs Reviewer.")
    fixed_code: str = Field(..., description="Final corrected snippet incorporating all audit corrections")