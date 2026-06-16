"""LangGraph state model for the research workflow."""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import add_messages


def dict_merge(current: dict, update: dict) -> dict:
    """Reducer: merge two dicts, with update taking precedence."""
    return {**current, **update}


def str_replace(current: str, update: str) -> str:
    """Reducer: replace current value with update (last-writer-wins for strings)."""
    return update


class ResearchState(TypedDict):
    """Core state flowing through the supervisor graph.

    Reducers:
      - lists: operator.add (concatenation)
      - dicts: dict_merge (shallow merge, update wins)
      - strings: str_replace (last-writer-wins)
    """

    messages: Annotated[list, add_messages]
    user_query: str
    company: Annotated[str, str_replace]
    ticker: Annotated[str, str_replace]
    research_findings: Annotated[str, str_replace]
    financial_metrics: Annotated[dict, dict_merge]
    valuation_results: Annotated[dict, dict_merge]
    risk_results: Annotated[dict, dict_merge]
    sources: Annotated[list[str], operator.add]
    final_report: Annotated[str, str_replace]
    reflection_feedback: Annotated[str, str_replace]
    cycle_count: int

    # Phase 2: Technical analysis, reflection loops, company comparison
    query_type: Annotated[str, str_replace]
    technical_analysis: Annotated[dict, dict_merge]
    comparison_results: Annotated[dict, dict_merge]
    target_companies: list[dict]       # [{"company": "...", "ticker": "..."}]
