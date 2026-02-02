"""
FastAPI main application for Short Report Rebuttal Assistant
"""
import logging
import uuid
from pathlib import Path
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app.claim_extract import extract_claims_from_text
from app.config import CHROMA_DIR, INTERNAL_DATA_DIR, REPORTS_DIR
from app.judge import judge_claim
from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    Claim,
    ClaimAnalysis,
    UploadReportResponse,
    UploadOnlyResponse,
)
from app.pdf_extract import extract_document_text
from app.report import create_analysis_report
from app.retrieval import retrieve_relevant_documents
from app.utils import load_json, logger, save_json
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Short Report Rebuttal Assistant API",
    description="API for analyzing short reports and generating rebuttal analysis",
    version="1.0.0"
)

# CORS middleware - allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
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
            "upload": "/api/upload_report",
            "analyze": "/api/analyze",
            "download": "/api/download_report/{report_id}"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    chroma_exists = CHROMA_DIR.exists()
    
    # Check if ChromaDB collection exists and has data
    collection_exists = False
    collection_count = 0
    if chroma_exists:
        try:
            import chromadb
            from chromadb.config import Settings
            client = chromadb.PersistentClient(
                path=str(CHROMA_DIR),
                settings=Settings(anonymized_telemetry=False)
            )
            try:
                collection = client.get_collection("internal_documents")
                collection_exists = True
                collection_count = collection.count()
            except Exception:
                collection_exists = False
        except Exception:
            pass
    
    return {
        "status": "healthy",
        "chroma_db_exists": chroma_exists,
        "collection_exists": collection_exists,
        "collection_count": collection_count,
        "reports_dir": str(REPORTS_DIR)
    }


@app.post("/api/check_and_index")
async def check_and_index():
    """
    Check if vector DB exists and has data, if not, index company_data.pdf
    """
    try:
        import chromadb
        from app.index_internal import index_internal_documents
        from chromadb.config import Settings
        
        # Check if collection exists and has data
        collection_exists = False
        collection_count = 0
        
        if CHROMA_DIR.exists():
            try:
                client = chromadb.PersistentClient(
                    path=str(CHROMA_DIR),
                    settings=Settings(anonymized_telemetry=False)
                )
                collection = client.get_collection("internal_documents")
                collection_exists = True
                collection_count = collection.count()
            except Exception:
                collection_exists = False
        
        if collection_exists and collection_count > 0:
            return {
                "indexed": True,
                "message": f"Vector DB already exists with {collection_count} chunks",
                "count": collection_count
            }
        
        # Index documents
        logger.info("Vector DB not found or empty, starting indexing...")
        logger.info(f"INTERNAL_DATA_DIR: {INTERNAL_DATA_DIR}")
        logger.info(f"INTERNAL_DATA_DIR exists: {INTERNAL_DATA_DIR.exists()}")
        
        try:
            index_internal_documents()
        except Exception as index_error:
            logger.error(f"Indexing failed: {index_error}")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Traceback: {error_trace}")
            return {
                "indexed": False,
                "message": f"Indexing failed: {str(index_error)}",
                "error": error_trace
            }
        
        # Check again after indexing
        try:
            client = chromadb.PersistentClient(
                path=str(CHROMA_DIR),
                settings=Settings(anonymized_telemetry=False)
            )
            collection = client.get_collection("internal_documents")
            final_count = collection.count()
            
            return {
                "indexed": True,
                "message": f"Successfully indexed {final_count} document chunks",
                "count": final_count
            }
        except Exception as check_error:
            logger.error(f"Failed to verify indexing: {check_error}")
            return {
                "indexed": False,
                "message": f"Indexing completed but verification failed: {str(check_error)}",
                "error": str(check_error)
            }
        
    except Exception as e:
        logger.error(f"Error checking/indexing: {e}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Traceback: {error_trace}")
        return {
            "indexed": False,
            "message": f"Error: {str(e)}",
            "error": error_trace
        }


@app.post("/api/upload_report", response_model=UploadOnlyResponse)
async def upload_report(file: UploadFile = File(...)):
    """
    Upload a short report (PDF, TXT, or DOCX) without extracting claims

    Returns:
        report_id, filename, and file_type
    """
    # Validate file extension
    valid_extensions = ['.pdf', '.txt', '.docx', '.doc']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(valid_extensions)} files are supported"
        )

    report_id = str(uuid.uuid4())
    report_path = REPORTS_DIR / f"{report_id}{file_ext}"
    extracted_path = REPORTS_DIR / f"{report_id}.extracted.json"

    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        # Save uploaded file
        with open(report_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Saved report {report_id} to {report_path}")

        # Extract text from document (for later use in claim extraction)
        pages = extract_document_text(report_path)
        if not pages:
            raise HTTPException(status_code=400, detail=f"Failed to extract text from {file_ext} file")

        # Save extracted document text for later claim extraction
        save_json(
            {
                "report_id": report_id,
                "filename": file.filename,
                "file_type": file_ext,
                "extracted_at": datetime.now().isoformat(),
                "pages": pages
            },
            extracted_path
        )

        logger.info(f"Saved extracted text for report {report_id}")

        return UploadOnlyResponse(
            report_id=report_id,
            filename=file.filename,
            file_type=file_ext,
            message="Document uploaded successfully. Click 'Next Step' to extract claims."
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error uploading report: {e}")
        logger.error(f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error processing report: {str(e)}")


@app.post("/api/extract_claims", response_model=UploadReportResponse)
async def extract_claims(request: AnalyzeRequest):
    """
    Extract claims from a previously uploaded report
    Performs LLM-based claim extraction on the document text
    """
    report_id = request.report_id
    extracted_path = REPORTS_DIR / f"{report_id}.extracted.json"
    claims_path = REPORTS_DIR / f"{report_id}.claims.json"

    # Check if document was uploaded
    if not extracted_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Report not found. Please upload a document first."
        )

    try:
        # Check if claims already extracted (return cached claims)
        if claims_path.exists():
            cached_data = load_json(claims_path)
            claims_data = cached_data.get("claims", [])
            if claims_data:
                claims = [Claim(**c) for c in claims_data]
                logger.info(f"Returning cached claims for report {report_id}")
                return UploadReportResponse(
                    report_id=report_id,
                    claims=claims,
                    message=f"Successfully retrieved {len(claims)} cached claims"
                )

        # Extract claims for the first time
        extracted_data = load_json(extracted_path)
        pages = extracted_data.get("pages", [])

        if not pages:
            raise HTTPException(status_code=400, detail="No document text found. Please upload a document.")

        # Perform LLM-based claim extraction
        full_text = "\n\n".join([f"Page {pnum}:\n{text}" for pnum, text in pages])
        claims = extract_claims_from_text(full_text, pages)

        if not claims:
            raise HTTPException(status_code=400, detail="Failed to extract claims from report")

        # Cache the extracted claims
        save_json(
            {
                "report_id": report_id,
                "claims": [c.dict() for c in claims],
                "pages": pages,
                "extracted_at": datetime.now().isoformat()
            },
            claims_path
        )

        logger.info(f"Extracted {len(claims)} claims from report {report_id}")

        return UploadReportResponse(
            report_id=report_id,
            claims=claims,
            message=f"Successfully extracted {len(claims)} claims"
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error extracting claims: {e}")
        logger.error(f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error extracting claims: {str(e)}")


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_claims(request: AnalyzeRequest):
    """
    Analyze claims by retrieving evidence and judging coverage
    """
    report_id = request.report_id
    top_k = request.top_k
    max_claims = request.max_claims
    
    claims_path = REPORTS_DIR / f"{report_id}.claims.json"
    if not claims_path.exists():
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found. Please upload first.")
    
    cached_data = load_json(claims_path)
    claims_data = cached_data.get("claims", [])
    
    if not claims_data:
        raise HTTPException(status_code=400, detail="No claims found in cached data")
    
    claims = [Claim(**c) for c in claims_data[:max_claims]]
    logger.info(f"Analyzing {len(claims)} claims for report {report_id}")
    
    analyses = []
    
    for i, claim in enumerate(claims, 1):
        logger.info(f"Processing claim {i}/{len(claims)}: {claim.claim_id}")
        
        try:
            citations = retrieve_relevant_documents(claim.claim_text, top_k=top_k)
            analysis = judge_claim(claim, citations)
            analyses.append(analysis)
            
        except Exception as e:
            logger.error(f"Error analyzing claim {claim.claim_id}: {e}")
            analyses.append(ClaimAnalysis(
                claim_id=claim.claim_id,
                coverage="not_addressed",
                reasoning=f"Error occurred during processing: {str(e)}",
                citations=[],
                confidence=0,
                gaps=["Requires reprocessing"],
                recommended_actions=["Check system errors"]
            ))
    
    report = create_analysis_report(report_id, claims, analyses)
    
    report_json_path = REPORTS_DIR / f"{report_id}.report.json"
    report_md_path = REPORTS_DIR / f"{report_id}.report.md"
    
    save_json(report.json_data, report_json_path)
    report_md_path.write_text(report.markdown, encoding='utf-8')
    
    logger.info(f"Generated report for {report_id}")
    
    return AnalyzeResponse(
        report=report,
        message=f"Successfully analyzed {len(claims)} claims"
    )


def get_chinese_font_name() -> str:
    """
    Find and register a Chinese font from the system
    Returns the font name to use in PDF generation
    """
    import os

    # Try common Windows Chinese font locations
    possible_paths = [
        r'C:\Windows\Fonts\SimSun.ttc',      # Simplified Chinese (most common)
        r'C:\Windows\Fonts\msyh.ttf',        # Microsoft YaHei
        r'C:\Windows\Fonts\SimHei.ttf',      # SimHei (bold)
        r'C:\Windows\Fonts\simsunb.ttf',     # SimSun Bold
    ]

    for font_path in possible_paths:
        if os.path.exists(font_path):
            try:
                font_name = 'ChineseFont'
                # Only register if not already registered
                if font_name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                logger.info(f"Registered Chinese font from {font_path}")
                return font_name
            except Exception as e:
                logger.warning(f"Failed to register font {font_path}: {e}")
                continue

    logger.warning("No Chinese font found on system, PDF may display Chinese as boxes")
    return 'Helvetica'


def markdown_to_pdf(markdown_text: str, title: str) -> BytesIO:
    """
    Convert markdown text to PDF with Unicode support for Chinese characters
    Uses reportlab Platypus for better text handling
    """
    pdf_buffer = BytesIO()

    # Get registered Chinese font
    font_name = get_chinese_font_name()

    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    # Create styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=16,
        textColor='black',
        spaceAfter=12,
        alignment=1  # Center
    )

    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=13,
        textColor='black',
        spaceAfter=8,
        spaceBefore=8
    )

    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontName=font_name,
        fontSize=11,
        textColor='black',
        spaceAfter=6,
        spaceBefore=6
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=10,
        alignment=0,  # Left
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['BodyText'],
        fontName=font_name,
        fontSize=10,
        leftIndent=20,
        spaceAfter=4
    )

    # Build content
    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Process markdown
    lines = markdown_text.split('\n')
    for line in lines:
        if line.startswith('# '):
            # H1 (skip, already added as title)
            continue
        elif line.startswith('## '):
            # H2
            text = line[3:].strip()
            if text:
                story.append(Paragraph(text, h2_style))
        elif line.startswith('### '):
            # H3
            text = line[4:].strip()
            if text:
                story.append(Paragraph(text, h3_style))
        elif line.startswith('- ') or line.startswith('* '):
            # Bullet point
            text = line[2:].strip()
            if text:
                story.append(Paragraph(f"• {text}", bullet_style))
        elif line.strip():
            # Regular paragraph
            story.append(Paragraph(line.strip(), body_style))
        else:
            # Empty line - add small spacer
            story.append(Spacer(1, 0.1 * inch))

    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer


@app.get("/api/download_report/{report_id}")
async def download_report(report_id: str, format: str = "md"):
    """
    Download generated report in specified format
    """
    if format == "md":
        file_path = REPORTS_DIR / f"{report_id}.report.md"
        media_type = "text/markdown"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=file_path.name
        )

    elif format == "json":
        file_path = REPORTS_DIR / f"{report_id}.report.json"
        media_type = "application/json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=file_path.name
        )

    elif format == "pdf":
        md_file_path = REPORTS_DIR / f"{report_id}.report.md"
        if not md_file_path.exists():
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

        try:
            # Read markdown content
            markdown_content = md_file_path.read_text(encoding='utf-8')

            # Convert to PDF
            pdf_bytes = markdown_to_pdf(markdown_content, f"Report {report_id}")

            return StreamingResponse(
                iter([pdf_bytes.getvalue()]),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"}
            )
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

    else:
        raise HTTPException(status_code=400, detail="Format must be 'md', 'json', or 'pdf'")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
