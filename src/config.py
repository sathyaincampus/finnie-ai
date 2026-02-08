"""
Finnie AI — Configuration Module

Centralized configuration management using pydantic-settings.
All environment variables are loaded and validated here.
"""

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Usage:
        from src.config import get_settings
        settings = get_settings()
        print(settings.openai_api_key)
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # =========================================================================
    # LLM Providers
    # =========================================================================
    
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    google_api_key: Optional[str] = Field(default=None, description="Google API key")
    
    default_llm_provider: Literal["openai", "anthropic", "google"] = Field(
        default="openai",
        description="Default LLM provider to use"
    )
    default_llm_model: str = Field(
        default="gpt-4o",
        description="Default LLM model to use"
    )
    
    # =========================================================================
    # Database Connections
    # =========================================================================
    
    neon_database_url: Optional[str] = Field(
        default=None,
        description="NeonDB PostgreSQL connection URL"
    )
    
    aura_uri: Optional[str] = Field(default=None, description="AuraDB Neo4j URI")
    aura_user: str = Field(default="neo4j", description="AuraDB username")
    aura_password: Optional[str] = Field(default=None, description="AuraDB password")
    
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis Cloud connection URL"
    )
    
    # =========================================================================
    # Observability
    # =========================================================================
    
    langfuse_public_key: Optional[str] = Field(default=None, description="LangFuse public key")
    langfuse_secret_key: Optional[str] = Field(default=None, description="LangFuse secret key")
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        description="LangFuse host URL"
    )
    
    # =========================================================================
    # Feature Flags
    # =========================================================================
    
    voice_enabled: bool = Field(default=True, description="Enable voice features")
    use_local_llm: bool = Field(default=False, description="Use local LLM instead of cloud")
    local_llm_endpoint: str = Field(
        default="http://localhost:8080/v1",
        description="Local LLM API endpoint"
    )
    graphrag_enabled: bool = Field(default=True, description="Enable GraphRAG features")
    
    # =========================================================================
    # Application Settings
    # =========================================================================
    
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment"
    )
    
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    
    streamlit_port: int = Field(default=8501, description="Streamlit server port")
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )
    
    # =========================================================================
    # Validators
    # =========================================================================
    
    @field_validator("default_llm_provider")
    @classmethod
    def validate_provider_has_key(cls, v: str, info) -> str:
        """Ensure the default provider has an API key configured."""
        # Note: This runs before all fields are populated, so we can't validate here
        # Validation is done in get_llm_api_key() instead
        return v
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def get_llm_api_key(self, provider: Optional[str] = None) -> str:
        """
        Get the API key for a specific provider.
        
        Args:
            provider: The provider name. If None, uses default_llm_provider.
            
        Returns:
            The API key for the provider.
            
        Raises:
            ValueError: If no API key is configured for the provider.
        """
        provider = provider or self.default_llm_provider
        
        key_map = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "google": self.google_api_key,
        }
        
        key = key_map.get(provider)
        if not key:
            raise ValueError(
                f"No API key configured for provider '{provider}'. "
                f"Please set the appropriate environment variable."
            )
        
        return key
    
    def has_database_config(self) -> bool:
        """Check if database connections are configured."""
        return bool(self.neon_database_url and self.redis_url)
    
    def has_graphrag_config(self) -> bool:
        """Check if GraphRAG (Neo4j) is configured."""
        return bool(self.aura_uri and self.aura_password)
    
    def has_observability_config(self) -> bool:
        """Check if LangFuse is configured."""
        return bool(self.langfuse_public_key and self.langfuse_secret_key)
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    
    Returns:
        Settings instance with all configuration loaded.
    """
    return Settings()


# =============================================================================
# Supported LLM Models Reference
# =============================================================================

SUPPORTED_MODELS = {
    "openai": [
        ("gpt-4o", "GPT-4o"),
        ("gpt-4o-mini", "GPT-4o Mini"),
        ("gpt-4-turbo", "GPT-4 Turbo"),
        ("gpt-3.5-turbo", "GPT-3.5 Turbo"),
    ],
    "anthropic": [
        ("claude-sonnet-4-20250514", "Claude Sonnet 4"),
        ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet"),
        ("claude-3-haiku-20240307", "Claude 3 Haiku"),
    ],
    "google": [
        ("gemini-2.0-flash", "Gemini 2.0 Flash"),
        ("gemini-1.5-pro", "Gemini 1.5 Pro"),
        ("gemini-1.5-flash", "Gemini 1.5 Flash"),
    ],
}


def get_available_providers(settings: Optional[Settings] = None) -> list[str]:
    """
    Get list of providers that have API keys configured.
    
    Args:
        settings: Settings instance. If None, uses get_settings().
        
    Returns:
        List of available provider names.
    """
    settings = settings or get_settings()
    
    available = []
    if settings.openai_api_key:
        available.append("openai")
    if settings.anthropic_api_key:
        available.append("anthropic")
    if settings.google_api_key:
        available.append("google")
    
    return available


def get_models_for_provider(provider: str) -> list[tuple[str, str]]:
    """
    Get list of supported models for a provider.
    
    Args:
        provider: Provider name (openai, anthropic, google).
        
    Returns:
        List of (model_id, display_name) tuples.
    """
    return SUPPORTED_MODELS.get(provider, [])
