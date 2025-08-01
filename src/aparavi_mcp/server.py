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
            is_healthy = await self.aparavi_client.health_check()
            
            if is_healthy:
                message = "✅ APARAVI MCP Server is healthy and connected to APARAVI API"
                self.logger.info("Health check passed")
            else:
                message = "⚠️ APARAVI MCP Server is running but cannot connect to APARAVI API"
                self.logger.warning("Health check failed - API connectivity issue")
            
            return {
                "content": [{"type": "text", "text": message}]
            }
            
        except Exception as e:
            error_msg = f"❌ Health check failed: {format_error_message(e)}"
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
            
            info_text = "🔧 APARAVI MCP Server Information:\n\n"
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
                        print(response_json, flush=True)
                    
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
