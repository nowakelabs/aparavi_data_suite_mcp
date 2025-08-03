#!/usr/bin/env python3
"""
Simple MCP server test to verify basic protocol compliance.
This script tests the MCP server directly without going through Claude.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from aparavi_mcp.server import AparaviMCPServer


async def test_mcp_protocol():
    """Test basic MCP protocol compliance."""
    print("Testing MCP Protocol Compliance...")
    
    try:
        # Initialize server
        server = AparaviMCPServer()
        
        # Test 1: Initialize request
        print("\n1. Testing initialize request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        init_response = await server.handle_request(init_request)
        print(f"Initialize response: {json.dumps(init_response, indent=2)}")
        
        # Validate initialize response
        if init_response and init_response.get("jsonrpc") == "2.0" and init_response.get("id") == 1:
            print("✓ Initialize request passed")
        else:
            print("✗ Initialize request failed")
            return False
        
        # Test 2: Tools list request
        print("\n2. Testing tools/list request...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        tools_response = await server.handle_request(tools_request)
        print(f"Tools response: {json.dumps(tools_response, indent=2)}")
        
        # Validate tools response
        if tools_response and tools_response.get("jsonrpc") == "2.0" and tools_response.get("id") == 2:
            print("✓ Tools list request passed")
        else:
            print("✗ Tools list request failed")
            return False
        
        # Test 3: Tool call request
        print("\n3. Testing tools/call request...")
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "guide_start_here",
                "arguments": {}
            }
        }
        
        call_response = await server.handle_request(call_request)
        print(f"Tool call response: {json.dumps(call_response, indent=2)}")
        
        # Validate call response
        if call_response and call_response.get("jsonrpc") == "2.0" and call_response.get("id") == 3:
            print("✓ Tool call request passed")
        else:
            print("✗ Tool call request failed")
            return False
        
        # Test 4: Invalid method request
        print("\n4. Testing invalid method request...")
        invalid_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "invalid/method",
            "params": {}
        }
        
        invalid_response = await server.handle_request(invalid_request)
        print(f"Invalid method response: {json.dumps(invalid_response, indent=2)}")
        
        # Validate error response
        if (invalid_response and 
            invalid_response.get("jsonrpc") == "2.0" and 
            invalid_response.get("id") == 4 and
            "error" in invalid_response):
            print("✓ Invalid method request handled correctly")
        else:
            print("✗ Invalid method request not handled correctly")
            return False
        
        print("\n✓ All MCP protocol tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ MCP protocol test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Set up environment for testing
    os.environ.setdefault("APARAVI_HOST", "localhost")
    os.environ.setdefault("APARAVI_PORT", "80")
    os.environ.setdefault("APARAVI_USERNAME", "test")
    os.environ.setdefault("APARAVI_PASSWORD", "test")
    
    success = asyncio.run(test_mcp_protocol())
    sys.exit(0 if success else 1)
