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
        
        Supports both forward projections and goal-based reverse projections.
        """
        user_input = state.get("enhanced_input", state.get("user_input", ""))
        
        # Check for goal-based projection first
        goal_params = self._extract_goal_parameters(user_input)
        if goal_params:
            return self._run_goal_projection(goal_params)
        
        # Try standard forward projection
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
    
    def _extract_goal_parameters(self, text: str) -> dict | None:
        """
        Extract goal-based projection parameters.
        
        Patterns:
        - "I need $1M by age 55"
        - "I want to save $500K in 15 years"
        - "How much monthly to reach $250K by 2040"
        """
        import re
        
        text_lower = text.lower()
        
        # Check for goal-based keywords
        goal_keywords = ["need", "want", "goal", "target", "reach", "save for", "have"]
        if not any(kw in text_lower for kw in goal_keywords):
            return None
        
        params = {}
        
        # Extract target amount ($1M, $500K, $1,000,000, etc.)
        amount_match = re.search(
            r'\$?([\d,]+)\s*([mMkK])?\b', text
        )
        if amount_match:
            amount = float(amount_match.group(1).replace(",", ""))
            multiplier = amount_match.group(2)
            if multiplier and multiplier.upper() == "M":
                amount *= 1_000_000
            elif multiplier and multiplier.upper() == "K":
                amount *= 1_000
            params["target_amount"] = amount
        
        # Extract "by age X"
        age_match = re.search(r'by\s+age\s+(\d+)', text, re.IGNORECASE)
        if age_match:
            target_age = int(age_match.group(1))
            # Estimate current age from text or default to 30
            current_age_match = re.search(r"i(?:'m| am)\s+(\d+)", text, re.IGNORECASE)
            current_age = int(current_age_match.group(1)) if current_age_match else 30
            params["years_to_goal"] = max(1, target_age - current_age)
            params["current_age"] = current_age
            params["target_age"] = target_age
        
        # Extract "in X years"
        if "years_to_goal" not in params:
            years_match = re.search(r'(?:in|within|next)\s+(\d+)\s+year', text, re.IGNORECASE)
            if years_match:
                params["years_to_goal"] = int(years_match.group(1))
        
        # Extract current savings
        savings_match = re.search(
            r'(?:have|saved|currently have|start with)\s+\$?([\d,]+)', text, re.IGNORECASE
        )
        params["current_savings"] = float(savings_match.group(1).replace(",", "")) if savings_match else 0
        
        # Risk profile
        if any(w in text_lower for w in ["aggressive", "high risk", "growth"]):
            params["risk_profile"] = "aggressive"
        elif any(w in text_lower for w in ["conservative", "safe", "low risk"]):
            params["risk_profile"] = "conservative"
        else:
            params["risk_profile"] = "moderate"
        
        # Need at least target amount and timeframe
        if "target_amount" in params and "years_to_goal" in params:
            return params
        
        return None
    
    def _run_goal_projection(self, params: dict) -> dict[str, Any]:
        """Run reverse projection: how much to invest monthly to reach a goal."""
        target = params["target_amount"]
        years = params["years_to_goal"]
        current = params.get("current_savings", 0)
        risk = params.get("risk_profile", "moderate")
        
        simulation = self._goal_based_simulation(target, years, current, risk)
        
        risk_emoji = {"conservative": "📉", "moderate": "📊", "aggressive": "📈"}.get(risk, "📊")
        
        content = f"""**🔮 Goal-Based Investment Projection**

**Your Goal:**
- Target Amount: ${target:,.0f}
- Time Horizon: {years} years{f" (age {params.get('current_age', '?')} → {params.get('target_age', '?')})" if 'target_age' in params else ''}
- Current Savings: ${current:,.0f}
- Risk Profile: {risk_emoji} {risk.title()}

---

**Required Monthly Investment:**

| Scenario | Monthly Needed | Annual Return | Final Value |
|----------|---------------|---------------|-------------|
| 📉 Conservative | ${simulation['monthly_conservative']:,.0f} | {simulation['return_conservative']:.1f}% | ${target:,.0f} |
| 📊 Expected | ${simulation['required_monthly']:,.0f} | {simulation['return_expected']:.1f}% | ${target:,.0f} |
| 📈 Aggressive | ${simulation['monthly_aggressive']:,.0f} | {simulation['return_aggressive']:.1f}% | ${target:,.0f} |

**Total Contributions (Expected):** ${simulation['total_contributions']:,.0f}
**Investment Growth:** ${target - simulation['total_contributions']:,.0f} ({simulation['growth_pct']:.0f}% gain)

---

**Action Plan:**
1. Set up automatic monthly transfer of **${simulation['required_monthly']:,.0f}**
2. Use tax-advantaged accounts (401K, Roth IRA) first
3. Invest in diversified index funds (S&P 500, total market)
4. Review and rebalance annually

⚠️ *Projections assume consistent contributions and average market returns. Actual results will vary.*"""
        
        return {
            "content": content,
            "data": {
                "params": params,
                "simulation": simulation,
                "projection_type": "goal_based",
            },
            "visualizations": [
                {
                    "type": "goal_projection_chart",
                    "data": simulation,
                    "title": f"Path to ${target:,.0f}",
                }
            ],
        }
    
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
    
    def _goal_based_simulation(
        self,
        target_amount: float,
        years_to_goal: int,
        current_savings: float = 0,
        risk_profile: str = "moderate",
    ) -> dict:
        """
        Reverse Monte Carlo: calculate required monthly contribution to reach a goal.
        
        Args:
            target_amount: How much money is needed.
            years_to_goal: How many years to reach the goal.
            current_savings: Current savings amount.
            risk_profile: conservative, moderate, or aggressive.
        """
        # Return assumptions by risk profile
        profiles = {
            "conservative": {"return": 0.06, "std": 0.10},
            "moderate": {"return": 0.08, "std": 0.15},
            "aggressive": {"return": 0.10, "std": 0.20},
        }
        
        profile = profiles.get(risk_profile, profiles["moderate"])
        annual_return = profile["return"]
        
        months = years_to_goal * 12
        monthly_rate = annual_return / 12
        
        # Future value of current savings
        fv_current = current_savings * ((1 + monthly_rate) ** months)
        
        # Remaining amount needed from contributions
        remaining = max(0, target_amount - fv_current)
        
        # Required monthly contribution (annuity formula)
        if monthly_rate > 0 and months > 0:
            required_monthly = remaining * monthly_rate / (((1 + monthly_rate) ** months) - 1)
        else:
            required_monthly = remaining / max(months, 1)
        
        total_contributions = current_savings + (required_monthly * months)
        
        # Also calculate for other risk profiles
        monthly_by_profile = {}
        for p_name, p_data in profiles.items():
            p_rate = p_data["return"] / 12
            fv = current_savings * ((1 + p_rate) ** months)
            rem = max(0, target_amount - fv)
            if p_rate > 0 and months > 0:
                monthly_by_profile[p_name] = rem * p_rate / (((1 + p_rate) ** months) - 1)
            else:
                monthly_by_profile[p_name] = rem / max(months, 1)
        
        return {
            "required_monthly": required_monthly,
            "total_contributions": total_contributions,
            "target_amount": target_amount,
            "growth_pct": ((target_amount / total_contributions) - 1) * 100 if total_contributions > 0 else 0,
            "monthly_conservative": monthly_by_profile.get("conservative", required_monthly),
            "monthly_aggressive": monthly_by_profile.get("aggressive", required_monthly),
            "return_conservative": profiles["conservative"]["return"] * 100,
            "return_expected": profiles[risk_profile]["return"] * 100,
            "return_aggressive": profiles["aggressive"]["return"] * 100,
        }
    
    def _get_parameter_request(self) -> str:
        """Ask user for projection parameters."""
        return """**🔮 Investment Projection Calculator**

I can help you with **two types** of projections:

**📊 Forward Projection** — "What will my money grow to?"
> Example: "If I invest $10,000 initially and add $500 monthly for 10 years"

**🎯 Goal-Based** — "How much do I need to invest?"
> Example: "I need $1M by age 55, currently have $50K saved"

Tell me your scenario and I'll run the numbers!"""
