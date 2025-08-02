#!/usr/bin/env python3
"""
Test script for the generate_aql_query MCP tool.
Tests the intelligent AQL query builder with various business questions.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aparavi_mcp.server import AparaviMCPServer


async def test_generate_aql_query():
    """Test the generate_aql_query tool with various business questions."""
    
    print("Testing generate_aql_query MCP tool...")
    print("=" * 60)
    
    # Initialize the server
    try:
        server = AparaviMCPServer()
        print("Server initialized successfully")
    except Exception as e:
        print(f"Failed to initialize server: {e}")
        return
    
    # Test cases with different types of business questions
    test_cases = [
        {
            "name": "Duplicate Files Analysis",
            "business_question": "Show me storage waste from duplicate files by department",
            "complexity_preference": "simple"
        },
        {
            "name": "Large File Analysis",
            "business_question": "Find large PDF files created in the last 30 days",
            "filters": ["PDF files", "large files", "recent files"],
            "complexity_preference": "simple"
        },
        {
            "name": "Classification Analysis",
            "business_question": "Analyze sensitive data distribution across data sources",
            "desired_fields": ["classification", "parentPath", "size"],
            "complexity_preference": "comprehensive"
        },
        {
            "name": "Storage Growth Analysis",
            "business_question": "Which file types are consuming the most storage space?",
            "complexity_preference": "simple"
        },
        {
            "name": "Stale Data Analysis",
            "business_question": "Find old unused files that haven't been accessed in over a year",
            "complexity_preference": "simple"
        },
        {
            "name": "Invalid Field Test",
            "business_question": "General file analysis",
            "desired_fields": ["invalid_field", "size", "another_invalid_field"],
            "complexity_preference": "simple"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 40)
        
        # Prepare arguments
        arguments = {
            "business_question": test_case["business_question"],
            "complexity_preference": test_case.get("complexity_preference", "simple")
        }
        
        if "desired_fields" in test_case:
            arguments["desired_fields"] = test_case["desired_fields"]
        
        if "filters" in test_case:
            arguments["filters"] = test_case["filters"]
        
        print(f"Business Question: {test_case['business_question']}")
        if "desired_fields" in arguments:
            print(f"Desired Fields: {arguments['desired_fields']}")
        if "filters" in arguments:
            print(f"Filters: {arguments['filters']}")
        print(f"Complexity: {arguments['complexity_preference']}")
        print()
        
        try:
            # Call the generate_aql_query handler
            result = await server._handle_generate_aql_query(arguments)
            
            if result.get("isError"):
                print(f"ERROR: {result['content'][0]['text']}")
            else:
                response_text = result['content'][0]['text']
                # Print first 500 characters for overview
                print("Response Preview:")
                print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                
                # Check if it contains expected elements
                if "Generated AQL Query" in response_text:
                    print("\n✅ Successfully generated AQL query")
                else:
                    print("\n❌ Missing generated query section")
                
                if "Query Explanation" in response_text:
                    print("✅ Includes query explanation")
                else:
                    print("❌ Missing query explanation")
                
                if "Important Notes" in response_text:
                    print("✅ Includes important notes")
                else:
                    print("❌ Missing important notes")
                
                if "Next Steps" in response_text:
                    print("✅ Includes next steps")
                else:
                    print("❌ Missing next steps")
        
        except Exception as e:
            print(f"ERROR: Exception during test: {e}")
        
        print("\n" + "=" * 60)
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    asyncio.run(test_generate_aql_query())
