#!/usr/bin/env python3
"""
Claude Desktop wrapper script for APARAVI MCP Server.
This ensures proper UV environment activation when launched from Claude Desktop.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main wrapper function."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.absolute()
    
    # Change to project directory
    os.chdir(project_root)
    
    # Set environment variables if not already set
    env = os.environ.copy()
    env.setdefault("APARAVI_HOST", "localhost")
    env.setdefault("APARAVI_PORT", "80")
    env.setdefault("APARAVI_API_VERSION", "v3")
    env.setdefault("LOG_LEVEL", "INFO")
    
    # Run the server using UV with explicit project path
    try:
        # Use UV to run the server with proper environment
        cmd = [
            "uv",
            "run",
            "--project", str(project_root),
            "python", 
            str(project_root / "scripts" / "start_server.py")
        ]
        
        # Execute the command
        subprocess.run(cmd, env=env, cwd=project_root, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running server: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"UV not found in PATH: {e}", file=sys.stderr)
        print("Please ensure UV is installed and available in your PATH", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
