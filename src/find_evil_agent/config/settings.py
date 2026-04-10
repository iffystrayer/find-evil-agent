"""Application Settings.

Configuration is loaded from:
1. Environment variables
2. .env file
3. Default values
"""

from enum import Enum
from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderEnum(str, Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class Settings(BaseSettings):
    """Application configuration.
    
    NOTE: These are placeholders that will be refined
    after April 15 starter code integration.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Application
    app_name: str = "Find Evil Agent"
    debug: bool = False
    log_level: str = "INFO"
    
    # SIFT Workstation
    sift_vm_host: str = "192.168.12.101"
    sift_vm_port: int = 16789
    sift_ssh_user: Optional[str] = "sansforensics"
    sift_ssh_key_path: Optional[str] = None
    
    # Security
    allowed_evidence_paths: list[str] = Field(
        default=["/mnt/evidence/", "/workspace/", "/tmp/sift-workspace/"]
    )
    max_tool_timeout: int = 3600  # 1 hour for intensive tools
    default_tool_timeout: int = 60  # 1 minute for most tools
    
    # LLM Configuration
    llm_provider: LLMProviderEnum = LLMProviderEnum.OLLAMA
    llm_model_name: str = "gemma4:31b-cloud"
    llm_temperature: float = 0.1  # Low temp for deterministic tool selection

    # Ollama Configuration
    ollama_base_url: str = "http://192.168.12.124:11434"

    # Provider API Keys (optional, based on selected provider)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Deprecated (kept for backward compatibility)
    default_llm_model: str = "claude-3-opus-20240229"
    
    # Tool Selector
    tool_confidence_threshold: float = 0.7
    semantic_search_top_k: int = 10
    
    # MCP
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 16790
    
    # Reporting
    default_report_format: str = "markdown"
    report_output_dir: str = "./reports"

    # Observability - Langfuse
    langfuse_secret_key: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_base_url: Optional[str] = None
    langfuse_enabled: bool = True  # Can disable for testing

    @model_validator(mode='after')
    def validate_provider_config(self) -> 'Settings':
        """Validate required configuration for selected LLM provider."""
        if self.llm_provider == LLMProviderEnum.OPENAI and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable required when using openai provider")
        if self.llm_provider == LLMProviderEnum.ANTHROPIC and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required when using anthropic provider")
        return self


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
