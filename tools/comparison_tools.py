"""Comparison tools — side-by-side analysis of two companies."""

import logging

import yfinance as yf
from langchain.tools import tool

logger = logging.getLogger(__name__)


@tool
def compare_financials(ticker_a: str, ticker_b: str) -> str:
    """Compare financial metrics side-by-side for two companies.

    Args:
        ticker_a: First stock ticker symbol
        ticker_b: Second stock ticker symbol

    Returns:
        Side-by-side comparison of key financial metrics.
    """
    try:
        stock_a = yf.Ticker(ticker_a)
        stock_b = yf.Ticker(ticker_b)

        info_a = stock_a.info
        info_b = stock_b.info

        metrics = {
            "Market Cap": ("marketCap", "marketCap"),
            "Trailing PE": ("trailingPE", "trailingPE"),
            "Forward PE": ("forwardPE", "forwardPE"),
            "Price to Book": ("priceToBook", "priceToBook"),
            "Price to Sales": ("priceToSalesTrailing12Months", "priceToSalesTrailing12Months"),
            "EV/EBITDA": ("enterpriseToEbitda", "enterpriseToEbitda"),
            "ROE": ("returnOnEquity", "returnOnEquity"),
            "ROA": ("returnOnAssets", "returnOnAssets"),
            "Profit Margin": ("profitMargins", "profitMargins"),
            "Operating Margin": ("operatingMargins", "operatingMargins"),
            "Revenue Growth": ("revenueGrowth", "revenueGrowth"),
            "Earnings Growth": ("earningsGrowth", "earningsGrowth"),
            "Debt to Equity": ("debtToEquity", "debtToEquity"),
            "Current Ratio": ("currentRatio", "currentRatio"),
            "Dividend Yield": ("dividendYield", "dividendYield"),
            "Beta": ("beta", "beta"),
            "52W High": ("fiftyTwoWeekHigh", "fiftyTwoWeekHigh"),
            "52W Low": ("fiftyTwoWeekLow", "fiftyTwoWeekLow"),
        }

        def fmt_val(v):
            if v is None or v == "N/A":
                return "N/A"
            if isinstance(v, float):
                if abs(v) > 1_000_000_000:
                    return f"${v / 1_000_000_000:.2f}B"
                if abs(v) > 1_000_000:
                    return f"${v / 1_000_000:.2f}M"
                if abs(v) < 1:
                    return f"{v * 100:.2f}%"
                return f"{v:.2f}"
            return str(v)

        def winner(key, val_a, val_b):
            """Determine which company has the better metric."""
            if val_a is None or val_b is None:
                return ""
            try:
                a = float(val_a)
                b = float(val_b)
            except (TypeError, ValueError):
                return ""

            # Lower is better for these metrics
            lower_better = {"Debt to Equity", "Trailing PE", "Forward PE", "Price to Book", "Price to Sales", "EV/EBITDA", "Beta"}
            # Higher is better for these
            higher_better = {"ROE", "ROA", "Profit Margin", "Operating Margin", "Revenue Growth", "Earnings Growth", "Dividend Yield", "Market Cap"}

            if key in lower_better:
                if a < b:
                    return f" <-- {ticker_a} better"
                elif b < a:
                    return f" <-- {ticker_b} better"
            elif key in higher_better:
                if a > b:
                    return f" <-- {ticker_a} better"
                elif b > a:
                    return f" <-- {ticker_b} better"
            return ""

        lines = [f"FINANCIAL COMPARISON: {ticker_a} vs {ticker_b}", "=" * 60, ""]

        header = f"{'Metric':<25} {'Value':>15}  {'Winner':>15}"
        lines.append(header)
        lines.append("-" * 60)

        for label, (key_a, key_b) in metrics.items():
            val_a = info_a.get(key_a)
            val_b = info_b.get(key_b)
            win = winner(label, val_a, val_b)
            lines.append(f"{label:<25} {fmt_val(val_a):>15}  {fmt_val(val_b):>15}{win}")

        # Summary
        lines.append("")
        lines.append("=" * 60)

        name_a = info_a.get("shortName", ticker_a)
        name_b = info_b.get("shortName", ticker_b)

        lines.append(f"\n{ticker_a} ({name_a}):")
        lines.append(f"  Sector: {info_a.get('sector', 'N/A')}")
        lines.append(f"  Industry: {info_a.get('industry', 'N/A')}")

        lines.append(f"\n{ticker_b} ({name_b}):")
        lines.append(f"  Sector: {info_b.get('sector', 'N/A')}")
        lines.append(f"  Industry: {info_b.get('industry', 'N/A')}")

        return "\n".join(lines)
    except Exception as e:
        logger.error("Failed to compare financials %s vs %s: %s", ticker_a, ticker_b, e)
        return f"Error comparing financials: {e}"


@tool
def compare_technicals(ticker_a: str, ticker_b: str) -> str:
    """Compare technical indicators side-by-side for two companies.

    Args:
        ticker_a: First stock ticker symbol
        ticker_b: Second stock ticker symbol

    Returns:
        Side-by-side comparison of technical indicators.
    """
    try:
        results = {}
        for ticker in [ticker_a, ticker_b]:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")

            if hist.empty or len(hist) < 20:
                results[ticker] = {"error": f"Insufficient data for {ticker}"}
                continue

            close = hist["Close"]
            current_price = close.iloc[-1]

            # RSI
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
            rs = gain / loss if loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))

            # MACD
            ema_12 = close.ewm(span=12, adjust=False).mean()
            ema_26 = close.ewm(span=26, adjust=False).mean()
            macd_line = (ema_12 - ema_26).iloc[-1]
            signal_line = close.ewm(span=9, adjust=False).mean().iloc[-1] - ema_26.iloc[-1]

            # Moving averages
            sma_20 = close.rolling(window=20).mean().iloc[-1]
            sma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None

            # Volatility (20-day)
            volatility = close.pct_change().rolling(window=20).std().iloc[-1] * (252 ** 0.5) * 100

            # 52-week position
            high_52w = hist["High"].max()
            low_52w = hist["Low"].min()
            position_52w = ((current_price - low_52w) / (high_52w - low_52w)) * 100 if high_52w != low_52w else 50

            # Period return
            period_return = ((current_price / close.iloc[0]) - 1) * 100

            results[ticker] = {
                "current_price": current_price,
                "rsi": rsi,
                "macd_line": macd_line,
                "signal_line": signal_line,
                "macd_signal": "Bullish" if macd_line > signal_line else "Bearish",
                "sma_20": sma_20,
                "sma_50": sma_50,
                "trend": "Bullish" if current_price > sma_20 else "Bearish",
                "volatility": volatility,
                "position_52w": position_52w,
                "period_return": period_return,
                "rsi_signal": "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral",
            }

        if "error" in results.get(ticker_a, {}) or "error" in results.get(ticker_b, {}):
            error_msgs = []
            for t in [ticker_a, ticker_b]:
                if "error" in results.get(t, {}):
                    error_msgs.append(results[t]["error"])
            return "; ".join(error_msgs)

        a = results[ticker_a]
        b = results[ticker_b]

        def fmt(v, suffix="", decimals=2):
            if v is None:
                return "N/A"
            return f"{v:.{decimals}f}{suffix}"

        def compare_val(label, val_a, val_b, higher_better=True):
            if val_a is None or val_b is None:
                return ""
            if higher_better:
                if val_a > val_b:
                    return f" <-- {ticker_a} stronger"
                elif val_b > val_a:
                    return f" <-- {ticker_b} stronger"
            else:
                if val_a < val_b:
                    return f" <-- {ticker_a} stronger"
                elif val_b < val_a:
                    return f" <-- {ticker_b} stronger"
            return ""

        lines = [f"TECHNICAL COMPARISON: {ticker_a} vs {ticker_b}", "=" * 60, ""]

        header = f"{'Indicator':<25} {ticker_a:>12}  {ticker_b:>12}"
        lines.append(header)
        lines.append("-" * 60)

        rows = [
            ("Current Price", fmt(a["current_price"]), fmt(b["current_price"])),
            ("RSI (14)", fmt(a["rsi"]), fmt(b["rsi"])),
            ("RSI Signal", a["rsi_signal"], b["rsi_signal"]),
            ("MACD Line", fmt(a["macd_line"]), fmt(b["macd_line"])),
            ("MACD Signal", a["macd_signal"], b["macd_signal"]),
            ("Trend (vs SMA20)", a["trend"], b["trend"]),
            ("Volatility (Ann.)", fmt(a["volatility"], "%"), fmt(b["volatility"], "%")),
            ("52W Position", fmt(a["position_52w"], "%"), fmt(b["position_52w"], "%")),
            ("Period Return", fmt(a["period_return"], "%"), fmt(b["period_return"], "%")),
        ]

        for label, val_a, val_b in rows:
            lines.append(f"{label:<25} {val_a:>12}  {val_b:>12}")

        # Momentum comparison
        lines.append("")
        lines.append("=" * 60)
        lines.append("MOMENTUM COMPARISON:")

        a_momentum_score = 0
        b_momentum_score = 0

        # RSI scoring
        if a["rsi"] > b["rsi"]:
            a_momentum_score += 1
        else:
            b_momentum_score += 1

        # MACD scoring
        if a["macd_signal"] == "Bullish":
            a_momentum_score += 1
        if b["macd_signal"] == "Bullish":
            b_momentum_score += 1

        # Trend scoring
        if a["trend"] == "Bullish":
            a_momentum_score += 1
        if b["trend"] == "Bullish":
            b_momentum_score += 1

        # Return scoring
        if a["period_return"] > b["period_return"]:
            a_momentum_score += 1
        else:
            b_momentum_score += 1

        lines.append(f"  {ticker_a} momentum score: {a_momentum_score}/4")
        lines.append(f"  {ticker_b} momentum score: {b_momentum_score}/4")

        if a_momentum_score > b_momentum_score:
            lines.append(f"  Winner: {ticker_a} (stronger momentum)")
        elif b_momentum_score > a_momentum_score:
            lines.append(f"  Winner: {ticker_b} (stronger momentum)")
        else:
            lines.append("  Tie (similar momentum)")

        return "\n".join(lines)
    except Exception as e:
        logger.error("Failed to compare technicals %s vs %s: %s", ticker_a, ticker_b, e)
        return f"Error comparing technicals: {e}"


@tool
def compare_valuation(ticker_a: str, ticker_b: str) -> str:
    """Compare relative valuation metrics between two companies.

    Args:
        ticker_a: First stock ticker symbol
        ticker_b: Second stock ticker symbol

    Returns:
        Relative valuation comparison with PEG, EV/EBITDA, and price-to-sales.
    """
    try:
        stock_a = yf.Ticker(ticker_a)
        stock_b = yf.Ticker(ticker_b)

        info_a = stock_a.info
        info_b = stock_b.info

        def safe_get(info, key):
            v = info.get(key)
            if v is None or v == "N/A":
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        # Core valuation metrics
        pe_a = safe_get(info_a, "trailingPE")
        pe_b = safe_get(info_b, "trailingPE")
        fwd_pe_a = safe_get(info_a, "forwardPE")
        fwd_pe_b = safe_get(info_b, "forwardPE")
        pb_a = safe_get(info_a, "priceToBook")
        pb_b = safe_get(info_b, "priceToBook")
        ps_a = safe_get(info_a, "priceToSalesTrailing12Months")
        ps_b = safe_get(info_b, "priceToSalesTrailing12Months")
        ev_ebitda_a = safe_get(info_a, "enterpriseToEbitda")
        ev_ebitda_b = safe_get(info_b, "enterpriseToEbitda")

        # Growth for PEG
        growth_a = safe_get(info_a, "earningsGrowth")
        growth_b = safe_get(info_b, "earningsGrowth")

        # PEG Ratio (Price/Earnings to Growth)
        peg_a = (pe_a / (growth_a * 100)) if (pe_a and growth_a and growth_a > 0) else None
        peg_b = (pe_b / (growth_b * 100)) if (pe_b and growth_b and growth_b > 0) else None

        def fmt(v, decimals=2):
            if v is None:
                return "N/A"
            return f"{v:.{decimals}f}x"

        def fmt_peg(v):
            if v is None:
                return "N/A"
            return f"{v:.2f}"

        def winner(label, val_a, val_b, lower_better=True):
            if val_a is None or val_b is None:
                return ""
            if lower_better:
                if val_a < val_b:
                    return f" <-- {ticker_a} cheaper"
                elif val_b < val_a:
                    return f" <-- {ticker_b} cheaper"
            else:
                if val_a > val_b:
                    return f" <-- {ticker_a} better"
                elif val_b > val_a:
                    return f" <-- {ticker_b} better"
            return ""

        lines = [f"RELATIVE VALUATION: {ticker_a} vs {ticker_b}", "=" * 60, ""]

        header = f"{'Metric':<25} {ticker_a:>12}  {ticker_b:>12}"
        lines.append(header)
        lines.append("-" * 60)

        rows = [
            ("Trailing PE", fmt(pe_a), fmt(pe_b), True),
            ("Forward PE", fmt(fwd_pe_a), fmt(fwd_pe_b), True),
            ("PEG Ratio", fmt_peg(peg_a), fmt_peg(peg_b), True),
            ("Price to Book", fmt(pb_a), fmt(pb_b), True),
            ("Price to Sales", fmt(ps_a), fmt(ps_b), True),
            ("EV/EBITDA", fmt(ev_ebitda_a), fmt(ev_ebitda_b), True),
        ]

        for label, val_a, val_b, lower_better in rows:
            win = winner(label, float(val_a.rstrip("x")) if val_a != "N/A" else None,
                         float(val_b.rstrip("x")) if val_b != "N/A" else None, lower_better)
            lines.append(f"{label:<25} {val_a:>12}  {val_b:>12}{win}")

        # Valuation summary
        lines.append("")
        lines.append("=" * 60)
        lines.append("VALUATION ASSESSMENT:")

        cheaper_count = 0
        total_comparable = 0

        metrics_for_summary = [
            (pe_a, pe_b), (fwd_pe_a, fwd_pe_b), (pb_a, pb_b),
            (ps_a, ps_b), (ev_ebitda_a, ev_ebitda_b),
        ]

        for va, vb in metrics_for_summary:
            if va is not None and vb is not None:
                total_comparable += 1
                if va < vb:
                    cheaper_count += 1
                elif vb < va:
                    cheaper_count -= 1

        if total_comparable > 0:
            if cheaper_count > 0:
                lines.append(f"  {ticker_a} appears more attractively valued on {cheaper_count}/{total_comparable} metrics")
            elif cheaper_count < 0:
                lines.append(f"  {ticker_b} appears more attractively valued on {abs(cheaper_count)}/{total_comparable} metrics")
            else:
                lines.append("  Both companies appear similarly valued")

        # PEG interpretation
        lines.append("")
        lines.append("PEG RATIO INTERPRETATION:")
        if peg_a is not None:
            if peg_a < 1:
                lines.append(f"  {ticker_a}: PEG {peg_a:.2f} — Potentially undervalued relative to growth")
            elif peg_a < 2:
                lines.append(f"  {ticker_a}: PEG {peg_a:.2f} — Fairly valued")
            else:
                lines.append(f"  {ticker_a}: PEG {peg_a:.2f} — Potentially overvalued relative to growth")
        else:
            lines.append(f"  {ticker_a}: PEG N/A (insufficient growth data)")

        if peg_b is not None:
            if peg_b < 1:
                lines.append(f"  {ticker_b}: PEG {peg_b:.2f} — Potentially undervalued relative to growth")
            elif peg_b < 2:
                lines.append(f"  {ticker_b}: PEG {peg_b:.2f} — Fairly valued")
            else:
                lines.append(f"  {ticker_b}: PEG {peg_b:.2f} — Potentially overvalued relative to growth")
        else:
            lines.append(f"  {ticker_b}: PEG N/A (insufficient growth data)")

        return "\n".join(lines)
    except Exception as e:
        logger.error("Failed to compare valuation %s vs %s: %s", ticker_a, ticker_b, e)
        return f"Error comparing valuation: {e}"


ALL_COMPARISON_TOOLS = [
    compare_financials,
    compare_technicals,
    compare_valuation,
]
