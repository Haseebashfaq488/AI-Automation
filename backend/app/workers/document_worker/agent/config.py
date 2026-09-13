import os
from typing import Optional

from app.core.config import settings

# The worker agent speaks the OpenAI chat API. Groq exposes the same schema
# and its free tier is far faster than free OpenRouter, so Groq is the
# default provider; OpenRouter (or anything else) works by overriding
# WORKER_LLM_BASE_URL + WORKER_LLM_API_KEY + WORKER_MODEL.

DEFAULT_WORKER_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_WORKER_MODEL = "openai/gpt-oss-120b"


def get_worker_base_url() -> str:
    return (
        os.getenv("WORKER_LLM_BASE_URL")
        or settings.WORKER_LLM_BASE_URL
        or DEFAULT_WORKER_BASE_URL
    )


def get_worker_api_key() -> Optional[str]:
    """Worker LLM key (empty/None → placeholder mode)."""
    return (
        os.getenv("WORKER_LLM_API_KEY")
        or settings.WORKER_LLM_API_KEY
        or settings.GROQ_API_KEY
        or os.getenv("OPENROUTER_API_KEY")
        or settings.OPENROUTER_API_KEY
        or None
    )


def get_worker_model() -> str:
    return (
        os.getenv("WORKER_MODEL")
        or settings.WORKER_MODEL
        or getattr(settings, "GROQ_MODEL", None)
        or DEFAULT_WORKER_MODEL
    )
