from pydantic import BaseModel
from typing import Dict, List

class FileResult(BaseModel):
    filename: str
    status: str  # e.g., "Processed", "Unsupported File Type", "Error"
    extracted_text: str | None  # None if unsupported or error occurred

class FileUploadResponse(BaseModel):
    files: List[FileResult]  # A list of results for all processed files
