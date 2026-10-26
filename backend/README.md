# AI-Assisted Research Submission and Metadata Processing Pipeline

A full-stack workflow platform for receiving, tracking, processing and preparing postgraduate research submissions for institutional repository ingestion.

The system is designed to reduce manual effort in thesis and dissertation intake by providing a structured digital submission process, automated document processing, AI-assisted metadata extraction, correction/resubmission workflows and staff verification before records are prepared for the institutional repository.

> **Important:** This platform is a workflow and preparation layer around the institutional repository. It does not replace OpenAIR@ABU or DSpace.

---

## Problem Statement

Research submissions such as theses and dissertations may pass through manual processes involving physical media, paper records, repeated file handling and manual metadata entry. These processes can create several operational challenges:

- Slow submission intake and document preparation.
- Limited visibility for students after submitting their research work.
- Difficulty tracking incomplete submissions or requested corrections.
- Repetitive manual extraction of metadata such as title, author, department, degree, year, abstract and keywords.
- Inconsistent metadata records.
- Delays between submission, verification and repository indexing.
- Limited traceability of document versions, corrections and approval decisions.

This project addresses these challenges with a secure, traceable and human-supervised digital workflow.

---

## Project Goals

The platform aims to:

- Provide an authenticated digital gateway for postgraduate research submissions.
- Generate a unique submission receipt/reference ID for every upload.
- Validate uploaded files and calculate SHA-256 checksums for integrity verification.
- Enable students to track submission progress.
- Allow authorised staff to request corrections and manage resubmissions.
- Extract text from PDF and DOCX documents.
- Run OCR on scanned documents where necessary.
- Generate candidate metadata using deterministic rules and AI-assisted extraction.
- Provide confidence scores and document-source evidence for extracted metadata.
- Require staff review and approval before metadata is treated as authoritative.
- Export repository-ready files and metadata for ingestion into DSpace/OpenAIR@ABU.
- Maintain an audit trail of important workflow actions and status changes.

---

## Key Features

### Student Portal

- Secure login and authenticated submission.
- Thesis/dissertation upload.
- File validation for supported document formats.
- Submission receipt/reference generation.
- Submission-status tracking.
- View correction requests from staff.
- Upload corrected document versions.
- View submission and correction history.

### Staff Review Dashboard

- View and filter incoming submissions.
- Review uploaded documents.
- View automatically extracted metadata.
- Inspect field-level confidence scores and source evidence.
- Edit and verify metadata.
- Request corrections from students.
- Approve or reject submissions.
- Export approved repository-ready records.
- View complete workflow and audit history.

### Document Processing Pipeline

- PDF text extraction.
- DOCX text extraction.
- OCR preprocessing for scanned documents.
- Metadata extraction.
- Research-area/keyword classification.
- Confidence scoring.
- Source-page and source-text evidence.
- Metadata error and hallucination benchmarking against verified data.

### Repository Preparation

- Repository-ready metadata export.
- Approved file packaging.
- Controlled export when direct repository access is unavailable.
- Future integration path for DSpace REST API, SWORD or another authorised institutional method.
- Safe development testing with a self-hosted DSpace instance.

---

## System Architecture

```text
                         ┌───────────────────────┐
                         │       Students        │
                         └──────────┬────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       Student Web Portal      │
                    │  Submission -  Status -  Fixes  │
                    └──────────┬───────────────────┘
                               │
                               ▼
                    ┌──────────────────────────────┐
                    │         FastAPI Backend       │
                    │ Authentication -  Workflow API │
                    │ Validation -  Audit Logging    │
                    └───────┬───────────┬──────────┘
                            │           │
                            │           │
                            ▼           ▼
              ┌──────────────────┐  ┌──────────────────┐
              │    PostgreSQL    │  │  Object Storage  │
              │ Users, metadata, │  │ PDFs, DOCX files │
              │ status, audit    │  │ OCR artefacts    │
              └──────────────────┘  └──────────────────┘
                            │
                            ▼
                    ┌──────────────────────────────┐
                    │   Background Processing Jobs  │
                    │ Redis + Celery/RQ Worker      │
                    └──────────┬───────────────────┘
                               │
                               ▼
                    ┌──────────────────────────────┐
                    │     Document AI Pipeline      │
                    │ PDF/DOCX Parsing → OCR →      │
                    │ Metadata → Classification →   │
                    │ Validation/Confidence         │
                    └──────────┬───────────────────┘
                               │
                               ▼
                    ┌──────────────────────────────┐
                    │      Staff Review Dashboard   │
                    │ Verify -  Correct -  Approve    │
                    └──────────┬───────────────────┘
                               │
                               ▼
                    ┌──────────────────────────────┐
                    │  DSpace / OpenAIR@ABU Export │
                    │ Institutional System of Record│
                    └──────────────────────────────┘
```

---

## Technology Stack

| Layer | Proposed Technologies |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python, Pydantic, SQLAlchemy |
| Database | PostgreSQL |
| Background processing | Redis, Celery or RQ |
| File storage | MinIO for local development; S3-compatible storage or approved server storage for deployment |
| OCR | Tesseract OCR and/or PaddleOCR |
| PDF processing | PyMuPDF |
| DOCX processing | `python-docx` |
| AI/NLP | Hugging Face Transformers, PyTorch, constrained JSON extraction |
| Containerization | Docker and Docker Compose |
| Repository integration | DSpace REST API, SWORD or controlled metadata/file export |
| Testing | Pytest, Playwright or Cypress, Postman/Bruno |
| CI/CD | GitHub Actions |

---

## Workflow

The system follows a controlled submission lifecycle to ensure every action is traceable.

```text
DRAFT
  │
  ▼
SUBMITTED
  │
  ▼
VALIDATING
  │
  ├── Validation failed ──────────────► FAILED
  │
  ▼
PROCESSING
  │
  ▼
READY_FOR_REVIEW
  │
  ├── Staff requests correction ──────► CORRECTION_REQUIRED
  │                                         │
  │                                         ▼
  │                                    RESUBMITTED
  │                                         │
  │                                         ▼
  │                                  READY_FOR_REVIEW
  │
  ├── Staff rejects submission ───────► REJECTED
  │
  └── Staff approves submission ──────► APPROVED
                                            │
                                            ▼
                                         EXPORTED
```

---

## User Roles

### Student

A student can:

- Submit a thesis or dissertation.
- View their own submissions.
- Track submission status.
- View staff correction requests.
- Upload corrected versions of documents.
- View submission history and receipt/reference ID.

### Reviewer / Digitization Staff

A reviewer can:

- View authorised submissions.
- Inspect documents and extracted metadata.
- Verify or modify metadata fields.
- Request corrections from students.
- Approve or reject submissions.
- Export approved records for repository ingestion.
- View audit history.

### Administrator

An administrator can:

- Manage user roles.
- Configure departments, degrees and submission rules.
- Review system logs.
- Manage storage and processing settings.
- Monitor processing jobs and failures.

---

## Core Data Model

The project uses versioned records to preserve traceability. Previous document versions and metadata records are not overwritten.

### Main entities

```text
User
  └── Submission
        ├── Submission File
        ├── Metadata Record
        │     └── Metadata Field Evidence
        ├── Correction Request
        ├── Processing Job
        └── Audit Log
```

### Important tables

| Table | Purpose |
|---|---|
| `users` | Student, reviewer and administrator accounts |
| `submissions` | Main submission record, workflow status and reference ID |
| `submission_files` | Uploaded files, file versions, checksums and storage references |
| `metadata_records` | Extracted and staff-verified metadata |
| `metadata_fields` | Field-level confidence scores and source evidence |
| `correction_requests` | Feedback and correction workflow |
| `processing_jobs` | OCR, parsing and metadata-processing job status |
| `audit_logs` | Immutable history of system actions and transitions |

---

## Metadata Fields

The platform will support metadata fields such as:

- Title
- Author
- Student ID
- Department
- Faculty
- Degree
- Programme
- Supervisor
- Year of submission
- Abstract
- Keywords
- Research area
- Document language
- File checksum
- Submission date
- Approval date
- Repository export status

Every AI-generated field should include:

```json
{
  "field_name": "title",
  "field_value": "AI-Assisted Research Submission Pipeline",
  "confidence_score": 0.96,
  "source_page": 1,
  "source_text": "AN AI-ASSISTED RESEARCH SUBMISSION PIPELINE",
  "verification_status": "PENDING"
}
```

AI-generated metadata is treated as a suggestion only. Authorised staff must verify and approve records before repository export.

---

## API Overview

### Authentication

```text
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
```

### Student Submission Endpoints

```text
POST   /api/v1/submissions
GET    /api/v1/submissions
GET    /api/v1/submissions/{submission_id}
POST   /api/v1/submissions/{submission_id}/files
POST   /api/v1/submissions/{submission_id}/resubmit
GET    /api/v1/submissions/{submission_id}/history
```

### Staff Review Endpoints

```text
GET    /api/v1/staff/submissions
GET    /api/v1/staff/submissions/{submission_id}
PATCH  /api/v1/staff/submissions/{submission_id}/metadata
POST   /api/v1/staff/submissions/{submission_id}/corrections
POST   /api/v1/staff/submissions/{submission_id}/approve
POST   /api/v1/staff/submissions/{submission_id}/reject
POST   /api/v1/staff/submissions/{submission_id}/export
```

### System Endpoints

```text
GET    /api/v1/health
GET    /api/v1/jobs/{job_id}
```

---

## Project Structure

```text
research-submission-pipeline/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── workers/
│   │   ├── utils/
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── infrastructure/
│   ├── docker/
│   ├── nginx/
│   └── dspace-dev/
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── database-schema.md
│   ├── security.md
│   └── deployment.md
│
├── docker-compose.yml
├── .env.example
├── LICENSE
└── README.md
```

---

## Local Development Setup

### Prerequisites

Install the following tools:

- Git
- Docker and Docker Compose
- Node.js 20 or later
- Python 3.11 or later
- PostgreSQL, if not using Docker
- Redis, if not using Docker
- Tesseract OCR, if testing OCR locally

### Clone the repository

```bash
git clone [https://github.com/your-organization/research-submission-pipeline.git](https://github.com/your-organization/research-submission-pipeline.git)
cd research-submission-pipeline
```

### Configure environment variables

Create an environment file from the example:

```bash
cp .env.example .env
```

Example environment variables:

```env
ENVIRONMENT=development

POSTGRES_DB=research_pipeline
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/research_pipeline

REDIS_URL=redis://redis:6379/0

SECRET_KEY=replace-with-a-secure-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=60

S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=research-submissions

MAX_UPLOAD_SIZE_MB=100
ALLOWED_FILE_TYPES=application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

> Never commit `.env` files, private keys, credentials, student records or research documents to GitHub.

### Start services with Docker

```bash
docker compose up --build
```

The expected local services are:

| Service | Example local address |
|---|---|
| Frontend | `http://localhost:3000` |
| FastAPI API | `http://localhost:8000` |
| API documentation | `http://localhost:8000/docs` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |
| MinIO Console | `http://localhost:9001` |

### Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### Stop services

```bash
docker compose down
```

---

## Security Principles

The system handles institutional research records and should be developed with security and privacy in mind.

- Authenticate all users.
- Apply role-based access control.
- Store passwords using Argon2 or bcrypt hashing.
- Use HTTPS in staging and production.
- Validate MIME type, extension and file size.
- Calculate SHA-256 checksums for uploaded files.
- Store uploaded research files in private storage.
- Use signed, time-limited file-download URLs.
- Maintain audit logs for workflow actions.
- Do not expose storage keys or internal infrastructure details in the frontend.
- Restrict students to their own submissions.
- Restrict staff access to authorised submissions.
- Apply retention rules approved by the institution.
- Use authorised or anonymised documents for testing.
- Keep a human approval stage before repository publication.

---

## Development Roadmap

### Phase 1: Foundation

- [ ] Create frontend and backend applications.
- [ ] Configure Docker Compose.
- [ ] Configure PostgreSQL and Redis.
- [ ] Implement database migrations.
- [ ] Add health-check endpoint.
- [ ] Set up environment-variable configuration.

### Phase 2: Authentication and Roles

- [ ] Implement student login.
- [ ] Implement reviewer login.
- [ ] Implement administrator role.
- [ ] Add role-based access control.
- [ ] Add protected frontend routes.

### Phase 3: Submission Workflow

- [ ] Create submission form.
- [ ] Implement document upload.
- [ ] Validate file type and file size.
- [ ] Generate SHA-256 checksum.
- [ ] Generate a unique submission reference.
- [ ] Store document in controlled storage.
- [ ] Display submission status.

### Phase 4: Corrections and Tracking

- [ ] Add student submission history.
- [ ] Add staff review queue.
- [ ] Add correction-request workflow.
- [ ] Add resubmission versioning.
- [ ] Add notification support.
- [ ] Add audit logs.

### Phase 5: Document Intelligence

- [ ] Extract text from PDF files.
- [ ] Extract text from DOCX files.
- [ ] Detect scanned documents.
- [ ] Add OCR preprocessing.
- [ ] Extract candidate metadata.
- [ ] Add confidence scoring.
- [ ] Store source-page evidence.
- [ ] Add research-area and keyword classification.

### Phase 6: Verification and Export

- [ ] Build staff metadata-review interface.
- [ ] Enable metadata correction and approval.
- [ ] Generate repository-ready metadata export.
- [ ] Package approved files for export.
- [ ] Test DSpace development integration.
- [ ] Evaluate API/SWORD integration after institutional authorisation.

### Phase 7: Evaluation

- [ ] Compare manual and AI-assisted processing time.
- [ ] Measure metadata completeness.
- [ ] Measure metadata accuracy.
- [ ] Measure correction rate.
- [ ] Measure processing throughput.
- [ ] Measure AI metadata error/hallucination rate.
- [ ] Collect usability feedback from staff and students.

---

## Success Metrics

The project will be evaluated using measurable operational and metadata-quality outcomes.

| Metric | Description |
|---|---|
| Processing time | Average time from submission to staff-ready record |
| Throughput | Number of documents processed per day |
| Metadata accuracy | Percentage of extracted fields matching verified metadata |
| Metadata completeness | Percentage of required metadata fields populated |
| Correction rate | Percentage of submissions requiring student corrections |
| AI error rate | Percentage of AI-generated fields found to be incorrect |
| Approval time | Average time from submission to staff approval |
| Resubmission time | Average time taken by students to resolve corrections |
| User satisfaction | Feedback from students and Digitization Unit staff |

---

## DSpace Integration Approach

The institutional repository remains the system of record.

The integration strategy follows this order:

1. Generate repository-ready metadata and approved files.
2. Export records in a controlled format.
3. Test ingestion against a self-hosted DSpace development environment.
4. Confirm the institution’s DSpace version, API access and permissions.
5. Integrate through an authorised DSpace REST API, SWORD endpoint or approved workflow.
6. Perform production integration only after institutional approval.

This approach allows the team to demonstrate the full workflow without requiring immediate production access to the institutional repository.

---

## Current Scope

The initial prototype focuses on:

- Postgraduate theses and dissertations.
- Digital PDF and DOCX submissions.
- Controlled, authorised sample documents.
- Student submission tracking.
- Staff review and correction workflow.
- AI-assisted metadata extraction with human verification.
- Repository-ready export.

The following are outside the initial prototype scope:

- Replacing the existing institutional repository.
- Direct production integration without institutional authorisation.
- Fully automated publication without staff approval.
- Large-scale physical scanning operations.
- Processing unauthorised, confidential or copyrighted documents.

---

## Team Responsibilities

| Work Package | Lead Responsibility | Main Output |
|---|---|---|
| Requirements and workflow mapping | Entire team and Digitization Unit | Process map, user roles, metadata schema and acceptance criteria |
| Portal and API | Frontend/backend team | Submission portal, receipt, tracking, correction workflow and staff dashboard |
| Metadata processing | AI/data team | Extraction pipeline, classification and evaluation dataset |
| Repository integration | Frontend/backend team | Export module and tested DSpace development pathway |
| Testing and evaluation | Entire team and staff stakeholders | Benchmark report, usability findings and deployment recommendations |

---

## Contribution Guidelines

1. Create a feature branch from `develop`.
2. Use clear branch names, such as:

```text
feature/student-upload
feature/staff-dashboard
feature/metadata-extraction
fix/file-validation
docs/api-documentation
```

3. Write meaningful commit messages:

```text
feat: add thesis submission endpoint
fix: validate uploaded file MIME type
docs: add local development instructions
test: add submission workflow tests
```

4. Open a pull request for review before merging.
5. Do not commit secrets, credentials, `.env` files or real student documents.
6. Add tests for new backend features where possible.
7. Update documentation whenever API contracts or workflows change.

---

## License

This project is currently developed as an academic/research prototype.

The final license, ownership model, deployment policy and access rules should be determined in collaboration with the relevant university stakeholders before production deployment.

---

## Disclaimer

This platform provides AI-assisted document processing and metadata suggestions. It does not make final institutional decisions and must not publish repository records automatically.

All metadata extracted by OCR, rules, NLP models or LLMs must be reviewed and approved by authorised staff before repository ingestion or publication.
