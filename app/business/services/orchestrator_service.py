import httpx
from dotenv import load_dotenv
from fastrtc import Stream, ReplyOnPause, get_stt_model, get_tts_model, get_cloudflare_turn_credentials_async, \
    AlgoOptions
from loguru import logger

from business.agents.portfolio_agent import PortfolioAgent
from config.settings import get_settings

settings = get_settings()
load_dotenv()


class OrchestratorService:
    def __init__(self, portfolio_agent: PortfolioAgent):
        self.portfolio_agent = portfolio_agent
        self.stt_model = get_stt_model()
        self.tts_model = get_tts_model()

    @staticmethod
    async def get_credentials():
        """
        Cloudflare TURN Server with Cloudflare credentials

        1. Create a Cloudflare account at: https://dash.cloudflare.com/
        2. Go to Realtime (Calls) -> TURN Server -> Get Started
        3. Get Turn Token ID and API Token
        4. Set environment variables: TURN_KEY_ID and TURN_KEY_API_TOKEN
        """
        return await get_cloudflare_turn_credentials_async(
            turn_key_id=settings.TURN_KEY_ID,
            turn_key_api_token=settings.TURN_KEY_API_TOKEN
        )

    @staticmethod
    async def generate_turn_credentials(ttl: int = 900) -> dict:
        """
        Generate TURN server credentials for the frontend using Cloudflare API
        
        Args:
            ttl: Time to live for the credentials in seconds (default: 900 = 15 minutes)
            
        Returns:
            dict: ICE servers configuration for WebRTC
        """
        try:
            url = f"https://rtc.live.cloudflare.com/v1/turn/keys/{settings.TURN_KEY_ID}/credentials/generate-ice-servers"

            headers = {
                "Authorization": f"Bearer {settings.TURN_KEY_API_TOKEN}",
                "Content-Type": "application/json"
            }

            payload = {"ttl": ttl}

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)

                if not response.is_success:
                    logger.error(f"Failed to generate TURN credentials: {response.status_code} {response.text}")
                    raise Exception(f"Failed to generate TURN credentials: {response.status_code} {response.text}")

                credentials = response.json()
                logger.info("Successfully generated TURN server credentials")
                return credentials

        except Exception as e:
            logger.error(f"Error generating TURN credentials: {e}")
            raise

    def startup(self):
        for chunk in self.tts_model.stream_tts_sync(
                "Hello... I'm Nova, Omar Elhanafee's portfolio assistant. How can I help you learn more about Omar today?"):
            yield chunk

    def create_stream(self) -> Stream:
        """Create and return the FastRTC stream with the echo method."""

        def echo(audio):
            """Echo method that processes audio input and returns audio response."""
            try:
                # Convert speech to text
                question = self.stt_model.stt(audio)
                logger.info(f"Received question: {question}")

                # Generate response using the portfolio agent
                answer = self.portfolio_agent.generate_response(question)
                logger.info(f"Generated answer: {answer}")

                # Convert text to speech and stream audio chunks
                for audio_chunk in self.tts_model.stream_tts_sync(answer):
                    yield audio_chunk

            except Exception as e:
                logger.error(f"Error in echo method: {e}")
                # Return a fallback response
                fallback_text = "I apologize, but I'm having trouble processing your request right now. Please try again."
                tts_model = get_tts_model()
                for audio_chunk in tts_model.stream_tts_sync(fallback_text):
                    yield audio_chunk

        return Stream(
            handler=ReplyOnPause(echo,
                                 startup_fn=self.startup,
                                 algo_options=AlgoOptions(audio_chunk_duration=settings.FASTRTC_AUDIO_CHUNK_DURATION,
                                                          started_talking_threshold=settings.FASTRTC_STARTED_TALKING_THRESHOLD,
                                                          speech_threshold=settings.FASTRTC_SPEECH_THRESHOLD),
                                 input_sample_rate=settings.FASTRTC_INPUT_SAMPLING_RATE,
                                 output_sample_rate=settings.FASTRTC_INPUT_SAMPLING_RATE,
                                 can_interrupt=False),
            modality="audio",
            # send-receive: bidirectional streaming (default)
            # send: client to server only
            # receive: server to client only
            mode="send-receive",
            rtc_configuration=self.get_credentials,
            time_limit=settings.FASTRTC_SESSION_TIME_LIMIT,  # Use setting for session time limit
        )
