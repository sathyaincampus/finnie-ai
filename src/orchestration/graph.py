"""
Finnie AI — LangGraph Definition

StateGraph construction for the multi-agent workflow.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from src.orchestration.state import FinnieState, AgentName
from src.orchestration.nodes import (
    execute_enhancer,
    parse_intent,
    execute_quant,
    execute_professor,
    execute_analyst,
    execute_advisor,
    execute_oracle,
    execute_scout,
    execute_planner,
    execute_crypto,
    execute_guardian,
    execute_scribe,
    aggregate_responses,
)


def create_finnie_graph() -> StateGraph:
    """
    Create the Finnie AI LangGraph workflow.
    
    The workflow follows this pattern:
    1. Enhance user prompt
    2. Parse intent from enhanced input
    3. Route to appropriate domain agents
    4. Guardian checks compliance
    5. Scribe formats final response
    6. Aggregate and return
    
    ```
    START
      │
      ▼
    enhancer
      │
      ▼
    parse_intent
      │
      ├──────────────────────────────────────────────────┐
      ▼       ▼         ▼        ▼       ▼       ▼      ▼
    quant  professor  analyst advisor oracle  planner  crypto
      │       │         │        │       │       │      │
      └───────┴─────────┴────────┴───────┴───────┴──────┘
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
    workflow = StateGraph(FinnieState)
    
    # ==========================================================================
    # Add nodes
    # ==========================================================================
    
    # Prompt enhancement (first node)
    workflow.add_node("execute_enhancer", execute_enhancer)
    
    # Intent parsing
    workflow.add_node("parse_intent", parse_intent)
    
    # Domain agent nodes
    workflow.add_node("execute_quant", execute_quant)
    workflow.add_node("execute_professor", execute_professor)
    workflow.add_node("execute_analyst", execute_analyst)
    workflow.add_node("execute_advisor", execute_advisor)
    workflow.add_node("execute_oracle", execute_oracle)
    workflow.add_node("execute_scout", execute_scout)
    workflow.add_node("execute_planner", execute_planner)
    workflow.add_node("execute_crypto", execute_crypto)
    
    # Always-run nodes
    workflow.add_node("execute_guardian", execute_guardian)
    workflow.add_node("execute_scribe", execute_scribe)
    workflow.add_node("aggregate_responses", aggregate_responses)
    
    # ==========================================================================
    # Add edges
    # ==========================================================================
    
    # Start -> Enhancer -> Parse Intent
    workflow.add_edge(START, "execute_enhancer")
    workflow.add_edge("execute_enhancer", "parse_intent")
    
    # Parse Intent -> Conditional routing to agents
    workflow.add_conditional_edges(
        "parse_intent",
        _route_by_intent,
        {
            "quant_only": "execute_quant",
            "professor_only": "execute_professor",
            "analyst_only": "execute_analyst",
            "advisor": "execute_advisor",
            "oracle": "execute_oracle",
            "scout": "execute_scout",
            "planner": "execute_planner",
            "crypto": "execute_crypto",
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
        "execute_planner",
        "execute_crypto",
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
        return "quant_only"
    elif intent == IntentType.FINANCIAL_PLAN:
        return "planner"
    elif intent == IntentType.GOAL_PLAN:
        return "oracle"
    elif intent == IntentType.CRYPTO:
        return "crypto"
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
    
    initial_state = create_initial_state(
        user_input=user_input,
        session_id=session_id,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
        portfolio_data=portfolio_data,
    )
    
    graph = compile_graph()
    result = await graph.ainvoke(initial_state)
    
    return result
