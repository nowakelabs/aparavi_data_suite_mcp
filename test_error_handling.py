#!/usr/bin/env python3
"""
Minimal test script to isolate where the APARAVI client freezes on syntax errors.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from aparavi_mcp.aparavi_client import AparaviClient
from aparavi_mcp.config import AparaviConfig

async def test_error_handling():
    """Test APARAVI client error handling with syntax error query."""
    
    print("Starting APARAVI Client Error Handling Test...")
    print("=" * 60)
    
    try:
        # Load configuration from environment variables
        config = AparaviConfig(
            host=os.getenv("APARAVI_HOST", "localhost"),
            port=int(os.getenv("APARAVI_PORT", "80")),
            username=os.getenv("APARAVI_USERNAME", ""),
            password=os.getenv("APARAVI_PASSWORD", ""),
            api_version=os.getenv("APARAVI_API_VERSION", "v3"),
            timeout=int(os.getenv("APARAVI_TIMEOUT", "30")),
            max_retries=int(os.getenv("APARAVI_MAX_RETRIES", "3"))
        )
        print(f"Server: {config.host}:{config.port}")
        print(f"Username: {config.username}")
        print(f"Timeout: {config.timeout} seconds")
        print()
        
        # Create logger
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        
        # Create APARAVI client
        client = AparaviClient(config, logger)
        
        # Test query with known syntax error (DISTINCT not supported)
        bad_query = """
SELECT    
  COMPONENTS(parentPath, 7) AS "Subfolder",
  COUNT(DISTINCT extension) AS "Unique Extensions"
FROM 
  STORE('/')
WHERE 
  ClassID = 'idxobject'
GROUP BY 
  COMPONENTS(parentPath, 7)
LIMIT 5
"""
        
        print("Testing query with syntax error...")
        print(f"Query: {bad_query.strip()}")
        print()
        print("Calling execute_query...")
        
        # This should NOT freeze - it should return an error response
        result = await client.execute_query(bad_query, format_type="json")
        
        print("execute_query completed!")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        # Check if it's an error response
        if isinstance(result, dict):
            if result.get("status") == "error":
                print("\nSUCCESS: Error was properly returned instead of freezing!")
                print(f"Error name: {result.get('name', 'Unknown')}")
                print(f"Error message: {result.get('message', 'No message')}")
            elif result.get("status") == "OK":
                print("\nUNEXPECTED: Query succeeded when it should have failed")
            else:
                print(f"\nUNEXPECTED: Unknown status: {result.get('status')}")
        else:
            print(f"\nUNEXPECTED: Result is not a dict: {result}")
            
    except Exception as e:
        print(f"\nEXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTest completed.")

if __name__ == "__main__":
    asyncio.run(test_error_handling())
