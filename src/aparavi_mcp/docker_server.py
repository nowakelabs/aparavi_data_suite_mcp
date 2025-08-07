"""
Docker-specific HTTP server implementation for Aparavi MCP Server.
This provides HTTP-based MCP protocol support for containerized deployments.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .server import AparaviMCPServer
from .config import load_config, validate_config
from .utils import setup_logging


class AparaviMCPDockerServer:
    """HTTP-based MCP server for Docker deployments."""
    
    def __init__(self, config_path: Optional[str] = None, reports_config_path: Optional[str] = None):
        """Initialize the Docker MCP server."""
        # Load configuration
        self.config = load_config(config_path)
        validate_config(self.config)
        
        # Set up logging
        self.logger = setup_logging(self.config.server.log_level)
        
        # Initialize the core MCP server
        self.mcp_server = AparaviMCPServer(config_path, reports_config_path)
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="Aparavi MCP Server",
            description="HTTP-based MCP server for Aparavi Data Suite",
            version=self.config.server.version,
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure as needed for security
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Set up routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up HTTP routes for MCP protocol."""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "server": "aparavi-mcp-server"}
        
        @self.app.get("/info")
        async def server_info():
            """Get server information."""
            return {
                "name": self.config.server.name,
                "version": self.config.server.version,
                "protocol": "http",
                "mode": "docker"
            }
        
        @self.app.post("/mcp/initialize")
        async def initialize(request: Request):
            """Initialize MCP session."""
            try:
                data = await request.json()
                # The core server handles initialization internally
                return {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    },
                    "serverInfo": {
                        "name": self.config.server.name,
                        "version": self.config.server.version
                    }
                }
            except Exception as e:
                self.logger.error(f"Initialization error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/mcp/tools/list")
        async def list_tools(request: Request):
            """List available tools."""
            try:
                # Get tools from the core MCP server
                tools_response = await self.mcp_server.handle_list_tools()
                return {"tools": tools_response.tools}
            except Exception as e:
                self.logger.error(f"List tools error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/mcp/tools/call")
        async def call_tool(request: Request):
            """Call a specific tool."""
            try:
                data = await request.json()
                tool_name = data.get("name")
                arguments = data.get("arguments", {})
                
                if not tool_name:
                    raise HTTPException(status_code=400, detail="Tool name is required")
                
                # Call the tool using the core MCP server
                result = await self.mcp_server.handle_call_tool(tool_name, arguments)
                
                return {
                    "content": result.content,
                    "isError": result.isError if hasattr(result, 'isError') else False
                }
            except Exception as e:
                self.logger.error(f"Tool call error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/mcp/resources/list")
        async def list_resources(request: Request):
            """List available resources."""
            try:
                # Get resources from the core MCP server
                resources_response = await self.mcp_server.handle_list_resources()
                return {"resources": resources_response.resources}
            except Exception as e:
                self.logger.error(f"List resources error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/mcp/resources/read")
        async def read_resource(request: Request):
            """Read a specific resource."""
            try:
                data = await request.json()
                uri = data.get("uri")
                
                if not uri:
                    raise HTTPException(status_code=400, detail="Resource URI is required")
                
                # Read the resource using the core MCP server
                result = await self.mcp_server.handle_read_resource(uri)
                
                return {
                    "contents": result.contents
                }
            except Exception as e:
                self.logger.error(f"Read resource error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/mcp/prompts/list")
        async def list_prompts(request: Request):
            """List available prompts."""
            try:
                # Get prompts from the core MCP server
                prompts_response = await self.mcp_server.handle_list_prompts()
                return {"prompts": prompts_response.prompts}
            except Exception as e:
                self.logger.error(f"List prompts error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/mcp/prompts/get")
        async def get_prompt(request: Request):
            """Get a specific prompt."""
            try:
                data = await request.json()
                name = data.get("name")
                arguments = data.get("arguments", {})
                
                if not name:
                    raise HTTPException(status_code=400, detail="Prompt name is required")
                
                # Get the prompt using the core MCP server
                result = await self.mcp_server.handle_get_prompt(name, arguments)
                
                return {
                    "description": result.description,
                    "messages": result.messages
                }
            except Exception as e:
                self.logger.error(f"Get prompt error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the HTTP server."""
        self.logger.info(f"Starting Aparavi MCP Docker Server on {host}:{port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level=self.config.server.log_level.lower(),
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()


async def async_main() -> None:
    """Async main entry point for the Docker MCP server."""
    try:
        # Get configuration from environment
        host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_HTTP_PORT", "8080"))
        
        # Create and start server
        server = AparaviMCPDockerServer()
        await server.start_server(host, port)
        
    except Exception as e:
        logging.error(f"Failed to start Docker server: {e}")
        raise


def main() -> None:
    """Main entry point for the Docker MCP server."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nDocker server stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Docker server failed to start: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
