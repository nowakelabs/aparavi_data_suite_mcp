"""
APARAVI MCP Server

A Model Context Protocol server for querying APARAVI data management systems.
Provides 20 predefined AQL reports as MCP tools for Claude Desktop integration.
"""

__version__ = "0.1.0"
__author__ = "Nowake Labs"
__email__ = "matt@nowakelabs.com"

from .server import AparaviMCPServer

__all__ = ["AparaviMCPServer"]
