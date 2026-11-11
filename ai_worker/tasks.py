import sys
from pathlib import Path

# Ensure workspace directory is in python path
workspace_dir = str(Path(__file__).parent.resolve())
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

import dramatiq
import broker  # Initializes RedisBroker and Results middleware
from pipeline import run_extraction_pipeline

@dramatiq.actor(store_results=True, max_retries=3)
def extract_pdf_metadata(
    file_path: str,
    mode: str = "auto",
    max_pages: int = 15,
    job_id: str = None,
    api_key: str = None
) -> dict:
    """
    Dramatiq Actor for asynchronous PDF metadata extraction.
    
    1. Picks up task from Redis queue.
    2. Runs classification, text extraction (PyMuPDF / PaddleOCR), and Gemini LLM extraction.
    3. Persists local JSON result.
    4. Stores result in Redis backend.
    """
    print(f"\n[Dramatiq Worker] Starting extraction job {job_id} for file: {file_path}")
    print(f"[Dramatiq Worker] Mode: {mode}, Max pages: {max_pages}")
    
    result = run_extraction_pipeline(
        file_path=file_path,
        mode=mode,
        max_pages=max_pages,
        job_id=job_id,
        api_key=api_key
    )
    
    print(f"[Dramatiq Worker] Job {result.job_id} finished with status: {result.status}")
    if result.output_file:
        print(f"[Dramatiq Worker] Output saved to: {result.output_file}")
    if result.error_message:
        print(f"[Dramatiq Worker] Warning/Error: {result.error_message}")
        
    return result.model_dump()
