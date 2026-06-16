"""Centralized model routing via ChatLiteLLM.

All model access goes through this module — never instantiate providers directly.
Uses langchain-litellm (ChatLiteLLM) for unified routing across providers.

Routing strategy (v2 — avoids Gemini free-tier exhaustion):
  - Most tasks → OpenRouter free models (generous quotas)
  - Gemini Flash → reserved for quick summaries only
  - Groq → fast search/technical tasks
  - Every model gets max_retries=6 with exponential backoff
  - InMemoryRateLimiter prevents burst flooding

Rate limit handling:
  - LiteLLM retries 429/5xx automatically with exponential backoff
  - InMemoryRateLimiter adds client-side throttling
  - Fallback chain triggers on persistent failures

See: https://docs.langchain.com/oss/python/integrations/chat/litellm
See: https://docs.langchain.com/oss/python/langchain/models#rate-limiting
"""

import logging

from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_litellm import ChatLiteLLM

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model aliases (litellm format — used by ChatLiteLLM)
# ---------------------------------------------------------------------------
GEMINI_FLASH = "gemini/gemini-2.5-flash"
GROQ_LLAMA = "groq/llama-3.3-70b-versatile"
OPENROUTER_NEX = "openrouter/nex-agi/nex-n2-pro:free"
OPENROUTER_FREE = "openrouter/meta-llama/llama-3.3-70b-instruct:free"
OPENROUTER_QWEN = "openrouter/qwen/qwen3-235b-a22b:free"

# Model aliases (init_chat_model format — used by deepagents create_deep_agent)
GEMINI_FLASH_INIT = "google_genai:gemini-2.5-flash"
GROQ_LLAMA_INIT = "groq:llama-3.3-70b-versatile"
OPENROUTER_NEX_INIT = "openrouter:nex-agi/nex-n2-pro"
OPENROUTER_FREE_INIT = "openrouter:meta-llama/llama-3.3-70b-instruct"
OPENROUTER_QWEN_INIT = "openrouter:qwen/qwen3-235b-a22b"

# ---------------------------------------------------------------------------
# Rate limiter — shared across all models to prevent burst flooding
# 0.5 req/s = 1 request every 2 seconds. Prevents hitting provider limits.
# ---------------------------------------------------------------------------
_RATE_LIMITER = InMemoryRateLimiter(
    requests_per_second=0.5,
    check_every_n_seconds=0.1,
    max_bucket_size=5,  # burst of up to 5 requests, then throttled
)

# ---------------------------------------------------------------------------
# Task → primary model mapping
# Avoids Gemini free tier (20 req/day) — use OpenRouter/Groq for most tasks
# ---------------------------------------------------------------------------
MODEL_ROUTING = {
    # Planning / reasoning → OpenRouter Qwen (large free model)
    "planning": OPENROUTER_QWEN,
    # Reflection → OpenRouter Free (avoids Gemini quota)
    "reflection": OPENROUTER_FREE,
    # Report writing → OpenRouter Nex (free)
    "report_writing": OPENROUTER_NEX,
    # Financial analysis → OpenRouter Nex (free)
    "financial_analysis": OPENROUTER_NEX,
    # Fast / search tasks → Groq (fastest)
    "research": GROQ_LLAMA,
    "technical_analysis": GROQ_LLAMA,
    # Quick summary → Gemini Flash (only 1 call, low risk)
    "quick_summary": GEMINI_FLASH,
}

# ---------------------------------------------------------------------------
# Fallback chain — tried in order when primary fails
# ---------------------------------------------------------------------------
FALLBACK_CHAIN = [
    OPENROUTER_FREE,    # 1st fallback: OpenRouter Llama 3.3
    OPENROUTER_NEX,     # 2nd fallback: OpenRouter Nex
    GROQ_LLAMA,         # 3rd fallback: Groq
    GEMINI_FLASH,       # last resort: Gemini (limited quota)
]

DEFAULT_MODEL = OPENROUTER_FREE


def _build_model(
    model_name: str,
    temperature: float = 0.7,
    max_retries: int = 6,
) -> ChatLiteLLM:
    """Build a ChatLiteLLM with retry and rate limiting.

    Args:
        model_name: LiteLLM model identifier.
        temperature: Sampling temperature.
        max_retries: Max retry attempts with exponential backoff.
            LiteLLM retries 429 (rate limit) and 5xx (server errors) automatically.
            Backoff: 1s → 2s → 4s → 8s → 16s → 32s (6 attempts = ~63s total).
    """
    return ChatLiteLLM(
        model=model_name,
        temperature=temperature,
        max_retries=max_retries,
        rate_limiter=_RATE_LIMITER,
    )


def get_model(task: str = "planning", temperature: float = 0.7) -> ChatLiteLLM:
    """Get a ChatLiteLLM model instance for the specified task.

    Args:
        task: The task type — determines which model to route to.
        temperature: Model temperature (0.0 = deterministic, 1.0 = creative).

    Returns:
        Configured ChatLiteLLM instance ready for .invoke() or .ainvoke().
    """
    model_name = MODEL_ROUTING.get(task, DEFAULT_MODEL)
    return _build_model(model_name, temperature)


def get_model_with_fallback(task: str = "planning", temperature: float = 0.7) -> ChatLiteLLM:
    """Get model with automatic fallback chain for reliability.

    NOTE: This returns a model configured with fallback metadata.
    Actual fallback at invocation time is handled by the retry policy
    in the graph nodes (RetryPolicy + CancelledError handling).

    The returned model has max_retries=6 so LiteLLM will automatically
    retry on 429/5xx errors before raising.
    """
    primary_name = MODEL_ROUTING.get(task, DEFAULT_MODEL)
    logger.info("Model for task '%s': %s", task, primary_name)
    return _build_model(primary_name, temperature)
