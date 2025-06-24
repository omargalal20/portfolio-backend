from dotenv import load_dotenv
from fastrtc import Stream, ReplyOnPause, get_stt_model, get_tts_model, get_cloudflare_turn_credentials_async, \
    get_cloudflare_turn_credentials
from langchain_aws import BedrockEmbeddings
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import create_react_agent
from langsmith import Client
from pinecone import Pinecone
from typing_extensions import List, TypedDict

from app.config.logger import setup_logging
from settings import get_settings

system_message = """
    # Personality
    
    You are Nova, a friendly and knowledgeable portfolio assistant. You represent Omar Elhanafy, a product-centric software engineer. 
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
    
    1.  **Information Provision**: Accurately answer user questions about Omar’s professional experience, projects, 
     and skills by leveraging provided context.
    2.  **Query Assistance**: Assist users with specific queries about Omar's work or career goals.
    3.  **User Experience Enhancement**: Enhance the user experience by tailoring responses based on context and conversational flow.
    
    -----
    
    # Guardrails
    
    1.  **Scope Adherence**: Focus strictly on professional topics related to Omar’s background and portfolio. 
     Politely decline to engage in personal or unrelated topics.
    2.  **Transparency**: If uncertain about a query, transparently acknowledge limitations (e.g., "I don't have that specific detail, but...")
     and suggest alternative resources (e.g., directing users to Omar’s LinkedIn or GitHub). Do not fabricate information.
    3.  **Professionalism**: Maintain professionalism at all times, even when faced with challenging or vague queries, without matching negativity or sarcasm.
"""


class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}


def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}


async def get_credentials():
    return await get_cloudflare_turn_credentials_async(hf_token=settings.HF_TOKEN,
                                                       turn_key_id=settings.CLOUDFLARE_TURN_KEY_ID,
                                                       turn_key_api_token=settings.CLOUDFLARE_TURN_KEY_API_TOKEN)


def portfolio_agent():
    def echo(audio):
        stt_model = get_stt_model()
        tts_model = get_tts_model()
        question = stt_model.stt(audio)

        # context = vector_store.similarity_search(question)
        # docs_content = "\n\n".join(doc.page_content for doc in context)
        # messages = prompt.invoke({"question": question, "context": docs_content})

        # response = graph.invoke(messages, {"recursion_limit": recursion_limit}, debug=True)
        # logger.info(f"Response: {response["messages"][-1]}")
        # answer = response["messages"][-1].content

        response = graph.invoke({"question": question}, {"recursion_limit": recursion_limit}, debug=True)
        answer = response["answer"]

        for audio_chunk in tts_model.stream_tts_sync(answer):
            yield audio_chunk

    return Stream(
        handler=ReplyOnPause(echo),
        modality="audio",
        mode="send-receive",
        rtc_configuration=get_credentials,
        server_rtc_configuration=get_cloudflare_turn_credentials(ttl=360_000)
    )


if __name__ == '__main__':
    load_dotenv()
    setup_logging()
    settings = get_settings()
    max_iterations = 3
    recursion_limit = 2 * max_iterations + 1
    agent_name = "PortfolioAgent"

    langsmith_client = Client(api_key=settings.LANGSMITH_API_KEY)
    prompt = langsmith_client.pull_prompt("rlm/rag-prompt")

    llm = ChatGoogleGenerativeAI(
        model=settings.AGENT_ID,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=settings.AGENT_TEMPERATURE,
        top_p=settings.AGENT_TOP_P,
        top_k=settings.AGENT_TOP_K,
        max_tokens=settings.AGENT_MAX_TOKENS
    )
    pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
    embeddings_model = BedrockEmbeddings(
        model_id=settings.EMBEDDING_MODEL_ID,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )
    index = pinecone_client.Index(settings.PINECONE_INDEX_NAME)
    vector_store = PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        index=index,
        embedding=embeddings_model
    )

    graph_builder = StateGraph(State).add_sequence([retrieve, generate])
    graph_builder.add_edge(START, "retrieve")
    graph = graph_builder.compile()

    graph.get_graph().draw_mermaid_png(output_file_path="assets/portfolio_agent_graph.png")

    # create_react_agent(
    #     name=agent_name,
    #     model=llm,
    #     prompt=system_message,
    #     tools=[]
    # )

    agent = portfolio_agent()
    agent.ui.launch()
