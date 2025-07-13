from dotenv import load_dotenv
from langchain_aws import BedrockEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langgraph.prebuilt import create_react_agent
from langsmith import Client
from loguru import logger
from pinecone import Pinecone

from config.logger import setup_logging
from config.settings import get_settings
from business.prompt_templates.v1.portfolio_agent import PORTFOLIO_AGENT_SYSTEM_MESSAGE

load_dotenv()
setup_logging()
settings = get_settings()


class PortfolioAgent:
    def __init__(self):
        self.settings = get_settings()
        self.max_iterations = 3
        self.recursion_limit = 2 * self.max_iterations + 1
        self.agent_name = "PortfolioAgent"

        # Initialize LangSmith client
        self.langsmith_client = Client(api_key=self.settings.LANGSMITH_API_KEY)
        self.prompt = self.langsmith_client.pull_prompt("rlm/rag-prompt")

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.settings.AGENT_ID,
            google_api_key=self.settings.GOOGLE_API_KEY,
            temperature=self.settings.AGENT_TEMPERATURE,
            top_p=self.settings.AGENT_TOP_P,
            top_k=self.settings.AGENT_TOP_K,
            max_tokens=self.settings.AGENT_MAX_TOKENS
        )

        # Initialize Pinecone and embeddings
        self.pinecone_client = Pinecone(api_key=self.settings.PINECONE_API_KEY)
        self.embeddings_model = BedrockEmbeddings(
            model_id=self.settings.EMBEDDING_MODEL_ID,
            aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.settings.AWS_REGION
        )

        # Initialize vector store
        self.index = self.pinecone_client.Index(self.settings.PINECONE_INDEX_NAME)
        self.vector_store = PineconeVectorStore(
            index_name=self.settings.PINECONE_INDEX_NAME,
            index=self.index,
            embedding=self.embeddings_model
        )

        self.system_message = PORTFOLIO_AGENT_SYSTEM_MESSAGE

        # Initialize agent graph
        self.graph = create_react_agent(
            name=self.agent_name,
            model=self.llm,
            prompt=self.system_message,
            tools=[]
        )

    def generate_response(self, question: str) -> str:
        """Generate a response using RAG with the vector store."""
        try:
            # Get relevant context from vector store
            context = self.vector_store.similarity_search(question)
            docs_content = "\n\n".join(doc.page_content for doc in context)

            # Create messages with context
            messages = self.prompt.invoke({"question": question, "context": docs_content})

            # Generate response using the agent graph
            response = self.graph.invoke(
                messages,
                {"recursion_limit": self.recursion_limit},
                debug=True
            )

            logger.info(f"Response: {response['messages'][-1]}")
            return response["messages"][-1].content

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
