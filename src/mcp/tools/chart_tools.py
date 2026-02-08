"""
Finnie AI — MCP Chart Tools

Standardized chart-generation tools exposed via MCP protocol.
Produces Plotly chart specifications for the UI to render.
"""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go


# =============================================================================
# Tool Definitions (MCP Schema)
# =============================================================================

CHART_TOOL_DEFINITIONS = [
    {
        "name": "create_price_chart",
        "description": "Create an interactive price chart (candlestick or line) for a stock ticker.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol",
                },
                "period": {
                    "type": "string",
                    "description": "Time period: 1mo, 3mo, 6mo, 1y, 2y, 5y",
                    "default": "6mo",
                },
                "chart_type": {
                    "type": "string",
                    "description": "Chart type: candlestick or line",
                    "default": "line",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "create_comparison_chart",
        "description": "Create a normalized comparison chart for multiple tickers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of ticker symbols to compare",
                },
                "period": {
                    "type": "string",
                    "description": "Time period for comparison",
                    "default": "1y",
                },
            },
            "required": ["tickers"],
        },
    },
    {
        "name": "create_sector_heatmap",
        "description": "Create a heatmap showing sector performance.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Time period",
                    "default": "1mo",
                },
            },
        },
    },
]


# =============================================================================
# Tool Implementations
# =============================================================================


def create_price_chart(
    ticker: str,
    period: str = "6mo",
    chart_type: str = "line",
) -> dict[str, Any]:
    """
    Create an interactive stock price chart.

    Returns:
        Dict with chart type, Plotly figure JSON, and metadata.
    """
    from src.mcp.tools.finance_tools import get_historical_data

    data = get_historical_data(ticker, period)
    if "error" in data:
        return data

    dates = data["dates"]
    template = "plotly_dark"

    if chart_type == "candlestick":
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=dates,
                    open=data["open"],
                    high=data["high"],
                    low=data["low"],
                    close=data["close"],
                    name=ticker.upper(),
                )
            ]
        )
    else:
        fig = go.Figure(
            data=[
                go.Scatter(
                    x=dates,
                    y=data["close"],
                    mode="lines",
                    name=ticker.upper(),
                    line=dict(color="#667eea", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(102, 126, 234, 0.1)",
                )
            ]
        )

    fig.update_layout(
        title=f"{ticker.upper()} — {period} Price Chart",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template=template,
        height=400,
        margin=dict(l=40, r=20, t=50, b=40),
        showlegend=False,
    )

    return {
        "chart_type": "plotly",
        "ticker": ticker.upper(),
        "period": period,
        "figure_json": fig.to_json(),
        "data_points": len(dates),
    }


def create_comparison_chart(
    tickers: list[str],
    period: str = "1y",
) -> dict[str, Any]:
    """
    Create a normalized comparison chart (rebased to 100).

    Returns:
        Dict with Plotly figure JSON comparing multiple tickers.
    """
    from src.mcp.tools.finance_tools import get_historical_data

    colors = [
        "#667eea", "#764ba2", "#f093fb", "#00d2ff",
        "#43e97b", "#f5576c", "#fda085", "#96e6a1",
    ]

    fig = go.Figure()
    valid_tickers = []

    for i, ticker in enumerate(tickers[:8]):  # Max 8 tickers
        data = get_historical_data(ticker, period)
        if "error" in data:
            continue

        closes = data["close"]
        if not closes or closes[0] == 0:
            continue

        # Normalize to base 100
        base = closes[0]
        normalized = [(c / base) * 100 for c in closes]

        fig.add_trace(
            go.Scatter(
                x=data["dates"],
                y=normalized,
                mode="lines",
                name=ticker.upper(),
                line=dict(color=colors[i % len(colors)], width=2),
            )
        )
        valid_tickers.append(ticker.upper())

    if not valid_tickers:
        return {"error": "No valid data found for any ticker"}

    fig.update_layout(
        title=f"Performance Comparison — {', '.join(valid_tickers)} ({period})",
        xaxis_title="Date",
        yaxis_title="Normalized Price (base = 100)",
        template="plotly_dark",
        height=400,
        margin=dict(l=40, r=20, t=50, b=40),
        hovermode="x unified",
    )

    # Add 100-line reference
    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color="rgba(255,255,255,0.3)",
        annotation_text="Starting Value",
    )

    return {
        "chart_type": "plotly",
        "tickers": valid_tickers,
        "period": period,
        "figure_json": fig.to_json(),
    }


def create_sector_heatmap(period: str = "1mo") -> dict[str, Any]:
    """
    Create a sector performance heatmap.

    Returns:
        Dict with Plotly figure JSON showing sector performance.
    """
    from src.mcp.tools.finance_tools import get_sector_performance

    perf = get_sector_performance(period)
    if not perf.get("sectors"):
        return {"error": "Could not fetch sector data"}

    sectors = list(perf["sectors"].keys())
    changes = [perf["sectors"][s]["change_percent"] for s in sectors]

    # Color based on performance
    colors = ["#e74c3c" if c < 0 else "#2ecc71" for c in changes]

    fig = go.Figure(
        data=[
            go.Bar(
                x=changes,
                y=sectors,
                orientation="h",
                marker=dict(color=colors),
                text=[f"{c:+.1f}%" for c in changes],
                textposition="outside",
            )
        ]
    )

    fig.update_layout(
        title=f"Sector Performance — {period}",
        xaxis_title="Change (%)",
        template="plotly_dark",
        height=450,
        margin=dict(l=150, r=60, t=50, b=40),
    )

    return {
        "chart_type": "plotly",
        "period": period,
        "figure_json": fig.to_json(),
        "sectors": perf["sectors"],
    }
