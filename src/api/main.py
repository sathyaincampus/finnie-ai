"""
Finnie AI — FastAPI Application

REST API + WebSocket for the Finnie AI multi-agent system.
Connects to LangGraph orchestration and MCP tool servers.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# =============================================================================
# Pydantic Models
# =============================================================================


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    message: str = Field(..., description="User message", min_length=1, max_length=5000)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    llm_provider: str = Field(default="openai", description="LLM provider: openai, anthropic, google")
    llm_model: str = Field(default="gpt-4o", description="Model name")
    llm_api_key: str = Field(default="", description="API key for the provider")
    portfolio_data: Optional[dict] = None


class ChatResponse(BaseModel):
    """Response body for the chat endpoint."""
    response: str
    session_id: str
    agent_used: Optional[str] = None
    visualizations: list[dict] = []
    disclaimers: list[str] = []
    latency_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class MarketDataResponse(BaseModel):
    """Response for market data endpoint."""
    ticker: str
    data: dict
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "2.0.0"
    agents: int = 8
    mcp_tools: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ToolListResponse(BaseModel):
    """Response for listing MCP tools."""
    tools: list[dict]
    count: int


class ToolCallRequest(BaseModel):
    """Request to call an MCP tool."""
    tool_name: str
    arguments: dict = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    """Response from calling an MCP tool."""
    tool: str
    result: dict
    success: bool
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# App Factory
# =============================================================================


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Finnie AI",
        description="Autonomous Financial Intelligence — Multi-Agent API",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # CORS (allow Streamlit frontend)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_routes(app)
    return app


# =============================================================================
# Route Registration
# =============================================================================


def _register_routes(app: FastAPI) -> None:
    """Register all API routes."""

    # ── Health ────────────────────────────────────────────────────

    @app.get("/api/health", response_model=HealthResponse, tags=["System"])
    async def health_check():
        """Health check endpoint."""
        from src.mcp.server import get_mcp_server
        server = get_mcp_server()
        return HealthResponse(mcp_tools=server.tool_count)

    # ── Chat ─────────────────────────────────────────────────────

    @app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
    async def chat(request: ChatRequest):
        """
        Process a user message through the LangGraph multi-agent system.
        
        Routes to the appropriate agent(s) based on intent parsing.
        """
        import time
        start = time.time()

        try:
            from src.orchestration.graph import run_finnie

            result = await run_finnie(
                user_input=request.message,
                session_id=request.session_id,
                llm_provider=request.llm_provider,
                llm_model=request.llm_model,
                llm_api_key=request.llm_api_key,
                portfolio_data=request.portfolio_data,
            )

            latency = int((time.time() - start) * 1000)

            return ChatResponse(
                response=result.get("final_response", "I couldn't process that request."),
                session_id=request.session_id,
                agent_used=result.get("primary_agent"),
                visualizations=result.get("visualizations", []),
                disclaimers=result.get("disclaimers", []),
                latency_ms=latency,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent processing error: {str(e)}")

    # ── Market Data ──────────────────────────────────────────────

    @app.get("/api/market/{ticker}", response_model=MarketDataResponse, tags=["Market"])
    async def get_market_data(ticker: str):
        """Get current market data for a stock ticker."""
        from src.mcp.server import call_tool

        result = call_tool("get_stock_price", ticker=ticker.upper())
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=f"Data not found for {ticker}")

        return MarketDataResponse(
            ticker=ticker.upper(),
            data=result["result"],
        )

    @app.get("/api/market/{ticker}/history", tags=["Market"])
    async def get_market_history(ticker: str, period: str = "1y"):
        """Get historical price data for a stock ticker."""
        from src.mcp.server import call_tool

        result = call_tool("get_historical_data", ticker=ticker.upper(), period=period)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=f"History not found for {ticker}")

        return result["result"]

    @app.get("/api/market/{ticker}/info", tags=["Market"])
    async def get_company_info(ticker: str):
        """Get detailed company information."""
        from src.mcp.server import call_tool

        result = call_tool("get_company_info", ticker=ticker.upper())
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=f"Company not found: {ticker}")

        return result["result"]

    # ── Sectors ──────────────────────────────────────────────────

    @app.get("/api/sectors", tags=["Market"])
    async def get_sectors(period: str = "1mo"):
        """Get sector performance data."""
        from src.mcp.server import call_tool

        result = call_tool("get_sector_performance", period=period)
        return result.get("result", {})

    # ── MCP Tools ────────────────────────────────────────────────

    @app.get("/api/tools", response_model=ToolListResponse, tags=["MCP"])
    async def list_mcp_tools():
        """List all available MCP tools (tool discovery)."""
        from src.mcp.server import list_tools

        tools = list_tools()
        return ToolListResponse(tools=tools, count=len(tools))

    @app.post("/api/tools/call", response_model=ToolCallResponse, tags=["MCP"])
    async def call_mcp_tool(request: ToolCallRequest):
        """Execute an MCP tool by name."""
        from src.mcp.server import call_tool

        result = call_tool(request.tool_name, **request.arguments)
        return ToolCallResponse(
            tool=request.tool_name,
            result=result.get("result", result),
            success=result.get("success", False),
        )

    # ── WebSocket (Streaming) ────────────────────────────────────

    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket):
        """
        WebSocket endpoint for streaming chat responses.
        
        Client sends JSON: {"message": "...", "session_id": "...", ...}
        Server streams JSON: {"type": "token"|"done"|"error", "content": "..."}
        """
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_json()
                message = data.get("message", "")
                if not message:
                    await websocket.send_json({"type": "error", "content": "Empty message"})
                    continue

                # Stream thinking indicator
                await websocket.send_json({"type": "status", "content": "Processing..."})

                try:
                    from src.orchestration.graph import run_finnie

                    result = await run_finnie(
                        user_input=message,
                        session_id=data.get("session_id", str(uuid.uuid4())),
                        llm_provider=data.get("llm_provider", "openai"),
                        llm_model=data.get("llm_model", "gpt-4o"),
                        llm_api_key=data.get("llm_api_key", ""),
                    )

                    response = result.get("final_response", "")

                    # Simulate token streaming
                    words = response.split()
                    for i in range(0, len(words), 3):
                        chunk = " ".join(words[i:i + 3])
                        await websocket.send_json({"type": "token", "content": chunk + " "})
                        await asyncio.sleep(0.05)

                    await websocket.send_json({
                        "type": "done",
                        "content": response,
                        "agent": result.get("primary_agent"),
                    })
                except Exception as e:
                    await websocket.send_json({"type": "error", "content": str(e)})

        except WebSocketDisconnect:
            pass


# =============================================================================
# App Instance
# =============================================================================

app = create_app()
