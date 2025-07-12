import hmac
from hashlib import sha256
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, HTTPException, status, Header

from config.settings import get_settings
from presentation.dependencies import IngestionServiceDependency
from presentation.schemas.requests.ingestion import UploadFileRequest

router = APIRouter(prefix="/ingestion")

settings = get_settings()


def verify_hmac_signature(signature: str, expected_signature: str) -> bool:
    """
    Verify HMAC signature using constant-time comparison to prevent timing attacks
    
    Args:
        signature: The signature from the request header
        expected_signature: The expected signature to compare against
        
    Returns:
        True if signatures match, False otherwise
    """
    if not signature or not expected_signature:
        return False

    return hmac.compare_digest(signature, expected_signature)


@router.post("/upload")
async def ingest_pdf(
        file: Annotated[UploadFile, File(description="PDF file to upload and ingest")],
        service: IngestionServiceDependency,
        x_omar_signature: str = Header(None, description="HMAC signature for request authentication"),
):
    """
    Upload a PDF file to Supabase storage and ingest it into the vector database
    
    Args:
        file: The PDF file to upload
        service: Injected ingestion service
        x_omar_signature: HMAC signature for request authentication
    """
    # Verify HMAC signature if authentication is enabled
    if not x_omar_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="HMAC signature header is required"
        )

    # Generate expected signature
    mac = hmac.new(
        key=settings.APP_SECRET_KEY.encode("utf-8"),
        msg=settings.APP_SECRET_MESSAGE.encode("utf-8"),
        digestmod=sha256,
    )
    expected_signature = mac.hexdigest()

    # Verify signature using constant-time comparison
    if not verify_hmac_signature(x_omar_signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid HMAC signature"
        )

    storage_path = file.filename

    # Create UploadFileRequest using UploadFile attributes
    upload_request = UploadFileRequest(
        file_path=file.filename,
        bucket_name=settings.SUPABASE_STORAGE_BUCKET_NAME,
        storage_path=storage_path,
        content_type=file.content_type or "application/pdf",
        file_object=file.file
    )

    # Call ingestion service with the file object directly
    service.ingest(upload_request)

    return {
        "message": "File uploaded and ingested successfully"
    }
