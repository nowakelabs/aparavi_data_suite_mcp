"""
Main MCP server implementation for APARAVI data management system.
This simplified version avoids the TaskGroup issues present in the standard MCP SDK.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from .config import Config, load_config, validate_config
from .utils import setup_logging, format_error_message
from .aparavi_client import AparaviClient


class AparaviMCPServer:
    """APARAVI MCP Server for querying data management systems."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the APARAVI MCP server.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Load and validate configuration
        self.config = load_config(config_path)
        validate_config(self.config)
        
        # Set up logging
        self.logger = setup_logging(self.config.server.log_level)
        self.logger.info(f"Initializing APARAVI MCP Server v{self.config.server.version}")
        
        # Initialize APARAVI client
        self.aparavi_client = AparaviClient(self.config.aparavi, self.logger)
        
        self.logger.info("APARAVI MCP Server initialized successfully")
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        self.logger.info("Handling initialize request")
        
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": self.config.server.name,
                "version": self.config.server.version
            }
        }
    
    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        self.logger.debug("Listing available tools")
        
        tools = [
            {
                "name": "health_check",
                "description": "Check the health and connectivity of the APARAVI MCP server",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "server_info",
                "description": "Get information about the APARAVI MCP server configuration",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "data_sources_overview",
                "description": "Get comprehensive analysis of data sources including size, activity indicators, and file categorization metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "subfolder_overview",
                "description": "Analyze subfolder structure showing size and file count distribution across deeper directory levels",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "file_type_extension_summary",
                "description": "Comprehensive analysis of file types including size metrics, distribution, and file size ranges by extension",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        self.logger.debug(f"Returning {len(tools)} tools")
        return {"tools": tools}
    
    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        self.logger.info(f"Executing tool: {tool_name}")
        
        try:
            if tool_name == "health_check":
                return await self._handle_health_check()
            elif tool_name == "server_info":
                return await self._handle_server_info()
            elif tool_name == "data_sources_overview":
                return await self._handle_data_sources_overview()
            elif tool_name == "subfolder_overview":
                return await self._handle_subfolder_overview()
            elif tool_name == "file_type_extension_summary":
                return await self._handle_file_type_extension_summary()
            else:
                error_msg = f"Unknown tool: {tool_name}"
                self.logger.error(error_msg)
                return {
                    "content": [{"type": "text", "text": error_msg}],
                    "isError": True
                }
                
        except Exception as e:
            error_msg = format_error_message(e, f"Tool execution failed for {tool_name}")
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
    
    async def _handle_health_check(self) -> Dict[str, Any]:
        """Handle health check requests."""
        self.logger.debug("Performing health check")
        
        try:
            # Test APARAVI API connectivity
            health_result = await self.aparavi_client.health_check()
            
            if isinstance(health_result, dict):
                # Successful response with API data
                import json
                formatted_response = json.dumps(health_result, indent=2)
                message = f"SUCCESS: APARAVI MCP Server is healthy and connected to APARAVI API\n\nAPARAVI API Response:\n{formatted_response}"
                self.logger.info("Health check passed with API response data")
            elif isinstance(health_result, str):
                # Error message from health check
                if "Error" in health_result or "failed" in health_result:
                    message = f"WARNING: {health_result}"
                    self.logger.warning(f"Health check failed: {health_result}")
                else:
                    message = f"SUCCESS: {health_result}"
                    self.logger.info(f"Health check passed: {health_result}")
            else:
                message = f"UNKNOWN: Unexpected health check result: {health_result}"
                self.logger.warning(f"Unexpected health check result type: {type(health_result)}")
            
            return {
                "content": [{"type": "text", "text": message}]
            }
            
        except Exception as e:
            error_msg = f"ERROR: Health check failed: {format_error_message(e)}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
    
    async def _handle_server_info(self) -> Dict[str, Any]:
        """Handle server info requests."""
        self.logger.debug("Getting server information")
        
        try:
            info = {
                "server_name": self.config.server.name,
                "server_version": self.config.server.version,
                "aparavi_host": self.config.aparavi.host,
                "aparavi_port": self.config.aparavi.port,
                "aparavi_api_version": self.config.aparavi.api_version,
                "cache_enabled": self.config.server.cache_enabled,
                "log_level": self.config.server.log_level
            }
            
            info_text = "APARAVI MCP Server Information:\n\n"
            for key, value in info.items():
                info_text += f"• {key.replace('_', ' ').title()}: {value}\n"
            
            return {
                "content": [{"type": "text", "text": info_text}]
            }
            
        except Exception as e:
            error_msg = f"Failed to get server info: {format_error_message(e)}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
    
    async def _handle_data_sources_overview(self) -> Dict[str, Any]:
        """Handle data sources overview report requests."""
        self.logger.debug("Generating data sources overview report")
        
        try:
            # AQL query for comprehensive data sources analysis
            aql_query = """
SELECT
 COMPONENTS(parentPath, 3) AS "Data Source",
 SUM(size)/1073741824 AS "Total Size (GB)",
 COUNT(name) AS "File Count",
 AVG(size)/1048576 AS "Average File Size (MB)",
 
 -- Recent activity indicators
 SUM(CASE WHEN (cast(NOW() as number) - createTime) < (30 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Files Created Last 30 Days",
 SUM(CASE WHEN (cast(NOW() as number) - accessTime) > (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Stale Files (>1 Year)",
 
 -- Size categories
 SUM(CASE WHEN size > 1073741824 THEN 1 ELSE 0 END) AS "Large Files (>1GB)",
 
 -- Duplicates
 SUM(CASE WHEN dupCount > 1 THEN 1 ELSE 0 END) AS "Files with Duplicates"

FROM 
 STORE('/')
WHERE 
 ClassID = 'idxobject'
GROUP BY 
 COMPONENTS(parentPath, 3)
ORDER BY 
 "Total Size (GB)" DESC
""".strip()
            
            self.logger.info("Executing data sources overview query")
            
            # Execute the AQL query
            result = await self.aparavi_client.execute_query(aql_query, format_type="json")
            
            if isinstance(result, dict) and result.get("status") == "OK":
                # Return raw JSON response for the agent to interpret
                import json
                json_response = json.dumps(result, indent=2)
                self.logger.info(f"Data sources overview query executed successfully")
                
                return {
                    "content": [{"type": "text", "text": f"# APARAVI Data Sources Overview\n\nRaw JSON Response:\n```json\n{json_response}\n```"}]
                }
                
            else:
                # Handle error response
                error_msg = "Failed to generate data sources overview report"
                if isinstance(result, str):
                    error_msg += f": {result}"
                elif isinstance(result, dict):
                    error_msg += f": {result.get('message', 'Unknown error')}"
                
                self.logger.error(error_msg)
                return {
                    "content": [{"type": "text", "text": error_msg}],
                    "isError": True
                }
                
        except Exception as e:
            error_msg = f"Error generating data sources overview: {format_error_message(e)}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
    

            
        else:
            # Handle error response
            error_msg = "Failed to generate data sources overview report"
            if isinstance(result, str):
                error_msg += f": {result}"
            elif isinstance(result, dict):
                error_msg += f": {result.get('message', 'Unknown error')}"
            
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }

    async def _handle_subfolder_overview(self) -> Dict[str, Any]:
        """Handle subfolder overview tool request."""
        try:
            self.logger.info("Generating subfolder overview report")
            
            # AQL query for subfolder analysis - EXACT from reference documentation
            aql_query = """
SELECT    
  COMPONENTS(parentPath, 7) AS Subfolder,
  SUM(size) as "Size",
  COUNT(name) as "Count"
WHERE ClassID LIKE 'idxobject'
GROUP BY Subfolder
ORDER BY SUM(size) DESC
"""
            
            # Execute the AQL query
            result = await self.aparavi_client.execute_query(aql_query, format_type="json")
            
            if isinstance(result, dict) and result.get("status") == "OK":
                # Return raw JSON response for the agent to interpret
                import json
                json_response = json.dumps(result, indent=2)
                self.logger.info(f"Subfolder overview query executed successfully")
                
                return {
                    "content": [{"type": "text", "text": f"# APARAVI Subfolder Overview\n\nRaw JSON Response:\n```json\n{json_response}\n```"}]
                }
            else:
                # Handle error response
                error_msg = f"Failed to execute subfolder overview query. Response: {result}"
                self.logger.error(error_msg)
                return {
                    "content": [{"type": "text", "text": error_msg}],
                    "isError": True
                }
                
        except Exception as e:
            error_msg = f"Error generating subfolder overview: {format_error_message(e)}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }

    async def _handle_file_type_extension_summary(self) -> Dict[str, Any]:
        """Handle file type extension summary tool request."""
        try:
            self.logger.info("Generating file type extension summary report")
            
            # AQL query for file type/extension analysis - EXACT from reference documentation
            aql_query = """
SELECT
 CASE
   WHEN extension IS NULL THEN 'No Extension'
   WHEN extension = '' THEN 'No Extension'
   ELSE extension
 END AS "File Type",
 COUNT(name) AS "File Count",
 SUM(size) AS "Total Size (Bytes)",
 SUM(size)/1048576 AS "Total Size (MB)",
 AVG(size)/1048576 AS "Average File Size (MB)",
 MIN(size)/1048576 AS "Smallest File (MB)",
 MAX(size)/1048576 AS "Largest File (MB)"
FROM 
 STORE('/')
WHERE
 ClassID = 'idxobject'
GROUP BY
 CASE
   WHEN extension IS NULL THEN 'No Extension'
   WHEN extension = '' THEN 'No Extension'
   ELSE extension
 END
ORDER BY
 SUM(size) DESC
"""
            
            # Execute the AQL query
            result = await self.aparavi_client.execute_query(aql_query, format_type="json")
            
            if isinstance(result, dict) and result.get("status") == "OK":
                # Return raw JSON response for the agent to interpret
                import json
                json_response = json.dumps(result, indent=2)
                self.logger.info(f"File type extension summary query executed successfully")
                
                return {
                    "content": [{"type": "text", "text": f"# APARAVI File Type / Extension Summary\n\nRaw JSON Response:\n```json\n{json_response}\n```"}]
                }
            else:
                # Handle error response
                error_msg = f"Failed to execute file type extension summary query. Response: {result}"
                self.logger.error(error_msg)
                return {
                    "content": [{"type": "text", "text": error_msg}],
                    "isError": True
                }
                
        except Exception as e:
            error_msg = f"Error generating file type extension summary: {format_error_message(e)}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        self.logger.debug(f"Handling request: {method}")
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_list_tools(params)
            elif method == "tools/call":
                result = await self.handle_call_tool(params)
            elif method == "notifications/initialized":
                # Handle initialization notification (no response needed)
                self.logger.debug("Received initialization notification")
                return None  # No response for notifications
            elif method == "resources/list":
                # We don't provide resources, return empty list
                result = {"resources": []}
            elif method == "prompts/list":
                # We don't provide prompts, return empty list
                result = {"prompts": []}
            else:
                raise ValueError(f"Unknown method: {method}")
            
            # Don't send response for notifications
            if method.startswith("notifications/"):
                return None
                
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            error_msg = format_error_message(e, f"Request handling failed for {method}")
            self.logger.error(error_msg)
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": error_msg
                }
            }
        
        return response
    
    async def run(self) -> None:
        """Run the MCP server."""
        self.logger.info("Starting APARAVI MCP Server")
        
        try:
            # Initialize APARAVI client connection
            await self.aparavi_client.initialize()
            
            # Read from stdin and write to stdout
            while True:
                try:
                    # Read JSON-RPC request from stdin
                    line = await asyncio.to_thread(sys.stdin.readline)
                    if not line:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse JSON request
                    request = json.loads(line)
                    
                    # Handle request
                    response = await self.handle_request(request)
                    
                    # Send JSON response to stdout
                    if response is not None:
                        response_json = json.dumps(response)
                        try:
                            print(response_json, flush=True)
                        except (OSError, IOError, UnicodeEncodeError) as e:
                            # Handle case where stdout is closed (e.g., when Claude Desktop disconnects)
                            self.logger.debug(f"Stdout write failed (connection closed): {e}")
                            break
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON received: {e}")
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing request: {e}")
                    continue
                    
        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested")
        except Exception as e:
            self.logger.error(f"Server error: {format_error_message(e)}")
            raise
        finally:
            # Ensure proper cleanup
            try:
                await self.aparavi_client.close()
            except Exception as e:
                self.logger.warning(f"Error during cleanup: {e}")
            self.logger.info("APARAVI MCP Server stopped")


async def async_main() -> None:
    """Async main entry point for the APARAVI MCP server."""
    try:
        server = AparaviMCPServer()
        await server.run()
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        raise


def main() -> None:
    """Main entry point for the APARAVI MCP server."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Server failed to start: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
