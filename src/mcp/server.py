"""
Finnie AI — MCP Server

Model Context Protocol server providing unified tool discovery and execution.
Agents interact with external tools through this standardized interface.
"""

from __future__ import annotations

from typing import Any, Callable
from datetime import datetime


# =============================================================================
# Tool Registry
# =============================================================================


class MCPToolRegistry:
    """
    Central registry for MCP tools.
    
    Provides tool discovery, schema listing, and execution.
    Follows the MCP (Model Context Protocol) specification for
    standardized agent-tool interaction.
    """

    def __init__(self):
        self._tools: dict[str, dict] = {}
        self._handlers: dict[str, Callable] = {}

    def register(
        self,
        name: str,
        description: str,
        handler: Callable,
        input_schema: dict,
    ) -> None:
        """Register a tool with its schema and handler."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self._handlers[name] = handler

    def list_tools(self) -> list[dict]:
        """Return all registered tool definitions (MCP ListTools)."""
        return list(self._tools.values())

    def get_tool(self, name: str) -> dict | None:
        """Get a single tool definition by name."""
        return self._tools.get(name)

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute a tool by name (MCP CallTool).

        Args:
            name: Tool name to execute.
            arguments: Input arguments matching the tool's inputSchema.

        Returns:
            Tool execution result as a dict.
        """
        if name not in self._handlers:
            return {"error": f"Unknown tool: {name}", "available": list(self._tools.keys())}

        handler = self._handlers[name]
        args = arguments or {}

        try:
            result = handler(**args)
            return {
                "tool": name,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "success": "error" not in result,
            }
        except Exception as e:
            return {
                "tool": name,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat(),
            }

    @property
    def tool_count(self) -> int:
        return len(self._tools)


# =============================================================================
# Server Instance (Singleton)
# =============================================================================

_server: MCPToolRegistry | None = None


def get_mcp_server() -> MCPToolRegistry:
    """
    Get or create the global MCP server instance.
    
    Lazily registers all available tools on first call.
    """
    global _server
    if _server is not None:
        return _server

    _server = MCPToolRegistry()
    _register_all_tools(_server)
    return _server


def _register_all_tools(registry: MCPToolRegistry) -> None:
    """Register all tool implementations with the registry."""

    # ── Finance Tools ─────────────────────────────────────────────
    from src.mcp.tools.finance_tools import (
        FINANCE_TOOL_DEFINITIONS,
        get_stock_price,
        get_historical_data,
        get_company_info,
        get_sector_performance,
    )

    finance_handlers = {
        "get_stock_price": get_stock_price,
        "get_historical_data": get_historical_data,
        "get_company_info": get_company_info,
        "get_sector_performance": get_sector_performance,
    }

    for tool_def in FINANCE_TOOL_DEFINITIONS:
        name = tool_def["name"]
        registry.register(
            name=name,
            description=tool_def["description"],
            handler=finance_handlers[name],
            input_schema=tool_def["inputSchema"],
        )

    # ── Chart Tools ───────────────────────────────────────────────
    from src.mcp.tools.chart_tools import (
        CHART_TOOL_DEFINITIONS,
        create_price_chart,
        create_comparison_chart,
        create_sector_heatmap,
    )

    chart_handlers = {
        "create_price_chart": create_price_chart,
        "create_comparison_chart": create_comparison_chart,
        "create_sector_heatmap": create_sector_heatmap,
    }

    for tool_def in CHART_TOOL_DEFINITIONS:
        name = tool_def["name"]
        registry.register(
            name=name,
            description=tool_def["description"],
            handler=chart_handlers[name],
            input_schema=tool_def["inputSchema"],
        )


# =============================================================================
# Convenience functions
# =============================================================================


def call_tool(name: str, **kwargs) -> dict[str, Any]:
    """Shortcut to call an MCP tool."""
    return get_mcp_server().call_tool(name, kwargs)


def list_tools() -> list[dict]:
    """Shortcut to list all MCP tools."""
    return get_mcp_server().list_tools()


# =============================================================================
# MCP Server Info (Agent Card)
# =============================================================================

MCP_SERVER_INFO = {
    "name": "finnie-ai-tools",
    "version": "1.0.0",
    "description": "Finnie AI MCP Tool Server — Financial data, charts, and analysis tools",
    "capabilities": {
        "tools": True,
        "resources": False,
        "prompts": False,
    },
}
