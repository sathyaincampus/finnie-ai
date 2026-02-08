"""
Finnie AI — The Analyst Agent

Handles news, research, and sentiment analysis.
"""

from typing import Any

from src.agents.base import BaseFinnieAgent
from src.orchestration.state import FinnieState


class AnalystAgent(BaseFinnieAgent):
    """
    The Analyst — Research & Sentiment Specialist
    
    Provides market news, research summaries, and sentiment analysis.
    
    Triggers: "News about...", research queries, sentiment analysis
    """
    
    @property
    def name(self) -> str:
        return "analyst"
    
    @property
    def description(self) -> str:
        return "Research specialist providing news and sentiment analysis"
    
    @property
    def emoji(self) -> str:
        return "🔍"
    
    @property
    def system_prompt(self) -> str:
        return """You are The Analyst, Finnie AI's research and sentiment specialist.

Your role:
- Provide relevant market news and developments
- Analyze sentiment around stocks and sectors
- Summarize research findings concisely
- Identify key factors affecting market movements

Communication style:
- Objective and fact-based
- Present multiple perspectives
- Use bullet points for news items
- Include source attribution when possible

When providing analysis:
1. Lead with the most important news
2. Provide context on why it matters
3. Include sentiment indicators (bullish/bearish/neutral)
4. Mention potential implications

Remember: You analyze and inform, you don't predict or advise."""
    
    async def process(self, state: FinnieState) -> dict[str, Any]:
        """
        Process a news/research request.
        
        For MVP, provides structured response about available analysis.
        Future: integrate with news APIs and sentiment models.
        """
        user_input = state.get("user_input", "")
        tickers = self._extract_tickers(user_input)
        
        if not state.get("llm_api_key"):
            return {
                "content": self._get_placeholder_response(tickers),
                "data": {"tickers": tickers},
            }
        
        # Use LLM for analysis
        messages = [
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = await self._call_llm(state, messages)
            return {
                "content": response,
                "data": {"tickers": tickers, "analyzed": True},
            }
        except Exception as e:
            return {
                "content": self._get_placeholder_response(tickers),
                "data": {"tickers": tickers, "error": str(e)},
            }
    
    def _get_placeholder_response(self, tickers: list[str]) -> str:
        """Placeholder response when news API is not available."""
        if tickers:
            ticker_str = ", ".join(tickers)
            return f"""**Market Analysis for {ticker_str}**

I'm currently unable to fetch live news data. Here's what I can tell you:

**General Market Context:**
- 📊 Markets are operating during normal hours
- 🔄 For live news, check financial news sources directly

**Suggested Sources:**
- Yahoo Finance: finance.yahoo.com
- MarketWatch: marketwatch.com
- Reuters: reuters.com/business

*Live news integration coming soon!*"""
        else:
            return """**Market Analysis**

I'd be happy to analyze market news and sentiment! Please specify:
- A stock ticker (e.g., AAPL, TSLA)
- A sector (e.g., "tech news", "energy sector")
- A topic (e.g., "Fed interest rates", "earnings season")

*Live news integration coming soon!*"""
