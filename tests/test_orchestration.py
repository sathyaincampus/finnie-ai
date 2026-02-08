"""
Finnie AI — Test Suite: Orchestration

Tests for LangGraph state machine and workflow.
"""

import pytest
from datetime import datetime

from src.orchestration.state import (
    FinnieState,
    AgentOutput,
    IntentType,
    AgentName,
    INTENT_AGENT_MAP,
    create_initial_state,
)


class TestFinnieState:
    """Tests for FinnieState TypedDict."""
    
    def test_create_initial_state(self):
        """Test creating initial state."""
        state = create_initial_state(
            user_input="What is AAPL?",
            session_id="session123",
            llm_provider="openai",
            llm_model="gpt-4o",
        )
        
        assert state["user_input"] == "What is AAPL?"
        assert state["session_id"] == "session123"
        assert state["llm_provider"] == "openai"
        assert state["agent_outputs"] == []
        assert state["disclaimers"] == []
        assert "start_time" in state["metadata"]
    
    def test_state_with_portfolio(self):
        """Test state with portfolio data."""
        portfolio = {
            "holdings": [
                {"ticker": "AAPL", "shares": 10, "value": 1500},
                {"ticker": "GOOGL", "shares": 5, "value": 700},
            ]
        }
        
        state = create_initial_state(
            user_input="Analyze my portfolio",
            session_id="test",
            portfolio_data=portfolio,
        )
        
        assert state["portfolio_data"] == portfolio
        assert len(state["portfolio_data"]["holdings"]) == 2


class TestIntentMapping:
    """Tests for intent to agent mapping."""
    
    def test_market_data_intent(self):
        """Test market data intent maps to Quant."""
        agents = INTENT_AGENT_MAP[IntentType.MARKET_DATA]
        assert AgentName.QUANT in agents
    
    def test_education_intent(self):
        """Test education intent maps to Professor."""
        agents = INTENT_AGENT_MAP[IntentType.EDUCATION]
        assert AgentName.PROFESSOR in agents
    
    def test_portfolio_intent(self):
        """Test portfolio intent maps to Advisor and Quant."""
        agents = INTENT_AGENT_MAP[IntentType.PORTFOLIO]
        assert AgentName.ADVISOR in agents
        assert AgentName.QUANT in agents
    
    def test_projection_intent(self):
        """Test projection intent maps to Oracle."""
        agents = INTENT_AGENT_MAP[IntentType.PROJECTION]
        assert AgentName.ORACLE in agents


class TestNodeFunctions:
    """Tests for graph node functions."""
    
    @pytest.mark.asyncio
    async def test_parse_intent_market_data(self):
        """Test intent parsing for market data queries."""
        from src.orchestration.nodes import parse_intent
        
        state = create_initial_state(
            user_input="What's the price of AAPL?",
            session_id="test",
        )
        
        result = await parse_intent(state)
        
        assert result["intent"] == IntentType.MARKET_DATA
        assert result["intent_confidence"] > 0.9
        assert AgentName.QUANT in result["selected_agents"]
    
    @pytest.mark.asyncio
    async def test_parse_intent_education(self):
        """Test intent parsing for education queries."""
        from src.orchestration.nodes import parse_intent
        
        state = create_initial_state(
            user_input="What is a stock?",
            session_id="test",
        )
        
        result = await parse_intent(state)
        
        assert result["intent"] == IntentType.EDUCATION
        assert AgentName.PROFESSOR in result["selected_agents"]
    
    @pytest.mark.asyncio
    async def test_parse_intent_always_includes_guardian_scribe(self):
        """Test that Guardian and Scribe are always included."""
        from src.orchestration.nodes import parse_intent
        
        state = create_initial_state(
            user_input="Random query",
            session_id="test",
        )
        
        result = await parse_intent(state)
        
        assert AgentName.GUARDIAN in result["selected_agents"]
        assert AgentName.SCRIBE in result["selected_agents"]
    
    def test_route_by_intent(self):
        """Test routing function returns correct node names."""
        from src.orchestration.nodes import route_to_agents
        
        state = FinnieState(
            user_input="test",
            session_id="test",
            selected_agents=[AgentName.QUANT, AgentName.PROFESSOR],
        )
        
        nodes = route_to_agents(state)
        
        assert "execute_quant" in nodes
        assert "execute_professor" in nodes
    
    @pytest.mark.asyncio
    async def test_aggregate_responses_fallback(self):
        """Test aggregation when no final response exists."""
        from src.orchestration.nodes import aggregate_responses
        
        state = FinnieState(
            user_input="test",
            session_id="test",
            agent_outputs=[{
                "agent_name": AgentName.QUANT,
                "content": "AAPL: $150",
                "data": None,
                "timestamp": "2024-01-01",
            }],
            final_response="",
            disclaimers=["Test disclaimer"],
        )
        
        result = await aggregate_responses(state)
        
        assert "AAPL: $150" in result["final_response"]
        assert "⚠️" in result["final_response"]  # Disclaimer marker


class TestGraphConstruction:
    """Tests for graph construction."""
    
    def test_create_finnie_graph(self):
        """Test that graph is created without errors."""
        from src.orchestration.graph import create_finnie_graph
        
        graph = create_finnie_graph()
        
        # Check that essential nodes exist
        assert "parse_intent" in graph.nodes
        assert "execute_quant" in graph.nodes
        assert "execute_guardian" in graph.nodes
        assert "execute_scribe" in graph.nodes
        assert "aggregate_responses" in graph.nodes
    
    def test_compile_graph(self):
        """Test that graph compiles successfully."""
        from src.orchestration.graph import compile_graph
        
        compiled = compile_graph()
        
        # Compiled graph should have invoke method
        assert hasattr(compiled, "invoke") or hasattr(compiled, "ainvoke")
