from uuid import uuid4

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_aws import BedrockEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from loguru import logger
from pinecone import Pinecone

from business.clients.supabase_client import SupabaseClient
from config.settings import get_settings
from presentation.schemas.requests.ingestion import UploadFileRequest, GetFileRequest

settings = get_settings()


class IngestionService:
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase_client = supabase_client
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

    async def ingest(self, upload_request: UploadFileRequest):
        """
        Ingest a file by uploading to Supabase, then indexing to Pinecone
        
        Args:
            upload_request: UploadFileRequest object containing file details and file object
        """
        logger.info(f"Starting ingestion for file: {upload_request.file_path}")

        # 1. Upload file to Supabase storage
        upload_response = await self.supabase_client.upload_file(upload_request)

        # 2. Get public URL for the uploaded file
        get_request = GetFileRequest(
            bucket_name=upload_request.bucket_name,
            storage_path=upload_response.path
        )
        file_url = await self.supabase_client.get_file_url(get_request)

        # 3. Load PDF directly from URL
        pdf_loader = PyPDFLoader(file_url)
        loaded_documents: list[Document] = pdf_loader.load()
        logger.info(f"Loaded {len(loaded_documents)} pages from the document")

        # 4. Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n"],
            chunk_size=500,
            chunk_overlap=0,
            length_function=len,
            is_separator_regex=False,
        )
        splitted_documents = text_splitter.split_documents(loaded_documents)
        logger.info(f"Split into {len(splitted_documents)} chunks")

        # 5. Generate unique UUIDs for each document
        uuids = [str(uuid4()) for _ in range(len(splitted_documents))]

        # 6. Embed and store in Pinecone
        self.vector_store.add_documents(documents=splitted_documents, ids=uuids)
        logger.info("Ingestion completed successfully")
