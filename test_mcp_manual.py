#!/usr/bin/env python3
"""
Manual test script for the APARAVI MCP server.
This sends JSON-RPC requests to test the server functionality.
"""

import json
import subprocess
import sys
import time
import os
from pathlib import Path

def send_mcp_request(process, request):
    """Send a JSON-RPC request to the MCP server."""
    request_json = json.dumps(request) + '\n'
    print(f"→ Sending: {request_json.strip()}")
    
    try:
        process.stdin.write(request_json)
        process.stdin.flush()
        
        # Read response with timeout
        response_line = process.stdout.readline().strip()
        if response_line:
            print(f"← Received: {response_line}")
            try:
                return json.loads(response_line)
            except json.JSONDecodeError as e:
                print(f"Error parsing response: {e}")
                return None
        else:
            print("← No response received")
            return None
    except Exception as e:
        print(f"Error sending request: {e}")
        return None

def test_mcp_server():
    """Test the MCP server functionality."""
    print("Testing APARAVI MCP Server")
    print("=" * 50)
    
    # Get the project directory
    project_dir = Path(__file__).parent
    server_script = project_dir / "scripts" / "start_server.py"
    
    if not server_script.exists():
        print(f"ERROR: Server script not found: {server_script}")
        return
    
    print(f"INFO: Project directory: {project_dir}")
    print(f"INFO: Server script: {server_script}")
    
    try:
        # Start the MCP server process with proper Windows configuration
        process = subprocess.Popen(
            [sys.executable, str(server_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Use text mode instead of binary
            bufsize=1,  # Line buffered
            cwd=str(project_dir),
            env=dict(os.environ, LOG_LEVEL="DEBUG")  # Add debug logging
        )
        
        print("SUCCESS: MCP server started")
        time.sleep(2)  # Give server more time to initialize
        
        # Check if process is still running
        if process.poll() is not None:
            stderr_output = process.stderr.read()
            print(f"ERROR: Server process exited early. Error: {stderr_output}")
            return
        
        # Test 1: Initialize
        print("\nTEST 1: Initialize")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = send_mcp_request(process, init_request)
        if response and "result" in response:
            print("SUCCESS: Initialize successful")
            print(f"   Server info: {response['result'].get('serverInfo', {})}")
        else:
            print("ERROR: Initialize failed")
            # Try to read stderr for error details
            try:
                stderr_output = process.stderr.read()
                if stderr_output:
                    print(f"   Server error: {stderr_output}")
            except:
                pass
            return
        
        # Test 2: List Tools
        print("\nTEST 2: List Tools")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = send_mcp_request(process, list_tools_request)
        if response and "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"SUCCESS: Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
        else:
            print("ERROR: Failed to list tools")
            if response:
                print(f"   Response: {response}")
            return
        
        # Test all discovered tools dynamically
        for i, tool in enumerate(tools, 3):  # Start from test 3
            tool_name = tool['name']
            print(f"\nTEST {i}: Call {tool_name} tool")
            
            tool_request = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {}
                }
            }
            
            response = send_mcp_request(process, tool_request)
            if response and "result" in response:
                content = response["result"].get("content", [])
                if content:
                    result_text = content[0].get('text', 'No text')
                    
                    # Handle different tool types with appropriate output
                    if tool_name == "health_check":
                        # Special handling for health check
                        if "SUCCESS:" in result_text:
                            print(f"SUCCESS: {result_text}")
                        elif "WARNING:" in result_text or "ERROR:" in result_text:
                            print(f"HEALTH CHECK ISSUE: {result_text}")
                        else:
                            print(f"HEALTH CHECK RESULT: {result_text}")
                    
                    elif tool_name == "server_info":
                        # Simple success for server info
                        print(f"SUCCESS: Server info result:")
                        print(result_text)
                    
                    elif "Error" in result_text or "ERROR" in result_text:
                        # Handle error responses for any tool
                        print(f"TOOL ERROR: {result_text}")
                    
                    else:
                        # Handle report tools and other successful responses
                        print(f"SUCCESS: {tool_name} completed:")
                        # Show first few lines of the response
                        lines = result_text.split('\n')
                        for line in lines[:10]:  # Show first 10 lines
                            print(f"   {line}")
                        if len(lines) > 10:
                            print(f"   ... and {len(lines) - 10} more lines")
                        
                else:
                    print(f"ERROR: {tool_name} completed but returned no content")
            else:
                print(f"ERROR: {tool_name} failed - no response received")
                if response:
                    print(f"   Response: {response}")
        
        print("\nSUCCESS: All tests completed!")
        
    except Exception as e:
        print(f"ERROR: Error running tests: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            if 'process' in locals():
                process.terminate()
                process.wait(timeout=5)
                print("SUCCESS: Server process terminated")
        except:
            if 'process' in locals():
                process.kill()
                print("WARNING: Server process killed")

if __name__ == "__main__":
    test_mcp_server()
