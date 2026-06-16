"""LangGraph state model for the research workflow."""

from typing import Annotated, TypedDict

from langgraph.graph import add_messages


class ResearchState(TypedDict):
    """Core state flowing through the supervisor graph."""

    messages: Annotated[list, add_messages]
    user_query: str
    company: str
    ticker: str
    research_findings: str
    financial_metrics: dict
    valuation_results: dict
    risk_results: dict
    sources: list[str]
    final_report: str
    reflection_feedback: str
    cycle_count: int

    # Phase 2: Technical analysis, reflection loops, company comparison
    query_type: str                    # "single_stock" | "comparison"
    technical_analysis: dict           # Technical indicator results
    comparison_results: dict           # Head-to-head comparison data
    target_companies: list[dict]       # [{"company": "...", "ticker": "..."}]
