"""
FastAPI main application for Short Report Rebuttal Assistant
"""
import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.config import REPORTS_DIR, CHROMA_DIR
from app.models import (
    UploadReportResponse, AnalyzeRequest, AnalyzeResponse,
    Claim, ClaimAnalysis
)
from app.pdf_extract import extract_pdf_text
from app.claim_extract import extract_claims_from_text
from app.retrieval import retrieve_relevant_documents
from app.judge import judge_claim
from app.report import create_analysis_report
from app.utils import save_json, load_json, logger

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Short Report Rebuttal Assistant",
    description="API for analyzing short reports and generating rebuttal analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Short Report Rebuttal Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload_report",
            "analyze": "/analyze",
            "download": "/download_report/{report_id}"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    # Check if ChromaDB exists
    chroma_exists = CHROMA_DIR.exists()
    
    return {
        "status": "healthy",
        "chroma_db_exists": chroma_exists,
        "reports_dir": str(REPORTS_DIR)
    }


@app.post("/upload_report", response_model=UploadReportResponse)
async def upload_report(file: UploadFile = File(...)):
    """
    Upload a short report PDF and extract claims
    
    Returns:
        report_id and extracted claims
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate report ID
    report_id = str(uuid.uuid4())
    report_path = REPORTS_DIR / f"{report_id}.pdf"
    claims_path = REPORTS_DIR / f"{report_id}.claims.json"
    
    try:
        # Save uploaded file
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Saved report {report_id} to {report_path}")
        
        # Extract text from first 3 pages
        pages = extract_pdf_text(report_path)
        if not pages:
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
        
        # Combine text for claim extraction
        full_text = "\n\n".join([f"Page {pnum}:\n{text}" for pnum, text in pages])
        
        # Extract claims
        claims = extract_claims_from_text(full_text, pages)
        
        if not claims:
            raise HTTPException(status_code=400, detail="Failed to extract claims from report")
        
        # Save claims to cache
        save_json(
            {
                "report_id": report_id,
                "claims": [c.dict() for c in claims],
                "pages": pages
            },
            claims_path
        )
        
        logger.info(f"Extracted {len(claims)} claims from report {report_id}")
        
        return UploadReportResponse(
            report_id=report_id,
            claims=claims,
            message=f"Successfully uploaded and extracted {len(claims)} claims"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error uploading report: {e}")
        logger.error(f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error processing report: {str(e)}")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_claims(request: AnalyzeRequest):
    # Set a longer timeout for this endpoint
    # This is a long-running operation
    """
    Analyze claims by retrieving evidence and judging coverage
    
    Args:
        request: AnalyzeRequest with report_id and options
    
    Returns:
        Complete analysis report in JSON and Markdown formats
    """
    report_id = request.report_id
    top_k = request.top_k
    max_claims = request.max_claims
    
    # Load cached claims
    claims_path = REPORTS_DIR / f"{report_id}.claims.json"
    if not claims_path.exists():
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found. Please upload first.")
    
    cached_data = load_json(claims_path)
    claims_data = cached_data.get("claims", [])
    
    if not claims_data:
        raise HTTPException(status_code=400, detail="No claims found in cached data")
    
    # Convert to Claim objects
    claims = [Claim(**c) for c in claims_data[:max_claims]]
    
    logger.info(f"Analyzing {len(claims)} claims for report {report_id}")
    
    # Analyze each claim
    analyses = []
    
    for i, claim in enumerate(claims, 1):
        logger.info(f"Processing claim {i}/{len(claims)}: {claim.claim_id}")
        
        try:
            # Retrieve relevant documents
            citations = retrieve_relevant_documents(claim.claim_text, top_k=top_k)
            
            # Judge the claim
            analysis = judge_claim(claim, citations)
            analyses.append(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing claim {claim.claim_id}: {e}")
            # Create default analysis for failed claims
            analyses.append(ClaimAnalysis(
                claim_id=claim.claim_id,
                coverage="not_addressed",
                reasoning=f"处理过程中出现错误: {str(e)}",
                citations=[],
                confidence=0,
                gaps=["需要重新处理"],
                recommended_actions=["检查系统错误"]
            ))
    
    # Generate report
    report = create_analysis_report(report_id, claims, analyses)
    
    # Save report
    report_json_path = REPORTS_DIR / f"{report_id}.report.json"
    report_md_path = REPORTS_DIR / f"{report_id}.report.md"
    
    save_json(report.json_data, report_json_path)
    report_md_path.write_text(report.markdown, encoding='utf-8')
    
    logger.info(f"Generated report for {report_id}")
    
    return AnalyzeResponse(
        report=report,
        message=f"Successfully analyzed {len(claims)} claims"
    )


@app.get("/download_report/{report_id}")
async def download_report(report_id: str, format: str = "md"):
    """
    Download generated report
    
    Args:
        report_id: Report identifier
        format: Report format ("md" or "json")
    
    Returns:
        File response with report
    """
    if format == "md":
        file_path = REPORTS_DIR / f"{report_id}.report.md"
        media_type = "text/markdown"
    elif format == "json":
        file_path = REPORTS_DIR / f"{report_id}.report.json"
        media_type = "application/json"
    else:
        raise HTTPException(status_code=400, detail="Format must be 'md' or 'json'")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
