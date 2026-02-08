"""
Finnie AI — Google LLM Adapter

Implementation of the LLM adapter for Google models (Gemini).
"""

from typing import AsyncGenerator, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage

from src.llm.adapter import (
    BaseLLMAdapter,
    LLMAdapterFactory,
    LLMResponse,
    StreamChunk,
)


class GoogleAdapter(BaseLLMAdapter):
    """
    Google LLM adapter using LangChain's ChatGoogleGenerativeAI.
    
    Supports Gemini 2.0 Flash, Gemini 1.5 Pro, Gemini 1.5 Flash.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize the Google adapter.
        
        Args:
            api_key: Google AI API key.
            model: Model to use (default: gemini-2.0-flash).
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.
        """
        super().__init__(api_key, model, temperature, max_tokens)
        
        self._client = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=model,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    
    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "google"
    
    async def chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> LLMResponse:
        """
        Send a chat completion request to Google.
        
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
            google_tools = self._convert_tools(tools)
            client = client.bind_tools(google_tools)
        
        # Make the request
        response = await client.ainvoke(lc_messages)
        
        # Extract usage info (Gemini provides this differently)
        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.get("prompt_token_count", 0),
                "completion_tokens": response.usage_metadata.get("candidates_token_count", 0),
                "total_tokens": response.usage_metadata.get("total_token_count", 0),
            }
        
        return LLMResponse(
            content=response.content,
            model=self.model,
            provider=self.provider_name,
            usage=usage,
            raw_response=response,
            finish_reason=None,  # Gemini doesn't expose this the same way
        )
    
    async def stream(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a chat completion response from Google.
        
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
            google_tools = self._convert_tools(tools)
            client = client.bind_tools(google_tools)
        
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
        Convert generic tool definitions to Google format.
        
        Google/Gemini uses a similar format to OpenAI.
        
        Args:
            tools: List of tool definitions.
            
        Returns:
            Tools in Google format.
        """
        google_tools = []
        for tool in tools:
            google_tools.append({
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
            })
        return google_tools


# Register with factory
LLMAdapterFactory.register("google", GoogleAdapter)
