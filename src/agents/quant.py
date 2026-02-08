"""
Finnie AI — The Quant Agent

Handles market data, stock prices, and technical analysis.
"""

from typing import Any, Optional

import yfinance as yf

from src.agents.base import BaseFinnieAgent
from src.orchestration.state import FinnieState


class QuantAgent(BaseFinnieAgent):
    """
    The Quant — Market Data Specialist
    
    Fetches real-time stock prices, company fundamentals,
    and provides technical analysis.
    
    Triggers: Stock tickers mentioned, price queries, technical indicators
    """
    
    @property
    def name(self) -> str:
        return "quant"
    
    @property
    def description(self) -> str:
        return "Market data specialist providing real-time prices and technical analysis"
    
    @property
    def emoji(self) -> str:
        return "📊"
    
    @property
    def system_prompt(self) -> str:
        return """You are The Quant, Finnie AI's market data specialist.

Your role:
- Provide accurate, real-time stock market data
- Explain technical indicators clearly
- Present data in well-formatted tables
- Always cite the data source (yFinance)

Communication style:
- Precise and data-driven
- Use markdown tables for multi-value comparisons
- Include relevant metrics (P/E, Market Cap, 52-week range)
- Be concise but thorough

When presenting stock data:
1. Current price and daily change
2. Key metrics (P/E, Market Cap, Volume)
3. 52-week high/low
4. Brief context if relevant

Remember: You provide DATA, not investment advice."""
    
    async def process(self, state: FinnieState) -> dict[str, Any]:
        """
        Process a market data request.
        
        Uses pre-extracted tickers from state if available,
        otherwise extracts from user input.
        """
        user_input = state.get("user_input", "")
        
        # Use pre-extracted tickers if passed, otherwise extract ourselves
        tickers = state.get("tickers") or self._extract_tickers(user_input)
        
        if not tickers:
            return {
                "content": "I couldn't identify any stock tickers in your request. Please include ticker symbols like AAPL, MSFT, or GOOGL.",
                "data": None,
            }
        
        # Fetch data for each ticker
        data = {}
        for ticker in tickers[:5]:  # Limit to 5 tickers
            stock_data = self._fetch_stock_data(ticker)
            if stock_data:
                data[ticker] = stock_data
        
        if not data:
            return {
                "content": f"I couldn't find data for the ticker(s): {', '.join(tickers)}. Please verify the symbol(s).",
                "data": None,
            }
        
        # Format response
        content = self._format_response(data)
        
        return {
            "content": content,
            "data": data,
        }
    
    def _fetch_stock_data(self, ticker: str) -> Optional[dict]:
        """
        Fetch stock data using yfinance.
        
        Args:
            ticker: Stock ticker symbol.
            
        Returns:
            Dict with stock data or None if not found.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get current price data
            history = stock.history(period="1d")
            
            if history.empty:
                return None
            
            current_price = history['Close'].iloc[-1] if not history.empty else info.get('regularMarketPrice', 0)
            prev_close = info.get('previousClose', current_price)
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0
            
            return {
                "ticker": ticker,
                "name": info.get("shortName", ticker),
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "previous_close": round(prev_close, 2),
                "open": round(info.get("open", 0), 2),
                "day_high": round(info.get("dayHigh", 0), 2),
                "day_low": round(info.get("dayLow", 0), 2),
                "volume": info.get("volume", 0),
                "avg_volume": info.get("averageVolume", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("trailingEps"),
                "dividend_yield": info.get("dividendYield"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
            }
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
    
    def _format_response(self, data: dict[str, dict]) -> str:
        """
        Format stock data into a readable response.
        
        Args:
            data: Dict mapping tickers to their data.
            
        Returns:
            Markdown-formatted response string.
        """
        if len(data) == 1:
            # Single stock - detailed view
            ticker, info = next(iter(data.items()))
            return self._format_single_stock(info)
        else:
            # Multiple stocks - comparison table
            return self._format_comparison_table(data)
    
    def _format_single_stock(self, info: dict) -> str:
        """Format detailed info for a single stock."""
        change_emoji = "📈" if info["change"] >= 0 else "📉"
        change_sign = "+" if info["change"] >= 0 else ""
        
        response = f"""**{info['name']}** ({info['ticker']})

**Current Price:** ${info['price']:,.2f} {change_emoji} {change_sign}${info['change']:.2f} ({change_sign}{info['change_percent']:.2f}%)

| Metric | Value |
|--------|-------|
| Open | ${info['open']:,.2f} |
| Day Range | ${info['day_low']:,.2f} - ${info['day_high']:,.2f} |
| 52-Week Range | ${info['fifty_two_week_low']:,.2f} - ${info['fifty_two_week_high']:,.2f} |
| Volume | {info['volume']:,} |
| Market Cap | ${info['market_cap']:,} |"""

        if info.get('pe_ratio'):
            response += f"\n| P/E Ratio | {info['pe_ratio']:.2f} |"
        
        if info.get('eps'):
            response += f"\n| EPS | ${info['eps']:.2f} |"
        
        if info.get('dividend_yield'):
            response += f"\n| Dividend Yield | {info['dividend_yield']*100:.2f}% |"
        
        if info.get('sector'):
            response += f"\n\n**Sector:** {info['sector']}"
            if info.get('industry'):
                response += f" | **Industry:** {info['industry']}"
        
        return response
    
    def _format_comparison_table(self, data: dict[str, dict]) -> str:
        """Format comparison table for multiple stocks."""
        header = "| Metric |"
        separator = "|--------|"
        
        for ticker in data.keys():
            header += f" {ticker} |"
            separator += "--------|"
        
        rows = []
        
        # Price row
        price_row = "| Price |"
        for info in data.values():
            change_sign = "+" if info["change_percent"] >= 0 else ""
            price_row += f" ${info['price']:,.2f} ({change_sign}{info['change_percent']:.1f}%) |"
        rows.append(price_row)
        
        # Market Cap row
        cap_row = "| Market Cap |"
        for info in data.values():
            cap = info["market_cap"]
            if cap >= 1e12:
                cap_str = f"${cap/1e12:.1f}T"
            elif cap >= 1e9:
                cap_str = f"${cap/1e9:.1f}B"
            else:
                cap_str = f"${cap/1e6:.1f}M"
            cap_row += f" {cap_str} |"
        rows.append(cap_row)
        
        # P/E row
        pe_row = "| P/E Ratio |"
        for info in data.values():
            pe = info.get("pe_ratio")
            pe_row += f" {pe:.2f} |" if pe else " N/A |"
        rows.append(pe_row)
        
        # 52-week range
        range_row = "| 52W Range |"
        for info in data.values():
            low = info.get("fifty_two_week_low", 0)
            high = info.get("fifty_two_week_high", 0)
            range_row += f" ${low:.0f}-${high:.0f} |"
        rows.append(range_row)
        
        return f"{header}\n{separator}\n" + "\n".join(rows)
