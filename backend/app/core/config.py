# backend/app/core/config.py
"""
Core configuration management for the SaaS platform.

This file handles all environment variables and app settings.
We use Pydantic's BaseSettings for type safety and validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Why use this approach?
    - Type safety (Pydantic validates types automatically)
    - Environment-specific configs (dev, staging, prod)
    - Secure secret management
    - Easy testing with different configs
    """
    
    # App Info
    app_name: str = "Sales Automation SaaS"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Database Configuration
    # We use PostgreSQL for production reliability and JSONB support
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/sales_automation",
        description="PostgreSQL database connection string"
    )
    
    # Security Settings
    secret_key: str = Field(
        default="your-super-secret-key-change-this-in-production",
        description="JWT signing key - MUST be changed in production!"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT token expiration time in minutes"
    )
    
    # Rate Limiting (for your 1000 DAU target)
    # These limits prevent abuse while allowing normal usage
    rate_limit_per_minute: int = Field(
        default=100,
        description="API requests per minute per user"
    )
    email_rate_limit_per_hour: int = Field(
        default=50,
        description="Emails per hour per company (prevents spam)"
    )
    
    # MCP Configuration
    mcp_timeout_seconds: int = Field(
        default=30,
        description="Timeout for MCP server communications"
    )
    mcp_max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed MCP calls"
    )
    
    # External Service Settings
    gmail_mcp_server_url: str = Field(
        default="ws://localhost:8001/mcp",
        description="Gmail MCP server WebSocket URL"
    )
    news_mcp_server_url: Optional[str] = Field(
        default=None,
        description="News research MCP server URL"
    )
    
    # Redis for Caching & Rate Limiting
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection for caching and rate limiting"
    )
    
    # CORS Settings (for your React frontend)
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed origins for CORS (add your frontend URL)"
    )
    
    #OPENAI Configuration
    openai_api_key: str = Field(
        default="",
        description="OpenAI API Key for Email Generation"
    )

    class Config:
        # Load from .env file
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
# This pattern allows easy testing and configuration switching
settings = Settings()

# Export commonly used values for convenience
DATABASE_URL = settings.database_url
SECRET_KEY = settings.secret_key
DEBUG = settings.debug