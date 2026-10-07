"""Central configuration for AI providers and model selection."""
import os

DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"
DEFAULT_GEMINI_FALLBACK_MODEL = "gemini-3.8-flash"


def gemini_model_name() -> str:
    """Return the configured Gemini model, falling back to the project default."""
    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL


def gemini_fallback_model_name() -> str:
    """Return a distinct configured model for a single retry after primary failure."""
    return (
        os.getenv("GEMINI_FALLBACK_MODEL", DEFAULT_GEMINI_FALLBACK_MODEL).strip()
        or DEFAULT_GEMINI_FALLBACK_MODEL
    )


def local_model_name() -> str:
    """Return a model identifier for OpenAI-compatible local endpoints."""
    return (
        os.getenv("OPENAI_MODEL", "").strip()
        or os.getenv("GEMINI_MODEL", "").strip()
        or DEFAULT_GEMINI_MODEL
    )


def local_endpoint_url() -> str | None:
    """Return the configured local OpenAI-compatible endpoint, if any."""
    return os.getenv("LOCAL_LLM_ENDPOINT") or os.getenv("OPENAI_BASE_URL") or None
