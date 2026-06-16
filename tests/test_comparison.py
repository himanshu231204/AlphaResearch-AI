"""Tests for comparison tools."""

from unittest.mock import patch, MagicMock
import pandas as pd
import pytest


class TestCompareFinancials:
    """Tests for the compare_financials tool."""

    @patch("tools.comparison_tools.yf.Ticker")
    def test_returns_comparison(self, mock_ticker):
        from tools.comparison_tools import compare_financials

        mock_stock_a = MagicMock()
        mock_stock_a.info = {
            "shortName": "Apple Inc",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "trailingPE": 28.5,
            "forwardPE": 25.0,
            "priceToBook": 45.2,
            "returnOnEquity": 0.156,
            "profitMargins": 0.265,
            "debtToEquity": 1.8,
            "marketCap": 3000000000000,
        }

        mock_stock_b = MagicMock()
        mock_stock_b.info = {
            "shortName": "Microsoft",
            "sector": "Technology",
            "industry": "Software",
            "trailingPE": 35.0,
            "forwardPE": 30.0,
            "priceToBook": 12.5,
            "returnOnEquity": 0.38,
            "profitMargins": 0.36,
            "debtToEquity": 0.5,
            "marketCap": 2800000000000,
        }

        def side_effect(ticker):
            if ticker == "AAPL":
                return mock_stock_a
            return mock_stock_b

        mock_ticker.side_effect = side_effect

        result = compare_financials.invoke({"ticker_a": "AAPL", "ticker_b": "MSFT"})

        assert "FINANCIAL COMPARISON" in result
        assert "AAPL" in result
        assert "MSFT" in result
        assert "Trailing PE" in result


class TestCompareTechnicals:
    """Tests for the compare_technicals tool."""

    @patch("tools.comparison_tools.yf.Ticker")
    def test_returns_comparison(self, mock_ticker):
        from tools.comparison_tools import compare_technicals

        dates = pd.date_range("2024-01-01", periods=100, freq="D")

        mock_stock_a = MagicMock()
        mock_stock_a.history.return_value = pd.DataFrame({
            "Close": [100 + i * 0.5 for i in range(100)],
            "High": [101 + i * 0.5 for i in range(100)],
            "Low": [99 + i * 0.5 for i in range(100)],
            "Volume": [1000000] * 100,
        }, index=dates)

        mock_stock_b = MagicMock()
        mock_stock_b.history.return_value = pd.DataFrame({
            "Close": [200 + i * 0.3 for i in range(100)],
            "High": [201 + i * 0.3 for i in range(100)],
            "Low": [199 + i * 0.3 for i in range(100)],
            "Volume": [500000] * 100,
        }, index=dates)

        def side_effect(ticker):
            if ticker == "AAPL":
                return mock_stock_a
            return mock_stock_b

        mock_ticker.side_effect = side_effect

        result = compare_technicals.invoke({"ticker_a": "AAPL", "ticker_b": "MSFT"})

        assert "TECHNICAL COMPARISON" in result
        assert "AAPL" in result
        assert "MSFT" in result
        assert "RSI" in result


class TestCompareValuation:
    """Tests for the compare_valuation tool."""

    @patch("tools.comparison_tools.yf.Ticker")
    def test_returns_valuation(self, mock_ticker):
        from tools.comparison_tools import compare_valuation

        mock_stock_a = MagicMock()
        mock_stock_a.info = {
            "shortName": "Apple Inc",
            "trailingPE": 28.5,
            "forwardPE": 25.0,
            "priceToBook": 45.2,
            "priceToSalesTrailing12Months": 7.5,
            "enterpriseToEbitda": 22.0,
            "earningsGrowth": 0.15,
        }

        mock_stock_b = MagicMock()
        mock_stock_b.info = {
            "shortName": "Microsoft",
            "trailingPE": 35.0,
            "forwardPE": 30.0,
            "priceToBook": 12.5,
            "priceToSalesTrailing12Months": 10.0,
            "enterpriseToEbitda": 25.0,
            "earningsGrowth": 0.20,
        }

        def side_effect(ticker):
            if ticker == "AAPL":
                return mock_stock_a
            return mock_stock_b

        mock_ticker.side_effect = side_effect

        result = compare_valuation.invoke({"ticker_a": "AAPL", "ticker_b": "MSFT"})

        assert "RELATIVE VALUATION" in result
        assert "AAPL" in result
        assert "MSFT" in result
        assert "PEG Ratio" in result
