import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from config import config
from models import ExtractionJobResult, DocumentText
from exceptions import AIWorkerException, ClassificationError
from pdf.classifier import classify_pdf
from pdf.digital import extract_digital_pdf
from pdf.scanned import extract_scanned_pdf
from llm.gemini import extract_metadata_with_gemini
from storage.json_writer import save_extraction_result

def run_extraction_pipeline(
    file_path: str,
    mode: str = "auto",
    max_pages: int = 15,
    job_id: Optional[str] = None,
    output_dir: Optional[Path] = None,
    api_key: Optional[str] = None,
) -> ExtractionJobResult:
    """
    Executes the complete extraction pipeline on a PDF:
    1. Classification (Digital vs Scanned)
    2. Page-level text extraction (PyMuPDF for digital, PaddleOCR for scanned)
    3. First-15-pages enforcement
    4. Google Gemini 3-field metadata extraction + evidence mapping
    5. Validation and local JSON persistence
    """
    current_job_id = job_id or str(uuid.uuid4())
    start_time = datetime.now(timezone.utc).isoformat()

    resolved_path = Path(file_path).resolve()
    if not resolved_path.is_file():
        result = ExtractionJobResult(
            job_id=current_job_id,
            file_path=str(resolved_path),
            classification="unknown",
            pages_processed=0,
            total_pages_in_doc=0,
            status="failed",
            error_message=f"File does not exist: {file_path}",
            created_at=start_time,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        out_file = save_extraction_result(result, output_dir=output_dir)
        result.output_file = str(out_file)
        return result

    # 1. Document Classification
    classification = mode.lower()
    if classification == "auto":
        try:
            classification = classify_pdf(str(resolved_path))
        except ClassificationError as ce:
            result = ExtractionJobResult(
                job_id=current_job_id,
                file_path=str(resolved_path),
                classification="ambiguous",
                pages_processed=0,
                total_pages_in_doc=0,
                status="EXTRACTION_STALLED",
                error_message=str(ce),
                created_at=start_time,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            out_file = save_extraction_result(result, output_dir=output_dir)
            result.output_file = str(out_file)
            return result
        except Exception as e:
            result = ExtractionJobResult(
                job_id=current_job_id,
                file_path=str(resolved_path),
                classification="unknown",
                pages_processed=0,
                total_pages_in_doc=0,
                status="failed",
                error_message=f"Classification error: {e}",
                created_at=start_time,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            out_file = save_extraction_result(result, output_dir=output_dir)
            result.output_file = str(out_file)
            return result

    # 2. Text Extraction (Digital vs Scanned)
    try:
        if classification == "digital":
            doc_text = extract_digital_pdf(str(resolved_path), max_pages=max_pages)
        elif classification == "scanned":
            doc_text = extract_scanned_pdf(str(resolved_path), max_pages=max_pages)
        else:
            raise ValueError(f"Invalid mode '{mode}'. Expected 'auto', 'digital', or 'scanned'.")
    except Exception as e:
        result = ExtractionJobResult(
            job_id=current_job_id,
            file_path=str(resolved_path),
            classification=classification,
            pages_processed=0,
            total_pages_in_doc=0,
            status="failed",
            error_message=f"Text extraction failed: {e}",
            created_at=start_time,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        out_file = save_extraction_result(result, output_dir=output_dir)
        result.output_file = str(out_file)
        return result

    # 3. LLM 3-Field Metadata Extraction & Evidence
    effective_key = api_key or config.GEMINI_API_KEY
    raw_response, candidate, evidence, llm_error = extract_metadata_with_gemini(
        doc_text, api_key=effective_key
    )

    # 4. Success / Stalled Determination
    if candidate is not None and llm_error is None:
        status = "completed"
        candidate_dict = candidate.model_dump()
        evidence_dict = evidence.model_dump() if evidence else None
        err_msg = None
    else:
        status = "EXTRACTION_STALLED"
        candidate_dict = None
        evidence_dict = evidence.model_dump() if evidence else None
        err_msg = llm_error

    result = ExtractionJobResult(
        job_id=current_job_id,
        file_path=str(resolved_path),
        classification=classification,
        pages_processed=doc_text.pages_processed,
        total_pages_in_doc=doc_text.total_pages_in_doc,
        status=status,
        candidate_metadata_raw=raw_response if raw_response else None,
        candidate_metadata=candidate_dict,
        evidence_data=evidence_dict,
        error_message=err_msg,
        created_at=start_time,
        completed_at=datetime.now(timezone.utc).isoformat(),
    )

    out_file = save_extraction_result(result, output_dir=output_dir)
    result.output_file = str(out_file)
    return result
