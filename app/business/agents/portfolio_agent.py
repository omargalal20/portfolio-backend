from dotenv import load_dotenv
from fastrtc import Stream, ReplyOnPause, get_stt_model, get_tts_model, get_cloudflare_turn_credentials_async, \
    get_cloudflare_turn_credentials
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from app.config.logger import setup_logging
from settings import get_settings

load_dotenv()
setup_logging()
settings = get_settings()


async def get_credentials():
    return await get_cloudflare_turn_credentials_async(hf_token=settings.HF_TOKEN,
                                                       turn_key_id=settings.CLOUDFLARE_TURN_KEY_ID,
                                                       turn_key_api_token=settings.CLOUDFLARE_TURN_KEY_API_TOKEN)


def portfolio_agent():
    model = ChatGoogleGenerativeAI(
        model=settings.AGENT_ID,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=settings.AGENT_TEMPERATURE,
        top_p=settings.AGENT_TOP_P,
        top_k=settings.AGENT_TOP_K,
        max_tokens=settings.AGENT_MAX_TOKENS
    )

    system_message = """
        You are helpful assistant. 
    """

    agent = create_react_agent(
        name="Portfolio Agent",
        model=model,
        prompt=system_message,
        tools=[]
    )

    def echo(audio):
        stt_model = get_stt_model()
        tts_model = get_tts_model()
        prompt = stt_model.stt(audio)
        max_iterations = 3
        recursion_limit = 2 * max_iterations + 1

        response = agent.invoke({"messages": prompt}, {"recursion_limit": recursion_limit})

        prompt = response["messages"][-1].content
        for audio_chunk in tts_model.stream_tts_sync(prompt):
            yield audio_chunk

    return Stream(
        handler=ReplyOnPause(echo),
        modality="audio",
        mode="send-receive",
        rtc_configuration=get_credentials,
        server_rtc_configuration=get_cloudflare_turn_credentials(ttl=360_000)
    )


if __name__ == "__main__":
    agent = portfolio_agent()
    agent.ui.launch()
