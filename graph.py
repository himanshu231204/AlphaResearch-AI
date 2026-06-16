"""LangGraph Server entry point.

This module exports the compiled research graph for use by the LangGraph
Agent Server (langgraph dev). The Agent Chat UI connects to this server.

The LangGraph API server handles persistence automatically, so this
graph is compiled WITHOUT custom checkpointer or store.

Usage:
    langgraph dev          # starts Agent Server on http://localhost:2024
    Agent Chat UI          # connects to http://localhost:2024
"""

from agents.supervisor import build_graph  # noqa: F401

# LangGraph API server handles persistence — use_platform_persistence=True
graph = build_graph(use_platform_persistence=True)
