"""
APARAVI API client for handling authentication and query execution.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Union
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
        
        # Store client object ID for tagging operations
        self.client_object_id = getattr(config, 'client_object_id', None)
    
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
        use_cache: bool = True,
        validate_only: bool = False
    ) -> Union[Dict[str, Any], str]:
        """
        Execute an AQL query against the APARAVI API.
        
        Args:
            query: AQL query string
            format_type: Response format ("json" or "csv")
            use_cache: Whether to use caching
            validate_only: If True, only validate query syntax without execution
            
        Returns:
            Union[Dict[str, Any], str]: Query results or validation response
            
        Raises:
            AparaviAPIError: If query execution fails
        """
        try:
            await self.initialize()
            
            # Skip cache for validation-only requests
            cache_key = None
            if use_cache and not validate_only:
                options = {"format": format_type, "stream": False, "validate": False}
                cache_key = generate_cache_key(query, options)
                cached_result = self._cache.get(cache_key)
                if cached_result is not None:
                    self.logger.debug("Returning cached query result")
                    return cached_result
            
            # Prepare request parameters
            params = {
                "select": encode_aql_query(query),
                "options": create_query_options(format_type=format_type, validate=validate_only)
            }
            
            if validate_only:
                self.logger.info(f"Validating AQL query: {query[:100]}...")
            else:
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
                            
                            # Check if the API returned an error within the 200 response
                            if isinstance(result, dict) and result.get("status") == "error":
                                if validate_only:
                                    self.logger.warning(f"APARAVI API validation failed: {result}")
                                else:
                                    self.logger.warning(f"APARAVI API returned error: {result}")
                                # Return the error response instead of raising an exception
                                # This allows the MCP server to handle and display the error properly
                                return result
                            
                            # Cache successful results only (not validation results)
                            if use_cache and cache_key and not validate_only:
                                self._cache.set(cache_key, result)
                            
                            if validate_only:
                                self.logger.info("Query validation successful")
                            else:
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
    
    # ==================== TAGGING FUNCTIONALITY ====================
    
    async def manage_tag_definitions(self, action: str, tag_names: List[str] = None) -> Dict[str, Any]:
        """
        Manage tag definitions (create/list/delete).
        
        Args:
            action: Action to perform ('create', 'list', 'delete')
            tag_names: List of tag names (required for create/delete)
            
        Returns:
            Dict[str, Any]: API response
            
        Raises:
            AparaviAPIError: If API request fails
        """
        try:
            await self.initialize()
            
            if not self.client_object_id:
                raise AparaviAPIError("Client object ID not configured for tagging operations")
            
            endpoint = f"{self.config.base_url}/tagDefinitions"
            headers = {"Authorization": self._auth_header, "Content-Type": "application/json"}
            
            if action == "list":
                params = {"clientObjectId": self.client_object_id}
                async with self._session.get(endpoint, params=params, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.logger.debug(f"Tag definitions API response: {result}")
                        
                        # Parse the actual API response format: {"status": "OK", "data": [...]}
                        tag_list = []
                        if isinstance(result, dict) and result.get('status') == 'OK':
                            tag_list = result.get('data', [])
                        elif isinstance(result, list):
                            tag_list = result
                        elif isinstance(result, dict):
                            # Fallback for other formats
                            tag_list = result.get('tagDefinitions', result.get('tags', []))
                        
                        self.logger.info(f"Retrieved {len(tag_list)} tag definitions")
                        # Normalize response format
                        return {"tagDefinitions": tag_list}
                    else:
                        error_text = await response.text()
                        raise AparaviAPIError(f"Failed to list tag definitions: {error_text}")
            
            elif action in ["create", "delete"]:
                if not tag_names:
                    raise AparaviAPIError(f"Tag names required for {action} operation")
                
                # Validate tag names
                validated_tags = self.validate_tag_names(tag_names)
                if not validated_tags:
                    raise AparaviAPIError("No valid tag names provided")
                
                payload = {
                    "clientObjectId": self.client_object_id,
                    "tagDefinitions": validated_tags
                }
                
                method = self._session.post if action == "create" else self._session.delete
                async with method(endpoint, json=payload, headers=headers) as response:
                    if response.status in [200, 201, 204]:
                        result = await response.json() if response.content_length else {"status": "success"}
                        self.logger.info(f"Successfully {action}d {len(validated_tags)} tag definitions")
                        return result
                    else:
                        error_text = await response.text()
                        raise AparaviAPIError(f"Failed to {action} tag definitions: {error_text}")
            
            else:
                raise AparaviAPIError(f"Invalid action '{action}'. Must be 'create', 'list', or 'delete'")
                
        except AparaviAPIError:
            raise
        except Exception as e:
            error_msg = format_error_message(e, f"Tag definition {action} failed")
            self.logger.error(error_msg)
            raise AparaviAPIError(error_msg)
    
    async def manage_file_tags(self, action: str, file_objects: List[Dict], tag_names: List[str]) -> Dict[str, Any]:
        """
        Apply or remove tags from files.
        
        Args:
            action: Action to perform ('apply' or 'remove')
            file_objects: List of file objects with objectId and instanceId
            tag_names: List of tag names to apply or remove
            
        Returns:
            Dict[str, Any]: API response
            
        Raises:
            AparaviAPIError: If API request fails
        """
        try:
            await self.initialize()
            
            if action not in ["apply", "remove"]:
                raise AparaviAPIError(f"Invalid action '{action}'. Must be 'apply' or 'remove'")
            
            if not file_objects:
                raise AparaviAPIError("No file objects provided")
            
            if not tag_names:
                raise AparaviAPIError("No tag names provided")
            
            # Validate file objects
            validated_objects = self._validate_file_objects(file_objects)
            if not validated_objects:
                raise AparaviAPIError("No valid file objects provided")
            
            # Validate tag names
            validated_tags = self.validate_tag_names(tag_names)
            if not validated_tags:
                raise AparaviAPIError("No valid tag names provided")
            
            endpoint = f"{self.config.base_url}/tags"
            headers = {"Authorization": self._auth_header, "Content-Type": "application/json"}
            
            payload = {
                "objects": validated_objects,
                "tags": validated_tags
            }
            
            method = self._session.post if action == "apply" else self._session.delete
            async with method(endpoint, json=payload, headers=headers) as response:
                if response.status in [200, 201, 204]:
                    result = await response.json() if response.content_length else {"status": "success"}
                    self.logger.info(f"Successfully {action}d {len(validated_tags)} tags to {len(validated_objects)} files")
                    return result
                else:
                    error_text = await response.text()
                    raise AparaviAPIError(f"Failed to {action} file tags: {error_text}")
                    
        except AparaviAPIError:
            raise
        except Exception as e:
            error_msg = format_error_message(e, f"File tag {action} failed")
            self.logger.error(error_msg)
            raise AparaviAPIError(error_msg)
    
    async def extract_file_objects_from_aql(self, aql_query: str) -> List[Dict]:
        """
        Extract objectId/instanceId from AQL query results.
        
        Args:
            aql_query: AQL query to execute
            
        Returns:
            List[Dict]: List of file objects with objectId and instanceId
            
        Raises:
            AparaviAPIError: If query execution fails
        """
        try:
            # Ensure query includes required fields
            if "objectId" not in aql_query or "instanceId" not in aql_query:
                # Modify query to include required fields
                if "SELECT" in aql_query.upper():
                    # Add objectId and instanceId to existing SELECT
                    select_match = re.search(r'SELECT\s+(.+?)\s+FROM', aql_query, re.IGNORECASE)
                    if select_match:
                        existing_fields = select_match.group(1).strip()
                        if existing_fields != "*":
                            if "objectId" not in existing_fields:
                                existing_fields += ",objectId"
                            if "instanceId" not in existing_fields:
                                existing_fields += ",instanceId"
                            aql_query = aql_query.replace(select_match.group(1), existing_fields)
                else:
                    raise AparaviAPIError("Query must be a SELECT statement")
            
            # Execute query
            results = await self.execute_query(aql_query, format_type="json")
            
            # Extract file objects from the correct AQL response format
            file_objects = []
            self.logger.debug(f"AQL query results format: {type(results)}")
            
            # Handle the actual AQL response format: {"status": "OK", "data": {"objects": [...]}}
            data_rows = []
            if isinstance(results, dict):
                if results.get('status') == 'OK' and 'data' in results:
                    # This is the correct AQL response format
                    data_section = results['data']
                    if isinstance(data_section, dict) and 'objects' in data_section:
                        data_rows = data_section['objects']
                        self.logger.debug(f"Found {len(data_rows)} objects in AQL response")
                    else:
                        self.logger.debug(f"No 'objects' key in data section. Data keys: {list(data_section.keys()) if isinstance(data_section, dict) else 'N/A'}")
                elif "data" in results and isinstance(results["data"], list):
                    # Fallback for direct data array
                    data_rows = results["data"]
                elif "results" in results:
                    data_rows = results["results"]
                elif "rows" in results:
                    data_rows = results["rows"]
                else:
                    self.logger.debug(f"Unexpected results format. Keys: {list(results.keys())}")
            elif isinstance(results, list):
                data_rows = results
            
            self.logger.debug(f"Found {len(data_rows)} data rows to process")
            
            for i, row in enumerate(data_rows):
                self.logger.debug(f"Processing row {i}: {row}")
                if isinstance(row, dict):
                    # Check for objectId and instanceId in various formats
                    object_id = row.get("objectId") or row.get("object_id") or row.get("ObjectId")
                    instance_id = row.get("instanceId") or row.get("instance_id") or row.get("InstanceId")
                    
                    if object_id is not None and instance_id is not None:
                        try:
                            file_objects.append({
                                "objectId": str(object_id),
                                "instanceId": int(instance_id)
                            })
                        except (ValueError, TypeError) as e:
                            self.logger.warning(f"Invalid objectId/instanceId format in row {i}: {e}")
                    else:
                        self.logger.debug(f"Row {i} missing objectId or instanceId: {list(row.keys())}")
            
            self.logger.info(f"Extracted {len(file_objects)} file objects from AQL query")
            return file_objects
            
        except Exception as e:
            error_msg = format_error_message(e, "Failed to extract file objects from AQL query")
            self.logger.error(error_msg)
            raise AparaviAPIError(error_msg)
    
    def validate_tag_names(self, tag_names: List[str]) -> List[str]:
        """Validate tag names according to Aparavi requirements.
        
        Args:
            tag_names: List of tag names to validate
            
        Returns:
            List of valid tag names
            
        Raises:
            AparaviAPIError: If no valid tag names provided
        """
        if not tag_names:
            return []
        
        valid_tags = []
        for tag in tag_names:
            if not isinstance(tag, str):
                self.logger.warning(f"Skipping non-string tag: {tag}")
                continue
                
            # Clean and validate tag
            cleaned_tag = tag.strip()
            if not cleaned_tag:
                self.logger.warning(f"Skipping empty tag: '{tag}'")
                continue
                
            if len(cleaned_tag) > 100:
                # Truncate instead of rejecting
                cleaned_tag = cleaned_tag[:100]
                self.logger.warning(f"Tag truncated to 100 chars: '{cleaned_tag}'")
                
            # More permissive validation - allow most printable characters except problematic ones
            import re
            # Remove problematic characters instead of rejecting the whole tag
            cleaned_tag = re.sub(r'[<>"\\|*?/]', '', cleaned_tag)
            
            if cleaned_tag and len(cleaned_tag.strip()) > 0:
                valid_tags.append(cleaned_tag.strip())
            else:
                self.logger.warning(f"Tag became empty after cleaning: '{tag}'")
        
        return valid_tags
    
    def _validate_file_objects(self, file_objects: List[Dict]) -> List[Dict]:
        """
        Validate file objects format.
        
        Args:
            file_objects: List of file objects to validate
            
        Returns:
            List[Dict]: List of valid file objects
        """
        valid_objects = []
        
        for obj in file_objects:
            if not isinstance(obj, dict):
                self.logger.warning(f"Skipping invalid file object: {obj}")
                continue
            
            if "objectId" not in obj or "instanceId" not in obj:
                self.logger.warning(f"File object missing required fields: {obj}")
                continue
            
            try:
                valid_objects.append({
                    "objectId": str(obj["objectId"]),
                    "instanceId": int(obj["instanceId"])
                })
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Invalid file object format: {obj} - {e}")
                continue
        
        return valid_objects
    
    def build_tag_search_query(self, tag_filters: Dict[str, Any], additional_filters: str = "", limit: int = 1000) -> str:
        """
        Build AQL query for tag-based file search.
        
        Args:
            tag_filters: Tag filter criteria
            additional_filters: Additional AQL WHERE conditions
            limit: Query result limit
            
        Returns:
            str: Generated AQL query
        """
        # Base SELECT with tag fields
        select_fields = "name,objectId,instanceId,size,createTime,modifyTime,userTag,userTags"
        
        # Build tag conditions
        conditions = []
        
        # Include tags (OR/AND logic)
        include_tags = tag_filters.get("include_tags", [])
        if include_tags:
            include_conditions = []
            for tag in include_tags:
                # Use LIKE pattern for tag matching
                include_conditions.append(f"userTags LIKE '%;{tag};%'")
            
            tag_logic = tag_filters.get("tag_logic", "OR")
            if tag_logic == "AND":
                conditions.extend(include_conditions)  # Each as separate condition
            else:  # OR logic
                conditions.append(f"({' OR '.join(include_conditions)})")
        
        # Exclude tags
        exclude_tags = tag_filters.get("exclude_tags", [])
        if exclude_tags:
            for tag in exclude_tags:
                conditions.append(f"userTags NOT LIKE '%;{tag};%'")
        
        # Combine all conditions
        where_clause = ""
        if conditions:
            where_clause = " AND ".join(conditions)
        
        if additional_filters:
            if where_clause:
                where_clause += f" AND {additional_filters}"
            else:
                where_clause = additional_filters
        
        # Build complete query
        query = f"SELECT {select_fields} FROM STORE('/')"
        if where_clause:
            query += f" WHERE {where_clause}"
        query += f" ORDER BY name,objectId,instanceId LIMIT {limit}"
        
        return query
