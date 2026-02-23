"""
Finnie AI — MCP Tools Package

Provides tool discovery and execution for the MCP (Model Context Protocol) layer.
"""

from src.mcp.tools.finance_tools import (
    FINANCE_TOOL_DEFINITIONS,
    get_stock_price,
    get_historical_data,
    get_company_info,
    get_sector_performance,
)
from src.mcp.tools.chart_tools import (
    CHART_TOOL_DEFINITIONS,
    create_price_chart,
    create_comparison_chart,
    create_sector_heatmap,
)


# Name → function mapping
_TOOL_REGISTRY = {
    "get_stock_price": get_stock_price,
    "get_historical_data": get_historical_data,
    "get_company_info": get_company_info,
    "get_sector_performance": get_sector_performance,
    "create_price_chart": create_price_chart,
    "create_comparison_chart": create_comparison_chart,
    "create_sector_heatmap": create_sector_heatmap,
}


def get_available_tools() -> list[dict]:
    """Return all available MCP tool definitions."""
    return FINANCE_TOOL_DEFINITIONS + CHART_TOOL_DEFINITIONS


def execute_tool(tool_name: str, **kwargs) -> dict:
    """Execute a tool by name. Returns result dict or error."""
    func = _TOOL_REGISTRY.get(tool_name)
    if func is None:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return func(**kwargs)
    except Exception as e:
        return {"error": f"Tool '{tool_name}' failed: {e}"}
