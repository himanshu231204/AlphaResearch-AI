"""Tests for financial data tools."""

from unittest.mock import patch, MagicMock
import pandas as pd
import pytest


class TestGetStockInfo:
    """Tests for the get_stock_info tool."""

    @patch("tools.financial_tools.yf.Ticker")
    def test_returns_company_info(self, mock_ticker):
        from tools.financial_tools import get_stock_info

        mock_stock = MagicMock()
        mock_stock.info = {
            "shortName": "Apple Inc",
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "country": "United States",
            "marketCap": 3000000000000,
            "currency": "USD",
            "website": "https://apple.com",
            "fullTimeEmployees": 164000,
            "summary": "Apple Inc. designs, manufactures, and markets smartphones.",
        }
        mock_ticker.return_value = mock_stock

        result = get_stock_info.invoke("AAPL")

        assert "Apple" in result
        assert "Technology" in result
        mock_ticker.assert_called_once_with("AAPL")

    @patch("tools.financial_tools.yf.Ticker")
    def test_handles_error(self, mock_ticker):
        from tools.financial_tools import get_stock_info

        mock_ticker.side_effect = Exception("API error")

        result = get_stock_info.invoke("INVALID")

        assert "Error" in result


class TestGetKeyMetrics:
    """Tests for the get_key_metrics tool."""

    @patch("tools.financial_tools.yf.Ticker")
    def test_returns_financial_ratios(self, mock_ticker):
        from tools.financial_tools import get_key_metrics

        mock_stock = MagicMock()
        mock_stock.info = {
            "trailingPE": 28.5,
            "forwardPE": 25.0,
            "priceToBook": 45.2,
            "returnOnEquity": 0.156,
            "profitMargins": 0.265,
            "debtToEquity": 1.8,
        }
        mock_ticker.return_value = mock_stock

        result = get_key_metrics.invoke("AAPL")

        assert "trailing_pe" in result
        assert "28.5" in result


class TestGetFinancialStatements:
    """Tests for the get_financial_statements tool."""

    @patch("tools.financial_tools.yf.Ticker")
    def test_returns_statements(self, mock_ticker):
        from tools.financial_tools import get_financial_statements

        mock_stock = MagicMock()
        mock_stock.income_stmt = pd.DataFrame({"Revenue": [1000000]})
        mock_stock.balance_sheet = pd.DataFrame({"Assets": [5000000]})
        mock_stock.cashflow = pd.DataFrame({"Cash": [200000]})
        mock_ticker.return_value = mock_stock

        result = get_financial_statements.invoke("AAPL")

        assert "INCOME STATEMENT" in result
        assert "BALANCE SHEET" in result
        assert "CASH FLOW" in result


class TestGetStockHistory:
    """Tests for the get_stock_history tool."""

    @patch("tools.financial_tools.yf.Ticker")
    def test_returns_history(self, mock_ticker):
        from tools.financial_tools import get_stock_history

        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        mock_hist = pd.DataFrame({
            "Close": [100 + i * 0.5 for i in range(100)],
            "High": [101 + i * 0.5 for i in range(100)],
            "Low": [99 + i * 0.5 for i in range(100)],
            "Volume": [1000000] * 100,
        }, index=dates)

        mock_stock = MagicMock()
        mock_stock.history.return_value = mock_hist
        mock_ticker.return_value = mock_stock

        result = get_stock_history.invoke("AAPL")

        assert "PRICE HISTORY" in result
        assert "latest_close" in result
