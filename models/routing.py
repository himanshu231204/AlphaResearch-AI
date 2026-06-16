"""Centralized model routing via ChatLiteLLM.

All model access goes through this module — never instantiate providers directly.
Uses langchain-litellm (ChatLiteLLM) for unified routing across providers.

Model string format (LiteLLM convention):
  provider/model-name  (e.g., "groq/llama-3.3-70b-versatile")

Default: Groq Llama 3.3 70B (free, fast, no vendor lock-in)
See: https://docs.langchain.com/oss/python/integrations/chat/litellm
"""

from langchain_litellm import ChatLiteLLM

# Task → model mapping (all tasks use free Groq Llama 3.3 70B)
DEFAULT_MODEL = "groq/llama-3.3-70b-versatile"

MODEL_ROUTING = {
    "planning": DEFAULT_MODEL,
    "research": DEFAULT_MODEL,
    "financial_analysis": DEFAULT_MODEL,
    "technical_analysis": DEFAULT_MODEL,
    "reflection": DEFAULT_MODEL,
    "report_writing": DEFAULT_MODEL,
    "quick_summary": DEFAULT_MODEL,
}


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
