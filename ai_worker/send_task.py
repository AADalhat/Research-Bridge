import sys
import argparse
import json
from pathlib import Path

# Ensure workspace directory is in python path
workspace_dir = str(Path(__file__).parent.resolve())
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

import broker
from config import config
from tasks import extract_pdf_metadata

def main():
    parser = argparse.ArgumentParser(
        description="Dispatch asynchronous PDF metadata extraction task to Redis via Dramatiq."
    )
    parser.add_argument("pdf_path", type=str, help="Path to the PDF document to extract")
    parser.add_argument(
        "--mode",
        choices=["auto", "digital", "scanned"],
        default="auto",
        help="Extraction mode (default: auto)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=15,
        help="Maximum pages to process (default: 15)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Gemini API Key (optional, defaults to GEMINI_API_KEY env or .env file)",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for the Dramatiq worker to finish and display the result",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds when waiting for result (default: 120)",
    )

    args = parser.parse_args()

    pdf_file = Path(args.pdf_path).resolve()
    if not pdf_file.exists():
        print(f"Error: File does not exist: {pdf_file}", file=sys.stderr)
        sys.exit(1)

    effective_api_key = args.api_key or config.GEMINI_API_KEY or ""

    print(f"Submitting task to Redis queue for file: {pdf_file}")
    print(f"Mode: {args.mode} | Max Pages: {args.max_pages}")
    if effective_api_key:
        masked = effective_api_key[:6] + "..." + effective_api_key[-4:] if len(effective_api_key) > 10 else "***"
        print(f"Gemini API Key configured: {masked}")
    else:
        print("Notice: No Gemini API Key detected in terminal or .env. Output will be marked EXTRACTION_STALLED.")

    # Dispatch to Dramatiq with api_key in payload
    message = extract_pdf_metadata.send(
        file_path=str(pdf_file),
        mode=args.mode,
        max_pages=args.max_pages,
        api_key=effective_api_key if effective_api_key else None
    )

    print(f"Task enqueued successfully! Message ID: {message.message_id}")

    if args.wait:
        print(f"Waiting for worker to complete (timeout: {args.timeout}s)...")
        try:
            result = message.get_result(block=True, timeout=args.timeout * 1000)
            print("\n" + "=" * 60)
            print("TASK RESULT RECEIVED FROM REDIS:")
            print("=" * 60)
            print(f"Job ID:          {result.get('job_id')}")
            print(f"Status:          {result.get('status')}")
            print(f"Classification:  {result.get('classification')}")
            print(f"Pages Processed: {result.get('pages_processed')} / {result.get('total_pages_in_doc')}")
            print(f"Output File:     {result.get('output_file')}")
            
            if result.get("error_message"):
                print(f"Error / Note:    {result.get('error_message')}")

            candidate = result.get("candidate_metadata")
            if candidate:
                print("\nCandidate Metadata (Validated):")
                print(f"  Title:    {candidate.get('title')}")
                print(f"  Keywords: {', '.join(candidate.get('subject_keywords', []))}")
                abstract = candidate.get('abstract', '')
                print(f"  Abstract: {abstract[:200]}..." if len(abstract) > 200 else f"  Abstract: {abstract}")
            else:
                print("\nCandidate Metadata: None (Extraction Stalled or Pending LLM)")

            evidence = result.get("evidence_data")
            if evidence:
                print(f"\nEvidence Version: Schema v{evidence.get('schema_version')}")

            print("=" * 60)
        except Exception as e:
            print(f"\nError waiting for result: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Task is running in background. You can check the worker logs or output directory.")

if __name__ == "__main__":
    main()
