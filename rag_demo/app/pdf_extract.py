"""
PDF extraction module: Extract text from first 3 pages of PDF
"""
import logging
from pathlib import Path
from typing import List, Tuple

# Try to import PDF libraries
HAS_PYPDF = False
HAS_PDFPLUMBER = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    pass

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    pass

if not HAS_PYPDF and not HAS_PDFPLUMBER:
    raise ImportError("Please install either pypdf or pdfplumber: pip install pypdf or pip install pdfplumber")

from app.config import MAX_PAGES

logger = logging.getLogger(__name__)


def extract_pdf_text(pdf_path: Path, max_pages: int = MAX_PAGES) -> List[Tuple[int, str]]:
    """
    Extract text from PDF, only processing first max_pages pages
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to process (default: 3)
    
    Returns:
        List of tuples (page_number, page_text)
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    logger.info(f"Extracting text from {pdf_path}, processing first {max_pages} pages")
    
    if HAS_PYPDF:
        try:
            # Try pypdf first
            reader = PdfReader(str(pdf_path))
            pages = []
            
            for i, page in enumerate(reader.pages[:max_pages], start=1):
                try:
                    text = page.extract_text()
                    if text.strip():
                        pages.append((i, text.strip()))
                        logger.debug(f"Extracted {len(text)} characters from page {i}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i}: {e}")
                    pages.append((i, ""))
            
            logger.info(f"Successfully extracted text from {len(pages)} pages")
            return pages
        except Exception as e:
            logger.warning(f"pypdf failed, trying pdfplumber: {e}")
    
    # Fallback to pdfplumber
    if HAS_PDFPLUMBER:
        try:
            pages = []
            
            with pdfplumber.open(str(pdf_path)) as pdf:
                for i, page in enumerate(pdf.pages[:max_pages], start=1):
                    try:
                        text = page.extract_text()
                        if text:
                            pages.append((i, text.strip()))
                            logger.debug(f"Extracted {len(text)} characters from page {i}")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {i}: {e}")
                        pages.append((i, ""))
            
            logger.info(f"Successfully extracted text from {len(pages)} pages using pdfplumber")
            return pages
        except Exception as e2:
            raise RuntimeError(f"Failed to extract text from PDF using pdfplumber: {e2}")
    
    # If we get here, neither library worked
    raise RuntimeError("Failed to extract text from PDF: no working PDF library available")


def extract_full_text(pdf_path: Path, max_pages: int = MAX_PAGES) -> str:
    """
    Extract full text from PDF as a single string
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to process
    
    Returns:
        Combined text from all pages
    """
    pages = extract_pdf_text(pdf_path, max_pages)
    return "\n\n".join([f"Page {page_num}:\n{text}" for page_num, text in pages])
