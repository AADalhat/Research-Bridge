# DATABASE INTEGRATION REFERENCE (CROWNBIRD RESEARCH BRIDGE v1.2)

> **Status:** Architectural Reference Document  
> **Target Audience:** Backend Engineers, Data Engineers, AI Worker Developers  
> **Boundary Notice:** The standalone metadata extraction application **must not** connect to PostgreSQL, Redis, or the CrownBird backend. This document specifies the verified database structure and data contract for the future production Dramatiq AI worker integration.

---

## 1. Authoritative Reference Files

The following three reference files prepared by the CrownBird Data Engineer define the authoritative project database architecture:

| File Name | Format | Role & Purpose |
|---|---|---|
| **`Research_Bridge1.2.pdf`** | PDF (2 pages) | Visual Entity-Relationship Diagram (ERD) defining relationships, foreign keys, and cardinalities across all 12 tables. |
| **`Research_Bridge_Database_Documentation_v1_2.docx`** | DOCX (618 lines) | Official PostgreSQL Schema Specification v1.2 detailing tables, data types, constraints, default values, JSONB schemas, indexes, and operational notes. |
| **`Research_Bridge_Workflow_Guide_for_current_version1.2.docx`** | DOCX (358 lines) | End-to-end workflow walkthrough detailing the submission lifecycle, human review, resubmission, DSpace publication, and background worker responsibilities. |

---

## 2. Database Architecture Summary

The Research Bridge PostgreSQL database comprises **12 tables** across five functional domains:

1. **Identity & Access Management:**
   - `users`: User accounts (students, staff, reviewers, admins).
   - `roles`: Role definitions (`student`, `reviewer`, `administrator`).
   - `user_roles`: Many-to-many relationship tracking role assignments.
2. **Academic Reference Data:**
   - `faculties`: University faculties (`faculty_id`, `faculty_name`, `faculty_code`).
   - `departments`: Academic departments linked to their parent faculty (`department_id`, `faculty_id`, `department_name`, `department_code`).
3. **Submission Intake:**
   - `file_uploads`: PDF file storage references (`object_reference`, `physical_path`). PDF binary bytes are stored outside PostgreSQL.
   - `submissions`: Core submission entity tracking current lifecycle status, student, file upload, faculty, department, and document type.
4. **Lifecycle, Activity & Asynchronous Workers:**
   - `submission_events`: Chronological append-only event log (`uploaded`, `extracted`, `approved`, `rejected`, `resubmitted`, `finalized`, `manual_edit`, `extraction_stalled`, `finalization_stalled`).
   - `processing_jobs`: Background worker execution tracker (`metadata_extraction`, `dspace_ingestion`) with status (`pending`, `running`, `completed`, `failed`).
5. **AI Metadata & Repository Publication:**
   - `metadata_extractions`: Raw LLM response (`candidate_metadata_raw`), structured validated candidate (`candidate_metadata`), and evidence (`evidence_data`).
   - `submissions_metadata`: Exactly one current reviewable metadata record per submission (author, publication_year, faculty_name, department_name, language, title, subject_keywords, abstract).
   - `finalizations`: Confirmed DSpace publication records (`dspace_item_id`, `dspace_handle`, `repository_uri`).

---

## 3. Core Tables for the AI Worker Integration

### 3.1 `submissions`
Tracks the business state and references the current active upload.

| Column | Type | Nullable | Description / Rules |
|---|---|---|---|
| `submission_id` | `UUID` | No | Primary Key (`gen_random_uuid()`). |
| `student_id` | `UUID` | No | FK to `users(user_id)`. |
| `file_upload_id` | `UUID` | No | FK to `file_uploads(file_upload_id)`. Current active PDF. |
| `faculty_id` | `UUID` | No | FK to `faculties(faculty_id)`. |
| `department_id` | `UUID` | No | Composite FK `(department_id, faculty_id)` references `departments`. |
| `document_type` | `VARCHAR(100)` | No | E.g. Thesis, Journal, Dissertation. No fixed DB CHECK. |
| `status` | `VARCHAR(30)` | No | Default `UPLOADED`. Allowed: `UPLOADED`, `EXTRACTED`, `APPROVED`, `REJECTED`, `FINALIZED`, `EXTRACTION_STALLED`, `FINALIZATION_STALLED`. |
| `created_at` | `TIMESTAMPTZ` | No | Default `NOW()`. |
| `updated_at` | `TIMESTAMPTZ` | No | Default `NOW()`. |

### 3.2 `processing_jobs`
Tracks execution state of the asynchronous worker.

| Column | Type | Nullable | Description / Rules |
|---|---|---|---|
| `job_id` | `UUID` | No | Primary Key (`gen_random_uuid()`). |
| `submission_id` | `UUID` | No | FK to `submissions(submission_id)`. |
| `job_type` | `VARCHAR(50)` | No | CHECK: `metadata_extraction`, `dspace_ingestion`. |
| `status` | `VARCHAR(30)` | No | Default `pending`. CHECK: `pending`, `running`, `completed`, `failed`. |
| `started_at` | `TIMESTAMPTZ` | Yes | Worker execution start timestamp. |
| `finished_at` | `TIMESTAMPTZ` | Yes | Worker completion/failure timestamp. Finished >= Started. |
| `error_message` | `TEXT` | Yes | Technical error / stack trace details. |
| `created_at` | `TIMESTAMPTZ` | No | Default `NOW()`. |

*Note: Unique constraint on `(job_id, submission_id)` supports the composite FK from `metadata_extractions`.*

### 3.3 `metadata_extractions`
Preserves every extraction attempt, raw LLM outputs, and evidence.

| Column | Type | Nullable | Description / Rules |
|---|---|---|---|
| `extraction_id` | `UUID` | No | Primary Key (`gen_random_uuid()`). |
| `submission_id` | `UUID` | No | FK to `submissions(submission_id)`. |
| `processing_job_id` | `UUID` | No | UNIQUE. Composite FK `(processing_job_id, submission_id)` references `processing_jobs`. |
| `candidate_metadata_raw` | `TEXT` | Yes | Exact, unadulterated response from Gemini, even if malformed. |
| `candidate_metadata` | `JSONB` | Yes | Validated 3-field JSON object. Must be `NULL` if unusable/malformed. |
| `evidence_data` | `JSONB` | Yes | Supporting evidence regions following schema version 1. |
| `created_at` | `TIMESTAMPTZ` | No | Default `NOW()`. |

### 3.4 `submissions_metadata`
Maintains exactly one current, structured, human-reviewable metadata record per submission.

| Column | Type | Nullable | Source | Description / Rules |
|---|---|---|---|---|
| `metadata_id` | `UUID` | No | Generated | Primary Key (`gen_random_uuid()`). |
| `submission_id` | `UUID` | No | System | UNIQUE. FK to `submissions(submission_id)`. Enforces 1:1. |
| `extraction_id` | `UUID` | Yes | AI Worker | Composite FK `(extraction_id, submission_id)` references `metadata_extractions`. |
| `author` | `TEXT` | No | Student | Confirmed author name (prefilled from student user). |
| `title` | `TEXT` | Yes | AI Worker | Extracted research title. `NULL` until extraction. |
| `publication_year` | `INTEGER` | No | Student | CHECK: `1000 <= publication_year <= 9999`. |
| `faculty_name` | `VARCHAR(100)` | No | Student/DB | Readable snapshot of selected faculty. |
| `department_name` | `VARCHAR(100)` | No | Student/DB | Readable snapshot of selected department. |
| `language` | `VARCHAR(50)` | No | Student | E.g. English, French, Arabic. |
| `subject_keywords` | `TEXT` | Yes | AI Worker | Comma-separated keyword string derived from LLM array. |
| `abstract` | `TEXT` | Yes | AI Worker | Extracted abstract text. `NULL` until extraction. |
| `created_at` | `TIMESTAMPTZ` | No | System | Default `NOW()`. |
| `updated_at` | `TIMESTAMPTZ` | No | System | Default `NOW()`. |

### 3.5 `submission_events`
Append-only audit trail.

| Column | Type | Nullable | Description / Rules |
|---|---|---|---|
| `event_id` | `UUID` | No | Primary Key (`gen_random_uuid()`). |
| `submission_id` | `UUID` | No | FK to `submissions(submission_id)`. |
| `user_id` | `UUID` | Yes | FK to `users(user_id)`. `NULL` for autonomous system events. |
| `event_type` | `VARCHAR(50)` | No | CHECK: `uploaded`, `extracted`, `approved`, `rejected`, `resubmitted`, `finalized`, `manual_edit`, `extraction_stalled`, `finalization_stalled`. |
| `event_notes` | `TEXT` | Yes | Context, reasoning, error messages, or changed field summaries. |
| `created_at` | `TIMESTAMPTZ` | No | Default `NOW()`. |

---

## 4. Metadata Contract & Field Mapping

### 4.1 Strict 3-Field Extraction Scope
The AI extraction model is strictly restricted to **exactly three fields**:
1. `title` (`string`): Non-empty trimmed title.
2. `subject_keywords` (`array of strings`): Reusable keywords extracted from content.
3. `abstract` (`string`): Non-empty trimmed summary/abstract.

> **CRITICAL BOUNDARY:** The AI extraction worker **must never overwrite** student-supplied intake fields: `author`, `publication_year`, `faculty_name`, `department_name`, `language`, or `document_type`.

### 4.2 JSON Schemas

#### A. Validated Candidate Metadata (`candidate_metadata` JSONB)
```json
{
  "title": "A Comparative Study of Deep Learning Techniques in Agriculture",
  "subject_keywords": [
    "Deep Learning",
    "Computer Vision",
    "Crop Disease Detection",
    "Precision Agriculture"
  ],
  "abstract": "This thesis explores convolutional neural networks applied to aerial imagery for early disease detection..."
}
```

#### B. Supporting Evidence Data (`evidence_data` JSONB - Version 1)
```json
{
  "schema_version": 1,
  "fields": {
    "title": [
      {
        "page_number": 1,
        "source_text": "A Comparative Study of Deep Learning Techniques in Agriculture"
      }
    ],
    "subject_keywords": [
      {
        "page_number": 2,
        "source_text": "Keywords: Deep Learning, Computer Vision, Crop Disease Detection, Precision Agriculture"
      }
    ],
    "abstract": [
      {
        "page_number": 3,
        "source_text": "Abstract—This thesis explores convolutional neural networks applied to aerial imagery..."
      }
    ]
  }
}
```

### 4.3 Database Field Transformation
When mapping from `metadata_extractions` to `submissions_metadata`:
- `candidate_metadata.title` ➔ `submissions_metadata.title` (`TEXT`)
- `candidate_metadata.subject_keywords` ➔ `submissions_metadata.subject_keywords` (`TEXT`, joined as comma-separated string: `"Deep Learning, Computer Vision, Crop Disease Detection"`)
- `candidate_metadata.abstract` ➔ `submissions_metadata.abstract` (`TEXT`)
- `extraction_id` ➔ `submissions_metadata.extraction_id` (`UUID`)

---

## 5. Execution Semantics: Worker Job Status vs Business Submission Status

The architecture enforces a strict separation between **worker execution status** (`processing_jobs.status`) and **submission lifecycle state** (`submissions.status`):

| Scenario | Raw LLM (`candidate_metadata_raw`) | Parsed Candidate (`candidate_metadata`) | Job Status (`processing_jobs.status`) | Submission Status (`submissions.status`) | Event Recorded (`submission_events.event_type`) |
|---|---|---|---|---|---|
| **Successful Extraction** | Complete text response | Valid JSON object | `completed` | `EXTRACTED` | `extracted` |
| **Malformed / Unusable LLM Output** | Complete raw response preserved | `NULL` | `completed` (Worker completed validation without crash) | `EXTRACTION_STALLED` | `extraction_stalled` (Notes detail validation issue) |
| **Technical Failure (Network/OCR crash after retries)** | Raw text if available; otherwise `NULL` | `NULL` | `failed` | `EXTRACTION_STALLED` | `extraction_stalled` (Notes detail technical error) |

---

## 6. Standalone Application vs Production Worker Boundary

| Feature / Requirement | Standalone Application (Phase 4–12) | Future Production Dramatiq Worker |
|---|---|---|
| **Execution Environment** | Local Python CLI / GUI | Background worker running in Dramatiq / Redis |
| **Database Connection** | **None** (No PostgreSQL access) | Direct PostgreSQL connection via connection pool |
| **Input Source** | Local file path selected by user | Object storage lookup via `submissions.file_upload_id` |
| **PDF Extraction Engine** | PyMuPDF (digital), PaddleOCR (scanned) | Shared Python PDF processing library |
| **Max Page Enforcement** | First 15 pages by default | First 15 pages by default |
| **LLM Provider** | Google Gemini (`google-genai` SDK) | Google Gemini (`google-genai` SDK) |
| **Extraction Schema** | `title`, `subject_keywords`, `abstract` | Identical schema and validation rules |
| **Output Destination** | Local timestamped JSON file | `metadata_extractions`, `submissions_metadata`, `submission_events` |

