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
    print("🧪 Testing APARAVI MCP Server")
    print("=" * 50)
    
    # Get the project directory
    project_dir = Path(__file__).parent
    server_script = project_dir / "scripts" / "start_server.py"
    
    if not server_script.exists():
        print(f"❌ Server script not found: {server_script}")
        return
    
    print(f"📁 Project directory: {project_dir}")
    print(f"🚀 Server script: {server_script}")
    
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
        
        print("✅ MCP server started")
        time.sleep(2)  # Give server more time to initialize
        
        # Check if process is still running
        if process.poll() is not None:
            stderr_output = process.stderr.read()
            print(f"❌ Server process exited early. Error: {stderr_output}")
            return
        
        # Test 1: Initialize
        print("\n📋 Test 1: Initialize")
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
            print("✅ Initialize successful")
            print(f"   Server info: {response['result'].get('serverInfo', {})}")
        else:
            print("❌ Initialize failed")
            # Try to read stderr for error details
            try:
                stderr_output = process.stderr.read()
                if stderr_output:
                    print(f"   Server error: {stderr_output}")
            except:
                pass
            return
        
        # Test 2: List Tools
        print("\n📋 Test 2: List Tools")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = send_mcp_request(process, list_tools_request)
        if response and "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
        else:
            print("❌ List tools failed")
            if response:
                print(f"   Response: {response}")
            return
        
        # Test 3: Call health_check tool
        print("\n📋 Test 3: Call health_check tool")
        health_check_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "health_check",
                "arguments": {}
            }
        }
        
        response = send_mcp_request(process, health_check_request)
        if response and "result" in response:
            content = response["result"].get("content", [])
            if content:
                print(f"✅ Health check result: {content[0].get('text', 'No text')}")
            else:
                print("✅ Health check completed (no content)")
        else:
            print("❌ Health check failed")
            if response:
                print(f"   Response: {response}")
        
        # Test 4: Call server_info tool
        print("\n📋 Test 4: Call server_info tool")
        server_info_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "server_info",
                "arguments": {}
            }
        }
        
        response = send_mcp_request(process, server_info_request)
        if response and "result" in response:
            content = response["result"].get("content", [])
            if content:
                print(f"✅ Server info result:")
                print(content[0].get('text', 'No text'))
            else:
                print("✅ Server info completed (no content)")
        else:
            print("❌ Server info failed")
            if response:
                print(f"   Response: {response}")
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            if 'process' in locals():
                process.terminate()
                process.wait(timeout=5)
                print("✅ Server process terminated")
        except:
            if 'process' in locals():
                process.kill()
                print("⚠️ Server process killed")

if __name__ == "__main__":
    test_mcp_server()
