from tempfile import SpooledTemporaryFile

from pydantic import BaseModel, Field


class UploadFileRequest(BaseModel):
    """Schema for file upload request events"""
    file_path: str = Field(..., description="The local file path to upload")
    bucket_name: str = Field(..., description="The Supabase storage bucket name")
    storage_path: str = Field(..., description="The path where the file should be stored in the bucket")
    content_type: str = Field(..., description="The content type of the file (e.g., application/pdf)")
    file_object: SpooledTemporaryFile = Field(..., description="The file object to upload")

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "file_path": "/path/to/local/file.pdf",
                "bucket_name": "supabase-bucket-name",
                "storage_path": "documents/portfolio.pdf",
                "content_type": "application/pdf"
            }
        }


class GetFileRequest(BaseModel):
    """Schema for file retrieval request events"""
    bucket_name: str = Field(..., description="The Supabase storage bucket name")
    storage_path: str = Field(..., description="The path of the file in the bucket")

    class Config:
        json_schema_extra = {
            "example": {
                "bucket_name": "supabase-bucket-name",
                "storage_path": "documents/portfolio.pdf"
            }
        }
