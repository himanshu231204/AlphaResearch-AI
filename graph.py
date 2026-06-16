"""LangGraph Server entry point.

This module exports the compiled research graph for use by the LangGraph
Agent Server (langgraph dev). The Agent Chat UI connects to this server.

Usage:
    langgraph dev          # starts Agent Server on http://localhost:2024
    Agent Chat UI          # connects to http://localhost:2024
"""

from agents.supervisor import graph  # noqa: F401 — re-export for langgraph.json
