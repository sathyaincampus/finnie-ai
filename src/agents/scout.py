"""
Finnie AI — The Scout Agent

Handles trend discovery and market movers.
"""

from typing import Any

import yfinance as yf

from src.agents.base import BaseFinnieAgent
from src.orchestration.state import FinnieState


class ScoutAgent(BaseFinnieAgent):
    """
    The Scout — Trend Discovery Specialist
    
    Discovers trending stocks, sectors, and market themes.
    
    Triggers: "What's trending...", "Hot stocks", market movers
    """
    
    @property
    def name(self) -> str:
        return "scout"
    
    @property
    def description(self) -> str:
        return "Trend discovery specialist tracking market movers"
    
    @property
    def emoji(self) -> str:
        return "🌍"
    
    @property
    def system_prompt(self) -> str:
        return """You are The Scout, Finnie AI's trend discovery specialist.

Your role:
- Track market movers and trending stocks
- Identify sector rotations and themes
- Surface interesting market developments
- Explain why things are trending

Communication style:
- Energetic and informative
- Use data to back up trends
- Include context on why things move
- Connect trends to bigger themes

When presenting trends:
1. List top movers with data
2. Explain the catalyst if known
3. Mention related opportunities/risks
4. Connect to broader market context"""
    
    async def process(self, state: FinnieState) -> dict[str, Any]:
        """
        Process a trend discovery request.
        
        Detects timeframe from user input and fetches movers accordingly.
        """
        user_input = state.get("user_input", "").lower()
        period, period_label = self._detect_period(user_input)
        
        trending = self._get_market_movers(period)
        
        if trending:
            trending["period_label"] = period_label
            content = self._format_trending(trending)
            return {
                "content": content,
                "data": trending,
            }
        
        return {
            "content": self._get_fallback_response(),
            "data": None,
        }
    
    def _detect_period(self, text: str) -> tuple[str, str]:
        """Detect the requested time period from user text.
        
        Returns (yfinance_period, human_label).
        For forward-looking questions, uses recent data with appropriate framing.
        """
        text = text.lower()
        # Forward-looking (predictions) — show recent momentum as context
        if any(p in text for p in ["tomorrow", "next week", "next month", "on monday",
                                    "on tuesday", "on wednesday", "on thursday", "on friday",
                                    "will move", "predict", "forecast", "outlook", "going to"]):
            return "5d", "Recent Momentum (past 5 days)"
        elif any(p in text for p in ["last week", "past week", "1 week", "this week", "5 day", "5 days"]):
            return "5d", "Past Week"
        elif any(p in text for p in ["last month", "past month", "1 month", "this month", "30 day"]):
            return "1mo", "Past Month"
        elif any(p in text for p in ["last 3 month", "3 months", "quarter", "past quarter"]):
            return "3mo", "Past 3 Months"
        elif any(p in text for p in ["last 6 month", "6 months", "half year"]):
            return "6mo", "Past 6 Months"
        elif any(p in text for p in ["last year", "past year", "1 year", "12 month", "this year", "ytd"]):
            return "1y", "Past Year"
        else:
            return "1d", "Today"

    def _get_market_movers(self, period: str = "1d") -> dict | None:
        """
        Get market movers using major tickers.
        
        Args:
            period: yfinance period string (1d, 5d, 1mo, etc.)
        """
        try:
            tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOGL"]
            
            movers = []
            for ticker in tickers:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                info = stock.info
                
                if not hist.empty and len(hist) >= 1:
                    current = hist['Close'].iloc[-1]
                    start = hist['Close'].iloc[0] if len(hist) > 1 else info.get('previousClose', current)
                    change_pct = ((current - start) / start * 100) if start else 0
                    
                    movers.append({
                        "ticker": ticker,
                        "name": info.get("shortName", ticker),
                        "price": round(current, 2),
                        "change_percent": round(change_pct, 2),
                    })
            
            movers.sort(key=lambda x: abs(x["change_percent"]), reverse=True)
            
            return {
                "top_gainers": [m for m in movers if m["change_percent"] > 0][:3],
                "top_losers": [m for m in movers if m["change_percent"] < 0][:3],
                "all_movers": movers,
            }
        except Exception as e:
            print(f"Error fetching market movers: {e}")
            return None
    
    def _format_trending(self, data: dict) -> str:
        """Format trending data into response."""
        period_label = data.get("period_label", "Today")
        content = f"**🌍 Market Movers — {period_label}**\n\n"
        
        if data.get("top_gainers"):
            content += "**📈 Top Gainers:**\n"
            for stock in data["top_gainers"]:
                content += f"- **{stock['ticker']}** ({stock['name']}): "
                content += f"${stock['price']:.2f} ({stock['change_percent']:+.1f}%)\n"
            content += "\n"
        
        if data.get("top_losers"):
            content += "**📉 Top Losers:**\n"
            for stock in data["top_losers"]:
                content += f"- **{stock['ticker']}** ({stock['name']}): "
                content += f"${stock['price']:.2f} ({stock['change_percent']:+.1f}%)\n"
            content += "\n"
        
        content += "*Showing major tech & index movers. Ask about a specific sector for more!*"
        
        # Add context for prediction-style questions
        if "Momentum" in period_label:
            content += "\n\n💡 *I can't predict the future, but stocks with strong recent momentum often continue their trend. Watch for earnings reports and macro events that could shift direction.*"
        
        return content
    
    def _get_fallback_response(self) -> str:
        """Fallback when data isn't available."""
        return """**🌍 Market Trends**

I'm having trouble fetching live market data right now.

**What I can track:**
- Top gainers and losers
- Sector movements
- Popular stock activity
- Index performance (SPY, QQQ, DIA)

**Try asking about:**
- "What's moving in tech today?"
- "How did the market move last week?"
- "Show me today's biggest gainers"

*Real-time data integration in progress!*"""

