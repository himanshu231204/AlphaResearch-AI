"""Tests for technical analysis tools."""

from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import pytest


class TestCalculateTechnicalIndicators:
    """Tests for the calculate_technical_indicators tool."""

    @patch("tools.technical_tools.yf.Ticker")
    def test_returns_indicators(self, mock_ticker):
        from tools.technical_tools import calculate_technical_indicators

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

        result = calculate_technical_indicators.invoke("AAPL")

        assert "TECHNICAL ANALYSIS" in result
        assert "RSI" in result
        assert "MACD" in result

    @patch("tools.technical_tools.yf.Ticker")
    def test_handles_insufficient_data(self, mock_ticker):
        from tools.technical_tools import calculate_technical_indicators

        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        mock_hist = pd.DataFrame({
            "Close": [100] * 5,
            "High": [101] * 5,
            "Low": [99] * 5,
            "Volume": [1000000] * 5,
        }, index=dates)

        mock_stock = MagicMock()
        mock_stock.history.return_value = mock_hist
        mock_ticker.return_value = mock_stock

        result = calculate_technical_indicators.invoke("AAPL")

        assert "Insufficient" in result or "Error" in result


class TestGetSupportResistance:
    """Tests for the get_support_resistance tool."""

    @patch("tools.technical_tools.yf.Ticker")
    def test_returns_support_resistance(self, mock_ticker):
        from tools.technical_tools import get_support_resistance

        # Create price data with clear support/resistance levels
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        prices = []
        for i in range(100):
            if i < 20:
                prices.append(100 + i * 0.5)  # Uptrend
            elif i < 40:
                prices.append(110 - (i - 20) * 0.5)  # Downtrend
            elif i < 60:
                prices.append(100 + (i - 40) * 0.5)  # Uptrend
            elif i < 80:
                prices.append(110 - (i - 60) * 0.5)  # Downtrend
            else:
                prices.append(100 + (i - 80) * 0.5)  # Uptrend

        mock_hist = pd.DataFrame({
            "Close": prices,
            "High": [p + 1 for p in prices],
            "Low": [p - 1 for p in prices],
            "Volume": [1000000] * 100,
        }, index=dates)

        mock_stock = MagicMock()
        mock_stock.history.return_value = mock_hist
        mock_ticker.return_value = mock_stock

        result = get_support_resistance.invoke("AAPL")

        assert "SUPPORT/RESISTANCE" in result
        assert "Current Price" in result

    @patch("tools.technical_tools.yf.Ticker")
    def test_handles_insufficient_data(self, mock_ticker):
        from tools.technical_tools import get_support_resistance

        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        mock_hist = pd.DataFrame({
            "Close": [100] * 5,
            "High": [101] * 5,
            "Low": [99] * 5,
            "Volume": [1000000] * 5,
        }, index=dates)

        mock_stock = MagicMock()
        mock_stock.history.return_value = mock_hist
        mock_ticker.return_value = mock_stock

        result = get_support_resistance.invoke("AAPL")

        assert "Insufficient" in result or "Error" in result


class TestGetVolumeAnalysis:
    """Tests for the get_volume_analysis tool."""

    @patch("tools.technical_tools.yf.Ticker")
    def test_returns_volume_analysis(self, mock_ticker):
        from tools.technical_tools import get_volume_analysis

        dates = pd.date_range("2024-01-01", periods=60, freq="D")
        mock_hist = pd.DataFrame({
            "Close": [100 + i * 0.5 for i in range(60)],
            "High": [101 + i * 0.5 for i in range(60)],
            "Low": [99 + i * 0.5 for i in range(60)],
            "Volume": [1000000 + i * 10000 for i in range(60)],
        }, index=dates)

        mock_stock = MagicMock()
        mock_stock.history.return_value = mock_hist
        mock_ticker.return_value = mock_stock

        result = get_volume_analysis.invoke("AAPL")

        assert "VOLUME ANALYSIS" in result
        assert "OBV" in result
        assert "Volume Trend" in result


class TestGetTrendAnalysis:
    """Tests for the get_trend_analysis tool."""

    @patch("tools.technical_tools.yf.Ticker")
    def test_returns_trend_analysis(self, mock_ticker):
        from tools.technical_tools import get_trend_analysis

        dates = pd.date_range("2024-01-01", periods=120, freq="D")
        mock_hist = pd.DataFrame({
            "Close": [100 + i * 0.5 for i in range(120)],
            "High": [101 + i * 0.5 for i in range(120)],
            "Low": [99 + i * 0.5 for i in range(120)],
            "Volume": [1000000] * 120,
        }, index=dates)

        mock_stock = MagicMock()
        mock_stock.history.return_value = mock_hist
        mock_ticker.return_value = mock_stock

        result = get_trend_analysis.invoke("AAPL")

        assert "TREND ANALYSIS" in result
        assert "ADX" in result
        assert "Moving Averages" in result
