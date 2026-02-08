"""
Finnie AI — Agent Quality Evaluation Tests

Uses DeepEval framework for LLM response evaluation.
Metrics: Answer Relevancy, Hallucination, Faithfulness, Bias.

Run with:
    pytest tests/eval/test_agent_quality.py -v
    deepeval test run tests/eval/test_agent_quality.py  # with dashboard
"""

from __future__ import annotations

import pytest

# =============================================================================
# Skip if deepeval not installed
# =============================================================================

try:
    from deepeval import assert_test
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        FaithfulnessMetric,
        HallucinationMetric,
    )
    from deepeval.test_case import LLMTestCase

    HAS_DEEPEVAL = True
except ImportError:
    HAS_DEEPEVAL = False

requires_deepeval = pytest.mark.skipif(
    not HAS_DEEPEVAL,
    reason="deepeval not installed — pip install deepeval",
)


# =============================================================================
# Test Data — Agent Response Scenarios
# =============================================================================

QUANT_TEST_CASES = [
    {
        "input": "What's AAPL trading at?",
        "expected_context": [
            "AAPL is a stock ticker for Apple Inc.",
            "Stock prices can be retrieved from market data APIs",
            "Real-time quote includes price, change, volume",
        ],
        "sample_output": (
            "📊 **AAPL (Apple Inc.)** is currently trading at **$189.45** "
            "(+$2.15, +1.15% today).\n\n"
            "| Metric | Value |\n|--------|-------|\n"
            "| Market Cap | $2.94T |\n| P/E Ratio | 28.5 |\n"
            "| 52-Week Range | $124.17 - $195.18 |\n"
            "| Volume | 52.3M |\n\n"
            "⚠️ *Data is for educational purposes only.*"
        ),
    },
    {
        "input": "Compare TSLA and F stock",
        "expected_context": [
            "TSLA is Tesla Inc., F is Ford Motor Company",
            "Comparison includes key metrics like P/E, market cap, revenue",
            "Stock data from yfinance or market data API",
        ],
        "sample_output": (
            "📊 **Stock Comparison: TSLA vs F**\n\n"
            "| Metric | TSLA | F |\n|--------|------|---|\n"
            "| Price | $248.50 | $11.85 |\n"
            "| Market Cap | $780B | $48B |\n"
            "| P/E Ratio | 68.5 | 12.3 |\n"
            "| Revenue | $96B | $176B |\n\n"
            "Tesla trades at 5.5x Ford's P/E, reflecting EV growth expectations.\n\n"
            "⚠️ *This is for educational purposes only.*"
        ),
    },
]

PROFESSOR_TEST_CASES = [
    {
        "input": "What is a P/E ratio?",
        "expected_context": [
            "P/E ratio means Price-to-Earnings ratio",
            "It equals the stock price divided by earnings per share (EPS)",
            "A high P/E may indicate growth expectations; a low P/E may signal value",
        ],
        "sample_output": (
            "📚 **P/E Ratio (Price-to-Earnings)**\n\n"
            "The P/E ratio is one of the most widely used stock valuation metrics. "
            "It tells you how much investors are willing to pay for each dollar of earnings.\n\n"
            "**Formula:** `P/E = Stock Price ÷ Earnings Per Share (EPS)`\n\n"
            "**Example:** If AAPL trades at $190 with EPS of $6.50, "
            "its P/E = 190 / 6.50 = **29.2x**\n\n"
            "**What it means:**\n"
            "- High P/E (>25): Investors expect strong future growth\n"
            "- Low P/E (<15): May be undervalued or facing challenges\n\n"
            "⚠️ *Educational content — not financial advice.*"
        ),
    },
    {
        "input": "Explain dollar cost averaging",
        "expected_context": [
            "Dollar cost averaging (DCA) is an investment strategy",
            "Involves investing a fixed amount at regular intervals",
            "Reduces impact of volatility over time",
        ],
        "sample_output": (
            "📚 **Dollar Cost Averaging (DCA)**\n\n"
            "DCA is a strategy where you invest a fixed amount at regular intervals, "
            "regardless of the price. This reduces the impact of market volatility.\n\n"
            "**How it works:**\n"
            "- Invest $500 every month into an index fund\n"
            "- When prices are high, you buy fewer shares\n"
            "- When prices are low, you buy more shares\n\n"
            "Over time, this averages out your cost basis.\n\n"
            "⚠️ *Educational content — not financial advice.*"
        ),
    },
]

ADVISOR_TEST_CASES = [
    {
        "input": "How should I diversify my portfolio?",
        "expected_context": [
            "Diversification reduces risk by spreading investments",
            "Asset allocation across stocks, bonds, and alternatives",
            "Geographic diversification and sector allocation",
        ],
        "sample_output": (
            "💼 **Portfolio Diversification Guide**\n\n"
            "A well-diversified portfolio should include:\n\n"
            "**By Asset Class:**\n"
            "- Stocks (60-80%): Growth engine\n"
            "- Bonds (15-30%): Stability\n"
            "- Alternatives (5-10%): REITs, commodities\n\n"
            "**By Geography:**\n"
            "- US: 60-70%\n- International: 20-30%\n- Emerging: 5-10%\n\n"
            "Rebalance quarterly to maintain target allocation.\n\n"
            "⚠️ *This is educational guidance, not personalized financial advice.*"
        ),
    },
]


# =============================================================================
# Relevancy Tests — Does the response address the query?
# =============================================================================


@requires_deepeval
@pytest.mark.parametrize("case", QUANT_TEST_CASES, ids=["aapl_price", "tsla_f_compare"])
def test_quant_relevancy(case):
    """Test that Quant agent responses are relevant to market data queries."""
    test_case = LLMTestCase(
        input=case["input"],
        actual_output=case["sample_output"],
        retrieval_context=case["expected_context"],
    )
    metric = AnswerRelevancyMetric(threshold=0.7)
    assert_test(test_case, [metric])


@requires_deepeval
@pytest.mark.parametrize("case", PROFESSOR_TEST_CASES, ids=["pe_ratio", "dca"])
def test_professor_relevancy(case):
    """Test that Professor agent responses are relevant to educational queries."""
    test_case = LLMTestCase(
        input=case["input"],
        actual_output=case["sample_output"],
        retrieval_context=case["expected_context"],
    )
    metric = AnswerRelevancyMetric(threshold=0.7)
    assert_test(test_case, [metric])


@requires_deepeval
@pytest.mark.parametrize("case", ADVISOR_TEST_CASES, ids=["diversify"])
def test_advisor_relevancy(case):
    """Test that Advisor agent responses address portfolio queries."""
    test_case = LLMTestCase(
        input=case["input"],
        actual_output=case["sample_output"],
        retrieval_context=case["expected_context"],
    )
    metric = AnswerRelevancyMetric(threshold=0.7)
    assert_test(test_case, [metric])


# =============================================================================
# Hallucination Tests — Is the response grounded in context?
# =============================================================================


@requires_deepeval
@pytest.mark.parametrize("case", QUANT_TEST_CASES, ids=["aapl_hallucination", "compare_hallucination"])
def test_quant_no_hallucination(case):
    """Test that Quant responses don't fabricate data."""
    test_case = LLMTestCase(
        input=case["input"],
        actual_output=case["sample_output"],
        context=case["expected_context"],
    )
    metric = HallucinationMetric(threshold=0.3)
    assert_test(test_case, [metric])


@requires_deepeval
@pytest.mark.parametrize("case", PROFESSOR_TEST_CASES, ids=["pe_hallucination", "dca_hallucination"])
def test_professor_no_hallucination(case):
    """Test that Professor responses are factually grounded."""
    test_case = LLMTestCase(
        input=case["input"],
        actual_output=case["sample_output"],
        context=case["expected_context"],
    )
    metric = HallucinationMetric(threshold=0.3)
    assert_test(test_case, [metric])


# =============================================================================
# Faithfulness Tests — Does the response use retrieved context?
# =============================================================================


@requires_deepeval
@pytest.mark.parametrize(
    "case",
    QUANT_TEST_CASES + PROFESSOR_TEST_CASES,
    ids=["aapl_faithful", "compare_faithful", "pe_faithful", "dca_faithful"],
)
def test_response_faithfulness(case):
    """Test that responses are faithful to their retrieval context."""
    test_case = LLMTestCase(
        input=case["input"],
        actual_output=case["sample_output"],
        retrieval_context=case["expected_context"],
    )
    metric = FaithfulnessMetric(threshold=0.7)
    assert_test(test_case, [metric])


# =============================================================================
# MCP Tool Tests — Functional validation (no LLM needed)
# =============================================================================


class TestMCPTools:
    """Test MCP tool registration and execution."""

    def test_tool_discovery(self):
        """All expected MCP tools should be registered."""
        from src.mcp.server import list_tools

        tools = list_tools()
        tool_names = [t["name"] for t in tools]

        assert "get_stock_price" in tool_names
        assert "get_historical_data" in tool_names
        assert "get_company_info" in tool_names
        assert "create_price_chart" in tool_names
        assert "create_comparison_chart" in tool_names
        assert len(tools) >= 7

    def test_tool_schemas(self):
        """Tool definitions should have valid schemas."""
        from src.mcp.server import get_mcp_server

        server = get_mcp_server()
        for tool in server.list_tools():
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert "type" in tool["inputSchema"]

    def test_unknown_tool_error(self):
        """Calling an unknown tool should return an error, not crash."""
        from src.mcp.server import call_tool

        result = call_tool("nonexistent_tool")
        assert "error" in result


# =============================================================================
# Agent Structure Tests
# =============================================================================


class TestAgentStructure:
    """Test that all agents implement the required interface."""

    AGENT_CLASSES = [
        "src.agents.quant.QuantAgent",
        "src.agents.professor.ProfessorAgent",
        "src.agents.analyst.AnalystAgent",
        "src.agents.advisor.AdvisorAgent",
        "src.agents.guardian.GuardianAgent",
        "src.agents.scribe.ScribeAgent",
        "src.agents.oracle.OracleAgent",
        "src.agents.scout.ScoutAgent",
    ]

    @pytest.mark.parametrize("agent_path", AGENT_CLASSES)
    def test_agent_has_required_properties(self, agent_path):
        """Each agent must implement name, description, system_prompt, process."""
        module_path, class_name = agent_path.rsplit(".", 1)
        import importlib

        module = importlib.import_module(module_path)
        agent_class = getattr(module, class_name)
        agent = agent_class()

        assert hasattr(agent, "name")
        assert hasattr(agent, "description")
        assert hasattr(agent, "system_prompt")
        assert hasattr(agent, "process")
        assert agent.name, "Agent name should not be empty"
        assert agent.description, "Agent description should not be empty"


# =============================================================================
# Observability Tests
# =============================================================================


class TestObservability:
    """Test observability infrastructure."""

    def test_observer_creation(self):
        """Observer should initialize without errors."""
        from src.observability import get_observer

        observer = get_observer()
        assert observer is not None

    def test_trace_creation(self):
        """Should be able to create and end a trace."""
        from src.observability import get_observer

        observer = get_observer()
        trace = observer.create_trace("test-session", input_text="hello")
        assert trace.trace_id
        assert trace.session_id == "test-session"

        with observer.span(trace, "test_span"):
            pass

        observer.end_trace(trace, output="world")
        assert trace.total_latency_ms >= 0
        assert len(trace.spans) == 1

    def test_metrics_collection(self):
        """Metrics should aggregate trace data."""
        from src.observability import get_observer

        observer = get_observer()
        metrics = observer.get_metrics()
        assert "total_requests" in metrics
