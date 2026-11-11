import io
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pymupdf
from PIL import Image, ImageDraw

from config import config
from models import CandidateMetadata, DocumentText, PageExtraction, ExtractionJobResult
from exceptions import (
    DocumentNotFoundError,
    DocumentCorruptError,
    PasswordProtectedError,
    ClassificationError,
)
from pdf.classifier import classify_pdf
from pdf.digital import extract_digital_pdf
from pdf.scanned import extract_scanned_pdf
from llm.gemini import extract_metadata_with_gemini
from storage.json_writer import save_extraction_result
from pipeline import run_extraction_pipeline

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

@pytest.fixture(scope="session")
def multi_page_pdf():
    """Generates a 20-page digital PDF to test first-15-page limit."""
    pdf_path = FIXTURES_DIR / "twenty_pages.pdf"
    doc = pymupdf.open()
    for i in range(20):
        page = doc.new_page()
        page.insert_text((50, 72), f"This is page {i+1} of twenty. Sample academic body text discussing methods and findings.")
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)

@pytest.fixture(scope="session")
def password_pdf():
    """Generates an encrypted password-protected PDF."""
    pdf_path = FIXTURES_DIR / "password_protected.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Confidential thesis manuscript.")
    perm = int(
        pymupdf.PDF_PERM_ACCESSIBILITY
        | pymupdf.PDF_PERM_PRINT
        | pymupdf.PDF_PERM_COPY
        | pymupdf.PDF_PERM_ANNOTATE
    )
    doc.save(str(pdf_path), encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="secret123", permissions=perm)
    doc.close()
    return str(pdf_path)

@pytest.fixture(scope="session")
def corrupt_pdf():
    """Generates a corrupt PDF file."""
    path = FIXTURES_DIR / "corrupt.pdf"
    path.write_bytes(b"NOT_A_VALID_PDF_HEADER_CORRUPTED_BYTES_1234567890")
    return str(path)

@pytest.fixture(scope="session")
def zero_byte_pdf():
    """Generates a 0-byte file."""
    path = FIXTURES_DIR / "zero_byte.pdf"
    path.write_bytes(b"")
    return str(path)

@pytest.fixture(scope="session")
def scanned_image_pdf():
    """Generates a purely scanned/image-only PDF with no embedded machine-readable fonts."""
    pdf_path = FIXTURES_DIR / "scanned_image.pdf"
    
    # Create image using PIL
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 100), "CROWNBIRD RESEARCH BRIDGE SCANNED PAGE", fill=(0, 0, 0))
    draw.text((50, 150), "Keywords: OCR, Research, Fellowship", fill=(0, 0, 0))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    page.insert_image(page.rect, stream=img_bytes)
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)

# --- Test Cases ---

def test_first_15_pages_enforcement(multi_page_pdf):
    """Test that a document with 20 pages processes only the first 15 pages."""
    doc_text = extract_digital_pdf(multi_page_pdf, max_pages=15)
    assert doc_text.total_pages_in_doc == 20
    assert doc_text.pages_processed == 15
    assert len(doc_text.pages) == 15
    assert doc_text.pages[0].page_number == 1
    assert doc_text.pages[14].page_number == 15

def test_document_with_fewer_than_15_pages():
    """Test that a document with 2 pages processes exactly 2 pages."""
    pdf_path = r"C:\Users\DELL 3520\Desktop\ai worker\Research_Bridge1.2.pdf"
    doc_text = extract_digital_pdf(pdf_path, max_pages=15)
    assert doc_text.total_pages_in_doc == 2
    assert doc_text.pages_processed == 2

def test_password_protected_rejection(password_pdf):
    """Test that password-protected PDFs raise PasswordProtectedError."""
    with pytest.raises(PasswordProtectedError):
        classify_pdf(password_pdf)

    with pytest.raises(PasswordProtectedError):
        extract_digital_pdf(password_pdf)

def test_corrupt_pdf_rejection(corrupt_pdf):
    """Test that corrupted PDFs raise DocumentCorruptError."""
    with pytest.raises(DocumentCorruptError):
        classify_pdf(corrupt_pdf)

def test_zero_byte_pdf_rejection(zero_byte_pdf):
    """Test that 0-byte PDFs raise DocumentCorruptError."""
    with pytest.raises(DocumentCorruptError):
        classify_pdf(zero_byte_pdf)

def test_scanned_pdf_classification(scanned_image_pdf):
    """Test that image-only PDF is classified as scanned."""
    classification = classify_pdf(scanned_image_pdf)
    assert classification == "scanned"

def test_duplicate_filename_handling(tmp_path):
    """Test that saving duplicate results produces distinct filenames with counter."""
    res1 = ExtractionJobResult(
        job_id="job-1111-aaaa",
        file_path="thesis.pdf",
        classification="digital",
        pages_processed=5,
        total_pages_in_doc=5,
        status="completed"
    )
    res2 = ExtractionJobResult(
        job_id="job-1111-aaaa",
        file_path="thesis.pdf",
        classification="digital",
        pages_processed=5,
        total_pages_in_doc=5,
        status="completed"
    )
    path1 = save_extraction_result(res1, output_dir=tmp_path)
    path2 = save_extraction_result(res2, output_dir=tmp_path)
    assert path1 != path2
    assert path1.exists()
    assert path2.exists()

def test_gemini_success_mock():
    """Test successful Gemini response parsing and evidence extraction."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Machine Learning in Agricultural Yield Forecasting",
        "subject_keywords": ["Agriculture", "Machine Learning", "Forecasting"],
        "abstract": "This study presents novel predictive modeling techniques for crop yields.",
        "evidence": {
            "title": [{"page_number": 1, "source_text": "Machine Learning in Agricultural Yield Forecasting"}],
            "subject_keywords": [{"page_number": 1, "source_text": "Keywords: Agriculture, Machine Learning"}],
            "abstract": [{"page_number": 2, "source_text": "This study presents novel predictive..."}]
        }
    })

    doc_text = DocumentText(
        file_path="test.pdf",
        doc_type="digital",
        total_pages_in_doc=2,
        pages_processed=2,
        pages=[PageExtraction(page_number=1, text="Sample text")]
    )

    with patch("google.genai.Client") as MockClient:
        instance = MockClient.return_value
        instance.models.generate_content.return_value = mock_response

        raw, candidate, evidence, err = extract_metadata_with_gemini(
            doc_text, api_key="fake-test-key", model_name="gemini-2.5-flash"
        )

        assert err is None
        assert candidate is not None
        assert candidate.title == "Machine Learning in Agricultural Yield Forecasting"
        assert len(candidate.subject_keywords) == 3
        assert evidence is not None
        assert evidence.schema_version == 1
        assert len(evidence.fields.title) == 1
        assert evidence.fields.title[0].page_number == 1

def test_gemini_malformed_json_stalls_gracefully():
    """Test that malformed LLM response sets status to EXTRACTION_STALLED and preserves raw text."""
    mock_response = MagicMock()
    mock_response.text = "NOT_VALID_JSON { title: incomplete... "

    doc_text = DocumentText(
        file_path="test.pdf",
        doc_type="digital",
        total_pages_in_doc=1,
        pages_processed=1,
        pages=[PageExtraction(page_number=1, text="Sample text")]
    )

    with patch("google.genai.Client") as MockClient:
        instance = MockClient.return_value
        instance.models.generate_content.return_value = mock_response

        raw, candidate, evidence, err = extract_metadata_with_gemini(
            doc_text, api_key="fake-test-key"
        )

        assert candidate is None
        assert "Malformed JSON" in err
        assert raw == mock_response.text

def test_gemini_missing_abstract_stalls():
    """Test that missing abstract in LLM response fails validation and stalls."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "Title Without Abstract",
        "subject_keywords": ["Test"]
        # abstract omitted
    })

    doc_text = DocumentText(
        file_path="test.pdf",
        doc_type="digital",
        total_pages_in_doc=1,
        pages_processed=1,
        pages=[PageExtraction(page_number=1, text="Sample text")]
    )

    with patch("google.genai.Client") as MockClient:
        instance = MockClient.return_value
        instance.models.generate_content.return_value = mock_response

        raw, candidate, evidence, err = extract_metadata_with_gemini(
            doc_text, api_key="fake-test-key"
        )

        assert candidate is None
        assert "Validation failed" in err
        assert raw is not None

