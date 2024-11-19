from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
from app.services.file_processing import process_files

router = APIRouter()

@router.post("/uploadfile/")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload one or multiple files and process them.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    # Prepare files for processing
    decoded_files = []
    for file in files:
        try:
            data = await file.read()
            decoded_files.append({"mime_type": file.content_type, "data": data, "file_name": file.filename})
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error reading file {file.filename}: {e}"
            )

    # Process files asynchronously
    results = await process_files(decoded_files)
    return {"files": results}
