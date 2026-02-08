"""
Finnie AI — MCP Finance Tools

Standardized finance data tools exposed via MCP protocol.
Wraps yfinance for stock data, company info, and historical prices.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import yfinance as yf


# =============================================================================
# Tool Definitions (MCP Schema)
# =============================================================================

FINANCE_TOOL_DEFINITIONS = [
    {
        "name": "get_stock_price",
        "description": "Get current stock price, daily change, and basic market metrics for a ticker.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., AAPL, MSFT, TSLA)",
                }
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_historical_data",
        "description": "Get historical OHLCV price data for charting and analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol",
                },
                "period": {
                    "type": "string",
                    "description": "Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max",
                    "default": "1y",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_company_info",
        "description": "Get detailed company information including sector, industry, description, and key financials.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol",
                }
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_sector_performance",
        "description": "Get performance data for major market sectors using sector ETFs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Time period for performance calculation: 1d, 5d, 1mo, 3mo, 6mo, 1y",
                    "default": "1mo",
                }
            },
        },
    },
]


# =============================================================================
# Tool Implementations
# =============================================================================


def get_stock_price(ticker: str) -> dict[str, Any]:
    """
    Get current stock price and basic market metrics.

    Returns:
        Dict with price, change, market cap, PE ratio, 52-week range.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        if not info or not info.get("shortName"):
            return {"error": f"Ticker '{ticker}' not found", "ticker": ticker}

        price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose", 0)
        prev_close = info.get("previousClose", price)
        change = price - prev_close if price and prev_close else 0
        change_pct = (change / prev_close * 100) if prev_close else 0

        return {
            "ticker": ticker.upper(),
            "name": info.get("shortName", ticker),
            "price": round(price, 2) if price else 0,
            "previous_close": round(prev_close, 2) if prev_close else 0,
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("forwardPE") or info.get("trailingPE"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "volume": info.get("regularMarketVolume"),
            "avg_volume": info.get("averageVolume"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_historical_data(ticker: str, period: str = "1y") -> dict[str, Any]:
    """
    Get historical price data (OHLCV) for a ticker.

    Returns:
        Dict with dates, open, high, low, close, volume arrays.
    """
    valid_periods = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"}
    if period not in valid_periods:
        period = "1y"

    try:
        stock = yf.Ticker(ticker.upper())
        history = stock.history(period=period)

        if history.empty:
            return {"error": f"No historical data for '{ticker}'", "ticker": ticker}

        return {
            "ticker": ticker.upper(),
            "period": period,
            "data_points": len(history),
            "dates": history.index.strftime("%Y-%m-%d").tolist(),
            "open": [round(v, 2) for v in history["Open"].tolist()],
            "high": [round(v, 2) for v in history["High"].tolist()],
            "low": [round(v, 2) for v in history["Low"].tolist()],
            "close": [round(v, 2) for v in history["Close"].tolist()],
            "volume": history["Volume"].tolist(),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_company_info(ticker: str) -> dict[str, Any]:
    """
    Get detailed company information.

    Returns:
        Dict with company name, sector, industry, description, employees, financials.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        if not info or not info.get("shortName"):
            return {"error": f"Company info not found for '{ticker}'", "ticker": ticker}

        return {
            "ticker": ticker.upper(),
            "name": info.get("shortName", ticker),
            "long_name": info.get("longName", ""),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "country": info.get("country", "N/A"),
            "website": info.get("website", ""),
            "description": info.get("longBusinessSummary", "")[:500],
            "employees": info.get("fullTimeEmployees"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
            "revenue": info.get("totalRevenue"),
            "net_income": info.get("netIncomeToCommon"),
            "profit_margin": info.get("profitMargins"),
            "roe": info.get("returnOnEquity"),
            "debt_to_equity": info.get("debtToEquity"),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


def get_sector_performance(period: str = "1mo") -> dict[str, Any]:
    """
    Get sector performance using sector ETFs.

    Returns:
        Dict with sector names and their performance over the period.
    """
    sector_etfs = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Consumer Discretionary": "XLY",
        "Communication Services": "XLC",
        "Industrials": "XLI",
        "Consumer Staples": "XLP",
        "Energy": "XLE",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Materials": "XLB",
    }

    results = {}
    for sector, etf in sector_etfs.items():
        try:
            stock = yf.Ticker(etf)
            hist = stock.history(period=period)
            if not hist.empty and len(hist) >= 2:
                start_price = hist["Close"].iloc[0]
                end_price = hist["Close"].iloc[-1]
                change_pct = ((end_price - start_price) / start_price) * 100
                results[sector] = {
                    "etf": etf,
                    "change_percent": round(change_pct, 2),
                    "start_price": round(start_price, 2),
                    "end_price": round(end_price, 2),
                }
        except Exception:
            continue

    # Sort by performance
    sorted_sectors = dict(
        sorted(results.items(), key=lambda x: x[1]["change_percent"], reverse=True)
    )

    return {
        "period": period,
        "sectors": sorted_sectors,
        "top_performer": next(iter(sorted_sectors), None),
        "worst_performer": list(sorted_sectors.keys())[-1] if sorted_sectors else None,
        "timestamp": datetime.now().isoformat(),
    }
