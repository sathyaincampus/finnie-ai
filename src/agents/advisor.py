"""
Finnie AI — The Advisor Agent

Handles portfolio analysis and investment guidance.
"""

from typing import Any

from src.agents.base import BaseFinnieAgent
from src.orchestration.state import FinnieState


class AdvisorAgent(BaseFinnieAgent):
    """
    The Advisor — Portfolio Management Specialist
    
    Analyzes portfolio allocation, calculates metrics,
    and provides rebalancing suggestions.
    
    Triggers: Portfolio queries, allocation questions, risk assessment
    """
    
    @property
    def name(self) -> str:
        return "advisor"
    
    @property
    def description(self) -> str:
        return "Portfolio specialist providing allocation analysis and guidance"
    
    @property
    def emoji(self) -> str:
        return "💼"
    
    @property
    def system_prompt(self) -> str:
        return """You are The Advisor, Finnie AI's portfolio management specialist.

Your role:
- Analyze portfolio composition and allocation
- Calculate key risk metrics
- Suggest rebalancing strategies
- Provide diversification insights

Communication style:
- Professional but accessible
- Use data to support observations
- Present balanced perspectives
- Always emphasize risk awareness

When analyzing portfolios:
1. Summarize current allocation by asset class/sector
2. Identify concentration risks
3. Compare to common benchmarks
4. Suggest improvements (not specific trades)

Remember: You educate about portfolio concepts, you don't give specific investment advice.
Always remind users to consult a licensed financial advisor for personalized guidance."""
    
    async def process(self, state: FinnieState) -> dict[str, Any]:
        """
        Process a portfolio-related request.
        """
        user_input = state.get("user_input", "")
        portfolio_data = state.get("portfolio_data")
        
        if portfolio_data:
            return self._analyze_portfolio(portfolio_data)
        
        if not state.get("llm_api_key"):
            return {
                "content": self._get_no_portfolio_response(),
                "data": None,
            }
        
        # Use LLM for general portfolio discussion
        messages = [
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = await self._call_llm(state, messages)
            return {
                "content": response,
                "data": None,
            }
        except Exception:
            return {
                "content": self._get_no_portfolio_response(),
                "data": None,
            }
    
    def _analyze_portfolio(self, portfolio: dict) -> dict[str, Any]:
        """
        Analyze a user's portfolio.
        
        Args:
            portfolio: Dict with holdings data.
            
        Returns:
            Analysis results.
        """
        holdings = portfolio.get("holdings", [])
        
        if not holdings:
            return {
                "content": "Your portfolio appears to be empty. Would you like to add some holdings?",
                "data": None,
            }
        
        # Calculate totals
        total_value = sum(h.get("value", 0) for h in holdings)
        
        # Calculate allocation
        allocations = []
        for h in holdings:
            pct = (h.get("value", 0) / total_value * 100) if total_value else 0
            allocations.append({
                "ticker": h.get("ticker", "Unknown"),
                "value": h.get("value", 0),
                "percent": round(pct, 1),
            })
        
        # Sort by allocation
        allocations.sort(key=lambda x: x["percent"], reverse=True)
        
        # Format response
        content = f"""**Portfolio Analysis**

**Total Value:** ${total_value:,.2f}

**Allocation:**
"""
        for a in allocations:
            bar = "█" * int(a["percent"] / 5)  # Visual bar
            content += f"- **{a['ticker']}**: {a['percent']}% (${a['value']:,.2f}) {bar}\n"
        
        # Add insights
        if allocations and allocations[0]["percent"] > 40:
            content += f"\n⚠️ **Concentration Alert:** {allocations[0]['ticker']} represents over 40% of your portfolio.\n"
        
        content += "\n*For personalized advice, please consult a licensed financial advisor.*"
        
        return {
            "content": content,
            "data": {
                "total_value": total_value,
                "allocations": allocations,
            },
        }
    
    def _get_no_portfolio_response(self) -> str:
        """Response when no portfolio data is available."""
        return """**Portfolio Analysis**

I don't have your portfolio data yet. To get personalized analysis:

1. **Add Holdings** in the Portfolio tab
2. Enter your stock positions and quantities
3. I'll analyze your allocation and provide insights

**In the meantime, here are some general portfolio concepts:**

📊 **Diversification** — Spread investments across asset classes
⚖️ **Rebalancing** — Periodically adjust to maintain target allocation
🎯 **Risk Tolerance** — Match investments to your comfort level

*Would you like me to explain any of these concepts in detail?*"""
