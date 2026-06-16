"""Centralized model routing via ChatLiteLLM.

All model access goes through this module — never instantiate providers directly.
Uses langchain-litellm (ChatLiteLLM) for unified routing across providers.

Routing strategy:
  - Logical/reasoning tasks → Gemini 2.5 Flash (strong reasoning, free tier)
  - Financial analysis → OpenRouter Nex N2 Pro (free) with Gemini Flash fallback
  - Fast/search tasks → Groq Llama 3.3 70B (fast, free)

See: https://docs.langchain.com/oss/python/integrations/chat/litellm
"""

import logging

from langchain_litellm import ChatLiteLLM

logger = logging.getLogger(__name__)

# Model aliases
GEMINI_FLASH = "gemini/gemini-2.5-flash"
GROQ_LLAMA = "groq/llama-3.3-70b-versatile"
OPENROUTER_NEX = "openrouter/nex-agi/nex-n2-pro:free"

# Task → model mapping
MODEL_ROUTING = {
    # Logical / reasoning tasks → Gemini Flash
    "planning": GEMINI_FLASH,
    "reflection": GEMINI_FLASH,
    "report_writing": GEMINI_FLASH,
    # Financial analysis → OpenRouter Nex (free) with Gemini Flash fallback
    "financial_analysis": OPENROUTER_NEX,
    # Fast / search tasks → Groq Llama
    "research": GROQ_LLAMA,
    "technical_analysis": GROQ_LLAMA,
    "quick_summary": GROQ_LLAMA,
}

# Fallback model when primary fails
FALLBACK_MODEL = GEMINI_FLASH
DEFAULT_MODEL = GEMINI_FLASH


def get_model(task: str = "planning", temperature: float = 0.7) -> ChatLiteLLM:
    """Get a ChatLiteLLM model instance for the specified task.

    If the primary model fails to initialize, falls back to Gemini Flash.

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
    """Get model with automatic fallback to Gemini Flash on failure.

    Use this for critical tasks like financial analysis where the primary
    model (OpenRouter) may have intermittent availability.
    """
    primary_name = MODEL_ROUTING.get(task, DEFAULT_MODEL)

    try:
        model = ChatLiteLLM(model=primary_name, temperature=temperature)
        return model
    except Exception as e:
        logger.warning("Primary model %s failed for task '%s': %s — falling back to %s",
                       primary_name, task, e, FALLBACK_MODEL)
        return ChatLiteLLM(model=FALLBACK_MODEL, temperature=temperature)
