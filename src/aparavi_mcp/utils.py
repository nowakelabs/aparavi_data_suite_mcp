"""
Utility functions and helpers for APARAVI MCP Server.
"""

import logging
import json
import hashlib
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger("aparavi_mcp")
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Set log level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create console handler with formatting
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def encode_aql_query(query: str) -> str:
    """
    Prepare an AQL query string for API requests.
    Note: aiohttp automatically handles URL encoding, so we return the query as-is
    to prevent double encoding.
    
    Args:
        query: Raw AQL query string
        
    Returns:
        str: Query string (not URL encoded - aiohttp handles this)
    """
    return query


def create_query_options(
    format_type: str = "json",
    stream: bool = False,
    validate: bool = False
) -> str:
    """
    Create options JSON string for APARAVI API queries.
    
    Args:
        format_type: Response format ("json" or "csv")
        stream: Whether to stream the response
        validate: Whether to validate the query
        
    Returns:
        str: JSON string of options
    """
    options = {
        "format": format_type,
        "stream": stream,
        "validate": validate
    }
    return json.dumps(options)


def generate_cache_key(query: str, options: Dict[str, Any]) -> str:
    """
    Generate a cache key for a query and options combination.
    
    Args:
        query: AQL query string
        options: Query options dictionary
        
    Returns:
        str: SHA256 hash as cache key
    """
    # Create a consistent string representation
    cache_data = f"{query}:{json.dumps(options, sort_keys=True)}"
    return hashlib.sha256(cache_data.encode()).hexdigest()


def parse_api_response(response_text: str, format_type: str = "json") -> Union[Dict[str, Any], str]:
    """
    Parse APARAVI API response based on format type.
    
    Args:
        response_text: Raw response text from API
        format_type: Expected format ("json" or "csv")
        
    Returns:
        Union[Dict[str, Any], str]: Parsed response data
        
    Raises:
        ValueError: If JSON parsing fails
    """
    if format_type.lower() == "json":
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")
    else:
        return response_text


def format_error_message(error: Exception, context: Optional[str] = None) -> str:
    """
    Format error messages for consistent logging and user feedback.
    
    Args:
        error: Exception that occurred
        context: Optional context information
        
    Returns:
        str: Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"{context}: {error_type} - {error_msg}"
    else:
        return f"{error_type}: {error_msg}"


def validate_aql_query(query: str) -> bool:
    """
    Basic validation of AQL query syntax.
    
    Args:
        query: AQL query string to validate
        
    Returns:
        bool: True if query appears valid, False otherwise
    """
    if not query or not query.strip():
        return False
    
    # Basic checks for AQL structure
    query_upper = query.upper().strip()
    
    # Must start with SELECT
    if not query_upper.startswith("SELECT"):
        return False
    
    # Must contain FROM clause
    if " FROM " not in query_upper:
        return False
    
    return True


def sanitize_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize query parameters to prevent injection attacks.
    
    Args:
        params: Dictionary of query parameters
        
    Returns:
        Dict[str, Any]: Sanitized parameters
    """
    sanitized = {}
    
    for key, value in params.items():
        if isinstance(value, str):
            # Remove potentially dangerous characters
            sanitized_value = value.replace(';', '').replace('--', '').replace('/*', '').replace('*/', '')
            sanitized[key] = sanitized_value.strip()
        else:
            sanitized[key] = value
    
    return sanitized


class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if datetime.now() > entry["expires"]:
            del self._cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self._default_ttl
        expires = datetime.now() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            "value": value,
            "expires": expires
        }
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of cached entries."""
        return len(self._cache)
