class AIWorkerException(Exception):
    """Base exception for AI worker pipeline."""
    pass

class DocumentNotFoundError(AIWorkerException):
    """Raised when PDF file is not found at given path."""
    pass

class DocumentCorruptError(AIWorkerException):
    """Raised when PDF is damaged, empty, or unreadable."""
    pass

class PasswordProtectedError(AIWorkerException):
    """Raised when PDF requires an authentication password."""
    pass

class ClassificationError(AIWorkerException):
    """Raised when document cannot be reliably classified as digital or scanned."""
    pass

class DigitalExtractionError(AIWorkerException):
    """Raised when PyMuPDF extraction fails."""
    pass

class ScannedExtractionError(AIWorkerException):
    """Raised when PaddleOCR extraction fails."""
    pass

class LLMExtractionError(AIWorkerException):
    """Raised when Gemini API request fails or encounters network error."""
    pass

class MetadataValidationError(AIWorkerException):
    """Raised when LLM output violates the strict 3-field schema."""
    pass

