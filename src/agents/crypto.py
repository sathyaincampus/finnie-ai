"""
Finnie AI — The Crypto Agent

Real-time cryptocurrency data, portfolio allocation, tax implications,
and market analysis using CoinGecko API.
"""

from typing import Any

from src.agents.base import BaseFinnieAgent
from src.orchestration.state import FinnieState


# Top cryptocurrencies with their CoinGecko IDs
CRYPTO_MAP = {
    "BTC": ("bitcoin", "Bitcoin"),
    "ETH": ("ethereum", "Ethereum"),
    "SOL": ("solana", "Solana"),
    "BNB": ("binancecoin", "BNB"),
    "XRP": ("ripple", "XRP"),
    "ADA": ("cardano", "Cardano"),
    "DOGE": ("dogecoin", "Dogecoin"),
    "AVAX": ("avalanche-2", "Avalanche"),
    "DOT": ("polkadot", "Polkadot"),
    "LINK": ("chainlink", "Chainlink"),
    "MATIC": ("matic-network", "Polygon"),
    "UNI": ("uniswap", "Uniswap"),
    "ATOM": ("cosmos", "Cosmos"),
    "LTC": ("litecoin", "Litecoin"),
    "NEAR": ("near", "NEAR Protocol"),
    "APT": ("aptos", "Aptos"),
    "ARB": ("arbitrum", "Arbitrum"),
    "OP": ("optimism", "Optimism"),
    "SUI": ("sui", "Sui"),
    "PEPE": ("pepe", "Pepe"),
}


class CryptoAgent(BaseFinnieAgent):
    """
    The Crypto Agent — Cryptocurrency Specialist
    
    Provides:
    - Real-time crypto prices via CoinGecko API
    - Portfolio allocation suggestions (crypto %)
    - Tax implications of crypto transactions
    - Market analysis and trend identification
    - Staking/yield opportunities overview
    
    Triggers: bitcoin, ethereum, crypto, blockchain, BTC, ETH, defi, nft
    """
    
    @property
    def name(self) -> str:
        return "crypto"
    
    @property
    def description(self) -> str:
        return "Cryptocurrency specialist — prices, allocation, tax, analysis"
    
    @property
    def emoji(self) -> str:
        return "🪙"
    
    @property
    def system_prompt(self) -> str:
        return """You are The Crypto Agent, Finnie AI's cryptocurrency specialist.

Your role:
- Provide crypto market analysis and price information
- Suggest portfolio allocation for crypto (typically 1-10% of total)
- Explain crypto tax implications clearly
- Cover DeFi, staking, yield farming basics
- Compare crypto investment to traditional assets

Key knowledge areas:
1. MARKET DATA: Real-time prices, market cap, 24h volume, 7d change
2. PORTFOLIO ALLOCATION:
   - Conservative: 1-3% crypto (BTC/ETH only)
   - Moderate: 3-7% crypto (BTC, ETH, SOL, top 10)
   - Aggressive: 7-15% crypto (includes altcoins)
3. TAX RULES (US):
   - Crypto is property for tax purposes
   - Short-term gains (<1 year): ordinary income rates
   - Long-term gains (>1 year): 0%, 15%, or 20%
   - Every swap/sale is a taxable event
   - Mining/staking income is ordinary income
4. SECURITY: Hardware wallets, exchange risks, self-custody
5. STAKING: ETH staking (~3-4% APY), SOL staking (~6-7% APY)

Communication style:
- Clear and educational
- Always mention volatility risks
- Compare to traditional assets for context
- Use specific numbers and percentages

When presenting crypto data:
1. Show current price and key metrics
2. Provide context (52-week range, trend)
3. Discuss risk factors
4. Suggest allocation based on risk profile
5. Mention tax implications"""
    
    async def process(self, state: FinnieState) -> dict[str, Any]:
        """
        Process a crypto-related query.
        
        Fetches live data when available, falls back to LLM knowledge.
        """
        user_input = state.get("enhanced_input", state.get("user_input", ""))
        
        # Try to fetch live crypto data
        crypto_data = self._fetch_crypto_data(user_input)
        
        if crypto_data:
            # Build response with live data
            return self._format_crypto_response(crypto_data, user_input)
        
        # Fallback to LLM for analysis/education
        try:
            response = await self._call_llm(
                state=state,
                messages=[
                    {"role": "user", "content": user_input}
                ],
            )
            return {"content": response, "data": None}
        except Exception:
            return {"content": self._get_fallback_response(), "data": None}
    
    def _fetch_crypto_data(self, query: str) -> dict | None:
        """Fetch real-time crypto data from CoinGecko."""
        try:
            from pycoingecko import CoinGeckoAPI
            cg = CoinGeckoAPI()
            
            # Detect which coins user is asking about
            coins = self._extract_crypto_symbols(query)
            
            if not coins:
                # Default to top coins overview
                coins = ["bitcoin", "ethereum", "solana"]
            
            # Fetch price data
            ids = ",".join(coins)
            data = cg.get_price(
                ids=ids,
                vs_currencies="usd",
                include_market_cap=True,
                include_24hr_vol=True,
                include_24hr_change=True,
            )
            
            return {"prices": data, "coins": coins}
            
        except ImportError:
            return None
        except Exception:
            return None
    
    def _extract_crypto_symbols(self, text: str) -> list[str]:
        """Extract cryptocurrency identifiers from text."""
        text_upper = text.upper()
        found = []
        
        # Check for symbol mentions (BTC, ETH, etc.)
        for symbol, (gecko_id, _) in CRYPTO_MAP.items():
            if symbol in text_upper:
                found.append(gecko_id)
        
        # Check for name mentions
        text_lower = text.lower()
        name_map = {
            "bitcoin": "bitcoin",
            "ethereum": "ethereum",
            "solana": "solana",
            "dogecoin": "dogecoin",
            "cardano": "cardano",
            "ripple": "ripple",
            "polkadot": "polkadot",
            "avalanche": "avalanche-2",
            "chainlink": "chainlink",
            "polygon": "matic-network",
        }
        for name, gecko_id in name_map.items():
            if name in text_lower and gecko_id not in found:
                found.append(gecko_id)
        
        return found
    
    def _format_crypto_response(self, data: dict, query: str) -> dict[str, Any]:
        """Format crypto data into a rich response."""
        prices = data.get("prices", {})
        
        if not prices:
            return {"content": "Unable to fetch crypto data.", "data": None}
        
        # Build table
        rows = []
        for coin_id, info in prices.items():
            # Find display name
            display_name = coin_id.title()
            symbol = coin_id.upper()[:4]
            for sym, (gid, name) in CRYPTO_MAP.items():
                if gid == coin_id:
                    display_name = name
                    symbol = sym
                    break
            
            price = info.get("usd", 0)
            change_24h = info.get("usd_24h_change", 0)
            market_cap = info.get("usd_market_cap", 0)
            volume = info.get("usd_24h_vol", 0)
            
            # Format price based on magnitude
            if price >= 1000:
                price_str = f"${price:,.2f}"
            elif price >= 1:
                price_str = f"${price:.2f}"
            else:
                price_str = f"${price:.6f}"
            
            change_emoji = "🟢" if change_24h >= 0 else "🔴"
            
            rows.append(
                f"| {symbol} | {display_name} | {price_str} | "
                f"{change_emoji} {change_24h:+.2f}% | "
                f"${market_cap/1e9:.1f}B | ${volume/1e6:.0f}M |"
            )
        
        table = (
            "| Symbol | Name | Price | 24h Change | Market Cap | Volume |\n"
            "|--------|------|-------|------------|------------|--------|\n"
            + "\n".join(rows)
        )
        
        content = f"""**🪙 Crypto Market Data**

{table}

---

**Portfolio Allocation Guide:**
| Risk Profile | Suggested Crypto % | Focus |
|-------------|-------------------|-------|
| 📉 Conservative | 1-3% | BTC, ETH only |
| 📊 Moderate | 3-7% | BTC, ETH, SOL, top 10 |
| 📈 Aggressive | 7-15% | Includes altcoins |

**Tax Reminder:** Every crypto sale/swap is a taxable event in the US.
- Hold >1 year for long-term capital gains rates (0%, 15%, 20%)
- Short-term gains taxed as ordinary income

⚠️ *Cryptocurrency is highly volatile. This is educational, not financial advice.*"""
        
        return {
            "content": content,
            "data": {
                "prices": prices,
                "coins": data.get("coins", []),
            },
            "visualizations": [
                {
                    "type": "crypto_overview",
                    "data": prices,
                    "title": "Crypto Market Overview",
                }
            ],
        }
    
    def _get_fallback_response(self) -> str:
        """Return a fallback response when data is unavailable."""
        return """**🪙 Crypto Overview**

I can help you with cryptocurrency topics:

- **Prices:** Real-time data for BTC, ETH, SOL, and 20+ coins
- **Allocation:** How much crypto belongs in your portfolio  
- **Tax:** Understanding crypto tax obligations
- **Staking:** Earning yield on your holdings
- **DeFi:** Decentralized finance basics

Try asking: "What's Bitcoin trading at?" or "How much crypto should I hold?"

⚠️ *Cryptocurrency is highly volatile. This is educational, not financial advice.*"""
