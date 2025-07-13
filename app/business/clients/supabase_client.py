import os
from typing import Optional

from loguru import logger
from supabase import create_async_client, AsyncClient

from config.settings import get_settings
from presentation.schemas.requests.ingestion import UploadFileRequest, GetFileRequest

settings = get_settings()


class SupabaseClient:
    _instance = None
    _client: Optional[AsyncClient] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if not hasattr(self, '_initialized'):
            self._initialized = True

    async def initialize(self):
        """Initialize the async Supabase client (only once)"""
        if not self._initialized or self._client is None:
            self._client = await create_async_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            self._initialized = True
            logger.info("Supabase client initialized (singleton)")

    async def _ensure_client(self):
        """Ensure the client is initialized before use"""
        if self._client is None:
            await self.initialize()

    async def get_buckets(self):
        """Get all buckets from Supabase storage"""
        await self._ensure_client()
        response = await self._client.storage.list_buckets()
        logger.info(f"Buckets: {response}")
        return response

    async def get_bucket(self, bucket_name: str):
        """Get a specific bucket from Supabase storage"""
        await self._ensure_client()
        response = await self._client.storage.get_bucket(bucket_name)
        logger.info(f"Bucket: {response}")
        return response

    async def upload_file(self, upload_request: UploadFileRequest):
        """
        Upload a file to Supabase storage
        
        Args:
            upload_request: UploadFileRequest object containing file details and file object
            
        Returns:
            The upload response from Supabase
        """
        await self._ensure_client()
        
        file_options = {"cache-control": "3600", "upsert": "false"}
        if upload_request.content_type:
            file_options["content-type"] = upload_request.content_type

        # Read the file content and pass as bytes
        file_content = upload_request.file_object.read()
        response = await (
            self._client.storage
            .from_(upload_request.bucket_name)
            .upload(
                file=file_content,
                path=upload_request.storage_path,
                file_options=file_options
            )
        )

        logger.info(f"File uploaded successfully to {upload_request.bucket_name}/{upload_request.storage_path}")
        return response

    async def download_file(self, get_request: GetFileRequest, local_path: str):
        """
        Download a file from Supabase storage
        
        Args:
            get_request: GetFileRequest object containing bucket and storage path
            local_path: Local path where the file should be saved
            
        Returns:
            The download response from Supabase
        """
        await self._ensure_client()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        response = await (
            self._client.storage
            .from_(get_request.bucket_name)
            .download(path=get_request.storage_path)
        )

        # Save the downloaded content to local file
        with open(local_path, "wb") as f:
            f.write(response)

        logger.info(
            f"File downloaded successfully from {get_request.bucket_name}/{get_request.storage_path} to {local_path}")
        return response

    async def get_file_url(self, get_request: GetFileRequest) -> str:
        """
        Get the public URL for a file in Supabase storage
        
        Args:
            get_request: GetFileRequest object containing bucket and storage path
            
        Returns:
            The public URL of the file
        """
        await self._ensure_client()
        
        url = await (
            self._client.storage
            .from_(get_request.bucket_name)
            .get_public_url(get_request.storage_path)
        )
        # Remove any trailing query parameters that might cause issues
        clean_url = url.split('?')[0] if '?' in url else url
        logger.info(f"Public URL for {get_request.bucket_name}/{get_request.storage_path}: {clean_url}")
        return clean_url
