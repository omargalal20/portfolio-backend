from dotenv import load_dotenv

from agent import voice_agent
from logger import setup_logging

load_dotenv()
setup_logging()

if __name__ == "__main__":
    agent = voice_agent()
    agent.ui.launch()
