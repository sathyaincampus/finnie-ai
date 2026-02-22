"""
Finnie AI — Test Suite: New Agents (v2.5)

Tests for the 3 new agents: Enhancer, Planner, Crypto.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.orchestration.state import FinnieState


# ─────────────────────────────────────────────────────────────────────────────
# Enhancer Agent Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEnhancerAgent:
    """Tests for The Enhancer agent."""

    def _make_agent(self):
        from src.agents.enhancer import EnhancerAgent
        return EnhancerAgent()

    def test_agent_properties(self):
        """Test agent metadata properties."""
        agent = self._make_agent()
        assert agent.name == "enhancer"
        assert agent.emoji == "✨"
        assert "optimization" in agent.description.lower()

    @pytest.mark.asyncio
    async def test_skips_short_greetings(self):
        """Test that very short inputs are passed through unchanged."""
        agent = self._make_agent()
        state = FinnieState(
            user_input="hi",
            session_id="test",
            agent_outputs=[],
        )
        result = await agent.process(state)
        assert result["content"] == "hi"
        assert result["enhanced_input"] == "hi"

    @pytest.mark.asyncio
    async def test_skips_greeting_words(self):
        """Test that common greetings bypass enhancement."""
        agent = self._make_agent()

        for greeting in ["hello", "hey", "thanks", "bye", "ok"]:
            state = FinnieState(
                user_input=greeting,
                session_id="test",
                agent_outputs=[],
            )
            result = await agent.process(state)
            assert result["content"] == greeting

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self):
        """Test that original input is returned when LLM fails."""
        agent = self._make_agent()

        # Patch _call_llm to raise an exception
        agent._call_llm = AsyncMock(side_effect=Exception("LLM unavailable"))

        state = FinnieState(
            user_input="should i invest in stocks?",
            session_id="test",
            agent_outputs=[],
        )
        result = await agent.process(state)

        # Should fall back to original input
        assert result["content"] == "should i invest in stocks?"
        assert result["enhanced_input"] == "should i invest in stocks?"

    @pytest.mark.asyncio
    async def test_successful_enhancement(self):
        """Test that LLM-enhanced prompt is returned correctly."""
        agent = self._make_agent()

        enhanced_text = (
            "The user is asking for investment guidance on stock markets. "
            "Provide asset allocation recommendations with risk context."
        )
        agent._call_llm = AsyncMock(return_value=enhanced_text)

        state = FinnieState(
            user_input="should i invest?",
            session_id="test",
            agent_outputs=[],
        )
        result = await agent.process(state)

        assert result["content"] == enhanced_text
        assert result["enhanced_input"] == enhanced_text

    @pytest.mark.asyncio
    async def test_rejects_too_short_enhancement(self):
        """Test that suspiciously short LLM output falls back to original."""
        agent = self._make_agent()

        # Return something much shorter than original (< 50%)
        agent._call_llm = AsyncMock(return_value="ok")

        state = FinnieState(
            user_input="What is the best way to plan for retirement savings?",
            session_id="test",
            agent_outputs=[],
        )
        result = await agent.process(state)

        # Should fall back to original because enhanced is too short
        assert result["content"] == "What is the best way to plan for retirement savings?"

    def test_system_prompt_content(self):
        """Test that system prompt covers key financial domains."""
        agent = self._make_agent()
        prompt = agent.system_prompt.lower()

        assert "market data" in prompt
        assert "education" in prompt
        assert "portfolio" in prompt
        assert "projections" in prompt
        assert "crypto" in prompt


# ─────────────────────────────────────────────────────────────────────────────
# Planner Agent Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPlannerAgent:
    """Tests for The Planner agent."""

    def _make_agent(self):
        from src.agents.planner import PlannerAgent
        return PlannerAgent()

    def test_agent_properties(self):
        """Test agent metadata properties."""
        agent = self._make_agent()
        assert agent.name == "planner"
        assert agent.emoji == "📋"

    def test_detect_retirement(self):
        """Test retirement topic detection."""
        agent = self._make_agent()
        assert agent._detect_planning_type("How should I plan for retirement?") == "retirement"
        assert agent._detect_planning_type("What's the 401k limit?") == "retirement"
        assert agent._detect_planning_type("Should I open a Roth IRA?") == "retirement"
        assert agent._detect_planning_type("Tell me about social security") == "retirement"

    def test_detect_education(self):
        """Test education savings detection."""
        agent = self._make_agent()
        assert agent._detect_planning_type("How does a 529 plan work?") == "education"
        assert agent._detect_planning_type("Saving for college") == "education"
        assert agent._detect_planning_type("Education savings options") == "education"

    def test_detect_tax(self):
        """Test tax optimization detection."""
        agent = self._make_agent()
        assert agent._detect_planning_type("How can I reduce my tax bill?") == "tax"
        assert agent._detect_planning_type("What tax bracket am I in?") == "tax"
        assert agent._detect_planning_type("Capital gain tax rates") == "tax"

    def test_detect_visa(self):
        """Test visa/immigration detection."""
        agent = self._make_agent()
        assert agent._detect_planning_type("Financial planning on H1B visa") == "visa"
        assert agent._detect_planning_type("NRE account rules") == "visa"
        assert agent._detect_planning_type("FBAR filing requirements") == "visa"
        assert agent._detect_planning_type("Immigration and investing") == "visa"

    def test_detect_budget(self):
        """Test expense/budget detection."""
        agent = self._make_agent()
        assert agent._detect_planning_type("Help me budget my expenses") == "expense"
        assert agent._detect_planning_type("My mortgage payment is too high") == "expense"
        assert agent._detect_planning_type("Insurance costs") == "expense"

    def test_detect_side_hustle(self):
        """Test side hustle detection."""
        agent = self._make_agent()
        assert agent._detect_planning_type("Good side hustle ideas for tech") == "side_hustle"
        assert agent._detect_planning_type("How to start consulting on the side?") == "side_hustle"
        assert agent._detect_planning_type("Passive income opportunities") == "side_hustle"

    def test_detect_goal(self):
        """Test goal-based detection."""
        agent = self._make_agent()
        assert agent._detect_planning_type("I want to save for a down payment") == "goal"
        assert agent._detect_planning_type("Emergency fund advice") == "goal"

    def test_detect_general(self):
        """Test unrecognized queries fall to general."""
        agent = self._make_agent()
        assert agent._detect_planning_type("Hello, how are you?") == "general"

    def test_fallback_retirement(self):
        """Test retirement fallback contains key info."""
        agent = self._make_agent()
        response = agent._get_fallback_response("How should I plan for retirement?")
        assert "401" in response
        assert "Roth" in response or "IRA" in response
        assert "HSA" in response

    def test_fallback_education(self):
        """Test education fallback contains key info."""
        agent = self._make_agent()
        response = agent._get_fallback_response("How does a 529 plan work?")
        assert "529" in response
        assert "education" in response.lower() or "Education" in response

    def test_fallback_visa(self):
        """Test visa fallback contains key info."""
        agent = self._make_agent()
        response = agent._get_fallback_response("H1B financial planning")
        assert "H1B" in response or "visa" in response.lower()
        assert "NRE" in response or "FBAR" in response

    def test_fallback_general(self):
        """Test general fallback lists all categories."""
        agent = self._make_agent()
        response = agent._get_fallback_response("What can you help with?")
        assert "Retirement" in response
        assert "Education" in response
        assert "Tax" in response

    @pytest.mark.asyncio
    async def test_process_without_llm(self):
        """Test process falls back gracefully without LLM."""
        agent = self._make_agent()

        agent._call_llm = AsyncMock(side_effect=Exception("No LLM"))

        state = FinnieState(
            user_input="How should I plan for retirement?",
            session_id="test",
            agent_outputs=[],
        )
        result = await agent.process(state)

        # Should get a fallback response with retirement content
        assert "content" in result
        assert len(result["content"]) > 50


# ─────────────────────────────────────────────────────────────────────────────
# Crypto Agent Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCryptoAgent:
    """Tests for The Crypto agent."""

    def _make_agent(self):
        from src.agents.crypto import CryptoAgent
        return CryptoAgent()

    def test_agent_properties(self):
        """Test agent metadata."""
        agent = self._make_agent()
        assert agent.name == "crypto"
        assert agent.emoji == "🪙"

    def test_extract_btc_symbol(self):
        """Test Bitcoin symbol extraction."""
        agent = self._make_agent()
        symbols = agent._extract_crypto_symbols("What's BTC trading at?")
        assert "bitcoin" in symbols

    def test_extract_by_name(self):
        """Test extraction by coin name."""
        agent = self._make_agent()
        symbols = agent._extract_crypto_symbols("What's bitcoin price?")
        assert "bitcoin" in symbols

        symbols = agent._extract_crypto_symbols("How is ethereum doing?")
        assert "ethereum" in symbols

    def test_extract_multiple_coins(self):
        """Test extracting multiple cryptocurrencies."""
        agent = self._make_agent()
        symbols = agent._extract_crypto_symbols("Compare BTC and ETH")
        assert "bitcoin" in symbols
        assert "ethereum" in symbols

    def test_extract_solana(self):
        """Test Solana extraction."""
        agent = self._make_agent()
        symbols = agent._extract_crypto_symbols("Is SOL a good investment?")
        assert "solana" in symbols

    def test_extract_no_crypto(self):
        """Test no crypto found returns empty."""
        agent = self._make_agent()
        symbols = agent._extract_crypto_symbols("What is AAPL trading at?")
        # Should not match stock tickers as crypto
        assert "bitcoin" not in symbols
        assert "ethereum" not in symbols

    def test_format_crypto_response_with_data(self):
        """Test formatting response with real-ish data."""
        agent = self._make_agent()

        data = {
            "prices": {
                "bitcoin": {
                    "usd": 97234.50,
                    "usd_24h_change": 2.35,
                    "usd_market_cap": 1900000000000,
                    "usd_24h_vol": 55000000000,
                },
                "ethereum": {
                    "usd": 3412.00,
                    "usd_24h_change": -1.20,
                    "usd_market_cap": 410000000000,
                    "usd_24h_vol": 18000000000,
                },
            },
            "coins": ["bitcoin", "ethereum"],
        }

        result = agent._format_crypto_response(data, "crypto prices")

        assert "content" in result
        assert "BTC" in result["content"]
        assert "ETH" in result["content"]
        assert "$97,234" in result["content"]
        assert "🟢" in result["content"]  # BTC is positive
        assert "🔴" in result["content"]  # ETH is negative
        assert "data" in result

    def test_format_crypto_empty_data(self):
        """Test formatting with no price data."""
        agent = self._make_agent()
        data = {"prices": {}}
        result = agent._format_crypto_response(data, "test")
        assert "Unable to fetch" in result["content"]

    def test_fallback_response(self):
        """Test fallback when no data is available."""
        agent = self._make_agent()
        response = agent._get_fallback_response()
        assert "BTC" in response or "Bitcoin" in response
        assert "volatile" in response.lower()

    def test_format_small_price(self):
        """Test formatting for coins with sub-dollar prices."""
        agent = self._make_agent()

        data = {
            "prices": {
                "cardano": {
                    "usd": 0.987654,
                    "usd_24h_change": 0.5,
                    "usd_market_cap": 35000000000,
                    "usd_24h_vol": 800000000,
                },
            },
            "coins": ["cardano"],
        }

        result = agent._format_crypto_response(data, "ADA price")
        assert "content" in result
        assert "ADA" in result["content"]

    def test_system_prompt_covers_key_areas(self):
        """Test that system prompt covers expected domains."""
        agent = self._make_agent()
        prompt = agent.system_prompt.lower()
        assert "price" in prompt
        assert "portfolio" in prompt or "allocation" in prompt
        assert "tax" in prompt

    @pytest.mark.asyncio
    async def test_process_with_mocked_coingecko(self):
        """Test full process with mocked CoinGecko API."""
        agent = self._make_agent()

        mock_data = {
            "bitcoin": {
                "usd": 97000,
                "usd_24h_change": 1.5,
                "usd_market_cap": 1900000000000,
                "usd_24h_vol": 55000000000,
            },
        }

        with patch("pycoingecko.CoinGeckoAPI") as mock_cg_class:
            mock_cg = MagicMock()
            mock_cg.get_price.return_value = mock_data
            mock_cg_class.return_value = mock_cg

            state = FinnieState(
                user_input="What's Bitcoin trading at?",
                session_id="test",
                agent_outputs=[],
            )

            result = await agent.process(state)
            assert "content" in result
            assert "BTC" in result["content"] or "Bitcoin" in result["content"]
