import pytest
from pathlib import Path
from pdf.classifier import classify_pdf
from pdf.digital import extract_digital_pdf

TEST_PDF = Path(r"C:\Users\DELL 3520\Desktop\ai worker\Research_Bridge1.2.pdf")

def test_classify_pdf():
    assert TEST_PDF.exists(), "Test PDF must exist in workspace"
    classification = classify_pdf(str(TEST_PDF))
    assert classification in ["digital", "scanned"]

def test_extract_digital_pdf():
    assert TEST_PDF.exists()
    doc_text = extract_digital_pdf(str(TEST_PDF), max_pages=15)
    assert doc_text.doc_type == "digital"
    assert doc_text.pages_processed == 2
    assert len(doc_text.pages) == 2
    assert doc_text.pages[0].page_number == 1
    assert "users" in doc_text.pages[0].text

