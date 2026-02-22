"""
Finnie AI — Test Suite: UI Tabs

Tests for the modular UI tab calculator logic.
"""

import pytest


class TestProjectionCalculations:
    """Test projection calculation logic."""

    def test_monte_carlo_simulation(self):
        """Test Monte Carlo returns valid distribution."""
        from src.agents.oracle import OracleAgent

        agent = OracleAgent()
        result = agent._monte_carlo_simulation(
            initial=50000,
            monthly=1000,
            years=20,
            num_simulations=100,
        )

        assert result["conservative"] < result["expected"] < result["optimistic"]
        assert result["total_contributions"] == 50000 + (1000 * 20 * 12)
        # After 20 years with 8% return, expected should exceed contributions
        assert result["expected"] > result["total_contributions"]

    def test_goal_based_calculation(self):
        """Test goal-based reverse projection math."""
        import math

        target = 1_000_000
        current_savings = 50000
        years = 25
        rate = 0.08

        months = years * 12
        monthly_rate = rate / 12

        fv_current = current_savings * ((1 + monthly_rate) ** months)
        remaining = max(0, target - fv_current)

        monthly_needed = remaining * monthly_rate / (((1 + monthly_rate) ** months) - 1)

        # At 8% over 25 years, $50K grows to ~$342K
        # Need ~$658K more from monthly contributions
        # Monthly needed should be reasonable (< $2000)
        assert monthly_needed > 100
        assert monthly_needed < 2000

        # Verify total reaches target
        balance = current_savings
        for _ in range(months):
            balance = balance * (1 + monthly_rate) + monthly_needed
        assert abs(balance - target) < 100  # Within $100 of target

    def test_529_compound_growth(self):
        """Test 529 plan compound growth calculation."""
        monthly = 200
        years = 13  # Start at age 5, college at 18
        monthly_rate = 0.07 / 12
        months = years * 12

        fv = 0
        for _ in range(months):
            fv = (fv + monthly) * (1 + monthly_rate)

        # $200/month for 13 years at 7% should grow to ~$55K
        assert fv > 45000
        assert fv < 65000
        # Should be more than raw contributions ($200 * 156 = $31,200)
        assert fv > monthly * months

    def test_retirement_4pct_rule(self):
        """Test 4% withdrawal rule calculation."""
        projected_balance = 2_000_000
        annual_income = projected_balance * 0.04
        monthly_income = annual_income / 12

        assert annual_income == 80000
        assert abs(monthly_income - 6666.67) < 1

    def test_tax_bracket_basic(self):
        """Test federal tax bracket calculation (single filer)."""
        brackets = [
            (11925, 0.10),
            (48475, 0.12),
            (103350, 0.22),
            (197300, 0.24),
        ]

        # $100K taxable income
        taxable = 100000
        tax = 0
        prev = 0
        for limit, rate in brackets:
            taxable_in_bracket = min(taxable, limit) - prev
            if taxable_in_bracket > 0:
                tax += taxable_in_bracket * rate
            prev = limit

        # Approximate check: $100K single, ~$17K in tax
        assert tax > 15000
        assert tax < 20000


class TestCryptoSymbolMapping:
    """Test crypto symbol mapping and formatting."""

    def test_crypto_map_exists(self):
        """Test that CRYPTO_MAP is properly defined."""
        from src.agents.crypto import CRYPTO_MAP
        assert "BTC" in CRYPTO_MAP
        assert "ETH" in CRYPTO_MAP
        assert "SOL" in CRYPTO_MAP

    def test_crypto_map_structure(self):
        """Test CRYPTO_MAP entries have correct tuple format."""
        from src.agents.crypto import CRYPTO_MAP
        for symbol, (gecko_id, name) in CRYPTO_MAP.items():
            assert isinstance(gecko_id, str)
            assert isinstance(name, str)
            assert len(gecko_id) > 0
            assert len(name) > 0


class TestPlannerDetectionCoverage:
    """Edge cases for planner detection."""

    def test_mixed_signals(self):
        """Test queries with multiple domain keywords."""
        from src.agents.planner import PlannerAgent
        agent = PlannerAgent()

        # First keyword match wins
        result = agent._detect_planning_type("401k tax implications for retirement")
        assert result in ("retirement", "tax")  # Either is acceptable

    def test_case_insensitivity(self):
        """Test that detection is case-insensitive."""
        from src.agents.planner import PlannerAgent
        agent = PlannerAgent()

        assert agent._detect_planning_type("RETIREMENT planning") == "retirement"
        assert agent._detect_planning_type("H1B visa") == "visa"
        assert agent._detect_planning_type("ROTH IRA") == "retirement"
