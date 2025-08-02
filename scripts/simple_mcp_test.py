#!/usr/bin/env python3
"""
Simple test for MCP validate_aql_query tool with user's specific query.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aparavi_mcp.server import AparaviMCPServer


async def test_mcp_validation():
    """Test MCP validate_aql_query tool with user's specific query."""
    
    # Test queries: valid and invalid
    queries = [
        {
            "name": "Valid Query",
            "query": "SELECT COUNT(extension) as \"Number of Documents\", extension WHERE extension IN('xls','xlsx','xlsm','xls') GROUP BY extension;",
            "expected": "VALID"
        },
        {
            "name": "Invalid Query (with FROM files)",
            "query": "SELECT COUNT(extension) as \"Number of Documents\", extension FROM files WHERE extension IN('xls','xlsx','xlsm','xls') GROUP BY extension;",
            "expected": "INVALID"
        }
    ]
    
    print("Simple MCP Validation Test")
    print("=" * 50)
    
    try:
        # Initialize MCP server
        server = AparaviMCPServer()
        print("[OK] MCP Server initialized")
        
        # Test each query
        for i, test_case in enumerate(queries, 1):
            print(f"\n{'='*60}")
            print(f"TEST {i}: {test_case['name']}")
            print(f"Expected: {test_case['expected']}")
            print(f"{'='*60}")
            print(f"Query: {test_case['query']}")
            print("-" * 60)
            
            # Test the validate_aql_query tool
            arguments = {"query": test_case['query']}
            result = await server._handle_validate_aql_query(arguments)
            
            # Check result
            if result.get("isError"):
                actual_status = "ERROR"
                print("[ERROR] Validation failed with error")
            else:
                content = result.get("content", [])
                if content and len(content) > 0:
                    text = content[0].get("text", "")
                    if "**Status:** VALID" in text:
                        actual_status = "VALID"
                        print("[RESULT] Query marked as VALID")
                    elif "**Status:** INVALID" in text:
                        actual_status = "INVALID"
                        print("[RESULT] Query marked as INVALID")
                        # Extract error message
                        if "**Error:**" in text:
                            error_start = text.find("**Error:**") + len("**Error:**")
                            error_end = text.find("\n\n", error_start)
                            if error_end > error_start:
                                error_msg = text[error_start:error_end].strip()
                                print(f"[ERROR] {error_msg}")
                    else:
                        actual_status = "UNKNOWN"
                        print("[WARN] Unexpected validation response")
                else:
                    actual_status = "NO_CONTENT"
                    print("[FAIL] No content returned from validation")
            
            # Check if result matches expectation
            if actual_status == test_case['expected']:
                print(f"[PASS] Test {i} PASSED - Expected {test_case['expected']}, got {actual_status}")
            else:
                print(f"[FAIL] Test {i} FAILED - Expected {test_case['expected']}, got {actual_status}")
        
        print(f"\n{'='*60}")
        print("TESTING COMPLETE")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n[FAIL] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_mcp_validation())
    sys.exit(exit_code)
