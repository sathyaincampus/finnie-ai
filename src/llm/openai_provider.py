"""
Finnie AI — OpenAI LLM Adapter

Implementation of the LLM adapter for OpenAI models (GPT-4o, etc.).
"""

from typing import AsyncGenerator, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

from src.llm.adapter import (
    BaseLLMAdapter,
    LLMAdapterFactory,
    LLMResponse,
    StreamChunk,
)


class OpenAIAdapter(BaseLLMAdapter):
    """
    OpenAI LLM adapter using LangChain's ChatOpenAI.
    
    Supports GPT-4o, GPT-4o-mini, GPT-4-turbo, and GPT-3.5-turbo.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize the OpenAI adapter.
        
        Args:
            api_key: OpenAI API key.
            model: Model to use (default: gpt-4o).
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.
        """
        super().__init__(api_key, model, temperature, max_tokens)
        
        self._client = ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True,
        )
    
    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "openai"
    
    async def chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> LLMResponse:
        """
        Send a chat completion request to OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt to prepend.
            tools: Optional list of tool definitions.
            
        Returns:
            LLMResponse with the generated content.
        """
        # Normalize messages
        lc_messages = self._normalize_messages(messages, system_prompt)
        
        # Bind tools if provided
        client = self._client
        if tools:
            # Convert to OpenAI tool format if needed
            openai_tools = self._convert_tools(tools)
            client = client.bind_tools(openai_tools)
        
        # Make the request
        response = await client.ainvoke(lc_messages)
        
        # Extract usage info
        usage = {}
        if hasattr(response, "response_metadata"):
            usage = response.response_metadata.get("token_usage", {})
        
        return LLMResponse(
            content=response.content,
            model=self.model,
            provider=self.provider_name,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            raw_response=response,
            finish_reason=response.response_metadata.get("finish_reason") if hasattr(response, "response_metadata") else None,
        )
    
    async def stream(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a chat completion response from OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt to prepend.
            tools: Optional list of tool definitions.
            
        Yields:
            StreamChunk objects with incremental content.
        """
        # Normalize messages
        lc_messages = self._normalize_messages(messages, system_prompt)
        
        # Bind tools if provided
        client = self._client
        if tools:
            openai_tools = self._convert_tools(tools)
            client = client.bind_tools(openai_tools)
        
        # Stream the response
        accumulated_content = ""
        async for chunk in client.astream(lc_messages):
            if chunk.content:
                accumulated_content += chunk.content
                yield StreamChunk(
                    content=chunk.content,
                    is_final=False,
                )
        
        # Final chunk with usage (if available)
        yield StreamChunk(
            content="",
            is_final=True,
            usage=None,  # OpenAI doesn't provide usage in streaming mode by default
        )
    
    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """
        Convert generic tool definitions to OpenAI format.
        
        Args:
            tools: List of tool definitions.
            
        Returns:
            Tools in OpenAI function calling format.
        """
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                }
            })
        return openai_tools


# Register with factory
LLMAdapterFactory.register("openai", OpenAIAdapter)
