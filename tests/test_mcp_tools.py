#!/usr/bin/env python3
"""
Comprehensive test script for Aparavi Data Suite MCP Server tools.
Tests all 7 available tools with various scenarios and validates responses.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aparavi_mcp.server import AparaviMCPServer
from aparavi_mcp.config import load_config


class MCPToolTester:
    """Test harness for MCP server tools."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the test harness."""
        self.server = None
        self.config_path = config_path
        self.test_results = []
        self.setup_logging()
        
    def setup_logging(self):
        """Set up logging for the test harness."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("MCPToolTester")
        
    async def initialize_server(self):
        """Initialize the MCP server for testing."""
        try:
            self.logger.info("Initializing MCP server...")
            self.server = AparaviMCPServer(config_path=self.config_path)
            
            # Initialize the server
            init_params = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
            
            init_result = await self.server.handle_initialize(init_params)
            self.logger.info(f"Server initialized: {init_result['serverInfo']['name']} v{init_result['serverInfo']['version']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize server: {e}")
            return False
    
    def log_test_result(self, tool_name: str, test_case: str, success: bool, 
                       response: Optional[Dict] = None, error: Optional[str] = None):
        """Log a test result."""
        result = {
            "tool": tool_name,
            "test_case": test_case,
            "success": success,
            "timestamp": time.time(),
            "response_length": len(str(response)) if response else 0,
            "error": error
        }
        self.test_results.append(result)
        
        status = "PASS" if success else "FAIL"
        self.logger.info(f"{status} - {tool_name}: {test_case}")
        if error:
            self.logger.error(f"  Error: {error}")
    
    async def test_tool(self, tool_name: str, test_case: str, arguments: Dict[str, Any]) -> bool:
        """Test a single tool with given arguments."""
        try:
            params = {
                "name": tool_name,
                "arguments": arguments
            }
            
            response = await self.server.handle_call_tool(params)
            
            # Check if response has expected structure
            if not isinstance(response, dict):
                raise ValueError("Response is not a dictionary")
            
            if "content" not in response:
                raise ValueError("Response missing 'content' field")
            
            # Check for actual error responses (isError flag)
            if response.get("isError", False):
                content = response.get("content", [])
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict):
                        text = first_content.get("text", "")
                        # This might be an expected error for some test cases
                        if "validation" not in test_case.lower() and "invalid" not in test_case.lower():
                            raise ValueError(f"Tool returned error: {text[:200]}...")
            
            self.log_test_result(tool_name, test_case, True, response)
            return True
            
        except Exception as e:
            self.log_test_result(tool_name, test_case, False, error=str(e))
            return False
    
    async def test_guide_start_here(self):
        """Test the guide_start_here tool."""
        self.logger.info("\n=== Testing guide_start_here tool ===")
        
        test_cases = [
            {
                "name": "New user with no parameters",
                "args": {}
            },
            {
                "name": "New user with specific goal",
                "args": {
                    "user_experience": "new",
                    "query_goal": "duplicates",
                    "preferred_approach": "guided",
                    "context_window": "medium"
                }
            },
            {
                "name": "Advanced user with custom query goal",
                "args": {
                    "user_experience": "advanced",
                    "query_goal": "custom",
                    "preferred_approach": "custom_queries",
                    "context_window": "large",
                    "specific_question": "I need to analyze file growth patterns by department"
                }
            },
            {
                "name": "Intermediate user with security focus",
                "args": {
                    "user_experience": "intermediate",
                    "query_goal": "security",
                    "preferred_approach": "reports"
                }
            }
        ]
        
        for test_case in test_cases:
            await self.test_tool("guide_start_here", test_case["name"], test_case["args"])
    
    async def test_health_check(self):
        """Test the health_check tool."""
        self.logger.info("\n=== Testing health_check tool ===")
        
        await self.test_tool("health_check", "Basic health check", {})
    
    async def test_server_info(self):
        """Test the server_info tool."""
        self.logger.info("\n=== Testing server_info tool ===")
        
        await self.test_tool("server_info", "Get server information", {})
    
    async def test_run_aparavi_report(self):
        """Test the run_aparavi_report tool."""
        self.logger.info("\n=== Testing run_aparavi_report tool ===")
        
        test_cases = [
            {
                "name": "List available reports",
                "args": {"report_name": "list"}
            },
            {
                "name": "List available workflows", 
                "args": {"workflow_name": "list"}
            },
            {
                "name": "Run data sources overview report",
                "args": {"report_name": "data_sources_overview"}
            },
            {
                "name": "Run storage audit workflow",
                "args": {"workflow_name": "storage_audit"}
            }
        ]
        
        for test_case in test_cases:
            await self.test_tool("run_aparavi_report", test_case["name"], test_case["args"])
    
    async def test_validate_aql_query(self):
        """Test the validate_aql_query tool."""
        self.logger.info("\n=== Testing validate_aql_query tool ===")
        
        test_cases = [
            {
                "name": "Valid simple query",
                "args": {"query": "SELECT name, size FROM STORE('/') WHERE ClassID = 'idxobject' AND size > 1000000"}
            },
            {
                "name": "Valid query with date filter",
                "args": {"query": "SELECT name, createTime FROM STORE('/') WHERE ClassID = 'idxobject' AND createTime > 1704067200"}
            },
            {
                "name": "Invalid query - syntax error",
                "args": {"query": "SELECT name FROM WHERE size"}
            },
            {
                "name": "Invalid query - unknown field",
                "args": {"query": "SELECT invalidField FROM STORE('/') WHERE ClassID = 'idxobject'"}
            }
        ]
        
        for test_case in test_cases:
            await self.test_tool("validate_aql_query", test_case["name"], test_case["args"])
    
    async def test_execute_custom_aql_query(self):
        """Test the execute_custom_aql_query tool."""
        self.logger.info("\n=== Testing execute_custom_aql_query tool ===")
        
        test_cases = [
            {
                "name": "Simple file count query",
                "args": {"query": "SELECT COUNT(*) as total_files FROM STORE('/') WHERE ClassID = 'idxobject'"}
            },
            {
                "name": "File size summary query",
                "args": {"query": "SELECT COUNT(*) as file_count, SUM(size) as total_size FROM STORE('/') WHERE ClassID = 'idxobject' AND size > 0"}
            },
            {
                "name": "Recent files query",
                "args": {"query": "SELECT name, size, createTime FROM STORE('/') WHERE ClassID = 'idxobject' AND (cast(NOW() as number) - createTime) < (7 * 24 * 60 * 60) ORDER BY createTime DESC"}
            }
        ]
        
        for test_case in test_cases:
            await self.test_tool("execute_custom_aql_query", test_case["name"], test_case["args"])
    
    async def test_generate_aql_query(self):
        """Test the generate_aql_query tool."""
        self.logger.info("\n=== Testing generate_aql_query tool ===")
        
        test_cases = [
            {
                "name": "Simple file analysis request",
                "args": {
                    "business_question": "Show me all PDF files larger than 10MB",
                    "complexity_preference": "simple"
                }
            },
            {
                "name": "Complex analysis with specific fields",
                "args": {
                    "business_question": "Analyze file growth patterns by department over the last 6 months",
                    "desired_fields": ["fileName", "fileSize", "createdTime", "department"],
                    "filters": ["created in last 6 months", "group by department"],
                    "complexity_preference": "comprehensive"
                }
            },
            {
                "name": "Security-focused query",
                "args": {
                    "business_question": "Find potentially sensitive files that haven't been accessed recently",
                    "desired_fields": ["fileName", "lastAccessTime", "classification"],
                    "filters": ["not accessed in 90 days", "contains PII or sensitive data"],
                    "complexity_preference": "simple"
                }
            },
            {
                "name": "Duplicate file analysis",
                "args": {
                    "business_question": "Identify duplicate files consuming the most storage space",
                    "complexity_preference": "comprehensive"
                }
            }
        ]
        
        for test_case in test_cases:
            await self.test_tool("generate_aql_query", test_case["name"], test_case["args"])
    
    async def test_manage_tag_definitions(self):
        """Test the manage_tag_definitions tool."""
        self.logger.info("\n=== Testing manage_tag_definitions tool ===")
        
        test_cases = [
            {
                "name": "List all tag definitions",
                "args": {"action": "list"}
            },
            {
                "name": "Create new tag definitions",
                "args": {
                    "action": "create",
                    "tag_names": ["test:category1", "test:category2", "project:testing"]
                }
            },
            {
                "name": "List tags after creation",
                "args": {"action": "list"}
            },
            {
                "name": "Delete test tag definitions",
                "args": {
                    "action": "delete",
                    "tag_names": ["test:category1", "test:category2", "project:testing"]
                }
            }
        ]
        
        for test_case in test_cases:
            await self.test_tool("manage_tag_definitions", test_case["name"], test_case["args"])
    
    async def test_apply_file_tags(self):
        """Test the apply_file_tags tool."""
        self.logger.info("\n=== Testing apply_file_tags tool ===")
        
        # First create some test tags
        await self.test_tool("manage_tag_definitions", "Create test tags for file tagging", {
            "action": "create",
            "tag_names": ["test:document", "test:budget", "test:handbook"]
        })
        
        test_cases = [
            {
                "name": "Tag PDF files via AQL query",
                "args": {
                    "action": "apply",
                    "file_selection": {
                        "method": "search_query",
                        "search_query": "SELECT name,objectId,instanceId FROM STORE('/') WHERE name IN ('2013-14-budget.pdf', '2019-2020-Employee-Handbook-.pdf')"
                    },
                    "tag_names": ["test:document", "test:budget"]
                }
            },
            {
                "name": "Tag specific file by object ID",
                "args": {
                    "action": "apply",
                    "file_selection": {
                        "method": "file_objects",
                        "file_objects": [
                            {
                                "objectId": "07d360d1-iobj-4dcb-a5df-619172de6392@f7388d0e-apag-4e86-86f0-1fbedb0b63db",
                                "instanceId": 1893
                            }
                        ]
                    },
                    "tag_names": ["test:handbook"]
                }
            },
            {
                "name": "Remove tags from files",
                "args": {
                    "action": "remove",
                    "file_selection": {
                        "method": "search_query",
                        "search_query": "SELECT name,objectId,instanceId FROM STORE('/') WHERE name = '2013-14-budget.pdf'"
                    },
                    "tag_names": ["test:budget"]
                }
            }
        ]
        
        for test_case in test_cases:
            await self.test_tool("apply_file_tags", test_case["name"], test_case["args"])
        
        # Clean up test tags
        await self.test_tool("manage_tag_definitions", "Clean up test tags", {
            "action": "delete",
            "tag_names": ["test:document", "test:budget", "test:handbook"]
        })
    
    async def test_search_files_by_tags(self):
        """Test the search_files_by_tags tool."""
        self.logger.info("\n=== Testing search_files_by_tags tool ===")
        
        # First create some test tags and apply them
        await self.test_tool("manage_tag_definitions", "Create test tags for search", {
            "action": "create",
            "tag_names": ["search:test1", "search:test2"]
        })
        
        await self.test_tool("apply_file_tags", "Apply test tags for search", {
            "action": "apply",
            "file_selection": {
                "method": "search_query",
                "search_query": "SELECT name,objectId,instanceId FROM STORE('/') WHERE name = '2013-14-budget.pdf'"
            },
            "tag_names": ["search:test1", "search:test2"]
        })
        
        test_cases = [
            {
                "name": "Search files with single tag",
                "args": {
                    "tag_filters": {
                        "include_tags": ["search:test1"],
                        "match_type": "any"
                    }
                }
            },
            {
                "name": "Search files with multiple tags (any match)",
                "args": {
                    "tag_filters": {
                        "include_tags": ["search:test1", "search:test2"],
                        "match_type": "any"
                    }
                }
            },
            {
                "name": "Search files with multiple tags (all match)",
                "args": {
                    "tag_filters": {
                        "include_tags": ["search:test1", "search:test2"],
                        "match_type": "all"
                    }
                }
            },
            {
                "name": "Search with non-existent tag",
                "args": {
                    "tag_filters": {
                        "include_tags": ["nonexistent:tag"],
                        "match_type": "any"
                    }
                }
            }
        ]
        
        for test_case in test_cases:
            await self.test_tool("search_files_by_tags", test_case["name"], test_case["args"])
        
        # Clean up test tags
        await self.test_tool("apply_file_tags", "Remove test tags for cleanup", {
            "action": "remove",
            "file_selection": {
                "method": "search_query",
                "search_query": "SELECT name,objectId,instanceId FROM STORE('/') WHERE name = '2013-14-budget.pdf'"
            },
            "tag_names": ["search:test1", "search:test2"]
        })
        
        await self.test_tool("manage_tag_definitions", "Delete test tags for cleanup", {
            "action": "delete",
            "tag_names": ["search:test1", "search:test2"]
        })
    
    async def run_all_tests(self):
        """Run all tool tests."""
        self.logger.info("Starting comprehensive MCP tool testing...")
        
        # Initialize server
        if not await self.initialize_server():
            self.logger.error("Failed to initialize server. Aborting tests.")
            return False
        
        # Run all tool tests
        try:
            await self.test_guide_start_here()
            await self.test_health_check()
            await self.test_server_info()
            await self.test_run_aparavi_report()
            await self.test_validate_aql_query()
            await self.test_execute_custom_aql_query()
            await self.test_generate_aql_query()
            await self.test_manage_tag_definitions()
            await self.test_apply_file_tags()
            await self.test_search_files_by_tags()
            
        except Exception as e:
            self.logger.error(f"Error during testing: {e}")
            return False
        
        return True
    
    def print_test_summary(self):
        """Print a summary of all test results."""
        self.logger.info("\n" + "="*60)
        self.logger.info("TEST SUMMARY")
        self.logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        self.logger.info(f"Total Tests: {total_tests}")
        self.logger.info(f"Passed: {passed_tests}")
        self.logger.info(f"Failed: {failed_tests}")
        self.logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Group results by tool
        tools_summary = {}
        for result in self.test_results:
            tool = result["tool"]
            if tool not in tools_summary:
                tools_summary[tool] = {"passed": 0, "failed": 0, "total": 0}
            
            tools_summary[tool]["total"] += 1
            if result["success"]:
                tools_summary[tool]["passed"] += 1
            else:
                tools_summary[tool]["failed"] += 1
        
        self.logger.info("\nResults by Tool:")
        for tool, stats in tools_summary.items():
            success_rate = (stats["passed"] / stats["total"]) * 100
            self.logger.info(f"  {tool}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Show failed tests
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            self.logger.info("\nFailed Tests:")
            for result in failed_results:
                self.logger.info(f"  FAILED: {result['tool']}: {result['test_case']}")
                if result["error"]:
                    self.logger.info(f"     Error: {result['error']}")
        
        # Save detailed results to JSON file
        results_file = Path(__file__).parent / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        self.logger.info(f"\nDetailed results saved to: {results_file}")


async def main():
    """Main entry point for the test script."""
    print("Aparavi Data Suite MCP Server - Tool Testing Script")
    print("="*60)
    
    # Check if .env file exists (primary configuration)
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print(f"WARNING: .env file not found at {env_path}")
        print("Please ensure the server is properly configured before running tests.")
        print("Copy .env.example to .env and configure your Aparavi connection settings.")
        return
    
    # Initialize and run tests (config_path is optional for YAML overrides)
    tester = MCPToolTester(config_path=None)
    
    try:
        success = await tester.run_all_tests()
        tester.print_test_summary()
        
        if success:
            print("\nTesting completed successfully!")
        else:
            print("\nSome tests encountered issues. Check the logs above.")
            
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
