"""Writer agent — generates professional research reports."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from prompts.workflow import WRITER_SYSTEM_PROMPT
from models.routing import get_model


def create_writer_chain():
    """Create the report writer chain.

    Uses centralized ChatLiteLLM model routing via models.routing.get_model().
    Routes to gemini/gemini-2.5-pro for report writing (low temperature).
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", WRITER_SYSTEM_PROMPT),
        ("human", """Generate a research report based on the following:

COMPANY: {company}
TICKER: {ticker}

RESEARCH FINDINGS:
{research_findings}

FINANCIAL ANALYSIS:
{financial_metrics}

TECHNICAL ANALYSIS:
{technical_analysis}

VALUATION RESULTS:
{valuation_results}

RISK ASSESSMENT:
{risk_results}

COMPARISON RESULTS:
{comparison_results}

SOURCES:
{sources}
"""),
    ])

    model = get_model(task="report_writing", temperature=0.3)
    parser = StrOutputParser()

    return prompt | model | parser
