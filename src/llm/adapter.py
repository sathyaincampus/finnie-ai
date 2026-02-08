"""
Finnie AI — Base LLM Adapter & Factory

Abstract base class for LLM providers and factory for creating adapters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    
    content: str
    """The generated text content."""
    
    model: str
    """The model that generated the response."""
    
    provider: str
    """The provider name (openai, anthropic, google)."""
    
    usage: dict = field(default_factory=dict)
    """Token usage information (prompt_tokens, completion_tokens, total_tokens)."""
    
    raw_response: Optional[Any] = None
    """The raw response object from the provider (for debugging)."""
    
    finish_reason: Optional[str] = None
    """Why the generation stopped (stop, length, tool_calls, etc.)."""


@dataclass
class StreamChunk:
    """A single chunk from a streaming response."""
    
    content: str
    """The text content of this chunk."""
    
    is_final: bool = False
    """Whether this is the final chunk."""
    
    usage: Optional[dict] = None
    """Token usage (only available in final chunk for some providers)."""


class BaseLLMAdapter(ABC):
    """
    Abstract base class for LLM provider adapters.
    
    Each provider (OpenAI, Anthropic, Google) implements this interface
    to provide a consistent API for the orchestration layer.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize the adapter.
        
        Args:
            api_key: The API key for authentication.
            model: The model identifier to use.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'anthropic', 'google')."""
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> LLMResponse:
        """
        Send a chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt to prepend.
            tools: Optional list of tool definitions for function calling.
            
        Returns:
            LLMResponse with the generated content.
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream a chat completion response.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt to prepend.
            tools: Optional list of tool definitions for function calling.
            
        Yields:
            StreamChunk objects with incremental content.
        """
        pass
    
    def _normalize_messages(
        self,
        messages: list[dict],
        system_prompt: Optional[str] = None,
    ) -> list[BaseMessage]:
        """
        Convert generic message dicts to LangChain message objects.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            system_prompt: Optional system prompt to prepend.
            
        Returns:
            List of LangChain message objects.
        """
        result: list[BaseMessage] = []
        
        # Add system prompt if provided
        if system_prompt:
            result.append(SystemMessage(content=system_prompt))
        
        # Convert each message
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                result.append(SystemMessage(content=content))
            elif role == "assistant":
                result.append(AIMessage(content=content))
            else:  # user or unknown
                result.append(HumanMessage(content=content))
        
        return result


class LLMAdapterFactory:
    """
    Factory for creating LLM adapters.
    
    Handles provider-specific instantiation and caching.
    """
    
    _adapters: dict[str, type[BaseLLMAdapter]] = {}
    
    @classmethod
    def register(cls, provider: str, adapter_class: type[BaseLLMAdapter]) -> None:
        """
        Register an adapter class for a provider.
        
        Args:
            provider: The provider name (e.g., 'openai').
            adapter_class: The adapter class to use.
        """
        cls._adapters[provider.lower()] = adapter_class
    
    @classmethod
    def create(
        cls,
        provider: str,
        model: str,
        api_key: str,
        **kwargs,
    ) -> BaseLLMAdapter:
        """
        Create an adapter instance for the specified provider.
        
        Args:
            provider: The provider name.
            model: The model identifier.
            api_key: The API key.
            **kwargs: Additional arguments passed to the adapter.
            
        Returns:
            An instance of the appropriate adapter.
            
        Raises:
            ValueError: If the provider is not registered.
        """
        provider = provider.lower()
        
        if provider not in cls._adapters:
            available = ", ".join(cls._adapters.keys())
            raise ValueError(
                f"Unknown provider '{provider}'. "
                f"Available providers: {available}"
            )
        
        adapter_class = cls._adapters[provider]
        return adapter_class(api_key=api_key, model=model, **kwargs)
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of registered providers."""
        return list(cls._adapters.keys())


def get_llm_adapter(
    provider: str,
    model: str,
    api_key: str,
    **kwargs,
) -> BaseLLMAdapter:
    """
    Convenience function to create an LLM adapter.
    
    Args:
        provider: The provider name (openai, anthropic, google).
        model: The model identifier.
        api_key: The API key.
        **kwargs: Additional arguments passed to the adapter.
        
    Returns:
        An instance of the appropriate adapter.
        
    Example:
        >>> adapter = get_llm_adapter("openai", "gpt-4o", "sk-...")
        >>> response = await adapter.chat([{"role": "user", "content": "Hello!"}])
    """
    return LLMAdapterFactory.create(provider, model, api_key, **kwargs)
