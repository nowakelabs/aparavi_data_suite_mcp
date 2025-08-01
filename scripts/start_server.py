#!/usr/bin/env python3
"""
Startup script for APARAVI MCP Server (Simplified Version).
This version avoids the TaskGroup issues present in the standard MCP SDK.
"""

import argparse
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from aparavi_mcp.server import main


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Start the APARAVI MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_server.py
  python start_server.py --log-level DEBUG
  python start_server.py --log-level INFO

Environment Variables:
  APARAVI_HOST          - APARAVI server hostname (default: localhost)
  APARAVI_PORT          - APARAVI server port (default: 80)
  APARAVI_USERNAME      - APARAVI username
  APARAVI_PASSWORD      - APARAVI password
  APARAVI_API_VERSION   - APARAVI API version (default: v3)
  LOG_LEVEL             - Logging level (default: INFO)
        """
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override log level from configuration"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Set environment variables from command line args if provided
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level
    
    try:
        # Don't print to stdout as it interferes with MCP JSON-RPC communication
        # The server will handle its own logging via the logging framework
        main()
    except KeyboardInterrupt:
        # Write to stderr instead of stdout to avoid interfering with MCP protocol
        print("\nServer stopped by user", file=sys.stderr)
