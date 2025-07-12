import os
from typing import Optional
from uuid import uuid4

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_aws import BedrockEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from loguru import logger
from pinecone import Pinecone
from pydantic import BaseModel, Field
from supabase import create_client, Client

from app.config.settings import get_settings

settings = get_settings()


class UploadFileRequest(BaseModel):
    """Schema for file upload request events"""
    file_path: str = Field(..., description="The local file path to upload")
    bucket_name: str = Field(..., description="The Supabase storage bucket name")
    storage_path: str = Field(..., description="The path where the file should be stored in the bucket")
    session_id: Optional[str] = Field(None, description="Optional session identifier")
    user_id: Optional[str] = Field(None, description="Optional user identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/path/to/local/file.pdf",
                "bucket_name": "rag",
                "storage_path": "documents/portfolio.pdf",
                "session_id": "session_123",
                "user_id": "user_456"
            }
        }


class IngestionService:
    def __init__(self):
        self.supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        self.pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.embeddings_model = BedrockEmbeddings(
            model_id=settings.EMBEDDING_MODEL_ID,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.index = self.pinecone_client.Index(settings.PINECONE_INDEX_NAME)
        self.vector_store = PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            index=self.index,
            embedding=self.embeddings_model
        )

    def get_buckets(self):
        response = (
            self.supabase_client.storage.list_buckets()
        )

        logger.info(f"Buckets: {response}")

    def get_bucket(self, bucket_name: str):
        response = (
            self.supabase_client.storage.get_bucket(bucket_name)
        )

        logger.info(f"Bucket: {response}")

    def upload_file(self, file: UploadFileRequest):
        """
        Upload a file to Supabase storage
        
        Args:
            file: Upload file object
            
        Returns:
            The upload response from Supabase
        """
        with open(file.file_path, "rb") as f:
            response = (
                self.supabase_client.storage
                .from_(file.bucket_name)
                .upload(
                    file=f,
                    path=file.storage_path,
                    file_options={"cache-control": "3600", "content-type": "application/pdf", "upsert": "false"}
                )
            )
            logger.info(f"File uploaded successfully to {file.bucket_name}/{file.storage_path}")
            return response

    def download_file(self, bucket_name: str, storage_path: str, local_path: str):
        """
        Download a file from Supabase storage
        
        Args:
            bucket_name: Name of the Supabase storage bucket
            storage_path: Path of the file in the bucket
            local_path: Local path where the file should be saved
            
        Returns:
            The download response from Supabase
        """

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        response = (
            self.supabase_client.storage
            .from_(bucket_name)
            .download(path=storage_path)
        )

        # Save the downloaded content to local file
        with open(local_path, "wb") as f:
            f.write(response)

        logger.info(f"File downloaded successfully from {bucket_name}/{storage_path} to {local_path}")
        return response

    def get_file_url(self, bucket_name: str, storage_path: str) -> str:
        """
        Get the public URL for a file in Supabase storage
        
        Args:
            bucket_name: Name of the Supabase storage bucket
            storage_path: Path of the file in the bucket
            
        Returns:
            The public URL of the file
        """
        url = (
            self.supabase_client.storage
            .from_(bucket_name)
            .get_public_url(storage_path)
        )
        # Remove any trailing query parameters that might cause issues
        clean_url = url.split('?')[0] if '?' in url else url
        logger.info(f"Public URL for {bucket_name}/{storage_path}: {clean_url}")
        return clean_url

    def ingest(self, file_path: str):
        logger.info(f"Starting ingestion for file: {file_path}")

        # Load PDF
        pdf_loader = PyPDFLoader(file_path)
        loaded_documents: list[Document] = pdf_loader.load()
        logger.info(f"Loaded {len(loaded_documents)} documents")

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n"],
            chunk_size=500,
            chunk_overlap=0,
            length_function=len,
            is_separator_regex=False,
        )
        splitted_documents = text_splitter.split_documents(loaded_documents)
        logger.info(f"Split into {len(splitted_documents)} chunks")

        # Generate unique UUIDs for each document
        uuids = [str(uuid4()) for _ in range(len(splitted_documents))]

        # Embed and store in Pinecone
        self.vector_store.add_documents(documents=splitted_documents, ids=uuids)
        logger.info("Ingestion completed successfully")


# Example usage
if __name__ == '__main__':
    settings = get_settings()
    ingestion_service = IngestionService()
    ingestion_service.get_bucket("rag")

    # Example workflow:
    # 1. Upload file to Supabase storage
    upload_file_request = UploadFileRequest(
        file_path="../rag_data/Test_Resume.pdf",
        bucket_name="rag",
        storage_path="Test_Resume.pdf",
        session_id="123",
        user_id="456"
    )
    upload_response = ingestion_service.upload_file(upload_file_request)

    # 2. Get public URL for the uploaded file
    file_url = ingestion_service.get_file_url(upload_file_request.bucket_name, upload_response.path)

    # 3. Download file from storage (if needed for local processing)
    ingestion_service.download_file(upload_file_request.bucket_name, upload_file_request.storage_path,
                                    f"../tmp/{upload_response.path}")

    # 4. Ingest the file into Pinecone (using public URL or local path)
    ingestion_service.ingest(file_url)  # or use local path
