"""
Aparavi Data Suite MCP Server Package

A Model Context Protocol (MCP) server for querying Aparavi Data Suite systems.
Provides tools for executing predefined AQL reports and managing data queries.
"""

__version__ = "1.0.0"
__author__ = "Nowake Labs"
__email__ = "ask@nowakelabs.com"

# Import main server class
from .server import AparaviMCPServer, main

__all__ = ["AparaviMCPServer", "main"]
