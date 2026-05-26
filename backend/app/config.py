from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Anthropic API
    ANTHROPIC_API_KEY: str

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/creative_storytelling.db"

    # RAG
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # LLM Models
    HAIKU_MODEL: str = "claude-haiku-4-5-20251001"
    SONNET_MODEL: str = "claude-sonnet-4-6"

    # Agent Worker
    AGENT_POLL_INTERVAL_SECONDS: float = 3.0
    AGENT_MAX_CONCURRENT_TASKS: int = 2

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra env vars like NEXT_PUBLIC_*


@lru_cache()
def get_settings() -> Settings:
    return Settings()
