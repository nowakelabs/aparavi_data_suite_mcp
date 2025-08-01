"""
Main MCP server implementation for APARAVI data management system.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR
)

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
        
        # Initialize MCP server
        self.server = Server(self.config.server.name)
        
        # Initialize APARAVI client
        self.aparavi_client = AparaviClient(self.config.aparavi, self.logger)
        
        # Register MCP handlers
        self._register_handlers()
        
        self.logger.info("APARAVI MCP Server initialized successfully")
    
    def _register_handlers(self) -> None:
        """Register MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available APARAVI query tools."""
            self.logger.debug("Listing available tools")
            
            # For Phase 1, we'll return a basic health check tool
            # Phase 2 will add the 20 APARAVI report tools
            tools = [
                Tool(
                    name="health_check",
                    description="Check the health and connectivity of the APARAVI MCP server",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="server_info",
                    description="Get information about the APARAVI MCP server configuration",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
            
            self.logger.debug(f"Returning {len(tools)} tools")
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool execution requests."""
            self.logger.info(f"Executing tool: {name}")
            
            try:
                if name == "health_check":
                    return await self._handle_health_check()
                elif name == "server_info":
                    return await self._handle_server_info()
                else:
                    error_msg = f"Unknown tool: {name}"
                    self.logger.error(error_msg)
                    return CallToolResult(
                        content=[TextContent(type="text", text=error_msg)],
                        isError=True
                    )
                    
            except Exception as e:
                error_msg = format_error_message(e, f"Tool execution failed for {name}")
                self.logger.error(error_msg)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )
    
    async def _handle_health_check(self) -> CallToolResult:
        """
        Handle health check requests.
        
        Returns:
            CallToolResult: Health check results
        """
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
            
            return CallToolResult(
                content=[TextContent(type="text", text=message)]
            )
            
        except Exception as e:
            error_msg = f"❌ Health check failed: {format_error_message(e)}"
            self.logger.error(error_msg)
            return CallToolResult(
                content=[TextContent(type="text", text=error_msg)],
                isError=True
            )
    
    async def _handle_server_info(self) -> CallToolResult:
        """
        Handle server info requests.
        
        Returns:
            CallToolResult: Server information
        """
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
            
            return CallToolResult(
                content=[TextContent(type="text", text=info_text)]
            )
            
        except Exception as e:
            error_msg = f"Failed to get server info: {format_error_message(e)}"
            self.logger.error(error_msg)
            return CallToolResult(
                content=[TextContent(type="text", text=error_msg)],
                isError=True
            )
    
    async def run(self) -> None:
        """Run the MCP server."""
        self.logger.info("Starting APARAVI MCP Server")
        
        try:
            # Initialize APARAVI client connection
            await self.aparavi_client.initialize()
            
            # Run the MCP server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=self.config.server.name,
                        server_version=self.config.server.version
                    )
                )
                
        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested")
        except Exception as e:
            self.logger.error(f"Server error: {format_error_message(e)}")
            raise
        finally:
            self.logger.info("APARAVI MCP Server stopped")


def main() -> None:
    """Main entry point for the APARAVI MCP server."""
    try:
        server = AparaviMCPServer()
        asyncio.run(server.run())
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
