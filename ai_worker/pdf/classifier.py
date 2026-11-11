from pathlib import Path
from typing import Literal
import pymupdf

from exceptions import (
    DocumentNotFoundError,
    DocumentCorruptError,
    PasswordProtectedError,
    ClassificationError,
)

def classify_pdf(file_path: str, sample_pages: int = 5) -> Literal["digital", "scanned"]:
    """
    Classifies a PDF as strictly 'digital' or 'scanned'.
    Hybrid classification is explicitly OUT OF SCOPE.
    
    Uses measurable text-extraction density, font inspection, and image coverage.
    Raises ClassificationError if the document cannot be reliably classified.
    """
    path = Path(file_path)
    if not path.is_file():
        raise DocumentNotFoundError(f"PDF file does not exist: {file_path}")

    if path.stat().st_size == 0:
        raise DocumentCorruptError(f"PDF file is empty (0 bytes): {file_path}")

    try:
        doc = pymupdf.open(file_path)
    except Exception as e:
        raise DocumentCorruptError(f"Failed to open PDF document: {e}")

    try:
        if doc.is_encrypted:
            raise PasswordProtectedError(f"PDF is encrypted/password protected: {file_path}")

        total_pages = len(doc)
        if total_pages == 0:
            raise DocumentCorruptError(f"PDF contains 0 pages: {file_path}")

        pages_to_check = min(sample_pages, total_pages)
        total_text_chars = 0
        total_fonts_found = 0
        pages_with_images = 0
        pages_with_substantial_text = 0

        for i in range(pages_to_check):
            page = doc[i]
            text = page.get_text().strip()
            total_text_chars += len(text)
            
            fonts = page.get_fonts()
            total_fonts_found += len(fonts)
            
            images = page.get_images()
            if len(images) > 0:
                pages_with_images += 1

            if len(text) >= 150:
                pages_with_substantial_text += 1

        avg_chars_per_page = total_text_chars / pages_to_check

        # Classification decision logic
        # 1. Clear Digital Document:
        # High text density, multiple embedded fonts, most sampled pages have substantial text
        if avg_chars_per_page > 150 and total_fonts_found > 0 and pages_with_substantial_text >= (pages_to_check / 2):
            return "digital"

        # 2. Clear Scanned Document:
        # Very low or zero text, all or most pages have images, negligible embedded fonts
        if avg_chars_per_page < 40 and pages_with_images > 0 and total_fonts_found <= 1:
            return "scanned"

        # If moderate text (40 - 150 chars/page) or conflicting signals, inspect more closely:
        if avg_chars_per_page > 80 and total_fonts_found >= 1:
            return "digital"
        elif avg_chars_per_page < 30:
            return "scanned"

        # If classification is genuinely ambiguous, fail loudly rather than guessing wrong
        raise ClassificationError(
            f"Cannot reliably classify PDF '{path.name}' (avg chars/page: {avg_chars_per_page:.1f}, "
            f"fonts: {total_fonts_found}, pages with images: {pages_with_images}/{pages_to_check}). "
            "Please specify mode explicitly ('digital' or 'scanned')."
        )
    finally:
        doc.close()

