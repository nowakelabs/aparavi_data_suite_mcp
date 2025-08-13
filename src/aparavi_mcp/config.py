"""
Configuration management for Aparavi Data Suite MCP Server.
"""

import os
import yaml
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AparaviConfig(BaseModel):
    """Configuration for Aparavi Data Suite API connection."""
    
    host: str = Field(default="localhost", description="Aparavi Data Suite server host")
    port: int = Field(default=80, description="Aparavi Data Suite server port")
    username: str = Field(..., description="Aparavi Data Suite username for authentication")
    password: str = Field(..., description="Aparavi Data Suite password for authentication")
    api_version: str = Field(default="v3", description="Aparavi Data Suite API version")
    timeout: int = Field(default=1800, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    client_object_id: Optional[str] = Field(default=None, description="Client object ID for tagging operations")
    
    @property
    def base_url(self) -> str:
        """Get the base URL for Aparavi Data Suite API."""
        return f"http://{self.host}:{self.port}/server/api/{self.api_version}"
    
    @property
    def query_endpoint(self) -> str:
        """Get the database query endpoint."""
        return f"{self.base_url}/database/query"


class MCPServerConfig(BaseModel):
    """Configuration for MCP server."""
    
    name: str = Field(default="Aparavi Data Suite MCP Server", description="Server name")
    version: str = Field(default="0.1.0", description="Server version")
    log_level: str = Field(default="INFO", description="Logging level")
    cache_enabled: bool = Field(default=True, description="Enable query caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")


class Config(BaseModel):
    """Main configuration container."""
    
    aparavi: AparaviConfig
    server: MCPServerConfig = Field(default_factory=MCPServerConfig)


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables and optional YAML file.
    
    Args:
        config_path: Optional path to YAML configuration file
        
    Returns:
        Config: Loaded configuration object
    """
    # Start with environment variables
    aparavi_config = AparaviConfig(
        host=os.getenv("APARAVI_HOST", "localhost"),
        port=int(os.getenv("APARAVI_PORT", "80")),
        username=os.getenv("APARAVI_USERNAME", ""),
        password=os.getenv("APARAVI_PASSWORD", ""),
        api_version=os.getenv("APARAVI_API_VERSION", "v3"),
        timeout=int(os.getenv("APARAVI_TIMEOUT", "1800")),
        max_retries=int(os.getenv("APARAVI_MAX_RETRIES", "3")),
        client_object_id=os.getenv("APARAVI_CLIENT_OBJECT_ID")
    )
    
    server_config = MCPServerConfig(
        name=os.getenv("MCP_SERVER_NAME", "Aparavi Data Suite MCP Server"),
        version=os.getenv("MCP_SERVER_VERSION", "0.1.0"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
        cache_ttl=int(os.getenv("CACHE_TTL", "300"))
    )
    
    config = Config(aparavi=aparavi_config, server=server_config)
    
    # Override with YAML file if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
            
        # Update configuration with YAML values
        if 'aparavi' in yaml_config:
            for key, value in yaml_config['aparavi'].items():
                if hasattr(config.aparavi, key):
                    setattr(config.aparavi, key, value)
                    
        if 'server' in yaml_config:
            for key, value in yaml_config['server'].items():
                if hasattr(config.server, key):
                    setattr(config.server, key, value)
    
    return config


def validate_config(config: Config) -> None:
    """
    Validate configuration settings.
    
    Args:
        config: Configuration to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    if not config.aparavi.username:
        raise ValueError("Aparavi Data Suite username is required")
    
    if not config.aparavi.password:
        raise ValueError("Aparavi Data Suite password is required")
    
    if config.aparavi.port <= 0 or config.aparavi.port > 65535:
        raise ValueError("Aparavi Data Suite port must be between 1 and 65535")
    
    if config.aparavi.timeout <= 0:
        raise ValueError("Aparavi Data Suite timeout must be positive")
    
    if config.aparavi.max_retries < 0:
        raise ValueError("Aparavi Data Suite max_retries must be non-negative")
