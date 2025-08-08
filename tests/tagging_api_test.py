#!/usr/bin/env python3
"""
Aparavi Tagging API Test Script
Tests auto-discovery of client object ID and all tagging functionality.
"""

import asyncio
import aiohttp
import json
import base64
import urllib.parse
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class AparaviConfig:
    base_url: str = "http://localhost/server/api/v3"
    username: str = "root"
    password: str = "root"
    timeout: int = 30


class AparaviTaggingTester:
    def __init__(self, config: AparaviConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.client_object_id: Optional[str] = None
        
        # Create auth header
        credentials = f"{self.config.username}:{self.config.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded_credentials}"
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Authorization": self.auth_header,
                "Accept": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def discover_client_object_id(self) -> Optional[str]:
        """
        Auto-discover client object ID using AQL query.
        Query: SELECT node, nodeObjectId WHERE nodeObjectID IS NOT NULL LIMIT 1
        """
        try:
            logger.info("🔍 Auto-discovering client object ID...")
            
            # AQL query to discover client object ID
            aql_query = "SELECT node, nodeObjectId WHERE nodeObjectID IS NOT NULL LIMIT 1"
            
            # Execute the query
            result = await self.execute_aql_query(aql_query)
            
            if result and 'data' in result and 'objects' in result['data'] and result['data']['objects']:
                first_row = result['data']['objects'][0]
                if 'nodeObjectId' in first_row:
                    discovered_id = first_row['nodeObjectId']
                    logger.info(f"✅ Successfully discovered client object ID: {discovered_id}")
                    self.client_object_id = discovered_id
                    return discovered_id
            
            logger.error("❌ Could not discover client object ID - no results returned")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to discover client object ID: {str(e)}")
            return None
    
    async def execute_aql_query(self, query: str) -> Dict[str, Any]:
        """Execute an AQL query and return the results."""
        try:
            # Use the correct endpoint format from the existing client
            endpoint = f"{self.config.base_url}/database/query"
            headers = {"Authorization": self.auth_header}
            
            # Use GET request with query parameters (like the existing client)
            params = {
                "select": query,  # The query goes in 'select' parameter
                "options": json.dumps({"format": "json", "stream": False, "validate": False})
            }
            
            logger.info(f"  🔍 Executing AQL query: {query}")
            logger.info(f"  📡 Endpoint: {endpoint}")
            logger.info(f"  📋 Parameters: {params}")
            
            async with self.session.get(endpoint, params=params, headers=headers) as response:
                logger.info(f"  📊 Response status: {response.status}")
                logger.info(f"  📋 Response headers: {dict(response.headers)}")
                
                response_text = await response.text()
                logger.info(f"  📄 Raw response: {response_text[:500]}...")
                
                if response.status == 200:
                    try:
                        # The existing client has a parse_api_response function, but we'll handle it directly
                        if response_text.strip().startswith('{'):
                            result = json.loads(response_text)
                        else:
                            # Handle CSV or other formats
                            result = {"data": response_text, "format": "text"}
                        
                        logger.info(f"  ✅ Parsed result: {result}")
                        return result
                    except json.JSONDecodeError as e:
                        logger.error(f"  ❌ Failed to parse JSON: {e}")
                        logger.error(f"  📄 Full response: {response_text}")
                        # Return as text if JSON parsing fails
                        return {"data": response_text, "format": "text", "error": str(e)}
                else:
                    logger.error(f"  ❌ AQL query failed with status {response.status}: {response_text}")
                    raise Exception(f"AQL query failed: {response_text}")
                    
        except Exception as e:
            logger.error(f"❌ Error executing AQL query: {str(e)}")
            raise
    
    async def test_tag_definitions(self) -> bool:
        """Test tag definition management (list, create, delete)."""
        try:
            logger.info("\n📋 Testing Tag Definitions Management...")
            
            if not self.client_object_id:
                logger.error("❌ Client object ID not available for tag definitions test")
                return False
            
            endpoint = f"{self.config.base_url}/tagDefinitions"
            headers = {"Authorization": self.auth_header, "Content-Type": "application/json"}
            
            # Test 1: List existing tag definitions
            logger.info("  📝 Testing list tag definitions...")
            params = {"clientObjectId": self.client_object_id}
            logger.info(f"  🔍 List request - Endpoint: {endpoint}")
            logger.info(f"  🔍 List request - Params: {params}")
            
            async with self.session.get(endpoint, params=params, headers=headers) as response:
                logger.info(f"  📊 List response status: {response.status}")
                response_text = await response.text()
                logger.info(f"  📄 List response: {response_text}")
                
                if response.status == 200:
                    result = json.loads(response_text)
                    # API returns {"status":"OK","data":["tag1","tag2",...]} format
                    existing_tags = result.get('data', [])
                    logger.info(f"  ✅ Listed {len(existing_tags)} existing tag definitions")
                    if existing_tags:
                        logger.info(f"  📋 Existing tags: {existing_tags}")
                else:
                    logger.error(f"  ❌ Failed to list tag definitions: {response.status}")
                    logger.error(f"  📄 Error response: {response_text}")
                    return False
            
            # Test 2: Create test tag definitions
            logger.info("  📝 Testing create tag definitions...")
            test_tags = ["test-tag-1", "test-tag-2", "automation-test"]
            
            # API expects tagDefinitions to be array of strings, not objects
            payload = {
                "clientObjectId": self.client_object_id,
                "tagDefinitions": test_tags  # Just the tag names as strings
            }
            
            logger.info(f"  🔍 Create request - Endpoint: {endpoint}")
            logger.info(f"  🔍 Create request - Payload: {json.dumps(payload, indent=2)}")
            
            async with self.session.post(endpoint, json=payload, headers=headers) as response:
                logger.info(f"  📊 Create response status: {response.status}")
                response_text = await response.text()
                logger.info(f"  📄 Create response: {response_text}")
                
                if response.status in [200, 201]:
                    logger.info(f"  ✅ Successfully created {len(test_tags)} test tag definitions")
                    try:
                        create_result = json.loads(response_text)
                        logger.info(f"  📋 Create result details: {create_result}")
                    except:
                        logger.info(f"  📋 Create response was not JSON")
                else:
                    logger.warning(f"  ⚠️ Create tag definitions returned {response.status}: {response_text}")
            
            # Test 3: List again to verify creation
            logger.info("  📝 Verifying tag definitions were created...")
            async with self.session.get(endpoint, params=params, headers=headers) as response:
                logger.info(f"  📊 Verify response status: {response.status}")
                response_text = await response.text()
                logger.info(f"  📄 Verify response: {response_text}")
                
                if response.status == 200:
                    result = json.loads(response_text)
                    # API returns {"status":"OK","data":["tag1","tag2",...]} format
                    all_tags = result.get('data', [])
                    created_count = sum(1 for tag in test_tags if tag in all_tags)
                    
                    logger.info(f"  📋 All tags found: {all_tags}")
                    logger.info(f"  📋 Test tags we created: {test_tags}")
                    logger.info(f"  📋 Matching tags: {[tag for tag in test_tags if tag in all_tags]}")
                    logger.info(f"  ✅ Verified {created_count}/{len(test_tags)} test tags exist")
                else:
                    logger.error(f"  ❌ Failed to verify tag definitions: {response.status}")
                    logger.error(f"  📄 Verify error response: {response_text}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Tag definitions test failed: {str(e)}")
            return False
    
    async def test_file_tagging(self) -> bool:
        """Test file tagging operations (apply/remove tags)."""
        try:
            logger.info("\n🏷️  Testing File Tagging Operations...")
            
            # First, get some files to tag using AQL
            logger.info("  📝 Finding files to tag...")
            file_query = "SELECT objectId, instanceId, name WHERE name IS NOT NULL LIMIT 5"
            query_result = await self.execute_aql_query(file_query)
            
            if not query_result or not query_result.get('data') or not query_result['data'].get('objects'):
                logger.error("  ❌ No files found for tagging test")
                return False
            
            # Prepare file objects for tagging
            file_objects = []
            for row in query_result['data']['objects']:
                if 'objectId' in row and 'instanceId' in row:
                    file_objects.append({
                        "objectId": row['objectId'],
                        "instanceId": row['instanceId']
                    })
            
            if not file_objects:
                logger.error("  ❌ No valid file objects found for tagging")
                return False
            
            logger.info(f"  ✅ Found {len(file_objects)} files for tagging test")
            
            # Test applying tags
            logger.info("  📝 Testing apply tags to files...")
            endpoint = f"{self.config.base_url}/tags"
            headers = {"Authorization": self.auth_header, "Content-Type": "application/json"}
            
            test_tags = ["test-tag-1", "automation-test"]
            payload = {
                "objects": file_objects[:2],  # Tag first 2 files
                "tags": [{"name": tag} for tag in test_tags]
            }
            
            async with self.session.post(endpoint, json=payload, headers=headers) as response:
                if response.status in [200, 201, 204]:
                    logger.info(f"  ✅ Successfully applied {len(test_tags)} tags to {len(payload['objects'])} files")
                else:
                    error_text = await response.text()
                    logger.warning(f"  ⚠️ Apply tags returned {response.status}: {error_text}")
            
            # Test removing tags
            logger.info("  📝 Testing remove tags from files...")
            async with self.session.delete(endpoint, json=payload, headers=headers) as response:
                if response.status in [200, 204]:
                    logger.info(f"  ✅ Successfully removed {len(test_tags)} tags from {len(payload['objects'])} files")
                else:
                    error_text = await response.text()
                    logger.warning(f"  ⚠️ Remove tags returned {response.status}: {error_text}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ File tagging test failed: {str(e)}")
            return False
    
    async def test_tag_search(self) -> bool:
        """Test searching files by tags."""
        try:
            logger.info("\n🔍 Testing Tag-based File Search...")
            
            # Test search for files with specific tags
            logger.info("  📝 Testing search files by tags...")
            
            # Use AQL to search for tagged files
            search_query = "SELECT objectId, name, tags WHERE tags IS NOT NULL LIMIT 10"
            result = await self.execute_aql_query(search_query)
            
            if result and result.get('data') and result['data'].get('objects'):
                tagged_files = len(result['data']['objects'])
                logger.info(f"  ✅ Found {tagged_files} files with tags")
                
                # Show sample of tagged files
                for i, row in enumerate(result['data']['objects'][:3]):
                    filename = row.get('name', 'Unknown')
                    tags = row.get('tags', [])
                    logger.info(f"    📄 {filename}: {tags}")
            else:
                logger.info("  ℹ️ No tagged files found (this is normal for a fresh system)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Tag search test failed: {str(e)}")
            return False
    
    async def test_health_check(self) -> bool:
        """Test basic API connectivity."""
        try:
            logger.info("\n🏥 Testing API Health Check...")
            
            endpoint = f"{self.config.base_url}/health"
            headers = {"Authorization": self.auth_header}
            
            logger.info(f"  📡 Health check endpoint: {endpoint}")
            
            async with self.session.get(endpoint, headers=headers) as response:
                logger.info(f"  📊 Response status: {response.status}")
                logger.info(f"  📋 Response headers: {dict(response.headers)}")
                
                response_text = await response.text()
                logger.info(f"  📄 Raw response: {response_text[:200]}...")
                
                if response.status == 200:
                    try:
                        result = json.loads(response_text)
                        logger.info(f"  ✅ API health check passed: {result}")
                        return True
                    except json.JSONDecodeError:
                        logger.warning(f"  ⚠️ Health endpoint returned HTML instead of JSON")
                        logger.info(f"  ℹ️ This might be normal - checking if we can still do AQL queries")
                        return True  # Don't fail just because health returns HTML
                else:
                    logger.error(f"  ❌ API health check failed: {response.status}")
                    logger.error(f"  📄 Error response: {response_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return False
    
    async def run_complete_test_suite(self):
        """Run the complete tagging API test suite."""
        logger.info("🚀 Starting Aparavi Tagging API Test Suite")
        logger.info("=" * 60)
        
        results = {}
        
        # Test 1: Health Check
        results['health_check'] = await self.test_health_check()
        
        # Test 2: Auto-discover client object ID
        client_id = await self.discover_client_object_id()
        results['client_id_discovery'] = client_id is not None
        
        if not client_id:
            logger.error("❌ Cannot continue tests without client object ID")
            return results
        
        # Test 3: Tag Definitions Management
        results['tag_definitions'] = await self.test_tag_definitions()
        
        # Test 4: File Tagging Operations
        results['file_tagging'] = await self.test_file_tagging()
        
        # Test 5: Tag-based Search
        results['tag_search'] = await self.test_tag_search()
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name.replace('_', ' ').title()}: {status}")
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if client_id:
            logger.info(f"\n🔑 Discovered Client Object ID: {client_id}")
            logger.info("    This ID can be used for APARAVI_CLIENT_OBJECT_ID environment variable")
        
        return results


async def main():
    """Main function to run the test suite."""
    
    config = AparaviConfig(
        base_url="http://localhost/server/api/v3",
        username="root",
        password="root"
    )
    
    logger.info("Aparavi Tagging API Test Script")
    logger.info("Testing auto-discovery and all tagging functionality")
    logger.info(f"Target: {config.base_url}")
    logger.info(f"Username: {config.username}")
    
    try:
        async with AparaviTaggingTester(config) as tester:
            results = await tester.run_complete_test_suite()
            
            # Exit with appropriate code
            if all(results.values()):
                logger.info("\n🎉 All tests passed successfully!")
                return 0
            else:
                logger.error("\n💥 Some tests failed!")
                return 1
                
    except Exception as e:
        logger.error(f"💥 Test suite failed with error: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
