"""Financial Analysis DeepAgent — autonomous financial analysis."""

from deepagents import create_deep_agent

from tools.financial_tools import ALL_FINANCIAL_TOOLS
from prompts.workflow import FINANCIAL_AGENT_PROMPT
from models.routing import OPENROUTER_NEX_INIT


def create_financial_agent():
    """Create a DeepAgent for autonomous financial analysis.

    Uses create_deep_agent with:
    - Gemini 2.5 Pro as the reasoning model
    - Financial data tools (yfinance, finnhub, alpha vantage)
    - Detailed financial analysis system prompt
    """
    agent = create_deep_agent(
        model=OPENROUTER_NEX_INIT,
        tools=ALL_FINANCIAL_TOOLS,
        system_prompt=FINANCIAL_AGENT_PROMPT,
    )

    return agent
