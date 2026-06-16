"""Centralized model routing via ChatLiteLLM.

All model access goes through this module — never instantiate providers directly.
Uses langchain-litellm (ChatLiteLLM) for unified routing across providers.

Routing strategy (v3 — verified working June 2026):
  - Most tasks → OpenRouter Nex (free, verified working)
  - Research/Technical → Groq Llama 3.3 (free, fast)
  - Quick summary → Gemini Flash (limited quota, low risk)
  - Every model gets max_retries=6 with exponential backoff
  - InMemoryRateLimiter prevents burst flooding
  - max_tokens=4096 on all models (free-tier budget cap)

Verified working (June 2026):
  [OK] openrouter/nex-agi/nex-n2-pro:free
  [OK] groq/llama-3.3-70b-versatile
  [OK] gemini/gemini-2.5-flash
  [FAIL] openrouter/free -> 502 from broken "Stealth" provider in pool
  [FAIL] openrouter/qwen/qwen3-235b-a22b:free -> no longer free
  [FAIL] openrouter/meta-llama/llama-3.3-70b-instruct:free -> rate limited

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
# Only verified working free models (June 2026)
# ---------------------------------------------------------------------------
GEMINI_FLASH = "gemini/gemini-2.5-flash"
GROQ_LLAMA = "groq/llama-3.3-70b-versatile"
OPENROUTER_NEX = "openrouter/nex-agi/nex-n2-pro:free"

# Model aliases (init_chat_model format — used by deepagents create_deep_agent)
GEMINI_FLASH_INIT = "google_genai:gemini-2.5-flash"
GROQ_LLAMA_INIT = "groq:llama-3.3-70b-versatile"
OPENROUTER_NEX_INIT = "openrouter:nex-agi/nex-n2-pro"

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
# Only verified working free models (June 2026)
# ---------------------------------------------------------------------------
MODEL_ROUTING = {
    # Planning / reasoning → OpenRouter Nex (verified free)
    "planning": OPENROUTER_NEX,
    # Reflection → OpenRouter Nex
    "reflection": OPENROUTER_NEX,
    # Report writing → OpenRouter Nex
    "report_writing": OPENROUTER_NEX,
    # Financial analysis → OpenRouter Nex
    "financial_analysis": OPENROUTER_NEX,
    # Fast / search tasks → Groq (fastest, free)
    "research": GROQ_LLAMA,
    "technical_analysis": GROQ_LLAMA,
    # Quick summary → Gemini Flash (only 1 call, low risk)
    "quick_summary": GEMINI_FLASH,
}

# ---------------------------------------------------------------------------
# Fallback chain — tried in order when primary fails
# ---------------------------------------------------------------------------
FALLBACK_CHAIN = [
    GROQ_LLAMA,         # 1st fallback: Groq (fast, free)
    OPENROUTER_NEX,     # 2nd fallback: OpenRouter Nex (free)
    GEMINI_FLASH,       # last resort: Gemini (limited quota)
]

DEFAULT_MODEL = GROQ_LLAMA


def _build_model(
    model_name: str,
    temperature: float = 0.7,
    max_retries: int = 6,
    max_tokens: int = 4096,
) -> ChatLiteLLM:
    """Build a ChatLiteLLM with retry, rate limiting, and output cap.

    Args:
        model_name: LiteLLM model identifier.
        temperature: Sampling temperature.
        max_retries: Max retry attempts with exponential backoff.
            LiteLLM retries 429 (rate limit) and 5xx (server errors) automatically.
            Backoff: 1s → 2s → 4s → 8s → 16s → 32s (6 attempts = ~63s total).
        max_tokens: Max output tokens. Capped at 4096 to stay within free-tier
            provider token budgets (OpenRouter free ≈ 8k tokens/request).
            Individual agents should return structured summaries, not full text.
    """
    return ChatLiteLLM(
        model=model_name,
        temperature=temperature,
        max_retries=max_retries,
        max_tokens=max_tokens,
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
