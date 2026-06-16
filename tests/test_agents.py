"""Tests for the LangGraph supervisor graph."""

import pytest

from models.state import ResearchState


def test_research_state_has_required_fields():
    """Verify the state model has all required fields."""
    expected_fields = {
        "messages", "user_query", "company", "ticker",
        "research_findings", "financial_metrics", "valuation_results",
        "risk_results", "sources", "final_report",
        "reflection_feedback", "cycle_count",
        # Phase 2 fields
        "query_type", "technical_analysis", "comparison_results",
        "target_companies",
    }

    annotations = ResearchState.__annotations__
    assert expected_fields == set(annotations.keys())


@pytest.mark.asyncio
async def test_reflection_stops_after_max_cycles():
    """Test reflection stops after 3 cycles."""
    from agents.supervisor import reflection_node

    state = {
        "research_findings": "",
        "financial_metrics": {},
        "technical_analysis": {},
        "cycle_count": 3,
    }

    result = await reflection_node(state)

    assert result["reflection_feedback"] == "RESEARCH_COMPLETE"


def test_route_after_supervisor_returns_parallel_nodes():
    """Test that supervisor routes to both research and technical subgraphs in parallel."""
    from agents.supervisor import route_after_supervisor

    state = {
        "query_type": "single_stock",
        "company": "Apple",
        "ticker": "AAPL",
    }

    result = route_after_supervisor(state)

    assert isinstance(result, list)
    assert "research_analysis" in result
    assert "technical_analysis" in result


def test_route_after_aggregation_single_stock():
    """Test aggregation routes to reflection for single stock queries."""
    from agents.supervisor import route_after_aggregation

    state = {"query_type": "single_stock"}

    result = route_after_aggregation(state)

    assert result == "reflection"


def test_route_after_aggregation_comparison():
    """Test aggregation routes to comparison for comparison queries."""
    from agents.supervisor import route_after_aggregation

    state = {"query_type": "comparison"}

    result = route_after_aggregation(state)

    assert result == "comparison"


def test_route_after_reflection_complete():
    """Test reflection routes to writer when complete."""
    from agents.supervisor import route_after_reflection

    state = {"reflection_feedback": "RESEARCH_COMPLETE"}

    result = route_after_reflection(state)

    assert result == "writer"


def test_route_after_reflection_needs_work():
    """Test reflection routes back to supervisor when work is needed."""
    from agents.supervisor import route_after_reflection

    state = {"reflection_feedback": "Issues found: missing data"}

    result = route_after_reflection(state)

    assert result == "supervisor"


def test_build_graph_creates_compiled_graph():
    """Test that build_graph returns a compiled LangGraph."""
    from agents.supervisor import build_graph

    graph = build_graph()

    assert graph is not None
    # Compiled graphs have an invoke method
    assert hasattr(graph, "invoke")
