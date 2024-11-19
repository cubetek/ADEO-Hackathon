# app/tasks.py
from app.celery_app import celery

@celery.task
def perform_ocr_task(image_data: bytes) -> str:
    # Implement OCR logic here
    return "Extracted text from image."

@celery.task
def extract_text_from_pdf_task(pdf_data: bytes) -> str:
    # Implement PDF extraction logic here
    return "Extracted text from PDF."
