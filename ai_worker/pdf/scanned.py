import io
from pathlib import Path
from typing import List, Optional
import numpy as np
from PIL import Image
import pymupdf

from models import PageExtraction, DocumentText
from exceptions import (
    DocumentNotFoundError,
    DocumentCorruptError,
    PasswordProtectedError,
    ScannedExtractionError,
)

_ocr_engine = None

def get_ocr_engine(lang: str = "en"):
    """Singleton getter for PaddleOCR engine."""
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR
            _ocr_engine = PaddleOCR(use_angle_cls=True, lang=lang)
        except Exception as e:
            raise ScannedExtractionError(f"Failed to initialize PaddleOCR engine: {e}")
    return _ocr_engine

def extract_scanned_pdf(file_path: str, max_pages: int = 15, lang: str = "en") -> DocumentText:
    """
    Renders scanned PDF pages into images and extracts text using PaddleOCR.
    
    - Enforces first 15 pages limit by default.
    - Preserves 1-based original page numbers.
    - Captures OCR confidence information.
    - Reports poor recognition quality.
    """
    path = Path(file_path)
    if not path.is_file():
        raise DocumentNotFoundError(f"File not found: {file_path}")

    try:
        doc = pymupdf.open(file_path)
    except Exception as e:
        raise DocumentCorruptError(f"Failed to open scanned PDF: {e}")

    try:
        if doc.is_encrypted:
            raise PasswordProtectedError(f"PDF is password protected: {file_path}")

        total_pages = len(doc)
        if total_pages == 0:
            raise DocumentCorruptError(f"PDF has 0 pages: {file_path}")

        ocr = get_ocr_engine(lang=lang)
        pages_to_process = min(max_pages, total_pages)
        page_extractions: List[PageExtraction] = []

        for idx in range(pages_to_process):
            page_num = idx + 1
            page = doc[idx]

            # Render page to high-res image (200 DPI for reliable OCR accuracy)
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            img_np = np.array(img)

            # Perform OCR
            result = ocr.ocr(img_np, cls=True)

            page_lines: List[str] = []
            confidences: List[float] = []

            # PaddleOCR returns a list of results per image: [[ [coords, (text, conf)], ... ]]
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text_part, conf_part = line[1][0], line[1][1]
                        if text_part:
                            page_lines.append(str(text_part).strip())
                            confidences.append(float(conf_part))

            extracted_text = "\n".join(page_lines).strip()
            avg_confidence = (sum(confidences) / len(confidences)) if confidences else 0.0

            page_extractions.append(
                PageExtraction(
                    page_number=page_num,
                    text=extracted_text,
                    confidence=round(avg_confidence, 4),
                )
            )

        return DocumentText(
            file_path=str(path.resolve()),
            doc_type="scanned",
            total_pages_in_doc=total_pages,
            pages_processed=pages_to_process,
            pages=page_extractions,
        )
    except (DocumentNotFoundError, DocumentCorruptError, PasswordProtectedError, ScannedExtractionError):
        raise
    except Exception as e:
        raise ScannedExtractionError(f"Error during scanned PDF extraction: {e}")
    finally:
        doc.close()

