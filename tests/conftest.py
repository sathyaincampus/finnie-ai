"""
Finnie AI — Test Suite Configuration

Pytest configuration and fixtures.
"""

import pytest
import asyncio
from unittest.mock import MagicMock


@pytest.fixture
def sample_state():
    """Create a sample FinnieState for testing."""
    from src.orchestration.state import create_initial_state
    
    return create_initial_state(
        user_input="What is AAPL trading at?",
        session_id="test-session-123",
        llm_provider="openai",
        llm_model="gpt-4o",
        llm_api_key="test-key",
    )


@pytest.fixture
def sample_portfolio():
    """Create sample portfolio data for testing."""
    return {
        "holdings": [
            {"ticker": "AAPL", "shares": 10, "value": 1500, "cost_basis": 100},
            {"ticker": "GOOGL", "shares": 5, "value": 700, "cost_basis": 120},
            {"ticker": "MSFT", "shares": 8, "value": 3200, "cost_basis": 350},
        ]
    }


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response."""
    from src.llm.adapter import LLMResponse
    
    return LLMResponse(
        content="This is a mock response from the LLM.",
        model="gpt-4o-mock",
        provider="openai",
        usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    )


@pytest.fixture
def mock_stock_data():
    """Create mock stock data."""
    return {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "price": 150.0,
        "change": 2.5,
        "change_percent": 1.69,
        "previous_close": 147.5,
        "open": 148.0,
        "day_high": 151.0,
        "day_low": 147.0,
        "volume": 50000000,
        "avg_volume": 45000000,
        "market_cap": 2500000000000,
        "pe_ratio": 28.5,
        "eps": 5.26,
        "dividend_yield": 0.005,
        "fifty_two_week_high": 180.0,
        "fifty_two_week_low": 120.0,
        "sector": "Technology",
        "industry": "Consumer Electronics",
    }


# =============================================================================
# Async test configuration
# =============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
