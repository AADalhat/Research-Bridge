import sys
import argparse
from pathlib import Path

# Ensure workspace directory is in python path
workspace_dir = str(Path(__file__).parent.resolve())
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from config import config
from pipeline import run_extraction_pipeline

def main():
    parser = argparse.ArgumentParser(
        description="CrownBird Standalone PDF Metadata Extraction CLI"
    )
    parser.add_argument("pdf_path", type=str, help="Path to PDF file")
    parser.add_argument(
        "--mode",
        choices=["auto", "digital", "scanned"],
        default="auto",
        help="Processing mode (default: auto)",
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
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory for JSON results",
    )

    args = parser.parse_args()

    pdf_file = Path(args.pdf_path).resolve()
    if not pdf_file.exists():
        print(f"Error: File does not exist: {pdf_file}", file=sys.stderr)
        sys.exit(1)

    effective_api_key = args.api_key or config.GEMINI_API_KEY or ""
    out_dir = Path(args.output_dir).resolve() if args.output_dir else None

    print(f"Running extraction on: {pdf_file}")
    print(f"Mode: {args.mode} | Max Pages: {args.max_pages}")
    if effective_api_key:
        masked = effective_api_key[:6] + "..." + effective_api_key[-4:] if len(effective_api_key) > 10 else "***"
        print(f"Gemini API Key configured: {masked}")
    else:
        print("Notice: No Gemini API Key detected in terminal or .env. Output will be marked EXTRACTION_STALLED.")

    result = run_extraction_pipeline(
        file_path=str(pdf_file),
        mode=args.mode,
        max_pages=args.max_pages,
        output_dir=out_dir,
        api_key=effective_api_key if effective_api_key else None
    )

    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Job ID:          {result.job_id}")
    print(f"Status:          {result.status}")
    print(f"Classification:  {result.classification}")
    print(f"Pages Processed: {result.pages_processed} of {result.total_pages_in_doc}")
    print(f"JSON Output:     {result.output_file}")

    if result.error_message:
        print(f"Error / Note:    {result.error_message}")

    if result.candidate_metadata:
        print("\nExtracted Candidate Metadata:")
        print(f"  Title:    {result.candidate_metadata.get('title')}")
        print(f"  Keywords: {', '.join(result.candidate_metadata.get('subject_keywords', []))}")
        abstract = result.candidate_metadata.get('abstract', '')
        print(f"  Abstract: {abstract[:200]}..." if len(abstract) > 200 else f"  Abstract: {abstract}")

    print("=" * 60)

if __name__ == "__main__":
    main()
