"""
APARAVI API client for handling authentication and query execution.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Union
import aiohttp
import base64
from .config import AparaviConfig
from .utils import (
    encode_aql_query,
    create_query_options,
    parse_api_response,
    format_error_message,
    SimpleCache,
    generate_cache_key
)


class AparaviAPIError(Exception):
    """Custom exception for APARAVI API errors."""
    pass


class AparaviClient:
    """Client for interacting with APARAVI API."""
    
    def __init__(self, config: AparaviConfig, logger: logging.Logger):
        """
        Initialize APARAVI client.
        
        Args:
            config: APARAVI configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache = SimpleCache(config.timeout) if hasattr(config, 'cache_ttl') else SimpleCache()
        
        # Create basic auth header
        credentials = f"{config.username}:{config.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self._auth_header = f"Basic {encoded_credentials}"
    
    async def initialize(self) -> None:
        """Initialize the HTTP session."""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": self._auth_header,
                    "Accept": "application/json"
                }
            )
            self.logger.info("APARAVI client session initialized")
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
            self.logger.info("APARAVI client session closed")
    
    async def health_check(self) -> Union[Dict[str, Any], str]:
        """
        Perform a health check against the APARAVI API.
        Tests API connectivity and validates AQL syntax using proper APARAVI query language.
        
        Returns:
            Union[Dict[str, Any], str]: API response data if successful, error message if failed
        """
        try:
            await self.initialize()
            
            # Use proper AQL syntax from reference guide to test connectivity
            # This validates syntax without executing the full query
            test_query = "SELECT name FROM STORE('/') WHERE ClassID = 'idxobject' LIMIT 1"
            
            self.logger.debug(f"Testing health check with query: {test_query}")
            
            # Execute the query to test both syntax and actual data retrieval
            params = {
                "select": encode_aql_query(test_query),
                "options": create_query_options(format_type="json", validate=False)
            }
            
            async with self._session.get(
                self.config.query_endpoint,
                params=params
            ) as response:
                self.logger.debug(f"Health check response status: {response.status}")
                if response.status == 200:
                    try:
                        response_text = await response.text()
                        self.logger.info(f"APARAVI API validation response: {response_text}")
                        
                        # Parse response to verify validation success
                        import json
                        response_data = json.loads(response_text)
                        
                        if response_data.get("status") == "OK":
                            self.logger.info("Health check passed - API accessible and AQL query executed successfully")
                            return response_data  # Return the actual API response data
                        elif response_data.get("status") == "error":
                            error_msg = response_data.get("message", "Unknown error")
                            self.logger.warning(f"Health check failed - AQL error: {error_msg}")
                            return f"AQL Error: {error_msg}"
                        else:
                            self.logger.info("Health check passed - API accessible (unexpected response format)")
                            return response_data  # Return whatever we got
                            
                    except Exception as e:
                        self.logger.warning(f"Could not parse response, but got 200 status: {format_error_message(e)}")
                        return f"Response received but could not parse JSON: {response_text[:200]}..."
                else:
                    self.logger.warning(f"Health check failed with status {response.status}")
                    return f"HTTP Error {response.status}: API request failed"
                    
        except Exception as e:
            error_msg = format_error_message(e)
            self.logger.error(f"Health check failed: {error_msg}")
            return f"Health check failed: {error_msg}"
    
    async def execute_query(
        self,
        query: str,
        format_type: str = "json",
        use_cache: bool = True
    ) -> Union[Dict[str, Any], str]:
        """
        Execute an AQL query against the APARAVI API.
        
        Args:
            query: AQL query string
            format_type: Response format ("json" or "csv")
            use_cache: Whether to use caching
            
        Returns:
            Union[Dict[str, Any], str]: Query results
            
        Raises:
            AparaviAPIError: If query execution fails
        """
        try:
            await self.initialize()
            
            # Check cache first
            cache_key = None
            if use_cache:
                options = {"format": format_type, "stream": False, "validate": True}
                cache_key = generate_cache_key(query, options)
                cached_result = self._cache.get(cache_key)
                if cached_result is not None:
                    self.logger.debug("Returning cached query result")
                    return cached_result
            
            # Prepare request parameters
            params = {
                "select": encode_aql_query(query),
                "options": create_query_options(format_type=format_type)
            }
            
            self.logger.info(f"Executing AQL query: {query[:100]}...")
            
            # Execute query with retries
            for attempt in range(self.config.max_retries + 1):
                try:
                    async with self._session.get(
                        self.config.query_endpoint,
                        params=params
                    ) as response:
                        
                        if response.status == 200:
                            response_text = await response.text()
                            result = parse_api_response(response_text, format_type)
                            
                            # Cache successful results
                            if use_cache and cache_key:
                                self._cache.set(cache_key, result)
                            
                            self.logger.info("Query executed successfully")
                            return result
                            
                        elif response.status == 401:
                            raise AparaviAPIError("Authentication failed - check username/password")
                        elif response.status == 400:
                            error_text = await response.text()
                            raise AparaviAPIError(f"Bad request - invalid query: {error_text}")
                        elif response.status == 404:
                            raise AparaviAPIError("API endpoint not found - check server configuration")
                        else:
                            error_text = await response.text()
                            raise AparaviAPIError(f"API request failed with status {response.status}: {error_text}")
                            
                except aiohttp.ClientError as e:
                    if attempt < self.config.max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        self.logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                    else:
                        raise AparaviAPIError(f"Request failed after {self.config.max_retries} retries: {e}")
                        
        except AparaviAPIError:
            raise
        except Exception as e:
            error_msg = format_error_message(e, "Query execution failed")
            self.logger.error(error_msg)
            raise AparaviAPIError(error_msg)
    
    async def validate_query(self, query: str) -> bool:
        """
        Validate an AQL query without executing it.
        
        Args:
            query: AQL query string to validate
            
        Returns:
            bool: True if query is valid, False otherwise
        """
        try:
            await self.initialize()
            
            params = {
                "select": encode_aql_query(query),
                "options": create_query_options(validate=True)
            }
            
            async with self._session.get(
                self.config.query_endpoint,
                params=params
            ) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Query validation failed: {format_error_message(e)}")
            return False
    
    def clear_cache(self) -> None:
        """Clear the query cache."""
        self._cache.clear()
        self.logger.info("Query cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        return {
            "cache_size": self._cache.size(),
            "cache_enabled": True
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
