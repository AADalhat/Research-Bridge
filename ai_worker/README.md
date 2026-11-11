# CrownBird Research Bridge — AI Extraction Engine

Production-grade asynchronous AI extraction engine powered by **Redis**, **Dramatiq**, **PyMuPDF**, **PaddleOCR**, and **Google Gemini** (`google-genai` SDK).

---

## 1. Architecture Overview

```
                      [ User / Client ]
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
      [ CLI / GUI ]                    [ send_task.py ]
   (Direct Execution)                 (Enqueue Message)
            │                                 │
            │                                 ▼
            │                        [ Redis (Memurai) ]
            │                         (Queue: default)
            │                                 │
            │                                 ▼
            │                      [ Dramatiq Worker Actor ]
            │                    (extract_pdf_metadata in tasks.py)
            │                                 │
            └────────────────┬────────────────┘
                             │
                             ▼
                 [ Document Classification ]
                 ├── Digital  ──► PyMuPDF  (Up to 15 pages)
                 └── Scanned  ──► PaddleOCR (Up to 15 pages)
                             │
                             ▼
                 [ Google Gemini Extraction ]
                 ├── Title (string)
                 ├── Subject Keywords (array of strings)
                 └── Abstract (string)
                 └── Supporting Evidence (Schema v1)
                             │
                             ▼
                 [ Local JSON Output / Storage ]
              (Preserves raw response, candidate, evidence)
```

---

## 2. Requirements & Environment

- **Python:** 3.13
- **Redis / Memurai:** Running on `localhost:6379` (Verified active service).
- **Core Libraries:**
  - `dramatiq[redis]` (2.2.1)
  - `redis` (8.1.0)
  - `pymupdf` (2.1)
  - `paddleocr` (3.7.0)
  - `google-genai` (2.30.0)
  - `pydantic` (2.14.1)

---

## 3. Quick Start & Execution

### Option A: End-to-End Dramatiq + Redis Worker Flow

1. **Start the Dramatiq Worker:**
   ```bash
   python run_worker.py
   ```
   *Worker connects to Redis on `localhost:6379` with 4 concurrent threads.*

2. **Dispatch a Task from Another Terminal:**
   ```bash
   # Submit task and wait for real-time result from Redis:
   python send_task.py "Research_Bridge1.2.pdf" --wait

   # Or submit asynchronously without blocking:
   python send_task.py "Research_Bridge1.2.pdf"
   ```

### Option B: Direct CLI Execution (Without Worker)

```bash
python cli.py "Research_Bridge1.2.pdf" --mode auto --max-pages 15
```

### Option C: Graphical User Interface (GUI)

```bash
python gui.py
```
*Provides a desktop interface to browse PDFs, select extraction mode, set Gemini API key, run tasks via Redis queue or direct execution, and inspect candidate metadata and evidence.*

---

## 4. Setting the Google Gemini API Key

To enable full LLM candidate metadata and evidence extraction:

```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your-api-key-here"

# Windows Command Prompt
set GEMINI_API_KEY=your-api-key-here
```

*(Note: If `GEMINI_API_KEY` is not set, the pipeline safely completes PDF text extraction, sets status to `EXTRACTION_STALLED`, records the diagnostic notice, and saves the output JSON without crashing).*

---

## 5. Running the Test Suite

Run all unit and end-to-end integration tests:

```bash
pytest tests -v
```

Tests verify:
- Schema validation & 3-field metadata contract (`test_models.py`)
- Evidence Schema Version 1 structure (`test_models.py`)
- Digital PDF classification and PyMuPDF text extraction (`test_pdf.py`)
- Live end-to-end Dramatiq worker execution via Redis queue (`test_dramatiq_end_to_end.py`)

---

## 6. Output Format

Results are persisted in `output/` as timestamped, collision-free JSON files:
```json
{
  "job_id": "3dc69bc4-b893-4a08-b375-e60bb613837e",
  "file_path": "C:\\Users\\...\\Research_Bridge1.2.pdf",
  "classification": "digital",
  "pages_processed": 2,
  "total_pages_in_doc": 2,
  "status": "completed",
  "candidate_metadata_raw": "...",
  "candidate_metadata": {
    "title": "A Comparative Study of Deep Learning Techniques...",
    "subject_keywords": ["Deep Learning", "Computer Vision", "Agriculture"],
    "abstract": "This thesis explores convolutional neural networks..."
  },
  "evidence_data": {
    "schema_version": 1,
    "fields": {
      "title": [{"page_number": 1, "source_text": "..."}],
      "subject_keywords": [{"page_number": 2, "source_text": "..."}],
      "abstract": [{"page_number": 3, "source_text": "..."}]
    }
  },
  "error_message": null,
  "created_at": "2026-11-09T14:24:00.148408+00:00",
  "completed_at": "2026-11-09T14:24:00.198637+00:00"
}
```

