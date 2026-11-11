import os
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from models import ExtractionJobResult
from config import config

def sanitize_filename(name: str) -> str:
    """Removes invalid filename characters."""
    return re.sub(r'[\\/*?:"<>| ]', '_', name)

def save_extraction_result(
    result: ExtractionJobResult,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Persists an ExtractionJobResult as a pretty-printed JSON file.
    Guarantees unique filename and prevents collisions.
    """
    target_dir = output_dir or config.OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    base_name = sanitize_filename(Path(result.file_path).stem)
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    short_id = result.job_id.split("-")[0] if "-" in result.job_id else result.job_id[:8]

    candidate_filename = f"{base_name}_{now_str}_{short_id}.json"
    file_path = target_dir / candidate_filename

    # If by some rare chance the file already exists, append an incremental counter
    counter = 1
    while file_path.exists():
        candidate_filename = f"{base_name}_{now_str}_{short_id}_{counter}.json"
        file_path = target_dir / candidate_filename
        counter += 1

    data = result.model_dump()
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return file_path

