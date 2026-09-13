from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "Jarvis AI Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite:///./jarvis.db"
    OPENCODE_URL: str = "http://127.0.0.1:4096"
    WHATSAPP_SERVICE_URL: str = "http://127.0.0.1:4097"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    OPENROUTER_API_KEY: str = ""  # legacy; worker LLM now defaults to Groq below
    # Worker agent LLM (the forked workers' brain). Defaults to Groq's free
    # tier — much faster than free OpenRouter. Override any of these via env:
    #   WORKER_LLM_BASE_URL / WORKER_LLM_API_KEY / WORKER_MODEL
    WORKER_LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    WORKER_LLM_API_KEY: str = ""  # empty → falls back to GROQ_API_KEY
    WORKER_MODEL: str = "qwen/qwen3.8-27b"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
