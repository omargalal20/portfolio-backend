import os
from functools import lru_cache
from typing import Sequence

from pydantic import field_validator
from pydantic_settings import BaseSettings


@lru_cache
def get_env_filename():
    runtime_env = os.getenv("ENV")
    return f".env.{runtime_env}" if runtime_env else ".env"


class Settings(BaseSettings):
    ENVIRONMENT: str

    APP_NAME: str
    APP_VERSION: str
    APP_PORT: int
    APP_SECRET_MESSAGE: str
    APP_SECRET_KEY: str

    AGENT_ID: str
    AGENT_TEMPERATURE: float
    AGENT_MAX_TOKENS: int
    AGENT_TOP_P: float
    AGENT_TOP_K: int

    GOOGLE_API_KEY: str

    CORS_ORIGINS: Sequence[str]

    LANGSMITH_TRACING: bool
    LANGSMITH_ENDPOINT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str

    CLOUDFLARE_TURN_KEY_ID: str
    CLOUDFLARE_TURN_KEY_API_TOKEN: str
    CLOUDFLARE_API_KEY: str

    HF_TOKEN: str

    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str

    EMBEDDING_MODEL_ID: str

    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_STORAGE_BUCKET_NAME: str

    class Config:
        env_file = get_env_filename()
        env_file_encoding = "utf-8"

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value


@lru_cache
def get_settings():
    return Settings()
