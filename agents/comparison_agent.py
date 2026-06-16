"""Comparison DeepAgent — autonomous head-to-head company comparison."""

from deepagents import create_deep_agent

from tools.comparison_tools import ALL_COMPARISON_TOOLS
from tools.search_tools import ALL_SEARCH_TOOLS
from prompts.workflow import COMPARISON_AGENT_PROMPT, COMPETITOR_RESEARCH_PROMPT


def create_comparison_agent():
    """Create a DeepAgent for autonomous company comparison.

    Uses create_deep_agent with:
    - Gemini 2.5 Pro as the reasoning model (complex comparison analysis)
    - Comparison tools (financial, technical, valuation side-by-side)
    - A competitor-researcher subagent for web search on competitive dynamics
    """
    competitor_researcher = {
        "name": "competitor-researcher",
        "description": (
            "Web research specialist for competitive dynamics. "
            "Use this subagent to research market share, competitive advantages, "
            "recent competitive moves, and analyst opinions on the companies being compared."
        ),
        "system_prompt": COMPETITOR_RESEARCH_PROMPT,
        "tools": ALL_SEARCH_TOOLS,
        "model": "google_genai:gemini-2.5-flash",
    }

    agent = create_deep_agent(
        model="gemini/gemini-2.5-pro",
        tools=ALL_COMPARISON_TOOLS,
        subagents=[competitor_researcher],
        system_prompt=COMPARISON_AGENT_PROMPT,
    )

    return agent
