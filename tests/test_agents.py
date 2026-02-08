"""
Finnie AI — Test Suite: Agents

Tests for the 8 specialized agents.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.orchestration.state import FinnieState


class TestQuantAgent:
    """Tests for The Quant agent."""
    
    def test_ticker_extraction(self):
        """Test extracting tickers from text."""
        from src.agents.quant import QuantAgent
        
        agent = QuantAgent()
        
        # Test $TICKER format
        tickers = agent._extract_tickers("What's $AAPL trading at?")
        assert "AAPL" in tickers
        
        # Test plain ticker
        tickers = agent._extract_tickers("Tell me about MSFT")
        assert "MSFT" in tickers
        
        # Test multiple tickers
        tickers = agent._extract_tickers("Compare AAPL vs GOOGL")
        assert "AAPL" in tickers
        assert "GOOGL" in tickers
        
        # Test filtering common words
        tickers = agent._extract_tickers("Is TSLA a good stock?")
        assert "TSLA" in tickers
        assert "IS" not in tickers
    
    @pytest.mark.asyncio
    @patch("yfinance.Ticker")
    async def test_fetch_stock_data(self, mock_ticker):
        """Test fetching stock data with mocked yfinance."""
        from src.agents.quant import QuantAgent
        
        # Mock yfinance response
        mock_instance = MagicMock()
        mock_instance.info = {
            "shortName": "Apple Inc.",
            "previousClose": 150.0,
            "regularMarketPrice": 155.0,
            "dayHigh": 156.0,
            "dayLow": 149.0,
            "volume": 1000000,
            "averageVolume": 800000,
            "marketCap": 2500000000000,
            "trailingPE": 28.5,
            "fiftyTwoWeekHigh": 180.0,
            "fiftyTwoWeekLow": 120.0,
        }
        mock_instance.history.return_value = MagicMock(
            empty=False,
            __getitem__=lambda self, x: MagicMock(iloc=MagicMock(__getitem__=lambda self, i: 155.0))
        )
        mock_ticker.return_value = mock_instance
        
        agent = QuantAgent()
        data = agent._fetch_stock_data("AAPL")
        
        assert data is not None
        assert data["ticker"] == "AAPL"
    
    def test_format_single_stock(self):
        """Test formatting single stock response."""
        from src.agents.quant import QuantAgent
        
        agent = QuantAgent()
        
        info = {
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "price": 155.0,
            "change": 5.0,
            "change_percent": 3.33,
            "open": 151.0,
            "day_high": 156.0,
            "day_low": 149.0,
            "fifty_two_week_high": 180.0,
            "fifty_two_week_low": 120.0,
            "volume": 1000000,
            "market_cap": 2500000000000,
            "pe_ratio": 28.5,
        }
        
        response = agent._format_single_stock(info)
        
        assert "Apple Inc." in response
        assert "$155.00" in response
        assert "📈" in response  # Positive change emoji


class TestProfessorAgent:
    """Tests for The Professor agent."""
    
    def test_topic_extraction(self):
        """Test extracting topics from questions."""
        from src.agents.professor import ProfessorAgent
        
        agent = ProfessorAgent()
        
        assert agent._extract_topic("What is a P/E ratio?") == "p/e ratio"
        assert agent._extract_topic("Explain market cap") == "market cap"
        assert agent._extract_topic("How does dividend work?") == "dividend work"
    
    def test_fallback_definitions(self):
        """Test fallback definitions for common terms."""
        from src.agents.professor import ProfessorAgent
        
        agent = ProfessorAgent()
        
        response = agent._get_fallback_response("What is P/E ratio?")
        assert "P/E" in response or "Price-to-Earnings" in response
        
        response = agent._get_fallback_response("What is market cap?")
        assert "Market" in response


class TestGuardianAgent:
    """Tests for The Guardian agent."""
    
    @pytest.mark.asyncio
    async def test_always_adds_base_disclaimer(self):
        """Test that Guardian always adds base disclaimer."""
        from src.agents.guardian import GuardianAgent
        
        agent = GuardianAgent()
        
        state = FinnieState(
            user_input="What is AAPL?",
            session_id="test",
            agent_outputs=[],
        )
        
        result = await agent.process(state)
        
        assert "disclaimers" in result
        assert len(result["disclaimers"]) >= 1
        assert any("educational" in d.lower() for d in result["disclaimers"])
    
    def test_high_risk_detection(self):
        """Test detection of high-risk queries."""
        from src.agents.guardian import GuardianAgent
        
        agent = GuardianAgent()
        
        # Should detect high risk
        assert agent._assess_risk("Should I buy TSLA?", []) == "high"
        assert agent._assess_risk("I'm going all in on crypto", []) == "high"
        
        # Should detect medium risk
        assert agent._assess_risk("How should I invest?", []) == "medium"
        
        # Should be low risk
        assert agent._assess_risk("What is AAPL's price?", []) == "low"
    
    def test_crypto_detection(self):
        """Test cryptocurrency mention detection."""
        from src.agents.guardian import GuardianAgent
        
        agent = GuardianAgent()
        
        assert agent._mentions_crypto("What about Bitcoin?") is True
        assert agent._mentions_crypto("ETH price") is True
        assert agent._mentions_crypto("What is AAPL?") is False


class TestOracleAgent:
    """Tests for The Oracle agent."""
    
    def test_parameter_extraction(self):
        """Test extracting investment parameters."""
        from src.agents.oracle import OracleAgent
        
        agent = OracleAgent()
        
        params = agent._extract_parameters(
            "If I invest $10,000 initially and add $500 monthly for 10 years"
        )
        
        assert params is not None
        assert params["initial"] == 10000
        assert params["monthly"] == 500
        assert params["years"] == 10
    
    def test_monte_carlo_simulation(self):
        """Test Monte Carlo simulation returns valid results."""
        from src.agents.oracle import OracleAgent
        
        agent = OracleAgent()
        
        result = agent._monte_carlo_simulation(
            initial=10000,
            monthly=500,
            years=5,
            num_simulations=100,  # Fewer for speed
        )
        
        assert "conservative" in result
        assert "expected" in result
        assert "optimistic" in result
        assert result["conservative"] < result["expected"] < result["optimistic"]
        assert result["total_contributions"] == 10000 + (500 * 5 * 12)


class TestScribeAgent:
    """Tests for The Scribe agent."""
    
    @pytest.mark.asyncio
    async def test_single_output_passthrough(self):
        """Test that single agent output passes through unchanged."""
        from src.agents.scribe import ScribeAgent
        from src.orchestration.state import AgentName
        
        agent = ScribeAgent()
        
        state = FinnieState(
            user_input="test",
            session_id="test",
            agent_outputs=[{
                "agent_name": AgentName.QUANT,
                "content": "AAPL is trading at $150",
                "data": None,
                "timestamp": "2024-01-01",
            }],
            disclaimers=[],
        )
        
        result = await agent.process(state)
        
        assert "AAPL is trading at $150" in result["final_response"]
    
    @pytest.mark.asyncio
    async def test_empty_outputs_fallback(self):
        """Test fallback when no agent outputs."""
        from src.agents.scribe import ScribeAgent
        
        agent = ScribeAgent()
        
        state = FinnieState(
            user_input="test",
            session_id="test",
            agent_outputs=[],
            disclaimers=[],
        )
        
        result = await agent.process(state)
        
        assert "apologize" in result["final_response"].lower()
