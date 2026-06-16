"""Centralized model routing via ChatLiteLLM.

All model access goes through this module — never instantiate providers directly.
Uses langchain-litellm (ChatLiteLLM) for unified routing across providers.

Routing strategy:
  - Logical/reasoning tasks → Gemini 2.5 Flash (strong reasoning, free tier)
  - Fast/search tasks → Groq Llama 3.3 70B (fast, free)

See: https://docs.langchain.com/oss/python/integrations/chat/litellm
"""

from langchain_litellm import ChatLiteLLM

# Model aliases
GEMINI_FLASH = "gemini/gemini-2.5-flash"
GROQ_LLAMA = "groq/llama-3.3-70b-versatile"

# Task → model mapping
MODEL_ROUTING = {
    # Logical / reasoning tasks → Gemini Flash
    "planning": GEMINI_FLASH,
    "reflection": GEMINI_FLASH,
    "report_writing": GEMINI_FLASH,
    "financial_analysis": GEMINI_FLASH,
    # Fast / search tasks → Groq Llama
    "research": GROQ_LLAMA,
    "technical_analysis": GROQ_LLAMA,
    "quick_summary": GROQ_LLAMA,
}

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


def get_model_name(task: str = "planning") -> str:
    """Get the model name string for a given task (useful for logging)."""
    return MODEL_ROUTING.get(task, DEFAULT_MODEL)
