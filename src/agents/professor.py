"""
Finnie AI — The Professor Agent

Handles financial education and concept explanations.
"""

from typing import Any

from src.agents.base import BaseFinnieAgent
from src.orchestration.state import FinnieState


class ProfessorAgent(BaseFinnieAgent):
    """
    The Professor — Financial Educator
    
    Explains financial concepts in clear, accessible language.
    Makes complex topics understandable for all experience levels.
    
    Triggers: "What is...", "Explain...", "How does...", educational queries
    """
    
    @property
    def name(self) -> str:
        return "professor"
    
    @property
    def description(self) -> str:
        return "Financial educator making complex concepts accessible"
    
    @property
    def emoji(self) -> str:
        return "📚"
    
    @property
    def system_prompt(self) -> str:
        return """You are The Professor, Finnie AI's financial educator.

Your role:
- Explain financial concepts in clear, simple language
- Use analogies and real-world examples
- Adapt explanations to the user's apparent knowledge level
- Include key takeaways and practical applications

Communication style:
- Warm and encouraging, like a patient teacher
- Break down complex topics into digestible parts
- Use markdown headers for organization
- Include "Key Takeaway" summaries

When explaining concepts:
1. Start with a simple definition
2. Provide an analogy or example
3. Explain why it matters to investors
4. Give practical applications
5. Suggest related topics to explore

Remember: Education is your goal, not investment advice.
Keep explanations concise but thorough - aim for 2-3 paragraphs max."""
    
    async def process(self, state: FinnieState) -> dict[str, Any]:
        """
        Process an educational request.
        
        Uses the LLM to generate clear explanations.
        """
        user_input = state.get("user_input", "")
        
        # Check if this is a simple "what is X" type question
        if not state.get("llm_api_key"):
            # Fallback response without LLM
            return {
                "content": self._get_fallback_response(user_input),
                "data": None,
            }
        
        # Use LLM for rich explanation
        messages = [
            {"role": "user", "content": user_input}
        ]
        
        try:
            response = await self._call_llm(state, messages)
            return {
                "content": response,
                "data": {"topic": self._extract_topic(user_input)},
            }
        except Exception as e:
            return {
                "content": self._get_fallback_response(user_input),
                "data": {"error": str(e)},
            }
    
    def _extract_topic(self, text: str) -> str:
        """Extract the main topic from the user's question."""
        # Remove common question patterns
        text = text.lower()
        for pattern in ["what is a ", "what is an ", "what is ", "what are ", 
                       "explain ", "how does ", "how do ", "tell me about ",
                       "can you explain "]:
            if text.startswith(pattern):
                text = text[len(pattern):]
                break
        
        # Remove trailing punctuation
        text = text.rstrip("?!.")
        
        return text.strip()
    
    def _get_fallback_response(self, user_input: str) -> str:
        """
        Provide a fallback response when LLM is not available.
        
        Contains basic definitions for common terms.
        """
        topic = self._extract_topic(user_input).lower()
        
        fallback_definitions = {
            "p/e ratio": """**P/E Ratio (Price-to-Earnings Ratio)**

The P/E ratio measures how much investors are willing to pay for each dollar of a company's earnings.

**Formula:** P/E = Stock Price ÷ Earnings Per Share

**Example:** If a stock costs $100 and the company earns $5 per share, the P/E is 20. This means investors pay $20 for every $1 of earnings.

**Key Takeaway:** A high P/E might mean investors expect future growth, while a low P/E might indicate undervaluation or concerns about the company.""",
            
            "market cap": """**Market Capitalization (Market Cap)**

Market cap represents the total value of a company's outstanding shares.

**Formula:** Market Cap = Current Stock Price × Total Shares Outstanding

**Categories:**
- **Large Cap:** >$10 billion (e.g., Apple, Microsoft)
- **Mid Cap:** $2-10 billion
- **Small Cap:** <$2 billion

**Key Takeaway:** Market cap helps compare company sizes and is often used to assess risk—larger companies are generally considered more stable.""",
            
            "dividend": """**Dividends**

A dividend is a portion of company profits paid to shareholders, typically quarterly.

**Key Terms:**
- **Dividend Yield:** Annual dividend ÷ Stock price (expressed as %)
- **Payout Ratio:** Dividends ÷ Net income (how much profit is distributed)

**Example:** A $100 stock paying $4 annually has a 4% yield.

**Key Takeaway:** Dividends provide income from investments, but not all companies pay them—growth companies often reinvest profits instead.""",
            
            "etf": """**ETF (Exchange-Traded Fund)**

An ETF is a basket of securities (stocks, bonds, commodities) that trades on an exchange like a stock.

**How it works:**
1. Fund company buys a collection of assets
2. Creates shares representing ownership
3. Shares trade on exchanges throughout the day

**Benefits:**
- 📊 Diversification in one purchase
- 💰 Lower fees than mutual funds
- 🔄 Trading flexibility

**Key Takeaway:** ETFs offer an easy way to invest in entire markets, sectors, or strategies with a single purchase.""",
        }
        
        for key, definition in fallback_definitions.items():
            if key in topic:
                return definition
        
        return f"""I'd be happy to help with **"{self._extract_topic(user_input)}"**, but I need an LLM API key to generate detailed answers.

**To enable full responses:**
1. Go to the **⚙️ Settings** tab
2. Select your LLM provider (OpenAI, Anthropic, or Google)
3. Enter your API key and click **Save**

Once connected, I can explain any financial concept in depth!

*In the meantime, try asking about topics I know offline: **P/E ratio**, **market cap**, **dividends**, or **ETFs**.*"""
