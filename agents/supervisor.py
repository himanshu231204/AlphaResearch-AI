"""LangGraph supervisor graph — orchestrates the research workflow.

Phase 3A capabilities:
  - Streaming: Agent Server streams state updates via stream_mode automatically
  - Stores: InMemoryStore for cross-thread long-term memory
  - Persistence: MemorySaver for per-thread checkpointing
  - Fault tolerance: RetryPolicy on all agent nodes with exponential backoff

Phase 3B capabilities:
  - Subgraphs: Research+financial and technical analysis as proper LangGraph subgraphs
  - Interrupts: Human-in-the-loop approval before report generation
  - Memory: Store-based user preferences and query history
"""

import json
import logging
import uuid
from typing import Literal, Sequence, TypedDict

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import RetryPolicy, interrupt
from pydantic import BaseModel

from models.state import ResearchState
from models.routing import get_model
from agents.research_deep_agent import create_research_agent
from agents.financial_deep_agent import create_financial_agent
from agents.technical_agent import create_technical_agent
from agents.comparison_agent import create_comparison_agent
from agents.writer import create_writer_chain
from prompts.workflow import (
    SUPERVISOR_SYSTEM_PROMPT,
    REFLECTION_PROMPT,
)

logger = logging.getLogger(__name__)

MAX_REFLECTION_CYCLES = 3

# Retry policy for agent nodes — handles transient API failures, rate limits
_AGENT_RETRY = RetryPolicy(
    max_attempts=3,
    initial_interval=1.0,     # seconds before first retry
    backoff_factor=2.0,       # exponential: 1s, 2s, 4s
    retry_on=(Exception,),    # retry on any exception
)


# ---------------------------------------------------------------------------
# Structured output models
# ---------------------------------------------------------------------------

class QueryPlan(BaseModel):
    """Structured output from the supervisor for query parsing."""

    query_type: str  # "single_stock" | "comparison"
    company: str
    ticker: str
    target_companies: list[dict]  # [{"company": "...", "ticker": "..."}]


class ReflectionResult(BaseModel):
    """Structured output from the reflection agent."""

    status: str  # "complete" | "needs_work"
    issues: list[str]
    feedback: str


# ---------------------------------------------------------------------------
# Subgraph state types — shared keys map automatically to parent ResearchState
# ---------------------------------------------------------------------------

class ResearchAnalysisState(TypedDict):
    """State for the research+financial analysis subgraph.

    Shared keys with ResearchState: company, ticker, research_findings,
    financial_metrics, sources. These map automatically when the subgraph
    is added via add_node().
    """

    company: str
    ticker: str
    research_findings: str
    financial_metrics: dict
    sources: list[str]


class TechnicalAnalysisState(TypedDict):
    """State for the technical analysis subgraph.

    Shared keys with ResearchState: company, ticker, technical_analysis.
    """

    company: str
    ticker: str
    technical_analysis: dict


# ---------------------------------------------------------------------------
# Supervisor node — LLM-powered query parsing
# ---------------------------------------------------------------------------

def supervisor_node(state: ResearchState, config: RunnableConfig = None) -> dict:
    """Parse user query and extract company/ticker information using LLM.

    Supports two input modes:
      1. Traditional: state["user_query"] is set directly (FastAPI, tests)
      2. Agent Chat UI: query extracted from messages list

    Phase 3B: Uses store for cross-thread user preferences and query history.
    """
    query = state.get("user_query", "")

    # Agent Chat UI sends messages as [{role: "human", content: "..."}]
    if not query and state.get("messages"):
        from langchain_core.messages import HumanMessage as _HM

        for msg in reversed(state["messages"]):
            if isinstance(msg, _HM) or getattr(msg, "type", None) == "human":
                query = msg.content if isinstance(msg, _HM) else msg.get("content", "")
                break

    if not query:
        query = "Analyze Apple (AAPL)"

    # Phase 3B: Load user preferences from store
    store = config.get("configurable", {}).get("store") if config else None
    user_preferences = _load_user_preferences(store)

    model = get_model(task="planning", temperature=0.0)
    parser = model.with_structured_output(QueryPlan)

    try:
        plan = parser.invoke([
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=query),
        ])
    except Exception as e:
        logger.error("Supervisor LLM failed, falling back to defaults: %s", e)
        plan = QueryPlan(
            query_type="single_stock",
            company=query,
            ticker="",
            target_companies=[{"company": query, "ticker": ""}],
        )

    # Phase 3B: Save query to store for history tracking
    _save_query_to_store(store, query, plan.company, plan.ticker)

    return {
        "user_query": query,
        "query_type": plan.query_type,
        "company": plan.company,
        "ticker": plan.ticker,
        "target_companies": plan.target_companies,
        # Reset analysis fields for a fresh run
        "research_findings": "",
        "financial_metrics": {},
        "technical_analysis": {},
        "comparison_results": {},
        "valuation_results": {},
        "risk_results": {},
        "sources": [],
        "final_report": "",
        "reflection_feedback": "",
        "cycle_count": 0,
    }


# ---------------------------------------------------------------------------
# Research node — web intelligence gathering
# ---------------------------------------------------------------------------

def research_node(state: ResearchState) -> dict:
    """Run the research DeepAgent to gather web intelligence."""
    agent = create_research_agent()
    company = state.get("company", "")
    ticker = state.get("ticker", "")
    query = f"{company} ({ticker})" if ticker else company

    research_prompt = (
        f"Research the following company comprehensively: {query}\n\n"
        f"Cover: company overview, recent news, sector analysis, "
        f"competitive landscape, management quality, and growth drivers."
    )

    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": research_prompt}],
        })

        findings = _extract_last_message(result)
        return {
            "research_findings": findings,
            "sources": _extract_sources(findings),
        }
    except Exception as e:
        logger.error("Research agent failed: %s", e)
        return {"research_findings": f"Research failed: {e}", "sources": []}


# ---------------------------------------------------------------------------
# Financial node — fundamental analysis
# ---------------------------------------------------------------------------

def financial_node(state: ResearchState) -> dict:
    """Run the financial analysis DeepAgent."""
    agent = create_financial_agent()
    company = state.get("company", "")
    ticker = state.get("ticker", "")
    query = f"{company} ({ticker})" if ticker else company

    financial_prompt = (
        f"Perform comprehensive financial analysis of: {query}\n\n"
        f"Analyze: key financial metrics, revenue trends, profitability, "
        f"valuation ratios, balance sheet health, and cash flows."
    )

    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": financial_prompt}],
        })

        analysis = _extract_last_message(result)
        return {
            "financial_metrics": {"analysis": analysis},
        }
    except Exception as e:
        logger.error("Financial agent failed: %s", e)
        return {"financial_metrics": {"error": str(e)}}


# ---------------------------------------------------------------------------
# Technical node — technical analysis (Phase 2)
# ---------------------------------------------------------------------------

def technical_node(state: ResearchState) -> dict:
    """Run the technical analysis DeepAgent."""
    agent = create_technical_agent()
    ticker = state.get("ticker", "")
    company = state.get("company", "")
    query = f"{company} ({ticker})" if ticker else company

    technical_prompt = (
        f"Perform comprehensive technical analysis of: {query}\n\n"
        f"Analyze: technical indicators (RSI, MACD, EMA, Bollinger Bands), "
        f"support/resistance levels, volume trends, and trend strength.\n"
        f"Provide a clear technical trading signal."
    )

    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": technical_prompt}],
        })

        analysis = _extract_last_message(result)
        return {
            "technical_analysis": {"analysis": analysis},
        }
    except Exception as e:
        logger.error("Technical agent failed: %s", e)
        return {"technical_analysis": {"error": str(e)}}


# ---------------------------------------------------------------------------
# Aggregate node — synchronization point for parallel branches
# ---------------------------------------------------------------------------

def aggregate_node(state: ResearchState) -> dict:
    """Synchronization point after parallel research+financial and technical branches.

    Both branches have already written their results to state.
    This node ensures all data is consolidated before routing forward.
    """
    # Verify both branches completed
    financial = state.get("financial_metrics", {})
    technical = state.get("technical_analysis", {})

    if not financial:
        logger.warning("Financial analysis missing at aggregation point")
    if not technical:
        logger.warning("Technical analysis missing at aggregation point")

    # State is already updated by child nodes — no additional work needed
    return {}


# ---------------------------------------------------------------------------
# Comparison node — head-to-head analysis (Phase 2)
# ---------------------------------------------------------------------------

def comparison_node(state: ResearchState) -> dict:
    """Run the comparison DeepAgent for multi-company queries."""
    agent = create_comparison_agent()
    target_companies = state.get("target_companies", [])

    if len(target_companies) < 2:
        return {"comparison_results": {"error": "Need at least 2 companies for comparison"}}

    company_a = target_companies[0]
    company_b = target_companies[1]

    ticker_a = company_a.get("ticker", "")
    ticker_b = company_b.get("ticker", "")
    name_a = company_a.get("company", ticker_a)
    name_b = company_b.get("company", ticker_b)

    comparison_prompt = (
        f"Perform a comprehensive head-to-head comparison of:\n"
        f"  Company A: {name_a} ({ticker_a})\n"
        f"  Company B: {name_b} ({ticker_b})\n\n"
        f"Use ALL comparison tools (compare_financials, compare_technicals, compare_valuation).\n"
        f"Delegate web research to the competitor-researcher subagent.\n"
        f"Declare a winner with clear reasoning across financial, technical, "
        f"and valuation dimensions."
    )

    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": comparison_prompt}],
        })

        analysis = _extract_last_message(result)
        return {
            "comparison_results": {"analysis": analysis},
        }
    except Exception as e:
        logger.error("Comparison agent failed: %s", e)
        return {"comparison_results": {"error": str(e)}}


# ---------------------------------------------------------------------------
# Reflection node — LLM-driven quality review (Phase 2)
# ---------------------------------------------------------------------------

def reflection_node(state: ResearchState) -> dict:
    """LLM-driven quality review of all research findings."""
    cycle_count = state.get("cycle_count", 0)

    if cycle_count >= MAX_REFLECTION_CYCLES:
        return {"reflection_feedback": "RESEARCH_COMPLETE"}

    model = get_model(task="reflection", temperature=0.0)
    parser = model.with_structured_output(ReflectionResult)

    context = _build_reflection_context(state)

    try:
        result = parser.invoke([
            SystemMessage(content=REFLECTION_PROMPT),
            HumanMessage(content=context),
        ])
    except Exception as e:
        logger.error("Reflection LLM failed, using fallback: %s", e)
        # Fallback: if LLM fails, check basic completeness
        return _fallback_reflection(state, cycle_count)

    if result.status == "complete":
        return {
            "reflection_feedback": "RESEARCH_COMPLETE",
            "cycle_count": cycle_count,
        }

    return {
        "reflection_feedback": "; ".join(result.issues),
        "cycle_count": cycle_count + 1,
    }


def _build_reflection_context(state: ResearchState) -> str:
    """Build the context string for the reflection agent."""
    parts = [
        f"Company: {state.get('company', 'Unknown')}",
        f"Ticker: {state.get('ticker', 'N/A')}",
        f"Query Type: {state.get('query_type', 'single_stock')}",
        f"\n--- RESEARCH FINDINGS ---\n{state.get('research_findings', 'None')}",
        f"\n--- FINANCIAL METRICS ---\n{_format_dict(state.get('financial_metrics', {}))}",
        f"\n--- TECHNICAL ANALYSIS ---\n{_format_dict(state.get('technical_analysis', {}))}",
    ]

    if state.get("query_type") == "comparison":
        parts.append(
            f"\n--- COMPARISON RESULTS ---\n{_format_dict(state.get('comparison_results', {}))}"
        )

    parts.append(f"\n--- SOURCES ---\n{chr(10).join(state.get('sources', []))}")

    return "\n".join(parts)


def _format_dict(d: dict) -> str:
    """Format a dict for display in reflection context."""
    if not d:
        return "None"
    return json.dumps(d, indent=2, default=str)


def _fallback_reflection(state: ResearchState, cycle_count: int) -> dict:
    """Fallback reflection when LLM fails — basic completeness checks."""
    issues = []

    research = state.get("research_findings", "")
    financial = state.get("financial_metrics", {})
    technical = state.get("technical_analysis", {})

    if not research or len(str(research)) < 100:
        issues.append("Research findings are too brief or missing")
    if not financial or "error" in str(financial).lower():
        issues.append("Financial analysis is missing or contains errors")
    if not technical or "error" in str(technical).lower():
        issues.append("Technical analysis is missing or contains errors")

    if state.get("query_type") == "comparison":
        comparison = state.get("comparison_results", {})
        if not comparison or "error" in str(comparison).lower():
            issues.append("Comparison results are missing or contain errors")

    if not issues:
        return {
            "reflection_feedback": "RESEARCH_COMPLETE",
            "cycle_count": cycle_count,
        }

    return {
        "reflection_feedback": "; ".join(issues),
        "cycle_count": cycle_count + 1,
    }


# ---------------------------------------------------------------------------
# Writer node — report generation
# ---------------------------------------------------------------------------

def writer_node(state: ResearchState) -> dict:
    """Generate the final research report.

    Phase 3B: Interrupts for human-in-the-loop approval before generation.
    The interrupt payload surfaces to Agent Chat UI for user decision.
    """
    # Phase 3B: Interrupt for user approval before generating report
    approval = interrupt({
        "action": "generate_report",
        "company": state.get("company", ""),
        "ticker": state.get("ticker", "N/A"),
        "query_type": state.get("query_type", "single_stock"),
        "preview": (
            f"A comprehensive research report for {state.get('company', 'Unknown')} "
            f"({state.get('ticker', 'N/A')}) will be generated based on the collected "
            f"analysis data. Approve to proceed."
        ),
    })

    # If user rejects, return early
    if approval is False or approval == "reject":
        return {"final_report": "Report generation cancelled by user."}

    chain = create_writer_chain()

    sources_list = state.get("sources", [])
    sources_text = "\n".join(f"- {s}" for s in sources_list)

    financial = state.get("financial_metrics", {})
    financial_text = (
        json.dumps(financial, indent=2, default=str)
        if isinstance(financial, dict)
        else str(financial)
    )

    technical = state.get("technical_analysis", {})
    technical_text = (
        json.dumps(technical, indent=2, default=str)
        if isinstance(technical, dict)
        else str(technical)
    )

    valuation = state.get("valuation_results", {})
    valuation_text = json.dumps(valuation, indent=2, default=str) if valuation else "Pending detailed valuation"

    risk = state.get("risk_results", {})
    risk_text = json.dumps(risk, indent=2, default=str) if risk else "Risk assessment included in financial analysis"

    comparison = state.get("comparison_results", {})
    comparison_text = (
        json.dumps(comparison, indent=2, default=str)
        if isinstance(comparison, dict) and comparison
        else ""
    )

    try:
        report = chain.invoke({
            "company": state.get("company", "Unknown"),
            "ticker": state.get("ticker", "N/A"),
            "research_findings": state.get("research_findings", ""),
            "financial_metrics": financial_text,
            "technical_analysis": technical_text,
            "valuation_results": valuation_text,
            "risk_results": risk_text,
            "comparison_results": comparison_text,
            "sources": sources_text,
        })

        return {"final_report": report}
    except Exception as e:
        logger.error("Writer agent failed: %s", e)
        return {"final_report": f"Report generation failed: {e}"}


# ---------------------------------------------------------------------------
# Routing functions — control graph flow
# ---------------------------------------------------------------------------

def route_after_supervisor(
    state: ResearchState,
) -> list[str]:
    """Fan out to research and technical subgraphs in parallel.

    Returns a list of subgraph node names to execute concurrently.
    LangGraph runs all listed nodes in parallel as part of the next superstep.
    """
    return ["research_analysis", "technical_analysis"]


def route_after_aggregation(
    state: ResearchState,
) -> str:
    """After all analysis branches complete, route based on query type.

    Comparison queries go to the comparison agent.
    Single-stock queries go directly to reflection.
    """
    if state.get("query_type") == "comparison":
        return "comparison"
    return "reflection"


def route_after_reflection(
    state: ResearchState,
) -> str:
    """Route based on reflection feedback.

    If research is complete, proceed to the writer.
    Otherwise, loop back to the supervisor for another cycle.
    """
    feedback = state.get("reflection_feedback", "")

    if feedback == "RESEARCH_COMPLETE":
        return "writer"

    return "supervisor"


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def _extract_last_message(result: dict) -> str:
    """Extract the last AI message content from an agent result."""
    messages = result.get("messages", [])
    if not messages:
        return ""

    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content:
            if isinstance(msg.content, str):
                return msg.content
            if isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        return block["text"]
    return ""


def _extract_sources(text: str) -> list[str]:
    """Extract URLs from text as sources."""
    import re
    urls = re.findall(r'https?://[^\s\)\]"\']+', text)
    return list(dict.fromkeys(urls))


# ---------------------------------------------------------------------------
# Store helpers — cross-thread memory (Phase 3B)
# ---------------------------------------------------------------------------

def _load_user_preferences(store) -> dict:
    """Load user preferences from the store.

    Returns empty dict if store is unavailable or no preferences exist.
    """
    if store is None:
        return {}

    try:
        items = store.search(("user", "preferences"), limit=1)
        if items:
            return items[0].value
    except Exception as e:
        logger.debug("Could not load user preferences: %s", e)

    return {}


def _save_query_to_store(store, query: str, company: str, ticker: str) -> None:
    """Save a query to the store for history tracking.

    Silently fails if store is unavailable.
    """
    if store is None:
        return

    try:
        store.put(
            ("user", "queries"),
            str(uuid.uuid4()),
            {
                "query": query,
                "company": company,
                "ticker": ticker,
            },
        )
    except Exception as e:
        logger.debug("Could not save query to store: %s", e)


# ---------------------------------------------------------------------------
# Subgraph builders — proper LangGraph subgraphs (Phase 3B)
# ---------------------------------------------------------------------------

def build_research_analysis_subgraph():
    """Build the research+financial analysis subgraph.

    Flow: research -> financial
    State shares keys with ResearchState for automatic mapping.
    """
    builder = StateGraph(ResearchAnalysisState)

    builder.add_node("research", research_node, retry_policy=_AGENT_RETRY)
    builder.add_node("financial", financial_node, retry_policy=_AGENT_RETRY)

    builder.add_edge(START, "research")
    builder.add_edge("research", "financial")
    builder.add_edge("financial", END)

    return builder.compile()


def build_technical_analysis_subgraph():
    """Build the technical analysis subgraph.

    Single node: technical analysis.
    State shares keys with ResearchState for automatic mapping.
    """
    builder = StateGraph(TechnicalAnalysisState)

    builder.add_node("technical", technical_node, retry_policy=_AGENT_RETRY)

    builder.add_edge(START, "technical")
    builder.add_edge("technical", END)

    return builder.compile()


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph():
    """Build and compile the LangGraph supervisor graph.

    Graph topology (Phase 3B — subgraphs + interrupts):

        START
          |
        supervisor  (loads user preferences from store)
          |
     [research_analysis, technical_analysis]  (parallel subgraphs)
          |                    |
     (research->financial)   (technical)
          |                    |
         aggregate  <-----------+  (synchronization point)
          |
     [comparison | reflection]  (conditional)
          |            |
        reflection   [loop]
          |
        writer  (interrupts for human approval)
          |
         END

    Phase 3A capabilities:
      - Store: InMemoryStore for cross-thread long-term memory
      - Checkpointer: MemorySaver for per-thread persistence
      - Retry policies: All agent nodes retry up to 3x on transient failures

    Phase 3B capabilities:
      - Subgraphs: research_analysis and technical_analysis as proper subgraphs
      - Interrupts: Human-in-the-loop approval before report generation
      - Memory: Store-based user preferences and query history
    """
    builder = StateGraph(ResearchState)

    # Create subgraphs
    research_subgraph = build_research_analysis_subgraph()
    technical_subgraph = build_technical_analysis_subgraph()

    # Nodes — subgraphs added via add_node() for automatic state mapping
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("research_analysis", research_subgraph)
    builder.add_node("technical_analysis", technical_subgraph)
    builder.add_node("aggregate", aggregate_node)
    builder.add_node("comparison", comparison_node, retry_policy=_AGENT_RETRY)
    builder.add_node("reflection", reflection_node, retry_policy=_AGENT_RETRY)
    builder.add_node("writer", writer_node, retry_policy=_AGENT_RETRY)

    # Edges
    builder.add_edge(START, "supervisor")

    # Parallel fan-out: supervisor -> [research_analysis, technical_analysis]
    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "research_analysis": "research_analysis",
            "technical_analysis": "technical_analysis",
        },
    )

    # Both subgraphs feed into aggregate (sync point)
    builder.add_edge("research_analysis", "aggregate")
    builder.add_edge("technical_analysis", "aggregate")

    # After aggregate: comparison or reflection
    builder.add_conditional_edges(
        "aggregate",
        route_after_aggregation,
        {"comparison": "comparison", "reflection": "reflection"},
    )

    # Comparison feeds into reflection
    builder.add_edge("comparison", "reflection")

    # Reflection: complete -> writer, needs work -> back to supervisor
    builder.add_conditional_edges(
        "reflection",
        route_after_reflection,
        {"writer": "writer", "supervisor": "supervisor"},
    )

    builder.add_edge("writer", END)

    checkpointer = MemorySaver()
    store = InMemoryStore()
    return builder.compile(checkpointer=checkpointer, store=store)


# ---------------------------------------------------------------------------
# Module-level compiled graph — used by LangGraph Server via langgraph.json
# ---------------------------------------------------------------------------

graph = build_graph()
