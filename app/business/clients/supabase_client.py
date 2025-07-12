import os

from loguru import logger
from supabase import create_client, Client

from config.settings import get_settings
from presentation.schemas.requests.ingestion import UploadFileRequest, GetFileRequest

settings = get_settings()


class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    def get_buckets(self):
        """Get all buckets from Supabase storage"""
        response = self.client.storage.list_buckets()
        logger.info(f"Buckets: {response}")
        return response

    def get_bucket(self, bucket_name: str):
        """Get a specific bucket from Supabase storage"""
        response = self.client.storage.get_bucket(bucket_name)
        logger.info(f"Bucket: {response}")
        return response

    def upload_file(self, upload_request: UploadFileRequest):
        """
        Upload a file to Supabase storage
        
        Args:
            upload_request: UploadFileRequest object containing file details and file object
            
        Returns:
            The upload response from Supabase
        """
        file_options = {"cache-control": "3600", "upsert": "false"}
        if upload_request.content_type:
            file_options["content-type"] = upload_request.content_type

        # Read the file content and pass as bytes
        file_content = upload_request.file_object.read()
        response = (
            self.client.storage
            .from_(upload_request.bucket_name)
            .upload(
                file=file_content,
                path=upload_request.storage_path,
                file_options=file_options
            )
        )

        logger.info(f"File uploaded successfully to {upload_request.bucket_name}/{upload_request.storage_path}")
        return response

    def download_file(self, get_request: GetFileRequest, local_path: str):
        """
        Download a file from Supabase storage
        
        Args:
            get_request: GetFileRequest object containing bucket and storage path
            local_path: Local path where the file should be saved
            
        Returns:
            The download response from Supabase
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        response = (
            self.client.storage
            .from_(get_request.bucket_name)
            .download(path=get_request.storage_path)
        )

        # Save the downloaded content to local file
        with open(local_path, "wb") as f:
            f.write(response)

        logger.info(
            f"File downloaded successfully from {get_request.bucket_name}/{get_request.storage_path} to {local_path}")
        return response

    def get_file_url(self, get_request: GetFileRequest) -> str:
        """
        Get the public URL for a file in Supabase storage
        
        Args:
            get_request: GetFileRequest object containing bucket and storage path
            
        Returns:
            The public URL of the file
        """
        url = (
            self.client.storage
            .from_(get_request.bucket_name)
            .get_public_url(get_request.storage_path)
        )
        # Remove any trailing query parameters that might cause issues
        clean_url = url.split('?')[0] if '?' in url else url
        logger.info(f"Public URL for {get_request.bucket_name}/{get_request.storage_path}: {clean_url}")
        return clean_url
