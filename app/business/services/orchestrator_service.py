from dotenv import load_dotenv
from fastrtc import Stream, ReplyOnPause, get_stt_model, get_tts_model, get_cloudflare_turn_credentials, \
    get_cloudflare_turn_credentials_async
from loguru import logger

from business.agents.portfolio_agent import PortfolioAgent
from config.settings import get_settings

settings = get_settings()
load_dotenv()


class OrchestratorService:
    def __init__(self, portfolio_agent: PortfolioAgent):
        self.portfolio_agent = portfolio_agent

    @staticmethod
    async def get_credentials():
        return await get_cloudflare_turn_credentials_async(
            hf_token=settings.HF_TOKEN,
            turn_key_id=settings.TURN_KEY_ID,
            turn_key_api_token=settings.TURN_KEY_API_TOKEN
        )

    def create_stream(self) -> Stream:
        """Create and return the FastRTC stream with the echo method."""

        def echo(audio):
            """Echo method that processes audio input and returns audio response."""
            try:
                stt_model = get_stt_model()
                tts_model = get_tts_model()

                # Convert speech to text
                question = stt_model.stt(audio)
                logger.info(f"Received question: {question}")

                # Generate response using the portfolio agent
                answer = self.portfolio_agent.generate_response(question)
                logger.info(f"Generated answer: {answer}")

                # Convert text to speech and stream audio chunks
                for audio_chunk in tts_model.stream_tts_sync(answer):
                    yield audio_chunk

            except Exception as e:
                logger.error(f"Error in echo method: {e}")
                # Return a fallback response
                fallback_text = "I apologize, but I'm having trouble processing your request right now. Please try again."
                tts_model = get_tts_model()
                for audio_chunk in tts_model.stream_tts_sync(fallback_text):
                    yield audio_chunk

        return Stream(
            handler=ReplyOnPause(echo),
            modality="audio",
            mode="send-receive",
            rtc_configuration=self.get_credentials,
            server_rtc_configuration=get_cloudflare_turn_credentials(ttl=360_000)
        )
