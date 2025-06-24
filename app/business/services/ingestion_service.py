import os
from uuid import uuid4

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_aws import BedrockEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from loguru import logger
from pinecone import Pinecone

from settings import get_settings

settings = get_settings()


class IngestionService:
    def __init__(self):
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

    def ingest(self, file_path: str):
        logger.info(f"Starting ingestion for file: {file_path}")

        # Load PDF
        pdf_loader = PyPDFLoader(file_path)
        loaded_documents: list[Document] = pdf_loader.load()
        logger.info(f"Loaded {len(loaded_documents)} documents")

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n"],
            chunk_size=1000,
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
    ingestion_service.ingest(os.path.abspath("../../../rag_data/omar_elhanafy_cv.pdf"))
