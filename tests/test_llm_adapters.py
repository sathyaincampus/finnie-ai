"""
Finnie AI — Test Suite: LLM Adapters

Tests for multi-provider LLM abstraction layer.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.llm.adapter import (
    BaseLLMAdapter,
    LLMAdapterFactory,
    LLMResponse,
    StreamChunk,
    get_llm_adapter,
)


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""
    
    def test_llm_response_creation(self):
        """Test creating an LLMResponse."""
        response = LLMResponse(
            content="Hello, world!",
            model="gpt-4o",
            provider="openai",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        
        assert response.content == "Hello, world!"
        assert response.model == "gpt-4o"
        assert response.provider == "openai"
        assert response.usage["total_tokens"] == 15
    
    def test_llm_response_defaults(self):
        """Test LLMResponse default values."""
        response = LLMResponse(
            content="Test",
            model="test-model",
            provider="test-provider",
        )
        
        assert response.usage == {}
        assert response.raw_response is None
        assert response.finish_reason is None


class TestStreamChunk:
    """Tests for StreamChunk dataclass."""
    
    def test_stream_chunk_creation(self):
        """Test creating a StreamChunk."""
        chunk = StreamChunk(content="Hello", is_final=False)
        
        assert chunk.content == "Hello"
        assert chunk.is_final is False
        assert chunk.usage is None
    
    def test_final_chunk(self):
        """Test creating a final StreamChunk."""
        chunk = StreamChunk(
            content="",
            is_final=True,
            usage={"total_tokens": 100},
        )
        
        assert chunk.is_final is True
        assert chunk.usage["total_tokens"] == 100


class TestLLMAdapterFactory:
    """Tests for LLMAdapterFactory."""
    
    def test_register_adapter(self):
        """Test registering a custom adapter."""
        class MockAdapter(BaseLLMAdapter):
            @property
            def provider_name(self) -> str:
                return "mock"
            
            async def chat(self, messages, system_prompt=None, tools=None):
                return LLMResponse(content="mock", model="mock", provider="mock")
            
            async def stream(self, messages, system_prompt=None, tools=None):
                yield StreamChunk(content="mock", is_final=True)
        
        LLMAdapterFactory.register("mock", MockAdapter)
        
        adapter = LLMAdapterFactory.create(
            provider="mock",
            model="mock-model",
            api_key="test-key",
        )
        
        assert adapter.provider_name == "mock"
    
    def test_unknown_provider_raises_error(self):
        """Test that unknown provider raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            LLMAdapterFactory.create(
                provider="unknown-provider",
                model="test",
                api_key="test",
            )
        
        assert "Unknown provider" in str(exc_info.value)
    
    def test_get_available_providers(self):
        """Test getting available providers."""
        providers = LLMAdapterFactory.get_available_providers()
        
        # Should include at least the default providers
        assert "openai" in providers or "mock" in providers


class TestGetLLMAdapter:
    """Tests for get_llm_adapter convenience function."""
    
    def test_get_adapter_calls_factory(self):
        """Test that get_llm_adapter uses factory."""
        with patch.object(LLMAdapterFactory, 'create') as mock_create:
            mock_create.return_value = MagicMock()
            
            get_llm_adapter(
                provider="openai",
                model="gpt-4o",
                api_key="test-key",
            )
            
            mock_create.assert_called_once_with("openai", "gpt-4o", "test-key")


# =============================================================================
# Integration tests (require API keys)
# =============================================================================

@pytest.mark.skipif(True, reason="Requires API keys")
class TestOpenAIAdapterIntegration:
    """Integration tests for OpenAI adapter."""
    
    @pytest.mark.asyncio
    async def test_chat_completion(self):
        """Test actual chat completion with OpenAI."""
        from src.llm import OpenAIAdapter
        import os
        
        adapter = OpenAIAdapter(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            model="gpt-4o-mini",
        )
        
        response = await adapter.chat(
            messages=[{"role": "user", "content": "Say hello in one word."}]
        )
        
        assert response.content
        assert response.provider == "openai"
