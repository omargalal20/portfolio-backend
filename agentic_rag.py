from dotenv import load_dotenv
from fastrtc import Stream, ReplyOnPause, get_stt_model, get_tts_model, get_cloudflare_turn_credentials_async, \
    get_cloudflare_turn_credentials
from langchain_aws import BedrockEmbeddings
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langgraph.graph import START, StateGraph
from langsmith import Client
from pinecone import Pinecone
from typing_extensions import List, TypedDict

from app.config.logger import setup_logging
from settings import get_settings


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

    agent = portfolio_agent()
    agent.ui.launch()
