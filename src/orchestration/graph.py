"""
Finnie AI — LangGraph Definition

StateGraph construction for the multi-agent workflow.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from src.orchestration.state import FinnieState, AgentName
from src.orchestration.nodes import (
    parse_intent,
    execute_quant,
    execute_professor,
    execute_analyst,
    execute_advisor,
    execute_oracle,
    execute_scout,
    execute_guardian,
    execute_scribe,
    aggregate_responses,
)


def create_finnie_graph() -> StateGraph:
    """
    Create the Finnie AI LangGraph workflow.
    
    The workflow follows this pattern:
    1. Parse intent from user input
    2. Route to appropriate domain agents (parallel)
    3. Guardian checks compliance
    4. Scribe formats final response
    5. Aggregate and return
    
    ```
    START
      │
      ▼
    parse_intent
      │
      ├─────────────────────────────────────┐
      ▼         ▼         ▼         ▼       ▼
    quant  professor  analyst  advisor  oracle/scout
      │         │         │         │       │
      └─────────┴─────────┴─────────┴───────┘
                          │
                          ▼
                      guardian
                          │
                          ▼
                       scribe
                          │
                          ▼
                    aggregate
                          │
                          ▼
                        END
    ```
    
    Returns:
        Compiled StateGraph ready for execution.
    """
    # Create the graph with our state type
    workflow = StateGraph(FinnieState)
    
    # ==========================================================================
    # Add nodes
    # ==========================================================================
    
    # Entry node - parse user intent
    workflow.add_node("parse_intent", parse_intent)
    
    # Domain agent nodes
    workflow.add_node("execute_quant", execute_quant)
    workflow.add_node("execute_professor", execute_professor)
    workflow.add_node("execute_analyst", execute_analyst)
    workflow.add_node("execute_advisor", execute_advisor)
    workflow.add_node("execute_oracle", execute_oracle)
    workflow.add_node("execute_scout", execute_scout)
    
    # Always-run nodes
    workflow.add_node("execute_guardian", execute_guardian)
    workflow.add_node("execute_scribe", execute_scribe)
    workflow.add_node("aggregate_responses", aggregate_responses)
    
    # ==========================================================================
    # Add edges
    # ==========================================================================
    
    # Start -> Parse Intent
    workflow.add_edge(START, "parse_intent")
    
    # Parse Intent -> Conditional routing to agents
    # Note: For MVP, we route to a single primary agent per intent
    # Parallel execution can be added in Phase 2
    workflow.add_conditional_edges(
        "parse_intent",
        _route_by_intent,
        # Map return values to node names (single node per route for MVP)
        {
            "quant_only": "execute_quant",
            "professor_only": "execute_professor",
            "analyst_only": "execute_analyst",
            "advisor": "execute_advisor",
            "oracle": "execute_oracle",
            "scout": "execute_scout",
            "default": "execute_professor",
        }
    )
    
    # All domain agents -> Guardian
    for agent_node in [
        "execute_quant",
        "execute_professor", 
        "execute_analyst",
        "execute_advisor",
        "execute_oracle",
        "execute_scout",
    ]:
        workflow.add_edge(agent_node, "execute_guardian")
    
    # Guardian -> Scribe
    workflow.add_edge("execute_guardian", "execute_scribe")
    
    # Scribe -> Aggregate
    workflow.add_edge("execute_scribe", "aggregate_responses")
    
    # Aggregate -> END
    workflow.add_edge("aggregate_responses", END)
    
    return workflow


def _route_by_intent(state: FinnieState) -> str:
    """
    Routing function for conditional edges.
    
    Based on the parsed intent, returns a key that maps to agent nodes.
    """
    intent = state.get("intent", "general")
    selected_agents = state.get("selected_agents", [])
    
    # Simple routing based on intent
    from src.orchestration.state import IntentType
    
    if intent == IntentType.MARKET_DATA:
        return "quant_only"
    elif intent == IntentType.EDUCATION:
        return "professor_only"
    elif intent == IntentType.NEWS:
        return "analyst_only"
    elif intent == IntentType.PORTFOLIO:
        return "advisor"
    elif intent == IntentType.PROJECTION:
        return "oracle"
    elif intent == IntentType.TREND:
        return "scout"
    elif intent == IntentType.COMPARISON:
        return "quant_only"  # Primary agent for comparison
    else:
        return "default"


def compile_graph():
    """
    Compile the graph for execution.
    
    Returns:
        Compiled graph ready for .invoke() or .stream().
    """
    graph = create_finnie_graph()
    return graph.compile()


# =============================================================================
# Convenience function for running the graph
# =============================================================================

async def run_finnie(
    user_input: str,
    session_id: str,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4o",
    llm_api_key: str = "",
    portfolio_data: dict | None = None,
) -> FinnieState:
    """
    Run the Finnie AI workflow.
    
    This is the main entry point for executing a user query.
    
    Args:
        user_input: The user's message.
        session_id: Unique session identifier.
        llm_provider: LLM provider to use.
        llm_model: Model to use.
        llm_api_key: API key for the provider.
        portfolio_data: Optional user portfolio.
        
    Returns:
        Final state with response and visualizations.
        
    Example:
        >>> result = await run_finnie(
        ...     user_input="What's AAPL trading at?",
        ...     session_id="user123",
        ...     llm_provider="openai",
        ...     llm_model="gpt-4o",
        ...     llm_api_key="sk-...",
        ... )
        >>> print(result["final_response"])
    """
    from src.orchestration.state import create_initial_state
    
    # Create initial state
    initial_state = create_initial_state(
        user_input=user_input,
        session_id=session_id,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        portfolio_data=portfolio_data,
    )
    
    # Compile and run the graph
    graph = compile_graph()
    result = await graph.ainvoke(initial_state)
    
    return result
