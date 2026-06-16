"""Technical analysis tools — indicators, support/resistance, volume, trend."""

import logging
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def calculate_technical_indicators(ticker: str) -> str:
    """Calculate technical analysis indicators (RSI, MACD, EMA, Bollinger Bands).

    Args:
        ticker: Stock ticker symbol

    Returns:
        Technical indicators summary with trend analysis.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")

        if hist.empty or len(hist) < 20:
            return f"Insufficient price data for technical analysis of {ticker}"

        close = hist["Close"]

        # Simple Moving Averages
        sma_20 = close.rolling(window=20).mean().iloc[-1]
        sma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None
        ema_12 = close.ewm(span=12, adjust=False).mean().iloc[-1]
        ema_26 = close.ewm(span=26, adjust=False).mean().iloc[-1]

        # RSI (14-day)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rs = gain / loss if loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))

        # MACD
        macd_line = ema_12 - ema_26
        signal_line = close.ewm(span=9, adjust=False).mean().iloc[-1] - ema_26

        # Bollinger Bands
        bb_middle = sma_20
        bb_std = close.rolling(window=20).std().iloc[-1]
        bb_upper = bb_middle + 2 * bb_std
        bb_lower = bb_middle - 2 * bb_std

        current_price = close.iloc[-1]
        sma_50_str = f"{sma_50:.2f}" if sma_50 is not None else "N/A"

        indicators = f"""TECHNICAL ANALYSIS for {ticker}:
  Current Price: {current_price:.2f}
  SMA 20: {sma_20:.2f}
  SMA 50: {sma_50_str}
  EMA 12: {ema_12:.2f}
  RSI (14): {rsi:.2f}
  MACD Line: {macd_line:.2f}
  Bollinger Upper: {bb_upper:.2f}
  Bollinger Middle: {bb_middle:.2f}
  Bollinger Lower: {bb_lower:.2f}

  Trend: {"Bullish" if current_price > sma_20 else "Bearish"}
  RSI Signal: {"Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"}
  MACD Signal: {"Bullish" if macd_line > signal_line else "Bearish"}"""

        return indicators
    except Exception as e:
        logger.error("Failed to calculate technicals for %s: %s", ticker, e)
        return f"Error calculating technical indicators: {e}"


@tool
def get_support_resistance(ticker: str, lookback_days: int = 120) -> str:
    """Detect support and resistance levels using pivot point analysis.

    Uses local minima/maxima detection on closing prices to identify
    significant price levels where buying/selling pressure concentrates.

    Args:
        ticker: Stock ticker symbol
        lookback_days: Number of days to analyze (default 120)

    Returns:
        Support and resistance levels with current position analysis.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{lookback_days}d")

        if hist.empty or len(hist) < 20:
            return f"Insufficient price data for support/resistance analysis of {ticker}"

        close = hist["Close"].values
        dates = hist.index
        current_price = close[-1]

        # Find local minima and maxima using rolling window
        window = 5
        support_levels = []
        resistance_levels = []

        for i in range(window, len(close) - window):
            # Local minimum: price is lowest in surrounding window
            if close[i] == min(close[i - window : i + window + 1]):
                support_levels.append((close[i], dates[i]))
            # Local maximum: price is highest in surrounding window
            if close[i] == max(close[i - window : i + window + 1]):
                resistance_levels.append((close[i], dates[i]))

        # Cluster nearby levels (within 2% of each other)
        def cluster_levels(levels: list, threshold_pct: float = 0.02) -> list[float]:
            if not levels:
                return []
            sorted_prices = sorted([p for p, _ in levels])
            clusters = [[sorted_prices[0]]]
            for price in sorted_prices[1:]:
                if abs(price - clusters[-1][-1]) / clusters[-1][-1] < threshold_pct:
                    clusters[-1].append(price)
                else:
                    clusters.append([price])
            # Return average of each cluster, weighted by number of touches
            return [(np.mean(c), len(c)) for c in clusters]

        clustered_support = cluster_levels(support_levels)
        clustered_resistance = cluster_levels(resistance_levels)

        # Sort by proximity to current price
        clustered_support = sorted(
            [(p, t) for p, t in clustered_support if p < current_price],
            key=lambda x: current_price - x[0],
        )
        clustered_resistance = sorted(
            [(p, t) for p, t in clustered_resistance if p > current_price],
            key=lambda x: x[0] - current_price,
        )

        # Format output
        lines = [f"SUPPORT/RESISTANCE ANALYSIS for {ticker}:", f"  Current Price: {current_price:.2f}", ""]

        lines.append("  SUPPORT LEVELS (from nearest to farthest):")
        if clustered_support:
            for level, touches in clustered_support[:3]:
                dist_pct = ((current_price - level) / current_price) * 100
                lines.append(f"    ${level:.2f} ({touches} touches, {dist_pct:.1f}% below)")
        else:
            lines.append("    No significant support levels detected")

        lines.append("")
        lines.append("  RESISTANCE LEVELS (from nearest to farthest):")
        if clustered_resistance:
            for level, touches in clustered_resistance[:3]:
                dist_pct = ((level - current_price) / current_price) * 100
                lines.append(f"    ${level:.2f} ({touches} touches, {dist_pct:.1f}% above)")
        else:
            lines.append("    No significant resistance levels detected")

        # Position assessment
        lines.append("")
        if clustered_support and clustered_resistance:
            nearest_support = clustered_support[0][0]
            nearest_resistance = clustered_resistance[0][0]
            range_pct = ((nearest_resistance - nearest_support) / nearest_support) * 100
            position_in_range = ((current_price - nearest_support) / (nearest_resistance - nearest_support)) * 100
            lines.append(f"  Position in Range: {position_in_range:.1f}% between support and resistance")
            lines.append(f"  Range Width: {range_pct:.1f}%")
        elif clustered_support:
            lines.append("  Position: Above all detected resistance (breakout territory)")
        elif clustered_resistance:
            lines.append("  Position: Below all detected support (breakdown territory)")

        return "\n".join(lines)
    except Exception as e:
        logger.error("Failed to calculate support/resistance for %s: %s", ticker, e)
        return f"Error calculating support/resistance: {e}"


@tool
def get_volume_analysis(ticker: str, lookback_days: int = 60) -> str:
    """Analyze volume trends, OBV (On-Balance Volume), and volume-price divergence.

    Args:
        ticker: Stock ticker symbol
        lookback_days: Number of days to analyze (default 60)

    Returns:
        Volume analysis summary with trend confirmation signals.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{lookback_days}d")

        if hist.empty or len(hist) < 20:
            return f"Insufficient volume data for analysis of {ticker}"

        close = hist["Close"]
        volume = hist["Volume"]
        current_price = close.iloc[-1]

        # On-Balance Volume (OBV)
        obv = pd.Series(0.0, index=close.index)
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i - 1]

        # Volume moving averages
        vol_sma_20 = volume.rolling(window=20).mean().iloc[-1]
        vol_sma_50 = volume.rolling(window=50).mean().iloc[-1] if len(volume) >= 50 else None
        current_volume = volume.iloc[-1]
        avg_volume = volume.mean()

        # Volume trend (is volume increasing or decreasing?)
        recent_vol = volume.iloc[-10:].mean()
        older_vol = volume.iloc[-30:-10].mean() if len(volume) >= 30 else volume.iloc[:10].mean()
        vol_trend = "Increasing" if recent_vol > older_vol * 1.1 else "Decreasing" if recent_vol < older_vol * 0.9 else "Stable"

        # OBV trend
        obv_sma_20 = obv.rolling(window=20).mean().iloc[-1]
        obv_current = obv.iloc[-1]
        obv_trend = "Rising (accumulation)" if obv_current > obv_sma_20 else "Falling (distribution)"

        # Volume-price divergence detection
        price_direction = "up" if close.iloc[-1] > close.iloc[-10] else "down"
        vol_direction = "up" if recent_vol > older_vol else "down"

        if price_direction == "up" and vol_direction == "down":
            divergence = "BEARISH DIVERGENCE — Price rising on declining volume (weak move)"
        elif price_direction == "down" and vol_direction == "up":
            divergence = "BULLISH DIVERGENCE — Price falling on increasing volume (potential reversal)"
        elif price_direction == "up" and vol_direction == "up":
            divergence = "CONFIRMATION — Price and volume both rising (strong move)"
        else:
            divergence = "CONFIRMATION — Price and volume both declining (expected selling)"

        # Relative volume
        rel_volume = current_volume / avg_volume if avg_volume > 0 else 0

        vol_sma_50_str = f"{vol_sma_50:,.0f}" if vol_sma_50 is not None else "N/A"

        analysis = f"""VOLUME ANALYSIS for {ticker}:
  Current Price: {current_price:.2f}
  Current Volume: {current_volume:,.0f}
  Average Volume: {avg_volume:,.0f}
  Relative Volume: {rel_volume:.2f}x average

  Volume Trend (20-day): {vol_trend}
  OBV Current: {obv_current:,.0f}
  OBV Trend: {obv_trend}

  Volume SMA 20: {vol_sma_20:,.0f}
  Volume SMA 50: {vol_sma_50_str}

  Volume-Price Relationship: {divergence}"""

        return analysis
    except Exception as e:
        logger.error("Failed to analyze volume for %s: %s", ticker, e)
        return f"Error analyzing volume: {e}"


@tool
def get_trend_analysis(ticker: str, lookback_days: int = 120) -> str:
    """Analyze trend strength and direction using ADX and multi-timeframe analysis.

    Args:
        ticker: Stock ticker symbol
        lookback_days: Number of days to analyze (default 120)

    Returns:
        Trend analysis with ADX, direction, and strength assessment.
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{lookback_days}d")

        if hist.empty or len(hist) < 30:
            return f"Insufficient price data for trend analysis of {ticker}"

        close = hist["Close"]
        high = hist["High"]
        low = hist["Low"]
        current_price = close.iloc[-1]

        # ADX (Average Directional Index) calculation
        # True Range
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low

        plus_dm = pd.Series(0.0, index=close.index)
        minus_dm = pd.Series(0.0, index=close.index)

        plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
        minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

        # Smoothed averages (14-period)
        period = 14
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # ADX
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
        adx = dx.rolling(window=period).mean()

        current_adx = adx.iloc[-1]
        current_plus_di = plus_di.iloc[-1]
        current_minus_di = minus_di.iloc[-1]

        # Trend strength interpretation
        if current_adx > 50:
            strength = "Very Strong"
        elif current_adx > 25:
            strength = "Strong"
        elif current_adx > 20:
            strength = "Moderate"
        else:
            strength = "Weak/Ranging"

        # Trend direction
        if current_plus_di > current_minus_di:
            direction = "Uptrend (+DI > -DI)"
        else:
            direction = "Downtrend (-DI > +DI)"

        # Multi-timeframe trend (using different SMAs as proxies)
        sma_10 = close.rolling(window=10).mean().iloc[-1]
        sma_20 = close.rolling(window=20).mean().iloc[-1]
        sma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None
        sma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else None

        # Short-term trend (10 vs 20 day)
        short_trend = "Bullish" if sma_10 > sma_20 else "Bearish"

        # Medium-term trend (20 vs 50 day)
        if sma_50 is not None:
            medium_trend = "Bullish" if sma_20 > sma_50 else "Bearish"
        else:
            medium_trend = "N/A (insufficient data)"

        # Long-term trend (50 vs 200 day)
        if sma_200 is not None:
            long_trend = "Bullish" if sma_50 > sma_200 else "Bearish"
        else:
            long_trend = "N/A (insufficient data)"

        # Price position relative to SMAs
        above_count = 0
        smas = [sma_10, sma_20]
        if sma_50 is not None:
            smas.append(sma_50)
        if sma_200 is not None:
            smas.append(sma_200)

        for sma in smas:
            if current_price > sma:
                above_count += 1

        position = f"Above {above_count}/{len(smas)} key moving averages"

        sma_50_str = f"{sma_50:.2f}" if sma_50 is not None else "N/A"
        sma_200_str = f"{sma_200:.2f}" if sma_200 is not None else "N/A"

        analysis = f"""TREND ANALYSIS for {ticker}:
  Current Price: {current_price:.2f}

  ADX (14): {current_adx:.2f}
  +DI: {current_plus_di:.2f}
  -DI: {current_minus_di:.2f}
  Trend Strength: {strength}
  Trend Direction: {direction}

  Moving Averages:
    SMA 10: {sma_10:.2f}
    SMA 20: {sma_20:.2f}
    SMA 50: {sma_50_str}
    SMA 200: {sma_200_str}

  Multi-Timeframe Trend:
    Short-term (10/20): {short_trend}
    Medium-term (20/50): {medium_trend}
    Long-term (50/200): {long_trend}

  Price Position: {position}"""

        return analysis
    except Exception as e:
        logger.error("Failed to analyze trend for %s: %s", ticker, e)
        return f"Error analyzing trend: {e}"


ALL_TECHNICAL_TOOLS = [
    calculate_technical_indicators,
    get_support_resistance,
    get_volume_analysis,
    get_trend_analysis,
]
