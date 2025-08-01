#!/usr/bin/env python3
"""
Startup script for APARAVI MCP Server.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
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
  python start_server.py --config ../config/config.yaml
  python start_server.py --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (YAML format)"
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
        print("🚀 Starting APARAVI MCP Server...")
        print("Press Ctrl+C to stop the server")
        main()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)
