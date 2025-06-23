from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.business.agents.portfolio_agent import portfolio_agent
from app.config.logger import setup_logging
from app.presentation.middleware.logger import LoggerMiddleware
from app.presentation.routers import health
from app.presentation.routers.v1 import ingestion
from settings import get_settings

settings = get_settings()
agent = portfolio_agent()


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

agent.mount(app)

# V1 APIs
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(ingestion.router, prefix="/api/v1", tags=["Ingestion"])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=settings.APP_PORT)
