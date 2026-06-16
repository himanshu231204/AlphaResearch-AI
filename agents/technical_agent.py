"""Technical Analysis DeepAgent — autonomous technical analysis with web research."""

from deepagents import create_deep_agent

from tools.technical_tools import ALL_TECHNICAL_TOOLS
from tools.search_tools import ALL_SEARCH_TOOLS
from prompts.workflow import TECHNICAL_AGENT_PROMPT
from models.routing import OPENROUTER_NEX_INIT

TECHNICAL_RESEARCHER_PROMPT = """You are a technical analysis research specialist.

Your job is to search for recent technical commentary, analyst opinions, and market context for a stock.

Research Areas:
1. Recent analyst technical ratings and price targets
2. Key technical events (breakouts, breakdowns, gap fills)
3. Sector-wide technical trends affecting the stock
4. Options flow and implied volatility context
5. Institutional positioning based on technical signals

Rules:
- Always cite sources with URLs
- Focus on recent information (last 30 days preferred)
- Include both bullish and bearish perspectives
- Note any upcoming technical catalysts (earnings, product launches)
- Be specific about price levels and dates
"""


def create_technical_agent():
    """Create a DeepAgent for autonomous technical analysis.

    Uses create_deep_agent with:
    - Grok as the reasoning model (per AGENTS.md: technical analysis uses Grok)
    - Technical analysis tools (indicators, support/resistance, volume, trend)
    - A technical-researcher subagent for web search context
    """
    technical_researcher = {
        "name": "technical-researcher",
        "description": (
            "Web research specialist for technical analysis context. "
            "Use this subagent to find recent analyst opinions, technical events, "
            "and market commentary related to the stock being analyzed."
        ),
        "system_prompt": TECHNICAL_RESEARCHER_PROMPT,
        "tools": ALL_SEARCH_TOOLS,
        "model": OPENROUTER_NEX_INIT,
    }

    agent = create_deep_agent(
        model=OPENROUTER_NEX_INIT,
        tools=ALL_TECHNICAL_TOOLS,
        subagents=[technical_researcher],
        system_prompt=TECHNICAL_AGENT_PROMPT,
    )

    return agent
