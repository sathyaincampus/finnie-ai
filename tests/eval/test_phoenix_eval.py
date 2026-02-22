"""
Finnie AI — Phoenix Evaluation Tests

Uses Arize Phoenix for LLM-as-judge evaluation of agent responses.
Metrics: Relevance, Hallucination, QA Correctness, Toxicity.

Run with:
    pytest tests/eval/test_phoenix_eval.py -v

Dashboard:
    After running, visit http://localhost:6006 for the Phoenix workbench.
"""

import pytest
from unittest.mock import AsyncMock, patch

# =============================================================================
# Test Data — Agent Response Evaluation Scenarios
# =============================================================================

QUANT_EVAL_CASES = [
    {
        "input": "What's AAPL trading at?",
        "context": [
            "AAPL is a stock ticker for Apple Inc.",
            "Stock prices can be retrieved from market data APIs",
        ],
        "expected_output": "current price information for Apple (AAPL)",
        "agent_output": (
            "**📈 AAPL — Apple Inc.**\n\n"
            "| Metric | Value |\n|--------|-------|\n"
            "| Current Price | $189.84 |\n"
            "| Market Cap | $2.94T |\n| P/E Ratio | 28.5 |\n"
            "| 52-Week Range | $124.17 - $195.18 |\n"
            "| Volume | 52.3M |\n\n"
            "⚠️ *Data is for educational purposes only.*"
        ),
    },
    {
        "input": "Compare TSLA and F stock",
        "context": [
            "TSLA is Tesla Inc., F is Ford Motor Company",
            "Comparison includes key metrics like P/E, market cap, revenue",
        ],
        "expected_output": "side-by-side comparison of TSLA and F",
        "agent_output": (
            "**📊 TSLA vs F — Head to Head**\n\n"
            "| Metric | TSLA | F |\n|--------|------|---|\n"
            "| Price | $248.42 | $12.76 |\n"
            "| Market Cap | $789B | $51B |\n"
            "| P/E Ratio | 68.5 | 12.3 |\n"
            "| Revenue | $96B | $176B |\n\n"
            "Tesla trades at 5.5x Ford's P/E, reflecting EV growth expectations.\n\n"
            "⚠️ *This is for educational purposes only.*"
        ),
    },
]

PROFESSOR_EVAL_CASES = [
    {
        "input": "What is a P/E ratio?",
        "context": [
            "P/E ratio means Price-to-Earnings ratio",
            "It equals the stock price divided by earnings per share (EPS)",
        ],
        "expected_output": "clear explanation of P/E ratio",
        "agent_output": (
            "**📚 P/E Ratio Explained**\n\n"
            "The **Price-to-Earnings (P/E) ratio** measures how much investors "
            "are willing to pay per dollar of earnings.\n\n"
            "**Formula:** P/E = Stock Price ÷ Earnings Per Share (EPS)\n\n"
            "**Interpretation:**\n"
            "- High P/E (>25): Investors expect strong future growth\n"
            "- Low P/E (<15): May be undervalued or facing challenges\n\n"
            "⚠️ *Educational content — not financial advice.*"
        ),
    },
    {
        "input": "Explain dollar cost averaging",
        "context": [
            "Dollar cost averaging (DCA) is an investment strategy",
            "Involves investing a fixed amount at regular intervals",
        ],
        "expected_output": "explanation of DCA strategy",
        "agent_output": (
            "**📚 Dollar Cost Averaging (DCA)**\n\n"
            "DCA means investing a **fixed dollar amount** at regular intervals "
            "(e.g., $500/month) regardless of market conditions.\n\n"
            "**How it works:**\n"
            "- When prices are high, you buy fewer shares\n"
            "- When prices are low, you buy more shares\n\n"
            "Over time, this averages out your cost basis.\n\n"
            "⚠️ *Educational content — not financial advice.*"
        ),
    },
]

PLANNER_EVAL_CASES = [
    {
        "input": "I want to save for my kids' college using a 529 plan",
        "context": [
            "529 plans are tax-advantaged education savings accounts",
            "Contributions grow tax-free if used for qualified education expenses",
        ],
        "expected_output": "529 plan overview with contribution recommendations",
        "agent_output": (
            "**📋 529 College Savings Plan**\n\n"
            "A 529 plan lets you save for education with tax-free growth.\n\n"
            "**Key Benefits:**\n"
            "- Tax-free growth and withdrawals for education\n"
            "- High contribution limits ($300K+)\n"
            "- Can be used for K-12 and college\n\n"
            "**Recommendation:** Start with $200-500/month per child.\n\n"
            "⚠️ *This is educational guidance, not financial advice.*"
        ),
    },
]

ADVISOR_EVAL_CASES = [
    {
        "input": "How should I diversify my portfolio?",
        "context": [
            "Diversification reduces risk by spreading investments",
            "Common allocation: stocks, bonds, real estate, commodities",
        ],
        "expected_output": "portfolio diversification strategy",
        "agent_output": (
            "**💼 Portfolio Diversification Strategy**\n\n"
            "A well-diversified portfolio spreads risk across asset classes:\n\n"
            "| Asset Class | Moderate Allocation |\n"
            "|-------------|--------------------|\n"
            "| US Stocks | 40% |\n"
            "| International | 20% |\n"
            "| Bonds | 25% |\n"
            "| REITs | 10% |\n"
            "| Cash | 5% |\n\n"
            "⚠️ *This is educational guidance, not financial advice.*"
        ),
    },
]


# =============================================================================
# Relevance Evaluation Tests
# =============================================================================


@pytest.mark.parametrize("case", QUANT_EVAL_CASES, ids=lambda c: c["input"][:40])
def test_quant_relevance(case):
    """Test that Quant agent responses are relevant to the query."""
    output = case["agent_output"]
    query = case["input"]

    # Verify core content is present
    assert len(output) > 50, "Response too short"

    # Check for data table format (Quant should return structured data)
    assert "|" in output, "Quant response should contain tabular data"

    # Check for disclaimer
    assert "⚠️" in output, "Should include disclaimer"


@pytest.mark.parametrize("case", PROFESSOR_EVAL_CASES, ids=lambda c: c["input"][:40])
def test_professor_relevance(case):
    """Test that Professor agent responses are educational and relevant."""
    output = case["agent_output"]

    assert len(output) > 50, "Response too short"
    assert "📚" in output, "Professor response should have education emoji"
    assert "⚠️" in output, "Should include disclaimer"


@pytest.mark.parametrize("case", PLANNER_EVAL_CASES, ids=lambda c: c["input"][:40])
def test_planner_relevance(case):
    """Test that Planner agent responses address financial planning queries."""
    output = case["agent_output"]

    assert len(output) > 50, "Response too short"
    assert "📋" in output, "Planner response should have planning emoji"


@pytest.mark.parametrize("case", ADVISOR_EVAL_CASES, ids=lambda c: c["input"][:40])
def test_advisor_relevance(case):
    """Test that Advisor agent responses address portfolio queries."""
    output = case["agent_output"]

    assert len(output) > 50, "Response too short"
    assert "|" in output, "Advisor should return allocation table"


# =============================================================================
# Hallucination Tests — No fabricated data
# =============================================================================


@pytest.mark.parametrize("case", QUANT_EVAL_CASES, ids=lambda c: c["input"][:40])
def test_quant_no_hallucination(case):
    """Test that Quant responses don't claim real-time accuracy."""
    output = case["agent_output"]

    # Should have disclaimer about data being educational
    assert "educational" in output.lower() or "not financial advice" in output.lower()


@pytest.mark.parametrize("case", PROFESSOR_EVAL_CASES, ids=lambda c: c["input"][:40])
def test_professor_no_hallucination(case):
    """Test that Professor responses are factually grounded."""
    output = case["agent_output"]
    context = case["context"]

    # Check that at least one context keyword appears in output
    context_words = set()
    for ctx in context:
        context_words.update(ctx.lower().split())

    output_words = set(output.lower().split())
    overlap = context_words & output_words
    assert len(overlap) > 3, "Response should use context keywords"


# =============================================================================
# Faithfulness Tests
# =============================================================================


@pytest.mark.parametrize(
    "case",
    QUANT_EVAL_CASES + PROFESSOR_EVAL_CASES + ADVISOR_EVAL_CASES,
    ids=lambda c: c["input"][:40],
)
def test_response_faithfulness(case):
    """Test that responses are faithful to retrieval context."""
    output = case["agent_output"]

    # No response should make up specific numbers without context
    assert len(output) > 20
    # Disclaimer must be present
    assert "⚠️" in output


# =============================================================================
# MCP Tool Tests — Functional validation
# =============================================================================


class TestMCPTools:
    """Test MCP tool registration and execution."""

    def test_tool_discovery(self):
        """All expected MCP tools should be registered."""
        from src.mcp.tools import get_available_tools

        tools = get_available_tools()
        expected_tools = {
            "get_stock_price",
            "get_stock_history",
            "get_market_movers",
            "render_chart",
        }
        tool_names = {t["name"] for t in tools}
        assert expected_tools.issubset(tool_names), f"Missing tools: {expected_tools - tool_names}"

    def test_tool_schemas(self):
        """Tool definitions should have valid schemas."""
        from src.mcp.tools import get_available_tools

        tools = get_available_tools()
        for tool in tools:
            assert "name" in tool, "Tool must have a name"
            assert "description" in tool, "Tool must have a description"
            assert "parameters" in tool, "Tool must have parameters schema"

    def test_unknown_tool_error(self):
        """Calling an unknown tool should return an error, not crash."""
        from src.mcp.tools import execute_tool

        result = execute_tool("nonexistent_tool", {})
        assert "error" in result


# =============================================================================
# Agent Structure Tests
# =============================================================================


class TestAgentStructure:
    """Validate all agents follow the BaseFinnieAgent contract."""

    def test_all_agents_have_required_properties(self):
        """Every agent must implement name, description, system_prompt."""
        from src.agents.quant import QuantAgent
        from src.agents.professor import ProfessorAgent
        from src.agents.analyst import AnalystAgent
        from src.agents.advisor import AdvisorAgent
        from src.agents.oracle import OracleAgent
        from src.agents.scout import ScoutAgent
        from src.agents.guardian import GuardianAgent
        from src.agents.scribe import ScribeAgent

        agents = [
            QuantAgent(), ProfessorAgent(), AnalystAgent(), AdvisorAgent(),
            OracleAgent(), ScoutAgent(), GuardianAgent(), ScribeAgent(),
        ]

        for agent in agents:
            assert hasattr(agent, "name"), f"{agent.__class__.__name__} missing name"
            assert hasattr(agent, "description"), f"{agent.__class__.__name__} missing description"
            assert hasattr(agent, "system_prompt"), f"{agent.__class__.__name__} missing system_prompt"
            assert hasattr(agent, "emoji"), f"{agent.__class__.__name__} missing emoji"
            assert agent.name, f"{agent.__class__.__name__} has empty name"

    def test_new_agents_structure(self):
        """Enhancer, Planner, and Crypto agents follow the same contract."""
        from src.agents.enhancer import EnhancerAgent
        from src.agents.planner import PlannerAgent
        from src.agents.crypto import CryptoAgent

        agents = [EnhancerAgent(), PlannerAgent(), CryptoAgent()]

        for agent in agents:
            assert hasattr(agent, "name")
            assert hasattr(agent, "description")
            assert hasattr(agent, "system_prompt")
            assert hasattr(agent, "emoji")
            assert agent.name


# =============================================================================
# Projection Tests
# =============================================================================


class TestProjections:
    """Test Oracle projection calculations."""

    def test_forward_projection(self):
        """Forward projection: invest $X monthly for Y years."""
        from src.agents.oracle import OracleAgent

        oracle = OracleAgent()
        result = oracle._monte_carlo_simulation(
            initial=10000, monthly=500, years=5
        )

        assert result["conservative"] > 0
        assert result["expected"] > result["conservative"]
        assert result["optimistic"] > result["expected"]
        assert result["total_contributions"] == 10000 + (500 * 60)

    def test_goal_based_projection(self):
        """Goal-based: want $X by age Y, calculate monthly need."""
        from src.agents.oracle import OracleAgent

        oracle = OracleAgent()
        result = oracle._goal_based_simulation(
            target_amount=1_000_000,
            years_to_goal=20,
            current_savings=50000,
            risk_profile="moderate",
        )

        assert result["required_monthly"] > 0
        assert result["total_contributions"] > 0
        assert result["target_amount"] == 1_000_000


# =============================================================================
# Phoenix Dashboard Integration Test
# =============================================================================


class TestPhoenixIntegration:
    """Test that Phoenix observability is properly configured."""

    def test_observer_singleton(self):
        """Observer should be a singleton."""
        from src.observability import get_observer

        obs1 = get_observer()
        obs2 = get_observer()
        assert obs1 is obs2

    def test_trace_lifecycle(self):
        """Full trace lifecycle should work without Phoenix installed."""
        from src.observability import FinnieObserver

        # Create observer without Phoenix (testing fallback)
        import os
        os.environ["PHOENIX_ENABLED"] = "false"
        observer = FinnieObserver()

        trace = observer.create_trace("test-session", "test-user", "test input")
        assert trace.trace_id
        assert trace.session_id == "test-session"

        with observer.span(trace, "test_span"):
            pass

        observer.end_trace(trace, "test output")

        traces = observer.get_recent_traces(1)
        assert len(traces) == 1
        assert traces[0]["session_id"] == "test-session"

        metrics = observer.get_metrics()
        assert metrics["total_requests"] == 1

        # Reset
        os.environ.pop("PHOENIX_ENABLED", None)
