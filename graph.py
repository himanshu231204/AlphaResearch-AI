"""LangGraph Server entry point.

This module exports the compiled research graph for use by the LangGraph
Agent Server (langgraph dev). The Agent Chat UI connects to this server.

The LangGraph API server handles persistence automatically, so this
graph is compiled WITHOUT custom checkpointer or store.

Usage:
    langgraph dev          # starts Agent Server on http://localhost:2024
    Agent Chat UI          # connects to http://localhost:2024
"""

import os
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LangSmith tracing — set env vars programmatically so LangChain/LangGraph
# actually picks them up. The pydantic-settings config stores the values,
# but LangChain reads from os.environ directly.
# ---------------------------------------------------------------------------

if settings.langsmith_api_key:
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key)
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)
    logger.info(
        "LangSmith tracing enabled — project: %s", settings.langsmith_project
    )
elif settings.langsmith_tracing:
    # Tracing enabled but no API key — log a warning
    logger.warning(
        "LANGCHAIN_TRACING_V2 is enabled in config but no LANGSMITH_API_KEY found. "
        "Set LANGSMITH_API_KEY in .env to enable tracing."
    )

from agents.supervisor import build_graph  # noqa: E402

# LangGraph API server handles persistence — use_platform_persistence=True
graph = build_graph(use_platform_persistence=True)
