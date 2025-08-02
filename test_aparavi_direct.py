#!/usr/bin/env python3
"""
Standalone test script to directly connect to APARAVI API and show response.
This bypasses the MCP server to isolate response reading issues.
"""

import asyncio
import aiohttp
import base64
import os
import json
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv


def load_env_config():
    """Load configuration from .env file."""
    # Look for .env file in project root
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        raise FileNotFoundError(f"Could not find .env file at {env_path}")
    
    load_dotenv(env_path)
    
    config = {
        'username': os.getenv('APARAVI_USERNAME'),
        'password': os.getenv('APARAVI_PASSWORD'),
        'server_url': os.getenv('APARAVI_SERVER_URL', 'http://localhost'),
        'server_port': os.getenv('APARAVI_SERVER_PORT', '80'),
        'timeout': int(os.getenv('APARAVI_TIMEOUT', '30'))
    }
    
    # Validate required config
    if not config['username'] or not config['password']:
        raise ValueError("APARAVI_USERNAME and APARAVI_PASSWORD must be set in .env file")
    
    return config


def encode_aql_query(query: str) -> str:
    """Prepare an AQL query string for API requests.
    Note: aiohttp automatically handles URL encoding, so we return the query as-is
    to prevent double encoding.
    """
    return query


def create_query_options(format_type: str = "json", validate: bool = True) -> str:
    """Create options JSON string for APARAVI API queries."""
    options = {
        "format": format_type,
        "stream": False,
        "validate": validate
    }
    return json.dumps(options)


async def test_aparavi_api():
    """Test direct connection to APARAVI API."""
    print("APARAVI API Direct Connection Test")
    print("=" * 50)
    
    try:
        # Load configuration
        print("Loading configuration from .env file...")
        config = load_env_config()
        print(f"Server: {config['server_url']}:{config['server_port']}")
        print(f"Username: {config['username']}")
        print(f"Timeout: {config['timeout']} seconds")
        print()
        
        # Create authentication header
        credentials = f"{config['username']}:{config['password']}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        auth_header = f"Basic {encoded_credentials}"
        
        # Build API endpoint URL
        api_url = f"{config['server_url']}:{config['server_port']}/server/api/v3/database/query"
        print(f"API Endpoint: {api_url}")
        
        # Test query - Subfolder Overview
        test_query = """
SELECT    
  COMPONENTS(parentPath, 7) AS "Subfolder",
  SUM(size)/1073741824 AS "Size (GB)",
  COUNT(name) AS "File Count",
  AVG(size)/1048576 AS "Average File Size (MB)",
  
  -- File type diversity
  COUNT(DISTINCT extension) AS "Unique Extensions",
  
  -- Activity indicators
  SUM(CASE WHEN (cast(NOW() as number) - createTime) < (30 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Files Created Last 30 Days",
  SUM(CASE WHEN (cast(NOW() as number) - accessTime) > (365 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Stale Files (>1 Year)"
  
FROM 
  STORE('/')
WHERE 
  ClassID = 'idxobject'
GROUP BY 
  COMPONENTS(parentPath, 7)
ORDER BY 
  "Size (GB)" DESC
LIMIT 50
""".strip()
        print(f"Test Query: {test_query}")
        print()
        
        # Prepare request parameters
        params = {
            "select": encode_aql_query(test_query),
            "options": create_query_options(format_type="json", validate=True)
        }
        
        print("Testing with validation mode (validate=true)...")
        print("-" * 30)
        
        # Create HTTP session
        timeout = aiohttp.ClientTimeout(total=config['timeout'])
        async with aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Authorization": auth_header,
                "Accept": "application/json"
            }
        ) as session:
            
            print("Making HTTP GET request...")
            async with session.get(api_url, params=params) as response:
                print(f"Response Status: {response.status}")
                print(f"Response Headers: {dict(response.headers)}")
                print()
                
                if response.status == 200:
                    print("SUCCESS: Got 200 status code")
                    print("Reading response body...")
                    
                    try:
                        # Try reading with timeout
                        response_text = await asyncio.wait_for(response.text(), timeout=5)
                        print("SUCCESS: Response body read successfully")
                        print(f"Response Length: {len(response_text)} characters")
                        print()
                        print("Response Content:")
                        print("-" * 20)
                        print(response_text)
                        print("-" * 20)
                        
                        # Try parsing as JSON
                        try:
                            response_data = json.loads(response_text)
                            print()
                            print("JSON Parsing: SUCCESS")
                            print("Parsed Response:")
                            print(json.dumps(response_data, indent=2))
                        except json.JSONDecodeError as e:
                            print(f"JSON Parsing: FAILED - {e}")
                            
                    except asyncio.TimeoutError:
                        print("ERROR: Timed out reading response body (5 seconds)")
                    except Exception as e:
                        print(f"ERROR: Failed to read response body - {e}")
                        
                else:
                    print(f"ERROR: Got non-200 status code: {response.status}")
                    try:
                        error_text = await response.text()
                        print(f"Error Response: {error_text}")
                    except:
                        print("Could not read error response")
        
        print()
        print("Testing with execution mode (validate=false)...")
        print("-" * 30)
        
        # Test with actual query execution
        params_exec = {
            "select": encode_aql_query(test_query),
            "options": create_query_options(format_type="json", validate=False)
        }
        
        async with aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Authorization": auth_header,
                "Accept": "application/json"
            }
        ) as session:
            
            print("Making HTTP GET request for execution...")
            async with session.get(api_url, params=params_exec) as response:
                print(f"Response Status: {response.status}")
                print()
                
                if response.status == 200:
                    print("SUCCESS: Got 200 status code")
                    print("Reading response body...")
                    
                    try:
                        response_text = await asyncio.wait_for(response.text(), timeout=5)
                        print("SUCCESS: Response body read successfully")
                        print(f"Response Length: {len(response_text)} characters")
                        print()
                        print("Response Content:")
                        print("-" * 20)
                        print(response_text)
                        print("-" * 20)
                        
                        try:
                            response_data = json.loads(response_text)
                            print()
                            print("JSON Parsing: SUCCESS")
                            print("Parsed Response:")
                            print(json.dumps(response_data, indent=2))
                        except json.JSONDecodeError as e:
                            print(f"JSON Parsing: FAILED - {e}")
                            
                    except asyncio.TimeoutError:
                        print("ERROR: Timed out reading response body (5 seconds)")
                    except Exception as e:
                        print(f"ERROR: Failed to read response body - {e}")
                        
                else:
                    print(f"ERROR: Got non-200 status code: {response.status}")
                    try:
                        error_text = await response.text()
                        print(f"Error Response: {error_text}")
                    except:
                        print("Could not read error response")
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting APARAVI API Direct Test...")
    print()
    asyncio.run(test_aparavi_api())
    print()
    print("Test completed.")
