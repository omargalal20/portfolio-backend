import os
import tempfile

from fastapi import APIRouter, UploadFile

from settings import get_settings
from app.presentation.dependencies import IngestionServiceDependency

router = APIRouter(prefix="/ingestion")

settings = get_settings()


@router.post("/upload")
async def ingest_pdf(file: UploadFile, service: IngestionServiceDependency):
    # Save uploaded file temporarily
    temp_dir = tempfile.gettempdir()  # Automatically gets the correct temp directory for the OS
    file_path = os.path.join(temp_dir, file.filename)

    # Save the uploaded file
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Call ingestion service
    service.ingest(file_path)
    return {"message": "File ingested successfully"}
