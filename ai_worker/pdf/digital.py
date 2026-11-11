from pathlib import Path
from typing import List
import pymupdf

from models import PageExtraction, DocumentText
from exceptions import (
    DocumentNotFoundError,
    DocumentCorruptError,
    PasswordProtectedError,
    DigitalExtractionError,
)

def extract_digital_pdf(file_path: str, max_pages: int = 15) -> DocumentText:
    """
    Extracts text from a digitally generated PDF using PyMuPDF.
    
    - Enforces first 15 pages limit by default.
    - Preserves 1-based original page numbers.
    - Preserves layout/reading order.
    - Flags pages with insufficient text.
    """
    path = Path(file_path)
    if not path.is_file():
        raise DocumentNotFoundError(f"File not found: {file_path}")

    try:
        doc = pymupdf.open(file_path)
    except Exception as e:
        raise DocumentCorruptError(f"Failed to open digital PDF: {e}")

    try:
        if doc.is_encrypted:
            raise PasswordProtectedError(f"PDF is password protected: {file_path}")

        total_pages = len(doc)
        if total_pages == 0:
            raise DocumentCorruptError(f"PDF has 0 pages: {file_path}")

        pages_to_process = min(max_pages, total_pages)
        page_extractions: List[PageExtraction] = []

        for idx in range(pages_to_process):
            page_num = idx + 1
            page = doc[idx]
            
            # Extract text preserving layout blocks where possible
            text = page.get_text("text").strip()
            
            page_extractions.append(
                PageExtraction(
                    page_number=page_num,
                    text=text,
                    confidence=1.0 if text else 0.0,
                )
            )

        return DocumentText(
            file_path=str(path.resolve()),
            doc_type="digital",
            total_pages_in_doc=total_pages,
            pages_processed=pages_to_process,
            pages=page_extractions,
        )
    except (DocumentNotFoundError, DocumentCorruptError, PasswordProtectedError):
        raise
    except Exception as e:
        raise DigitalExtractionError(f"Error during digital PDF extraction: {e}")
    finally:
        doc.close()

