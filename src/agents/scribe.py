"""
Finnie AI — The Scribe Agent

Synthesizes all agent outputs into a cohesive response.
"""

from typing import Any

from src.agents.base import BaseFinnieAgent
from src.orchestration.state import FinnieState, AgentName


class ScribeAgent(BaseFinnieAgent):
    """
    The Scribe — Response Synthesizer
    
    Combines outputs from all agents into a single,
    well-formatted, cohesive response.
    
    Triggers: Runs on EVERY response as the final step
    """
    
    @property
    def name(self) -> str:
        return "scribe"
    
    @property
    def description(self) -> str:
        return "Response synthesizer combining agent outputs"
    
    @property
    def emoji(self) -> str:
        return "✍️"
    
    @property
    def system_prompt(self) -> str:
        return """You are The Scribe, Finnie AI's response synthesizer.

Your role:
- Combine outputs from multiple agents into a cohesive response
- Ensure consistent formatting and tone
- Remove redundancy while preserving key information
- Add smooth transitions between sections

Communication style:
- Professional yet friendly
- Well-organized with clear sections
- Use markdown for formatting
- Concise but comprehensive"""
    
    async def process(self, state: FinnieState) -> dict[str, Any]:
        """
        Synthesize all agent outputs into a final response.
        """
        agent_outputs = state.get("agent_outputs", [])
        disclaimers = state.get("disclaimers", [])
        
        if not agent_outputs:
            return {
                "content": "",
                "final_response": "I apologize, but I couldn't process your request. Please try again.",
            }
        
        # Filter out empty outputs and meta-agents (Guardian, Scribe)
        content_outputs = [
            o for o in agent_outputs 
            if o.get("content") and o["agent_name"] not in [AgentName.GUARDIAN, AgentName.SCRIBE]
        ]
        
        if not content_outputs:
            return {
                "content": "",
                "final_response": "I apologize, but I couldn't generate a helpful response. Please try rephrasing your question.",
            }
        
        # Build final response
        final_response = self._synthesize(content_outputs)
        
        # Add disclaimers
        if disclaimers:
            final_response += "\n\n---\n"
            final_response += " | ".join(f"⚠️ {d}" for d in disclaimers[:2])  # Limit to 2 disclaimers
        
        return {
            "content": "",
            "final_response": final_response,
        }
    
    def _synthesize(self, outputs: list[dict]) -> str:
        """
        Synthesize multiple agent outputs.
        
        For single output, return as-is.
        For multiple, combine with clear sections.
        """
        if len(outputs) == 1:
            return outputs[0].get("content", "")
        
        # Multiple outputs - combine with agent attribution
        sections = []
        
        for output in outputs:
            agent = output.get("agent_name", "unknown")
            content = output.get("content", "")
            
            if content:
                emoji = self._get_agent_emoji(agent)
                # Don't add headers for single-paragraph responses
                if len(outputs) <= 2 and len(content) < 500:
                    sections.append(content)
                else:
                    sections.append(f"**{emoji} {self._get_agent_title(agent)}:**\n\n{content}")
        
        return "\n\n".join(sections)
    
    def _get_agent_emoji(self, agent_name: str) -> str:
        """Get emoji for an agent."""
        emojis = {
            AgentName.QUANT: "📊",
            AgentName.PROFESSOR: "📚",
            AgentName.ANALYST: "🔍",
            AgentName.ADVISOR: "💼",
            AgentName.ORACLE: "🔮",
            AgentName.SCOUT: "🌍",
        }
        return emojis.get(agent_name, "💡")
    
    def _get_agent_title(self, agent_name: str) -> str:
        """Get display title for an agent."""
        titles = {
            AgentName.QUANT: "Market Data",
            AgentName.PROFESSOR: "Explanation",
            AgentName.ANALYST: "Analysis",
            AgentName.ADVISOR: "Portfolio Insights",
            AgentName.ORACLE: "Projections",
            AgentName.SCOUT: "Trending",
        }
        return titles.get(agent_name, "Insights")
