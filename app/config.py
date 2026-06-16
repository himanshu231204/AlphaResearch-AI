"""AlphaResearch AI — Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Model provider keys
    gemini_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    xai_api_key: str = ""

    # Financial data APIs
    finnhub_api_key: str = ""
    alpha_vantage_api_key: str = ""

    # Search APIs
    tavily_api_key: str = ""
    google_search_api_key: str = ""
    google_search_cx: str = ""
    brave_search_api_key: str = ""

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_tracing: bool = True
    langsmith_project: str = "alpha-research-ai"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
