"""Financial data tools — wraps yfinance, finnhub, and alpha vantage.

Note: Technical indicator tools have been moved to tools/technical_tools.py
for better separation of concerns. This module focuses on fundamental
financial data (statements, metrics, history).
"""

import logging
from typing import Optional

import yfinance as yf
import pandas as pd
from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_stock_info(ticker: str) -> str:
    """Get company overview and key information for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, RELIANCE.NS)

    Returns:
        Structured company information including sector, industry, and summary.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        key_fields = [
            "shortName", "longName", "sector", "industry",
            "country", "marketCap", "currency", "website",
            "fullTimeEmployees", "summary",
        ]
        result = {k: info.get(k, "N/A") for k in key_fields}

        return str(result)
    except Exception as e:
        logger.error("Failed to get stock info for %s: %s", ticker, e)
        return f"Error fetching stock info: {e}"


@tool
def get_financial_statements(ticker: str) -> str:
    """Get income statement, balance sheet, and cash flow for a stock.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Recent financial statements as structured data.
    """
    try:
        stock = yf.Ticker(ticker)

        income = stock.income_stmt
        balance = stock.balance_sheet
        cashflow = stock.cashflow

        sections = []

        if income is not None and not income.empty:
            latest = income.iloc[:, 0] if len(income.columns) > 0 else pd.Series()
            sections.append(f"INCOME STATEMENT:\n{latest.to_string()}")

        if balance is not None and not balance.empty:
            latest = balance.iloc[:, 0] if len(balance.columns) > 0 else pd.Series()
            sections.append(f"BALANCE SHEET:\n{latest.to_string()}")

        if cashflow is not None and not cashflow.empty:
            latest = cashflow.iloc[:, 0] if len(cashflow.columns) > 0 else pd.Series()
            sections.append(f"CASH FLOW:\n{latest.to_string()}")

        if not sections:
            return f"No financial statements found for {ticker}"

        return "\n\n".join(sections)
    except Exception as e:
        logger.error("Failed to get financials for %s: %s", ticker, e)
        return f"Error fetching financial statements: {e}"


@tool
def get_key_metrics(ticker: str) -> str:
    """Get key financial ratios and metrics for a stock.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Key metrics including PE ratio, PB ratio, ROE, ROCE, debt/equity, margins.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        metrics = {
            "trailing_pe": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "price_to_book": info.get("priceToBook", "N/A"),
            "return_on_equity": info.get("returnOnEquity", "N/A"),
            "profit_margins": info.get("profitMargins", "N/A"),
            "operating_margins": info.get("operatingMargins", "N/A"),
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "current_ratio": info.get("currentRatio", "N/A"),
            "free_cashflow": info.get("freeCashflow", "N/A"),
            "revenue_growth": info.get("revenueGrowth", "N/A"),
            "earnings_growth": info.get("earningsGrowth", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "beta": info.get("beta", "N/A"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow", "N/A"),
        }

        formatted = "\n".join(f"  {k}: {v}" for k, v in metrics.items())
        return f"KEY METRICS for {ticker}:\n{formatted}"
    except Exception as e:
        logger.error("Failed to get metrics for %s: %s", ticker, e)
        return f"Error fetching key metrics: {e}"


@tool
def get_stock_history(ticker: str, period: str = "1y") -> str:
    """Get historical price data for a stock.

    Args:
        ticker: Stock ticker symbol
        period: Time period — 1mo, 3mo, 6mo, 1y, 2y, 5y, max

    Returns:
        Recent price history with key statistics.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            return f"No price history found for {ticker}"

        stats = {
            "latest_close": f"{hist['Close'].iloc[-1]:.2f}",
            "period_high": f"{hist['High'].max():.2f}",
            "period_low": f"{hist['Low'].min():.2f}",
            "period_return": f"{((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100:.2f}%",
            "avg_volume": f"{hist['Volume'].mean():,.0f}",
            "days": len(hist),
        }

        formatted = "\n".join(f"  {k}: {v}" for k, v in stats.items())
        return f"PRICE HISTORY for {ticker} ({period}):\n{formatted}"
    except Exception as e:
        logger.error("Failed to get history for %s: %s", ticker, e)
        return f"Error fetching price history: {e}"


ALL_FINANCIAL_TOOLS = [
    get_stock_info,
    get_financial_statements,
    get_key_metrics,
    get_stock_history,
]
