from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from business.agents.portfolio_agent import PortfolioAgent
from business.services.orchestrator_service import OrchestratorService
from config.logger import setup_logging
from config.settings import get_settings
from presentation.middleware.logger import LoggerMiddleware
from presentation.routers import health
from presentation.routers.v1 import ingestion

settings = get_settings()

# Initialize the portfolio agent and orchestrator service
portfolio_agent = PortfolioAgent()
orchestrator_service = OrchestratorService(portfolio_agent)
stream = orchestrator_service.create_stream()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggerMiddleware)

# Mount the FastRTC stream on the app
stream.mount(app)

# V1 APIs
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(ingestion.router, prefix="/api/v1", tags=["Ingestion"])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=settings.APP_PORT)
