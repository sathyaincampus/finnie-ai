"""
Finnie AI — The Oracle Agent

Handles investment projections and Monte Carlo simulations.
"""

from typing import Any
import random
import math

from src.agents.base import BaseFinnieAgent
from src.orchestration.state import FinnieState


class OracleAgent(BaseFinnieAgent):
    """
    The Oracle — Projection Specialist
    
    Provides investment growth projections using Monte Carlo simulations.
    
    Triggers: "If I invest...", projection queries, growth calculations
    """
    
    @property
    def name(self) -> str:
        return "oracle"
    
    @property
    def description(self) -> str:
        return "Projection specialist using Monte Carlo simulations"
    
    @property
    def emoji(self) -> str:
        return "🔮"
    
    @property
    def system_prompt(self) -> str:
        return """You are The Oracle, Finnie AI's projection specialist.

Your role:
- Run Monte Carlo simulations for investment projections
- Explain assumptions and limitations
- Present conservative, expected, and optimistic scenarios
- Emphasize that projections are estimates, not predictions

Communication style:
- Data-driven and transparent
- Always explain assumptions
- Show range of outcomes
- Emphasize uncertainty and risk

When presenting projections:
1. State the inputs (initial, contribution, time, return)
2. Show three scenarios (conservative, expected, optimistic)
3. Explain what could affect outcomes
4. Remind about past performance not guaranteeing future results"""
    
    async def process(self, state: FinnieState) -> dict[str, Any]:
        """
        Process a projection request.
        
        Parses input for investment parameters and runs simulation.
        """
        user_input = state.get("user_input", "")
        
        # Try to extract parameters from input
        params = self._extract_parameters(user_input)
        
        if params:
            return self._run_projection(params)
        
        # Need more info
        return {
            "content": self._get_parameter_request(),
            "data": None,
        }
    
    def _extract_parameters(self, text: str) -> dict | None:
        """
        Extract investment parameters from user input.
        
        Returns dict with: initial, monthly, years, return_rate
        """
        import re
        
        params = {}
        
        # Extract initial investment
        initial_match = re.search(r'\$?([\d,]+)\s*(initial|start|invest)', text, re.IGNORECASE)
        if initial_match:
            params["initial"] = float(initial_match.group(1).replace(",", ""))
        
        # Extract monthly contribution
        monthly_match = re.search(r'\$?([\d,]+)\s*(month|per month|monthly)', text, re.IGNORECASE)
        if monthly_match:
            params["monthly"] = float(monthly_match.group(1).replace(",", ""))
        
        # Extract time period
        years_match = re.search(r'(\d+)\s*(year|yr)', text, re.IGNORECASE)
        if years_match:
            params["years"] = int(years_match.group(1))
        
        # Use defaults if not specified
        params.setdefault("initial", 10000)
        params.setdefault("monthly", 500)
        params.setdefault("years", 5)
        params.setdefault("return_rate", 0.08)  # 8% average
        
        return params if any([initial_match, monthly_match, years_match]) else None
    
    def _run_projection(self, params: dict) -> dict[str, Any]:
        """
        Run Monte Carlo simulation and return projection.
        """
        initial = params.get("initial", 10000)
        monthly = params.get("monthly", 500)
        years = params.get("years", 5)
        
        # Run simulation
        simulation = self._monte_carlo_simulation(initial, monthly, years)
        
        # Format response
        content = f"""**🔮 Investment Projection**

**Inputs:**
- Initial Investment: ${initial:,.2f}
- Monthly Contribution: ${monthly:,.2f}
- Time Horizon: {years} years

---

**Projected Outcomes:**

| Scenario | Final Value | Total Growth |
|----------|-------------|--------------|
| 📉 Conservative (10th percentile) | ${simulation['conservative']:,.2f} | {simulation['growth_conservative']:.1f}% |
| 📊 Expected (50th percentile) | ${simulation['expected']:,.2f} | {simulation['growth_expected']:.1f}% |
| 📈 Optimistic (90th percentile) | ${simulation['optimistic']:,.2f} | {simulation['growth_optimistic']:.1f}% |

**Total Contributions:** ${simulation['total_contributions']:,.2f}

---

**Assumptions:**
- Average annual return: 8% (historical S&P 500)
- Standard deviation: 18% (typical market volatility)
- Monthly compounding
- Dividends reinvested

⚠️ *Past performance does not guarantee future results. Actual outcomes may vary significantly.*"""

        return {
            "content": content,
            "data": {
                "params": params,
                "simulation": simulation,
            },
            "visualizations": [
                {
                    "type": "projection_chart",
                    "data": simulation,
                    "title": "Investment Projection"
                }
            ],
        }
    
    def _monte_carlo_simulation(
        self, 
        initial: float, 
        monthly: float, 
        years: int,
        num_simulations: int = 1000,
        annual_return: float = 0.08,
        annual_std: float = 0.18,
    ) -> dict:
        """
        Run Monte Carlo simulation for investment projection.
        
        Args:
            annual_return: Expected average annual return (e.g. 0.05 conservative, 0.12 aggressive)
            annual_std: Annual volatility / standard deviation
        """
        
        monthly_return = annual_return / 12
        monthly_std = annual_std / math.sqrt(12)
        
        months = years * 12
        total_contributions = initial + (monthly * months)
        
        final_values = []
        
        for _ in range(num_simulations):
            value = initial
            for _ in range(months):
                # Random return for this month
                month_return = random.gauss(monthly_return, monthly_std)
                value = value * (1 + month_return) + monthly
            final_values.append(value)
        
        final_values.sort()
        
        conservative = final_values[int(num_simulations * 0.10)]
        expected = final_values[int(num_simulations * 0.50)]
        optimistic = final_values[int(num_simulations * 0.90)]
        
        return {
            "conservative": conservative,
            "expected": expected,
            "optimistic": optimistic,
            "total_contributions": total_contributions,
            "growth_conservative": (conservative / total_contributions - 1) * 100,
            "growth_expected": (expected / total_contributions - 1) * 100,
            "growth_optimistic": (optimistic / total_contributions - 1) * 100,
        }
    
    def _get_parameter_request(self) -> str:
        """Ask user for projection parameters."""
        return """**🔮 Investment Projection Calculator**

To calculate your projection, please provide:

1. **Initial Investment** — How much are you starting with?
2. **Monthly Contribution** — How much will you add each month?
3. **Time Horizon** — How many years until you need the money?

**Example:** "If I invest $10,000 initially and add $500 monthly for 10 years"

Or just tell me your scenario and I'll run the numbers!"""
