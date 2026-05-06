"""Application Settings.

Configuration is loaded from:
1. Environment variables
2. .env file
3. Default values
"""

from enum import Enum
from typing import Annotated, Any, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    sift_vm_host: str = "localhost"  # Override with SIFT_VM_HOST env var
    sift_vm_port: int = 16789
    sift_ssh_user: Optional[str] = "sansforensics"
    sift_ssh_key_path: Optional[str] = None
    # SSH host-key verification (A2 — defends against MITM).
    # When None, asyncssh falls back to ~/.ssh/known_hosts.
    ssh_known_hosts_path: Optional[str] = None
    # Set to False ONLY in transitional dev environments. When False,
    # asyncssh's host-key check is disabled — the connection is vulnerable
    # to MITM attacks. Default True (secure).
    ssh_strict_host_key_checking: bool = True
    
    # Security
    allowed_evidence_paths: Annotated[list[str], NoDecode] = Field(
        default=["/mnt/evidence/", "/workspace/", "/tmp/sift-workspace/"]
    )
    max_tool_timeout: int = 3600  # 1 hour for intensive tools
    default_tool_timeout: int = 60  # 1 minute for most tools
    
    # LLM Configuration
    llm_provider: LLMProviderEnum = LLMProviderEnum.OLLAMA
    llm_model_name: str = "gemma4:31b-cloud"
    llm_temperature: float = 0.1  # Low temp for deterministic tool selection

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"  # Override with OLLAMA_BASE_URL env var

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

    # API Server
    api_cors_origins: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:15173", "http://127.0.0.1:15173"]
    )
    # API key authentication (A4). Comma-separated list via API_KEYS env.
    # Empty list disables auth — for local dev only. Production deployments
    # must set at least one key.
    api_keys: Annotated[list[str], NoDecode] = Field(default_factory=list)

    # Observability - Langfuse
    langfuse_secret_key: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_base_url: Optional[str] = None
    langfuse_enabled: bool = True  # Can disable for testing

    @field_validator("api_keys", "api_cors_origins", "allowed_evidence_paths", mode="before")
    @classmethod
    def _split_csv_list(cls, v: Any) -> Any:
        """Accept comma-separated strings for list-typed env vars.

        Without this, pydantic-settings v2 expects JSON-encoded lists, which
        is unfriendly for shell `.env` files and breaks `API_KEYS=k1,k2`.
        """
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

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
