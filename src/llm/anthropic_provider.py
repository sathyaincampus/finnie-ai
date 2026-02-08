"""
Finnie AI — Anthropic LLM Adapter

Implementation of the LLM adapter for Anthropic models (Claude).
"""

from typing import AsyncGenerator, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage

from src.llm.adapter import (
    BaseLLMAdapter,
    LLMAdapterFactory,
    LLMResponse,
    StreamChunk,
)


class AnthropicAdapter(BaseLLMAdapter):
    """
    Anthropic LLM adapter using LangChain's ChatAnthropic.
    
    Supports Claude  Sonnet 4, Claude 3.5 Sonnet, Claude 3 Haiku.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize the Anthropic adapter.
        
        Args:
            api_key: Anthropic API key.
            model: Model to use (default: claude-sonnet-4-20250514).
            temperature: Sampling temperature (0-1).
            max_tokens: Maximum tokens to generate.
        """
        super().__init__(api_key, model, temperature, max_tokens)
        
        self._client = ChatAnthropic(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True,
        )
    
    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "anthropic"
    
    async def chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> LLMResponse:
        """
        Send a chat completion request to Anthropic.
        
        Anthropic handles system prompts differently - they go in a separate
        'system' parameter rather than as a message.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt.
            tools: Optional list of tool definitions.
            
        Returns:
            LLMResponse with the generated content.
        """
        # Normalize messages (without system prompt - Anthropic handles it separately)
        lc_messages = self._normalize_messages(messages)
        
        # Create client with system prompt if provided
        client = self._client
        if system_prompt:
            # Anthropic needs system prompt passed separately
            client = ChatAnthropic(
                api_key=self.api_key,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                system=system_prompt,
            )
        
        # Bind tools if provided
        if tools:
            anthropic_tools = self._convert_tools(tools)
            client = client.bind_tools(anthropic_tools)
        
        # Make the request
        response = await client.ainvoke(lc_messages)
        
        # Extract usage info
        usage = {}
        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata or {}
        
        return LLMResponse(
            content=response.content,
            model=self.model,
            provider=self.provider_name,
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            },
            raw_response=response,
            finish_reason=response.response_metadata.get("stop_reason") if hasattr(response, "response_metadata") else None,
        )
    
    async def stream(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a chat completion response from Anthropic.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt.
            tools: Optional list of tool definitions.
            
        Yields:
            StreamChunk objects with incremental content.
        """
        # Normalize messages
        lc_messages = self._normalize_messages(messages)
        
        # Create client with system prompt if provided
        client = self._client
        if system_prompt:
            client = ChatAnthropic(
                api_key=self.api_key,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                system=system_prompt,
                streaming=True,
            )
        
        # Bind tools if provided
        if tools:
            anthropic_tools = self._convert_tools(tools)
            client = client.bind_tools(anthropic_tools)
        
        # Stream the response
        async for chunk in client.astream(lc_messages):
            if chunk.content:
                yield StreamChunk(
                    content=chunk.content,
                    is_final=False,
                )
        
        # Final chunk
        yield StreamChunk(
            content="",
            is_final=True,
        )
    
    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """
        Convert generic tool definitions to Anthropic format.
        
        Anthropic uses a similar but slightly different tool format.
        
        Args:
            tools: List of tool definitions.
            
        Returns:
            Tools in Anthropic format.
        """
        anthropic_tools = []
        for tool in tools:
            anthropic_tools.append({
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "input_schema": tool.get("parameters", {"type": "object", "properties": {}}),
            })
        return anthropic_tools


# Register with factory
LLMAdapterFactory.register("anthropic", AnthropicAdapter)
