"""
APARAVI MCP Server Package

A Model Context Protocol (MCP) server for querying APARAVI data management systems.
Provides tools for executing predefined AQL reports and managing data queries.
"""

__version__ = "0.1.0"
__author__ = "Nowake Labs"
__email__ = "hello@nowakelabs.com"

# Import main server class
from .server import AparaviMCPServer, main

__all__ = ["AparaviMCPServer", "main"]
