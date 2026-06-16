"""Financial Analysis DeepAgent — autonomous financial analysis."""

from deepagents import create_deep_agent

from tools.financial_tools import ALL_FINANCIAL_TOOLS
from prompts.workflow import FINANCIAL_AGENT_PROMPT


def create_financial_agent():
    """Create a DeepAgent for autonomous financial analysis.

    Uses create_deep_agent with:
    - Gemini 2.5 Pro as the reasoning model
    - Financial data tools (yfinance, finnhub, alpha vantage)
    - Detailed financial analysis system prompt
    """
    agent = create_deep_agent(
        model="google_genai:gemini-2.5-pro",
        tools=ALL_FINANCIAL_TOOLS,
        system_prompt=FINANCIAL_AGENT_PROMPT,
    )

    return agent
