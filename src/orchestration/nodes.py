"""
Finnie AI — Graph Node Functions

Individual node implementations for the LangGraph workflow.
"""

import re
from datetime import datetime
from typing import Any, Literal

from src.orchestration.state import (
    FinnieState,
    AgentOutput,
    IntentType,
    AgentName,
    INTENT_AGENT_MAP,
)
from src.llm import get_llm_adapter


# =============================================================================
# Intent Parsing Node
# =============================================================================

async def parse_intent(state: FinnieState) -> dict[str, Any]:
    """
    Parse the user's intent from their input.
    
    This node uses the LLM to classify the user's query and determine
    which agents should handle it.
    
    Args:
        state: Current workflow state.
        
    Returns:
        Updated state dict with intent and selected_agents.
    """
    user_input = state["user_input"].lower()
    
    # Quick pattern matching for obvious intents
    if _matches_patterns(user_input, [r'\bprice\b', r'\bquote\b', r'\btrading at\b', r'\$[A-Z]+']):
        intent = IntentType.MARKET_DATA
        confidence = 0.95
    elif _matches_patterns(user_input, [r'\bwhat is\b', r'\bexplain\b', r'\bhow does\b', r'\bwhy\b']):
        intent = IntentType.EDUCATION
        confidence = 0.90
    elif _matches_patterns(user_input, [r'\bnews\b', r'\bheadlines\b', r'\bsentiment\b']):
        intent = IntentType.NEWS
        confidence = 0.90
    elif _matches_patterns(user_input, [r'\bportfolio\b', r'\bholdings\b', r'\ballocation\b', r'\brebalance\b']):
        intent = IntentType.PORTFOLIO
        confidence = 0.90
    elif _matches_patterns(user_input, [r'\bproject\b', r'\bif i invest\b', r'\bgrow\b', r'\bfuture\b']):
        intent = IntentType.PROJECTION
        confidence = 0.85
    elif _matches_patterns(user_input, [r'\btrending\b', r'\bhot\b', r'\bpopular\b', r'\bmovers\b']):
        intent = IntentType.TREND
        confidence = 0.85
    elif _matches_patterns(user_input, [r'\bcompare\b', r'\bvs\b', r'\bversus\b', r'\bbetter\b']):
        intent = IntentType.COMPARISON
        confidence = 0.90
    else:
        # Default to general - will use LLM for classification
        intent = IntentType.GENERAL
        confidence = 0.70
    
    # Get agents for this intent
    selected_agents = INTENT_AGENT_MAP.get(intent, [AgentName.PROFESSOR])
    
    # Always add Guardian and Scribe
    if AgentName.GUARDIAN not in selected_agents:
        selected_agents.append(AgentName.GUARDIAN)
    if AgentName.SCRIBE not in selected_agents:
        selected_agents.append(AgentName.SCRIBE)
    
    return {
        "intent": intent,
        "intent_confidence": confidence,
        "selected_agents": selected_agents,
    }


def _matches_patterns(text: str, patterns: list[str]) -> bool:
    """Check if text matches any of the given patterns."""
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# =============================================================================
# Agent Execution Nodes
# =============================================================================

async def execute_quant(state: FinnieState) -> dict[str, Any]:
    """
    Execute The Quant agent for market data.
    
    Fetches real-time stock data and technical indicators.
    """
    from src.agents.quant import QuantAgent
    
    agent = QuantAgent()
    result = await agent.process(state)
    
    return {
        "agent_outputs": [AgentOutput(
            agent_name=AgentName.QUANT,
            content=result.get("content", ""),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat(),
        )],
        "market_data": result.get("data"),
    }


async def execute_professor(state: FinnieState) -> dict[str, Any]:
    """
    Execute The Professor agent for education.
    
    Explains financial concepts in clear, accessible language.
    """
    from src.agents.professor import ProfessorAgent
    
    agent = ProfessorAgent()
    result = await agent.process(state)
    
    return {
        "agent_outputs": [AgentOutput(
            agent_name=AgentName.PROFESSOR,
            content=result.get("content", ""),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat(),
        )],
    }


async def execute_analyst(state: FinnieState) -> dict[str, Any]:
    """
    Execute The Analyst agent for news and research.
    """
    from src.agents.analyst import AnalystAgent
    
    agent = AnalystAgent()
    result = await agent.process(state)
    
    return {
        "agent_outputs": [AgentOutput(
            agent_name=AgentName.ANALYST,
            content=result.get("content", ""),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat(),
        )],
    }


async def execute_advisor(state: FinnieState) -> dict[str, Any]:
    """
    Execute The Advisor agent for portfolio guidance.
    """
    from src.agents.advisor import AdvisorAgent
    
    agent = AdvisorAgent()
    result = await agent.process(state)
    
    return {
        "agent_outputs": [AgentOutput(
            agent_name=AgentName.ADVISOR,
            content=result.get("content", ""),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat(),
        )],
    }


async def execute_oracle(state: FinnieState) -> dict[str, Any]:
    """
    Execute The Oracle agent for investment projections.
    """
    from src.agents.oracle import OracleAgent
    
    agent = OracleAgent()
    result = await agent.process(state)
    
    return {
        "agent_outputs": [AgentOutput(
            agent_name=AgentName.ORACLE,
            content=result.get("content", ""),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat(),
        )],
        "visualizations": result.get("visualizations", []),
    }


async def execute_scout(state: FinnieState) -> dict[str, Any]:
    """
    Execute The Scout agent for trend discovery.
    """
    from src.agents.scout import ScoutAgent
    
    agent = ScoutAgent()
    result = await agent.process(state)
    
    return {
        "agent_outputs": [AgentOutput(
            agent_name=AgentName.SCOUT,
            content=result.get("content", ""),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat(),
        )],
    }


# =============================================================================
# Guardian & Scribe Nodes
# =============================================================================

async def execute_guardian(state: FinnieState) -> dict[str, Any]:
    """
    Execute The Guardian agent for compliance.
    
    Adds appropriate disclaimers based on query risk level.
    """
    from src.agents.guardian import GuardianAgent
    
    agent = GuardianAgent()
    result = await agent.process(state)
    
    return {
        "agent_outputs": [AgentOutput(
            agent_name=AgentName.GUARDIAN,
            content=result.get("content", ""),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat(),
        )],
        "disclaimers": result.get("disclaimers", []),
    }


async def execute_scribe(state: FinnieState) -> dict[str, Any]:
    """
    Execute The Scribe agent for response formatting.
    
    Synthesizes all agent outputs into a cohesive response.
    """
    from src.agents.scribe import ScribeAgent
    
    agent = ScribeAgent()
    result = await agent.process(state)
    
    return {
        "agent_outputs": [AgentOutput(
            agent_name=AgentName.SCRIBE,
            content=result.get("content", ""),
            data=result.get("data"),
            timestamp=datetime.utcnow().isoformat(),
        )],
        "final_response": result.get("final_response", ""),
    }


# =============================================================================
# Routing Function
# =============================================================================

def route_to_agents(state: FinnieState) -> list[str]:
    """
    Determine which agent nodes to execute based on selected_agents.
    
    This is used by LangGraph's conditional edges.
    
    Args:
        state: Current workflow state.
        
    Returns:
        List of node names to execute.
    """
    selected = state.get("selected_agents", [])
    
    # Map agent names to node functions
    agent_node_map = {
        AgentName.QUANT: "execute_quant",
        AgentName.PROFESSOR: "execute_professor",
        AgentName.ANALYST: "execute_analyst",
        AgentName.ADVISOR: "execute_advisor",
        AgentName.ORACLE: "execute_oracle",
        AgentName.SCOUT: "execute_scout",
        # Guardian and Scribe are always at the end
    }
    
    nodes = []
    for agent in selected:
        if agent in agent_node_map:
            nodes.append(agent_node_map[agent])
    
    return nodes if nodes else ["execute_professor"]


# =============================================================================
# Aggregation Node
# =============================================================================

async def aggregate_responses(state: FinnieState) -> dict[str, Any]:
    """
    Final node to aggregate all outputs if Scribe hasn't done it.
    
    This is a fallback - normally Scribe handles synthesis.
    """
    if state.get("final_response"):
        return {}
    
    # Simple aggregation if Scribe didn't run
    outputs = state.get("agent_outputs", [])
    combined = "\n\n".join([
        o["content"] for o in outputs 
        if o.get("content") and o["agent_name"] != AgentName.GUARDIAN
    ])
    
    # Add disclaimers
    disclaimers = state.get("disclaimers", [])
    if disclaimers:
        combined += "\n\n---\n" + "\n".join(f"⚠️ {d}" for d in disclaimers)
    
    return {
        "final_response": combined or "I apologize, I couldn't process your request.",
    }
