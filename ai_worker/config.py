import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env from current directory or parent directories
load_dotenv()

def get_gemini_api_key() -> str:
    """Retrieves Gemini API key checking standard uppercase, titlecase, lowercase and Google alias."""
    return (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("Gemini_API_KEY")
        or os.getenv("gemini_api_key")
        or os.getenv("GOOGLE_API_KEY")
        or ""
    ).strip()

@dataclass
class Config:
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # Dramatiq Queue Name
    DEFAULT_QUEUE: str = "default"
    
    # PDF Processing Parameters
    DEFAULT_MAX_PAGES: int = 15
    MIN_TEXT_CHARS_PER_PAGE: int = 50
    
    # Gemini API Configuration (Default updated to gemini-3.8-flash)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    
    # Output Directory
    OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", r"C:\Users\DELL 3520\Desktop\ai worker\output"))
    
    @property
    def GEMINI_API_KEY(self) -> str:
        return get_gemini_api_key()

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

config = Config()
