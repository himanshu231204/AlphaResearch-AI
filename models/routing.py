"""Centralized model routing via ChatLiteLLM.

All model access goes through this module — never instantiate providers directly.
Uses langchain-litellm (ChatLiteLLM) for unified routing across providers.

Routing strategy:
  - Logical/reasoning tasks → Gemini 2.5 Flash
  - Financial analysis → OpenRouter Nex N2 Pro (free)
  - Fast/search tasks → Groq Llama 3.3 70B
  - Universal fallback → OpenRouter free model → Gemini Flash

See: https://docs.langchain.com/oss/python/integrations/chat/litellm
"""

import logging

from langchain_litellm import ChatLiteLLM

logger = logging.getLogger(__name__)

# Model aliases (litellm format — used by ChatLiteLLM)
GEMINI_FLASH = "gemini/gemini-2.5-flash"
GROQ_LLAMA = "groq/llama-3.3-70b-versatile"
OPENROUTER_NEX = "openrouter/nex-agi/nex-n2-pro:free"
OPENROUTER_FREE = "openrouter/meta-llama/llama-3.3-70b-instruct:free"

# Model aliases (init_chat_model format — used by deepagents create_deep_agent)
GEMINI_FLASH_INIT = "google_genai:gemini-2.5-flash"
GROQ_LLAMA_INIT = "groq:llama-3.3-70b-versatile"
OPENROUTER_NEX_INIT = "openrouter:nex-agi/nex-n2-pro"
OPENROUTER_FREE_INIT = "openrouter:meta-llama/llama-3.3-70b-instruct"

# Task → model mapping (primary models)
MODEL_ROUTING = {
    # Logical / reasoning tasks → Gemini Flash
    "planning": GEMINI_FLASH,
    "reflection": GEMINI_FLASH,
    "report_writing": GEMINI_FLASH,
    # Financial analysis → OpenRouter Nex (free)
    "financial_analysis": OPENROUTER_NEX,
    # Fast / search tasks → OpenRouter Free (avoiding Groq rate limits)
    "research": OPENROUTER_FREE,
    "technical_analysis": OPENROUTER_FREE,
    "quick_summary": OPENROUTER_FREE,
}

# Fallback chain: OpenRouter Free → Gemini Flash
FALLBACK_MODELS = [OPENROUTER_FREE, GEMINI_FLASH]
DEFAULT_MODEL = GEMINI_FLASH


def get_model(task: str = "planning", temperature: float = 0.7) -> ChatLiteLLM:
    """Get a ChatLiteLLM model instance for the specified task.

    Args:
        task: The task type — determines which model to route to.
        temperature: Model temperature (0.0 = deterministic, 1.0 = creative).

    Returns:
        Configured ChatLiteLLM instance ready for .invoke() or .pipe().
    """
    model_name = MODEL_ROUTING.get(task, DEFAULT_MODEL)

    return ChatLiteLLM(
        model=model_name,
        temperature=temperature,
    )


def get_model_with_fallback(task: str = "planning", temperature: float = 0.7) -> ChatLiteLLM:
    """Get model with automatic fallback chain for reliability.

    Fallback chain: Primary → OpenRouter Free → Gemini Flash
    """
    primary_name = MODEL_ROUTING.get(task, DEFAULT_MODEL)

    # Try primary model
    try:
        return ChatLiteLLM(model=primary_name, temperature=temperature)
    except Exception as e:
        logger.warning("Primary model %s failed for '%s': %s", primary_name, task, e)

    # Try fallback chain
    for fallback_name in FALLBACK_MODELS:
        try:
            logger.info("Trying fallback model %s for task '%s'", fallback_name, task)
            return ChatLiteLLM(model=fallback_name, temperature=temperature)
        except Exception as e:
            logger.warning("Fallback model %s also failed for '%s': %s", fallback_name, task, e)

    # Last resort
    logger.error("All models failed for task '%s', using Gemini Flash", task)
    return ChatLiteLLM(model=GEMINI_FLASH, temperature=temperature)
