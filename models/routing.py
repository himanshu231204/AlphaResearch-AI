"""Centralized model routing via ChatLiteLLM.

All model access goes through this module — never instantiate providers directly.
Uses langchain-litellm (ChatLiteLLM) for unified routing across providers.

Model string format (LiteLLM convention):
  provider/model-name  (e.g., "gemini/gemini-2.5-pro")

See: https://docs.langchain.com/oss/python/integrations/chat/litellm
"""

from langchain_litellm import ChatLiteLLM

# Task → model mapping per AGENTS.md
MODEL_ROUTING = {
    "planning": "gemini/gemini-2.5-pro",
    "research": "xai/grok-3",
    "financial_analysis": "gemini/gemini-2.5-pro",
    "technical_analysis": "xai/grok-3",
    "reflection": "gemini/gemini-2.5-pro",
    "report_writing": "gemini/gemini-2.5-pro",
    "quick_summary": "gemini/gemini-2.0-flash",
}

DEFAULT_MODEL = "gemini/gemini-2.5-pro"


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
