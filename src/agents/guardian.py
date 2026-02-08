"""
Finnie AI — The Guardian Agent

Handles compliance, disclaimers, and risk warnings.
"""

from typing import Any
import re

from src.agents.base import BaseFinnieAgent
from src.orchestration.state import FinnieState


class GuardianAgent(BaseFinnieAgent):
    """
    The Guardian — Compliance & Risk Specialist
    
    Reviews all responses and adds appropriate disclaimers.
    Ensures regulatory compliance and user protection.
    
    Triggers: Runs on EVERY response automatically
    """
    
    @property
    def name(self) -> str:
        return "guardian"
    
    @property
    def description(self) -> str:
        return "Compliance specialist ensuring appropriate disclaimers"
    
    @property
    def emoji(self) -> str:
        return "🛡️"
    
    @property
    def system_prompt(self) -> str:
        return """You are The Guardian, Finnie AI's compliance specialist.

Your role:
- Review responses for potential compliance issues
- Add appropriate risk disclaimers
- Ensure users understand this is educational, not advice
- Flag high-risk topics that need extra caution

You operate silently, adding disclaimers to responses.
You don't generate user-facing content directly."""
    
    async def process(self, state: FinnieState) -> dict[str, Any]:
        """
        Process the state and determine appropriate disclaimers.
        
        Reviews user input and existing outputs to assess risk level.
        """
        user_input = state.get("user_input", "").lower()
        agent_outputs = state.get("agent_outputs", [])
        
        disclaimers = []
        risk_level = self._assess_risk(user_input, agent_outputs)
        
        # Always add base disclaimer
        disclaimers.append("This is for educational purposes only, not financial advice.")
        
        # Add risk-specific disclaimers
        if risk_level == "high":
            disclaimers.append(
                "This topic involves significant financial risk. "
                "Please consult a licensed financial advisor before making any decisions."
            )
        
        # Check for specific high-risk patterns
        if self._mentions_options_or_derivatives(user_input):
            disclaimers.append(
                "Options and derivatives carry substantial risk and are not suitable for all investors."
            )
        
        if self._mentions_crypto(user_input):
            disclaimers.append(
                "Cryptocurrency investments are highly volatile and speculative."
            )
        
        if self._mentions_specific_buy_sell(user_input):
            disclaimers.append(
                "I cannot provide specific buy/sell recommendations. "
                "Consider consulting a registered investment advisor."
            )
        
        return {
            "content": "",  # Guardian doesn't add visible content
            "data": {"risk_level": risk_level},
            "disclaimers": disclaimers,
        }
    
    def _assess_risk(self, user_input: str, outputs: list) -> str:
        """
        Assess the risk level of the current interaction.
        
        Returns: "low", "medium", or "high"
        """
        high_risk_patterns = [
            r'\bshould i buy\b',
            r'\bshould i sell\b',
            r'\ball in\b',
            r'\byolo\b',
            r'\bguaranteed\b',
            r'\bget rich\b',
            r'\bquick money\b',
            r'\bmargin\b',
            r'\bleverage\b',
            r'\bshort\b',
            r'\boptions?\b',
            r'\bput\b.*\bcall\b',
            r'\bcrypto\b',
            r'\bbitcoin\b',
            r'\bethereruem\b',
        ]
        
        medium_risk_patterns = [
            r'\binvest\b',
            r'\bportfolio\b',
            r'\bretirement\b',
            r'\bsavings\b',
            r'\bstrategy\b',
        ]
        
        for pattern in high_risk_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return "high"
        
        for pattern in medium_risk_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return "medium"
        
        return "low"
    
    def _mentions_options_or_derivatives(self, text: str) -> bool:
        """Check if text mentions options or derivatives."""
        patterns = [r'\boptions?\b', r'\bputs?\b', r'\bcalls?\b', 
                   r'\bderivatives?\b', r'\bfutures?\b', r'\bswaps?\b']
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
    
    def _mentions_crypto(self, text: str) -> bool:
        """Check if text mentions cryptocurrency."""
        patterns = [r'\bcrypto\b', r'\bbitcoin\b', r'\bbtc\b', r'\bethereruem\b', 
                   r'\beth\b', r'\bsolana\b', r'\bdogecoin\b', r'\bnft\b']
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
    
    def _mentions_specific_buy_sell(self, text: str) -> bool:
        """Check if user is asking for specific buy/sell advice."""
        patterns = [r'should i (buy|sell)', r'(buy|sell) now', 
                   r'is it (a )?good time to (buy|sell)']
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
