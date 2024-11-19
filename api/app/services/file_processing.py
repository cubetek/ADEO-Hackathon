# app/services/file_processing.py

from typing import List, Dict
import asyncio
import base64
import logging
from PyPDF2 import PdfReader
from docx import Document
import pytesseract
from PIL import Image
import io
import hashlib

logger = logging.getLogger(__name__)

async def process_files(files: List[Dict]) -> List[Dict]:
    """
    Process uploaded files and extract text where applicable.
    Supports images (OCR), PDFs, DOC/DOCX, and plain text files.
    """
    processed_results = []

    tasks = [process_file(file, idx) for idx, file in enumerate(files)]
    processed_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Log any exceptions and filter results
    for idx, result in enumerate(processed_results):
        if isinstance(result, Exception):
            logger.error(f"Error processing file at index {idx}: {result}")
            processed_results[idx] = {
                "type": "file",
                "text": "Processing Failed",
                "status": "Failed",
                "file_name": files[idx].get("file_name", "Unknown"),
                "error": str(result),
            }

    return processed_results


async def process_file(file: Dict, idx: int) -> Dict:
    """
    Process a single file based on its MIME type.
    """
    file_name = file.get("file_name")
    if not file_name:
        raise ValueError(f"File name is missing for file at index {idx}")

    mime_type = file["mime_type"]
    data = file["data"]

    try:
        if mime_type.startswith("image/"):
            extracted_text = await perform_ocr(data)
            return {
                "type": "image",
                "text": f"Image file (OCR)",
                "status": "Processed",
                "file_name": file_name,
                "extracted_text": extracted_text,
                "image": f"data:{mime_type};base64,{base64.b64encode(data).decode('utf-8')}",
            }

        elif mime_type == "application/pdf":
            extracted_text = await extract_text_from_pdf(data)
            return {
                "type": "file",
                "text": "PDF Document",
                "status": "Processed",
                "file_name": file_name,
                "extracted_text": extracted_text,
                "file_id": generate_file_id(data),
            }

        elif mime_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ]:
            extracted_text = await extract_text_from_docx(data)
            return {
                "type": "file",
                "text": "Word Document",
                "status": "Processed",
                "file_name": file_name,
                "extracted_text": extracted_text,
                "file_id": generate_file_id(data),
            }

        elif mime_type == "text/plain":
            extracted_text = data.decode("utf-8")
            return {
                "type": "file",
                "text": "Text File",
                "status": "Processed",
                "file_name": file_name,
                "extracted_text": extracted_text,
                "file_id": generate_file_id(data),
            }

        else:
            raise ValueError(f"Unsupported file type: {mime_type}")

    except Exception as e:
        logger.error(f"Error processing file at index {idx}: {e}")
        raise


async def perform_ocr(image_data: bytes) -> str:
    """
    Perform OCR on image data to extract text.
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        extracted_text = pytesseract.image_to_string(image)
        return extracted_text.strip()
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return "OCR failed"


async def extract_text_from_pdf(pdf_data: bytes) -> str:
    """
    Extract text from PDF data.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_data))
        text = "\n".join(
            page.extract_text() for page in reader.pages if page.extract_text()
        )
        return text.strip()
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        return "PDF text extraction failed"


async def extract_text_from_docx(docx_data: bytes) -> str:
    """
    Extract text from DOCX or DOC data.
    """
    try:
        document = Document(io.BytesIO(docx_data))
        text = "\n".join([para.text for para in document.paragraphs])
        return text.strip()
    except Exception as e:
        logger.error(f"DOCX text extraction failed: {e}")
        return "DOCX text extraction failed"


def generate_file_id(data: bytes) -> str:
    """
    Generate a unique file ID for storage and retrieval.
    """
    return hashlib.md5(data).hexdigest()
