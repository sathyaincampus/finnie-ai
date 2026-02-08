"""
Finnie AI — State Definition

TypedDict defining the shared state for the LangGraph workflow.
"""

from dataclasses import dataclass, field
from typing import Annotated, Any, Optional, TypedDict
from operator import add
from datetime import datetime


class AgentOutput(TypedDict):
    """Output from a single agent."""
    agent_name: str
    content: str
    data: Optional[dict]
    timestamp: str


class Visualization(TypedDict):
    """Chart or visualization to display."""
    type: str  # candlestick, line, pie, bar
    data: dict
    title: Optional[str]


class FinnieState(TypedDict, total=False):
    """
    Shared state for the Finnie AI LangGraph workflow.
    
    This state is passed between all nodes in the graph and accumulates
    information as agents process the request.
    
    Attributes:
        user_input: The original user message.
        session_id: Unique session identifier.
        llm_provider: Selected LLM provider (openai, anthropic, google).
        llm_model: Selected model identifier.
        llm_api_key: API key for the selected provider.
        
        intent: Parsed intent from user input.
        selected_agents: List of agents to activate.
        agent_outputs: Accumulated outputs from agents.
        
        market_data: Fetched market data (cached).
        portfolio_data: User's portfolio holdings.
        
        final_response: Formatted response to display.
        visualizations: Charts to render.
        disclaimers: Compliance disclaimers to append.
        
        error: Error message if something failed.
        metadata: Additional metadata for tracing.
    """
    
    # Input
    user_input: str
    session_id: str
    
    # LLM Configuration
    llm_provider: str
    llm_model: str
    llm_api_key: str
    
    # Intent & Routing
    intent: str
    intent_confidence: float
    selected_agents: list[str]
    
    # Agent Outputs (uses Annotated with add to merge lists)
    agent_outputs: Annotated[list[AgentOutput], add]
    
    # Data
    market_data: Optional[dict]
    portfolio_data: Optional[dict]
    
    # Output
    final_response: str
    visualizations: list[Visualization]
    disclaimers: list[str]
    
    # Error Handling
    error: Optional[str]
    
    # Metadata
    metadata: dict


def create_initial_state(
    user_input: str,
    session_id: str,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4o",
    llm_api_key: str = "",
    portfolio_data: Optional[dict] = None,
) -> FinnieState:
    """
    Create a new initial state for a Finnie workflow execution.
    
    Args:
        user_input: The user's message.
        session_id: Unique session ID.
        llm_provider: The LLM provider to use.
        llm_model: The model to use.
        llm_api_key: API key for the provider.
        portfolio_data: Optional user portfolio.
        
    Returns:
        A FinnieState ready for graph execution.
    """
    return FinnieState(
        user_input=user_input,
        session_id=session_id,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        intent="",
        intent_confidence=0.0,
        selected_agents=[],
        agent_outputs=[],
        market_data=None,
        portfolio_data=portfolio_data,
        final_response="",
        visualizations=[],
        disclaimers=[],
        error=None,
        metadata={
            "start_time": datetime.utcnow().isoformat(),
            "version": "1.0.0",
        },
    )


# =============================================================================
# Intent Types
# =============================================================================

class IntentType:
    """Known intent types for routing."""
    
    MARKET_DATA = "market_data"          # Stock prices, quotes
    EDUCATION = "education"               # Explain concepts
    NEWS = "news"                          # Market news, sentiment
    PORTFOLIO = "portfolio"                # Holdings, allocation
    PROJECTION = "projection"              # Investment projections
    TREND = "trend"                        # What's trending
    COMPARISON = "comparison"              # Compare stocks/assets
    GENERAL = "general"                    # General financial chat


# =============================================================================
# Agent Names
# =============================================================================

class AgentName:
    """Agent identifiers."""
    
    QUANT = "quant"           # Market data
    PROFESSOR = "professor"   # Education
    ANALYST = "analyst"       # News/research
    ADVISOR = "advisor"       # Portfolio
    GUARDIAN = "guardian"     # Compliance
    SCRIBE = "scribe"         # Formatting
    ORACLE = "oracle"         # Projections
    SCOUT = "scout"           # Trends


# Intent to Agent mapping
INTENT_AGENT_MAP: dict[str, list[str]] = {
    IntentType.MARKET_DATA: [AgentName.QUANT],
    IntentType.EDUCATION: [AgentName.PROFESSOR],
    IntentType.NEWS: [AgentName.ANALYST],
    IntentType.PORTFOLIO: [AgentName.ADVISOR, AgentName.QUANT],
    IntentType.PROJECTION: [AgentName.ORACLE, AgentName.QUANT],
    IntentType.TREND: [AgentName.SCOUT, AgentName.ANALYST],
    IntentType.COMPARISON: [AgentName.QUANT, AgentName.ANALYST],
    IntentType.GENERAL: [AgentName.PROFESSOR],
}
