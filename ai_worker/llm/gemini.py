import os
import json
import re
from typing import Tuple, Optional, Dict, Any
from google import genai
from google.genai import types

from models import DocumentText, CandidateMetadata, EvidenceData, EvidenceFields, EvidenceItem
from config import config
from exceptions import LLMExtractionError, MetadataValidationError

EXTRACTION_SYSTEM_PROMPT = """You are an authoritative research metadata extraction specialist for an academic repository.
Analyze the provided academic document text (which includes page markers like --- PAGE 1 ---).
Extract EXACTLY three metadata fields:
1. "title": The official title of the research paper, thesis, or dissertation.
2. "subject_keywords": A list of relevant subject keywords or topic descriptors (between 3 and 10 keywords).
3. "abstract": The full executive summary or abstract of the research work.

You MUST also provide source evidence for each extracted field under "evidence", linking each claim to its exact 1-based page number and verbatim excerpt from the document text.

You MUST respond strictly with a valid JSON object in the following format:
{
  "title": "Document Title",
  "subject_keywords": ["Keyword1", "Keyword2", "Keyword3"],
  "abstract": "The research abstract text...",
  "evidence": {
    "title": [
      {"page_number": 1, "source_text": "Verbatim title text on page"}
    ],
    "subject_keywords": [
      {"page_number": 2, "source_text": "Keywords: Keyword1, Keyword2, Keyword3"}
    ],
    "abstract": [
      {"page_number": 3, "source_text": "Abstract text beginning..."}
    ]
  }
}
Do NOT include any commentary, explanations, or Markdown fences outside the JSON object.
"""

def extract_metadata_with_gemini(
    doc_text: DocumentText,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> Tuple[str, Optional[CandidateMetadata], Optional[EvidenceData], Optional[str]]:
    """
    Calls Google Gemini using the official google-genai SDK to extract the strict 3-field metadata contract.
    
    Returns:
        tuple: (candidate_metadata_raw, candidate_metadata, evidence_data, error_message)
    """
    key = api_key or os.getenv("GEMINI_API_KEY") or config.GEMINI_API_KEY
    model = model_name or config.GEMINI_MODEL

    if not key:
        err = "GEMINI_API_KEY is not configured. LLM extraction cannot proceed."
        return ("", None, None, err)

    client = genai.Client(api_key=key)

    user_prompt = f"""Extract the research metadata from the following academic document:

=== DOCUMENT TEXT (First {doc_text.pages_processed} pages) ===
{doc_text.full_text}
"""

    raw_response_text = ""
    try:
        response = client.models.generate_content(
            model=model,
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=EXTRACTION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.1,
            )
        )
        raw_response_text = response.text or ""
    except Exception as e:
        err = f"Gemini API request failed: {e}"
        return (raw_response_text, None, None, err)

    if not raw_response_text.strip():
        return ("", None, None, "Gemini returned an empty response")

    # Clean markdown fences if model inadvertently included them
    cleaned_json_text = raw_response_text.strip()
    if cleaned_json_text.startswith("```"):
        cleaned_json_text = re.sub(r"^```(?:json)?\s*", "", cleaned_json_text)
        cleaned_json_text = re.sub(r"\s*```$", "", cleaned_json_text)

    try:
        parsed_data = json.loads(cleaned_json_text)
    except json.JSONDecodeError as je:
        err = f"Malformed JSON in Gemini response: {je}"
        return (raw_response_text, None, None, err)

    if not isinstance(parsed_data, dict):
        err = "Gemini response root is not a JSON object"
        return (raw_response_text, None, None, err)

    # Validate the 3 candidate fields strictly
    try:
        candidate = CandidateMetadata(
            title=parsed_data.get("title", ""),
            subject_keywords=parsed_data.get("subject_keywords", []),
            abstract=parsed_data.get("abstract", "")
        )
    except Exception as ve:
        err = f"Validation failed for candidate metadata fields: {ve}"
        return (raw_response_text, None, None, err)

    # Parse and validate evidence
    evidence_raw = parsed_data.get("evidence", {})
    evidence_fields = EvidenceFields()

    if isinstance(evidence_raw, dict):
        for field_name in ["title", "subject_keywords", "abstract"]:
            items_list = evidence_raw.get(field_name, [])
            if isinstance(items_list, list):
                parsed_items = []
                for item in items_list:
                    if isinstance(item, dict) and "page_number" in item and "source_text" in item:
                        try:
                            p_num = int(item["page_number"])
                            s_text = str(item["source_text"]).strip()
                            if p_num >= 1 and s_text:
                                parsed_items.append(EvidenceItem(page_number=p_num, source_text=s_text))
                        except (ValueError, TypeError):
                            pass
                setattr(evidence_fields, field_name, parsed_items)

    evidence_data = EvidenceData(schema_version=1, fields=evidence_fields)

    return (raw_response_text, candidate, evidence_data, None)

