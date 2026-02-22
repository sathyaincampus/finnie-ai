"""
Finnie AI — The Enhancer Agent

Pre-processes user input to create structured, context-rich prompts
before routing to domain agents. Acts as a prompt optimization layer.
"""

from typing import Any, Optional

from src.agents.base import BaseFinnieAgent
from src.orchestration.state import FinnieState


class EnhancerAgent(BaseFinnieAgent):
    """
    The Enhancer — Prompt Optimization Specialist
    
    Sits between raw user input and intent parsing.
    Transforms vague or incomplete queries into structured,
    context-rich prompts that downstream agents can handle effectively.
    
    Example:
        Input:  "should i invest?"
        Output: "The user is asking for personalized investment guidance.
                 They need: asset allocation recommendations based on risk
                 tolerance, current market conditions, and common investment
                 vehicles (stocks, bonds, index funds). Provide actionable
                 suggestions with educational context."
    """
    
    @property
    def name(self) -> str:
        return "enhancer"
    
    @property
    def description(self) -> str:
        return "Prompt optimization specialist — refines raw user input"
    
    @property
    def emoji(self) -> str:
        return "✨"
    
    @property
    def system_prompt(self) -> str:
        return """You are The Enhancer, Finnie AI's prompt optimization layer.

Your role:
- Take a raw user query about finance and rewrite it as a clear, structured prompt
- Preserve the user's original intent exactly — do NOT change what they're asking
- Add financial context that helps downstream agents respond better
- Identify the specific data, metrics, or explanations the user likely needs
- If the query mentions specific tickers, keep them. If vague, don't add tickers.

Rules:
- Output ONLY the enhanced prompt, nothing else
- Keep it concise (2-4 sentences max)
- Do NOT add disclaimers or formatting — downstream agents handle that
- If the query is already clear and specific, return it mostly unchanged
- For greetings or off-topic, return the original input unchanged

Financial domains to consider:
- Market data (stock prices, charts, comparisons)
- Education (explain concepts like P/E, DCA, bonds)
- Portfolio management (allocation, diversification, rebalancing)
- Projections (Monte Carlo, goal-based planning)
- Financial planning (529, Roth IRA, retirement, tax optimization)
- Crypto (Bitcoin, Ethereum, altcoins, DeFi)
- News and trends (market movers, sentiment)
- Life planning (visa considerations, side hustles, expense management)"""
    
    async def process(self, state: FinnieState) -> dict[str, Any]:
        """
        Enhance the user's raw input into a structured prompt.
        
        Returns the enhanced input that downstream agents will use.
        """
        user_input = state.get("user_input", "")
        
        # Skip enhancement for very short greetings
        if len(user_input.strip()) < 5:
            return {"content": user_input, "enhanced_input": user_input}
        
        # Skip enhancement for already structured queries
        greeting_words = {"hi", "hello", "hey", "thanks", "thank", "bye", "ok", "okay"}
        if user_input.strip().lower() in greeting_words:
            return {"content": user_input, "enhanced_input": user_input}
        
        try:
            enhanced = await self._call_llm(
                state=state,
                messages=[
                    {"role": "user", "content": f"Enhance this financial query:\n\n{user_input}"}
                ],
            )
            
            # Sanity check: enhanced prompt shouldn't be empty or much shorter
            if enhanced and len(enhanced.strip()) >= len(user_input.strip()) * 0.5:
                return {
                    "content": enhanced.strip(),
                    "enhanced_input": enhanced.strip(),
                }
        except Exception:
            pass
        
        # Fallback: use original input
        return {"content": user_input, "enhanced_input": user_input}
