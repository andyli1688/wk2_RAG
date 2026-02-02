"""
Pydantic models for request/response schemas
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class Claim(BaseModel):
    """A single claim extracted from the short report"""
    claim_id: str = Field(..., description="Unique claim identifier (e.g., C001)")
    claim_text: str = Field(..., description="The text of the claim")
    page_numbers: List[int] = Field(..., description="Page numbers where this claim appears")
    claim_type: Literal["accounting", "business_model", "fraud", "related_party", "guidance", "metrics", "other"] = Field(
        ..., description="Type of claim"
    )


class Citation(BaseModel):
    """Citation to a source document"""
    doc_id: str = Field(..., description="Document identifier")
    doc_title: str = Field(..., description="Document title")
    chunk_id: str = Field(..., description="Chunk identifier within the document")
    quote: str = Field(..., description="Relevant quote from the source")
    similarity_score: Optional[float] = Field(None, description="Similarity score (0-1, higher is more similar)")


class ClaimAnalysis(BaseModel):
    """Analysis result for a single claim"""
    claim_id: str
    coverage: Literal["fully_addressed", "partially_addressed", "not_addressed"]
    reasoning: str = Field(..., description="5-10 bullet points explaining the analysis")
    citations: List[Citation]
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    gaps: Optional[List[str]] = Field(None, description="Missing evidence types if not fully addressed")
    recommended_actions: Optional[List[str]] = Field(None, description="Recommended follow-up actions")


class UploadOnlyResponse(BaseModel):
    """Response after uploading a report (without claim extraction)"""
    report_id: str
    filename: str
    file_type: str
    message: str


class UploadReportResponse(BaseModel):
    """Response after uploading a report"""
    report_id: str
    claims: List[Claim]
    message: str


class AnalyzeRequest(BaseModel):
    """Request to analyze claims"""
    report_id: str
    top_k: int = Field(default=6, ge=1, le=20, description="Number of documents to retrieve per claim")
    max_claims: int = Field(default=30, ge=1, le=50, description="Maximum number of claims to analyze")


class ReportSummary(BaseModel):
    """Summary statistics for the report"""
    total_claims: int
    fully_addressed: int
    partially_addressed: int
    not_addressed: int
    average_confidence: float
    key_gaps: List[str]
    priority_actions: List[str]


class AnalysisReport(BaseModel):
    """Complete analysis report"""
    report_id: str
    generated_at: datetime
    summary: ReportSummary
    claim_analyses: List[ClaimAnalysis]
    markdown: str = Field(..., description="Markdown formatted report")
    json_data: dict = Field(..., description="JSON representation of the report")
    
    @property
    def json(self) -> dict:
        """Alias for json_data for backward compatibility"""
        return self.json_data
    
    class Config:
        # Allow both json and json_data in serialization
        populate_by_name = True


class AnalyzeResponse(BaseModel):
    """Response from analysis endpoint"""
    report: AnalysisReport
    message: str
