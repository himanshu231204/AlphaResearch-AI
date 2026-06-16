"""Research API endpoint."""

import asyncio
import logging
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(tags=["research"])


class ResearchRequest(BaseModel):
    """Request body for equity research."""

    query: str


class ResearchResponse(BaseModel):
    """Response body for completed research."""

    company: str
    ticker: str
    query_type: str
    report: str
    sources: list[str]
    technical_analysis: dict
    comparison_results: dict
    status: str


class CompareRequest(BaseModel):
    """Request body for company comparison."""

    company_a: str
    ticker_a: str
    company_b: str
    ticker_b: str


@router.post("/research", response_model=ResearchResponse)
async def run_research(request: ResearchRequest):
    """Run autonomous equity research on a company.

    Accepts a natural language query like "Analyze Reliance Industries"
    and returns a comprehensive research report.

    Supports both single-stock analysis and company comparison:
    - Single stock: "Analyze Apple Inc"
    - Comparison: "Compare Apple with Microsoft" or "AAPL vs MSFT"
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        from agents.supervisor import build_graph

        graph = build_graph()

        # Use ainvoke to avoid blocking the event loop — graph.invoke()
        # inside an async endpoint starves asyncio and triggers CancelledError.
        result = await graph.ainvoke(
            {
                "user_query": request.query,
                "messages": [{"role": "user", "content": request.query}],
            },
            config={"configurable": {"thread_id": "research-session"}},
        )

        return ResearchResponse(
            company=result.get("company", "Unknown"),
            ticker=result.get("ticker", "N/A"),
            query_type=result.get("query_type", "single_stock"),
            report=result.get("final_report", "No report generated"),
            sources=result.get("sources", []),
            technical_analysis=result.get("technical_analysis", {}),
            comparison_results=result.get("comparison_results", {}),
            status="completed",
        )

    except asyncio.CancelledError:
        logger.warning("Research request was cancelled (client disconnect or shutdown)")
        raise HTTPException(
            status_code=499,  # 499 = client closed request
            detail="Research was cancelled",
        )
    except Exception as e:
        logger.error("Research failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Research failed: {e}",
        )


@router.post("/compare", response_model=ResearchResponse)
async def run_comparison(request: CompareRequest):
    """Run head-to-head comparison of two companies.

    Accepts two company names/tickers and returns a comparative analysis.
    """
    if not request.ticker_a.strip() or not request.ticker_b.strip():
        raise HTTPException(status_code=400, detail="Both tickers are required")

    query = f"Compare {request.company_a} ({request.ticker_a}) with {request.company_b} ({request.ticker_b})"

    try:
        from agents.supervisor import build_graph

        graph = build_graph()

        # Use ainvoke — same reason as run_research above.
        result = await graph.ainvoke(
            {
                "user_query": query,
                "messages": [{"role": "user", "content": query}],
            },
            config={"configurable": {"thread_id": f"compare-{request.ticker_a}-{request.ticker_b}"}},
        )

        return ResearchResponse(
            company=result.get("company", request.company_a),
            ticker=result.get("ticker", request.ticker_a),
            query_type="comparison",
            report=result.get("final_report", "No report generated"),
            sources=result.get("sources", []),
            technical_analysis=result.get("technical_analysis", {}),
            comparison_results=result.get("comparison_results", {}),
            status="completed",
        )

    except asyncio.CancelledError:
        logger.warning("Comparison request was cancelled (client disconnect or shutdown)")
        raise HTTPException(
            status_code=499,
            detail="Comparison was cancelled",
        )
    except Exception as e:
        logger.error("Comparison failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {e}",
        )
