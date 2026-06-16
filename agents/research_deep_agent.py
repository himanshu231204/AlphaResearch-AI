"""Research DeepAgent — autonomous web research with subagent delegation."""

from deepagents import create_deep_agent

from tools.search_tools import ALL_SEARCH_TOOLS
from prompts.workflow import RESEARCH_AGENT_PROMPT


RESEARCH_SUBAGENT_PROMPT = """You are a deep web research specialist.

Your job is to search for specific information and return detailed findings.

When researching:
1. Use multiple search queries to cover different angles
2. Look for recent news and developments
3. Check multiple sources for accuracy
4. Always include source URLs in your findings

Return structured findings with:
- Key facts and data points
- Source URLs for every claim
- Assessment of information recency and reliability
"""


def create_research_agent():
    """Create a DeepAgent for autonomous equity web research.

    Uses create_deep_agent with:
    - Gemini 2.5 Pro as the main reasoning model
    - Search tools for web research
    - A web-researcher subagent for delegated deep searches
    - AGENTS.md memory for project context
    """
    web_researcher = {
        "name": "web-researcher",
        "description": (
            "Deep web research specialist. Use this subagent for specific "
            "search queries that need thorough multi-source investigation."
        ),
        "system_prompt": RESEARCH_SUBAGENT_PROMPT,
        "tools": ALL_SEARCH_TOOLS,
        "model": "google_genai:gemini-2.5-flash",
    }

    agent = create_deep_agent(
        model="google_genai:gemini-2.5-pro",
        tools=ALL_SEARCH_TOOLS,
        subagents=[web_researcher],
        system_prompt=RESEARCH_AGENT_PROMPT,
    )

    return agent
