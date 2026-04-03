"""Application Settings.

Configuration is loaded from:
1. Environment variables
2. .env file
3. Default values
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    
    # SIFT Workstation (placeholders - update after starter code)
    sift_vm_host: str = "localhost"
    sift_vm_port: int = 8080
    sift_ssh_user: Optional[str] = None
    sift_ssh_key_path: Optional[str] = None
    
    # Security
    allowed_evidence_paths: list[str] = Field(
        default=["/mnt/evidence/", "/workspace/", "/tmp/sift-workspace/"]
    )
    max_tool_timeout: int = 3600  # 1 hour for intensive tools
    default_tool_timeout: int = 60  # 1 minute for most tools
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_llm_model: str = "claude-3-opus-20240229"
    llm_temperature: float = 0.1  # Low temp for deterministic tool selection
    
    # Tool Selector
    tool_confidence_threshold: float = 0.7
    semantic_search_top_k: int = 10
    
    # MCP
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 8080
    
    # Reporting
    default_report_format: str = "markdown"
    report_output_dir: str = "./reports"


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
