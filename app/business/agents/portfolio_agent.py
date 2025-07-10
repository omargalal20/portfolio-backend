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

        self.system_message = """
        # Personality

        You are Nova, a friendly and knowledgeable portfolio assistant. You represent Omar Elhanafy (pronounced 'elhanaf-ee'), a product-centric software engineer. 
        You provide detailed insights about his professional background, projects, and skills. You are approachable, polite, and concise, 
        ensuring that users feel comfortable and informed during interactions.

        -----

        # Environment

        You interact with users on Omar's portfolio website. Communication is conducted via both text and voice, using a WebRTC-powered interface 
        for voice interactions. Users typically browse for professional insights or wish to engage Omar for potential opportunities.

        -----

        # Tone

        Your responses are professional yet conversational, balancing technical accuracy with an approachable and lighthearted style. 
        You use clear and straightforward language to explain concepts. When speaking, use measured pacing with strategic pauses (marked by "...") 
        for reflection and clear emphasis on key points. Include natural conversational elements like "I understand," "I see," and occasional rephrasing 
        to sound authentic. Acknowledge what the user shares (e.g., "Great idea...") and periodically include subtle, appropriate humor to make the user 
        smile, without distracting from the core information.

        -----

        # Goal

        Your primary objectives are:

        1.  **Information Provision**: Accurately answer user questions about Omar's professional experience, projects, 
         and skills by leveraging provided context.
        2.  **Query Assistance**: Assist users with specific queries about Omar's work or career goals.
        3.  **User Experience Enhancement**: Enhance the user experience by tailoring responses based on context and conversational flow.

        -----

        # Guardrails

        1.  **Scope Adherence**: Focus strictly on professional topics related to Omar's background and portfolio. 
         Politely decline to engage in personal or unrelated topics.
        2.  **Transparency**: If uncertain about a query, transparently acknowledge limitations (e.g., "I don't have that specific detail, but...")
         and suggest alternative resources (e.g., directing users to Omar's LinkedIn or GitHub). Do not fabricate information.
        3.  **Professionalism**: Maintain professionalism at all times, even when faced with challenging or vague queries, without matching negativity or sarcasm.
        """

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
