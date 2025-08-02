"""
Main MCP server implementation for Aparavi Data Suite.
This simplified version avoids the TaskGroup issues present in the standard MCP SDK.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config, load_config, validate_config
from .utils import setup_logging, format_error_message
from .aparavi_client import AparaviClient


def load_reports_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load Aparavi Data Suite reports configuration from JSON file."""
    if config_path is None:
        # Default to config/aparavi_reports.json relative to this file
        current_dir = Path(__file__).parent
        config_path = current_dir.parent.parent / "config" / "aparavi_reports.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Reports configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in reports configuration file: {e}")


class AparaviMCPServer:
    """Aparavi Data Suite MCP Server for querying data management systems."""
    
    def __init__(self, config_path: Optional[str] = None, reports_config_path: Optional[str] = None):
        """
        Initialize the Aparavi Data Suite MCP server.
        
        Args:
            config_path: Optional path to configuration file
            reports_config_path: Optional path to reports configuration JSON file
        """
        # Load and validate configuration
        self.config = load_config(config_path)
        validate_config(self.config)
        
        # Set up logging
        self.logger = setup_logging(self.config.server.log_level)
        self.logger.info(f"Initializing Aparavi Data Suite MCP Server v{self.config.server.version}")
        
        # Load reports configuration
        try:
            reports_config = load_reports_config(reports_config_path)
            self.aparavi_reports = reports_config.get("reports", {})
            self.analysis_workflows = reports_config.get("workflows", {})
            self.logger.info(f"Loaded {len(self.aparavi_reports)} reports and {len(self.analysis_workflows)} workflows")
        except Exception as e:
            self.logger.error(f"Failed to load reports configuration: {e}")
            raise
        
        # Initialize Aparavi Data Suite client
        self.aparavi_client = AparaviClient(self.config.aparavi, self.logger)
        
        self.logger.info("Aparavi Data Suite MCP Server initialized successfully")
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        self.logger.info("Handling initialize request")
        
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": self.config.server.name,
                "version": self.config.server.version
            }
        }
    
    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        self.logger.debug("Listing available tools")
        
        tools = [
            {
                "name": "health_check",
                "description": "Check the health and connectivity of the Aparavi Data Suite MCP server and API connection, including validation of all configured AQL queries",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "server_info", 
                "description": "Get detailed information about the Aparavi Data Suite MCP server configuration and capabilities",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "run_aparavi_report",
                "description": "Execute Aparavi Data Suite AQL reports or analysis workflows. Use 'list' to discover available reports and workflows.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "report_name": {
                            "type": "string",
                            "description": "Name of the specific report to run, or 'list' to see all available reports"
                        },
                        "workflow_name": {
                            "type": "string", 
                            "description": "Name of the analysis workflow to run, or 'list' to see all available workflows"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "validate_aql_query",
                "description": "Validate a custom AQL query against the Aparavi Data Suite API without executing it. Returns validation status and any syntax errors.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The AQL query to validate"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "execute_custom_aql_query",
                "description": "Validate and execute a custom AQL query. First validates the query syntax, then executes it if valid. Returns raw JSON results for LLM interpretation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The AQL query to validate and execute"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
        
        return {
            "tools": tools
        }
    
    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        self.logger.info(f"Handling call_tool request for: {tool_name}")
        
        try:
            if tool_name == "health_check":
                return await self._handle_health_check()
            elif tool_name == "server_info":
                return await self._handle_server_info()
            elif tool_name == "run_aparavi_report":
                return await self._handle_run_aparavi_report(arguments)
            elif tool_name == "validate_aql_query":
                return await self._handle_validate_aql_query(arguments)
            elif tool_name == "execute_custom_aql_query":
                return await self._handle_execute_custom_aql_query(arguments)
            else:
                error_msg = f"Unknown tool: {tool_name}"
                self.logger.error(error_msg)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: {error_msg}"
                        }
                    ],
                    "isError": True
                }
                
        except Exception as e:
            error_msg = format_error_message(e, f"Tool execution failed for {tool_name}")
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
    
    async def _handle_health_check(self) -> Dict[str, Any]:
        """Handle comprehensive health check requests including API connectivity and AQL validation."""
        self.logger.debug("Performing comprehensive health check")
        
        health_report = []
        overall_status = "SUCCESS"
        
        try:
            # Step 1: Test Aparavi Data Suite API connectivity
            health_report.append("# Aparavi Data Suite MCP Server Health Check\n")
            health_report.append("## 1. API Connectivity Test\n")
            
            health_result = await self.aparavi_client.health_check()
            
            if isinstance(health_result, dict) and health_result.get("status") == "OK":
                health_report.append("[PASS] **API Connection**: PASSED - Successfully connected to Aparavi Data Suite API\n")
                self.logger.info("API connectivity check passed")
            else:
                health_report.append("[FAIL] **API Connection**: FAILED - Could not connect to Aparavi Data Suite API\n")
                overall_status = "WARNING"
                self.logger.warning("API connectivity check failed")
            
            # Step 2: Validate AQL queries in configuration
            health_report.append("\n## 2. AQL Query Validation\n")
            
            validation_results = await self._validate_all_aql_queries()
            total_queries = len(self.aparavi_reports)
            passed_queries = sum(1 for result in validation_results.values() if result["valid"])
            failed_queries = total_queries - passed_queries
            
            if failed_queries == 0:
                health_report.append(f"[PASS] **AQL Validation**: PASSED - All {total_queries} queries are syntactically valid\n")
                self.logger.info(f"AQL validation passed: {total_queries}/{total_queries} queries valid")
            else:
                health_report.append(f"[FAIL] **AQL Validation**: FAILED - {failed_queries}/{total_queries} queries have syntax errors\n")
                overall_status = "FAILED"
                self.logger.warning(f"AQL validation failed: {failed_queries} queries have errors")
                
                # List failed queries
                health_report.append("\n**Failed Queries:**\n")
                for report_name, result in validation_results.items():
                    if not result["valid"]:
                        health_report.append(f"- `{report_name}`: {result['error']}\n")
            
            # Step 3: Configuration validation
            health_report.append("\n## 3. Configuration Validation\n")
            
            config_issues = []
            
            # Check reports configuration
            if not self.aparavi_reports:
                config_issues.append("No reports loaded from configuration")
            
            # Check workflows configuration
            if not self.analysis_workflows:
                config_issues.append("No workflows loaded from configuration")
            
            # Validate workflow references
            for workflow_name, workflow_config in self.analysis_workflows.items():
                workflow_reports = workflow_config.get("reports", [])
                for report_name in workflow_reports:
                    if report_name not in self.aparavi_reports:
                        config_issues.append(f"Workflow '{workflow_name}' references unknown report '{report_name}'")
            
            if not config_issues:
                health_report.append(f"[PASS] **Configuration**: PASSED - {len(self.aparavi_reports)} reports and {len(self.analysis_workflows)} workflows loaded\n")
                self.logger.info("Configuration validation passed")
            else:
                health_report.append("[FAIL] **Configuration**: FAILED - Configuration issues detected\n")
                overall_status = "FAILED"
                for issue in config_issues:
                    health_report.append(f"- {issue}\n")
                self.logger.warning(f"Configuration validation failed: {len(config_issues)} issues")
            
            # Summary
            health_report.append("\n## Summary\n")
            if overall_status == "SUCCESS":
                health_report.append("[SUCCESS] **Overall Status**: HEALTHY - All systems operational\n")
                self.logger.info("Comprehensive health check passed")
            elif overall_status == "WARNING":
                health_report.append("[WARNING] **Overall Status**: WARNING - Some issues detected but server functional\n")
                self.logger.warning("Comprehensive health check completed with warnings")
            else:
                health_report.append("[ERROR] **Overall Status**: UNHEALTHY - Critical issues detected\n")
                self.logger.error("Comprehensive health check failed")
            
            return {
                "content": [{"type": "text", "text": "".join(health_report)}],
                "isError": overall_status == "FAILED"
            }
            
        except Exception as e:
            error_msg = f"ERROR: Comprehensive health check failed: {format_error_message(e)}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
    
    async def _validate_all_aql_queries(self) -> Dict[str, Dict[str, any]]:
        """Validate all AQL queries in the reports configuration."""
        self.logger.debug(f"Validating {len(self.aparavi_reports)} AQL queries")
        
        validation_results = {}
        
        for report_name, report_config in self.aparavi_reports.items():
            aql_query = report_config.get("query", "")
            
            if not aql_query:
                validation_results[report_name] = {
                    "valid": False,
                    "error": "No query found in configuration"
                }
                continue
            
            try:
                # Validate the query using Aparavi Data Suite API
                result = await self.aparavi_client.execute_query(
                    aql_query, 
                    format_type="json", 
                    validate_only=True
                )
                
                if isinstance(result, dict) and result.get("status") == "OK":
                    validation_results[report_name] = {
                        "valid": True,
                        "error": ""
                    }
                else:
                    error_msg = result.get("message", "Unknown validation error") if isinstance(result, dict) else str(result)
                    validation_results[report_name] = {
                        "valid": False,
                        "error": error_msg
                    }
                    
            except Exception as e:
                validation_results[report_name] = {
                    "valid": False,
                    "error": f"Exception during validation: {str(e)}"
                }
        
        return validation_results
    
    async def _handle_server_info(self) -> Dict[str, Any]:
        """Handle server info requests."""
        self.logger.debug("Getting server information")
        
        try:
            info = {
                "server_name": self.config.server.name,
                "server_version": self.config.server.version,
                "aparavi_host": self.config.aparavi.host,
                "aparavi_port": self.config.aparavi.port,
                "aparavi_api_version": self.config.aparavi.api_version,
                "cache_enabled": self.config.server.cache_enabled,
                "log_level": self.config.server.log_level
            }
            
            info_text = "Aparavi Data Suite MCP Server Information:\n\n"
            for key, value in info.items():
                info_text += f"• {key.replace('_', ' ').title()}: {value}\n"
            
            return {
                "content": [{"type": "text", "text": info_text}]
            }
            
        except Exception as e:
            error_msg = f"Failed to get server info: {format_error_message(e)}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
    
    async def _handle_run_aparavi_report(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle run_aparavi_report tool requests."""
        self.logger.debug("Handling run_aparavi_report request")
        
        try:
            report_name = arguments.get("report_name")
            workflow_name = arguments.get("workflow_name")
            
            # Handle list requests
            if report_name == "list":
                return self._list_available_reports()
            elif workflow_name == "list":
                return self._list_available_workflows()
            
            # Execute single report
            if report_name:
                return await self._execute_single_report(report_name)
            
            # Execute workflow
            if workflow_name:
                return await self._execute_analysis_workflow(workflow_name)
            
            # No valid parameters provided
            return {
                "content": [{
                    "type": "text", 
                    "text": "Please specify either 'report_name' or 'workflow_name'. Use 'list' to see available options."
                }],
                "isError": True
            }
            
        except Exception as e:
            error_msg = f"Error in run_aparavi_report: {format_error_message(e)}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }

    def _list_available_reports(self) -> Dict[str, Any]:
        """List all available Aparavi Data Suite reports."""
        report_list = "# Available Aparavi Data Suite Reports\n\n"
        
        for report_name, report_config in self.aparavi_reports.items():
            description = report_config.get("description", "No description available")
            keywords = ", ".join(report_config.get("keywords", []))
            report_list += f"**{report_name}**\n"
            report_list += f"- Description: {description}\n"
            report_list += f"- Keywords: {keywords}\n\n"
        
        return {
            "content": [{"type": "text", "text": report_list}]
        }
    
    def _list_available_workflows(self) -> Dict[str, Any]:
        """List all available analysis workflows."""
        workflow_list = "# Available Analysis Workflows\n\n"
        
        for workflow_name, workflow_config in self.analysis_workflows.items():
            description = workflow_config.get("description", "No description available")
            reports = ", ".join(workflow_config.get("reports", []))
            workflow_list += f"**{workflow_name}**\n"
            workflow_list += f"- Description: {description}\n"
            workflow_list += f"- Reports: {reports}\n\n"
        
        return {
            "content": [{"type": "text", "text": workflow_list}]
        }
    
    async def _execute_single_report(self, report_name: str) -> Dict[str, Any]:
        """Execute a single Aparavi Data Suite report."""
        self.logger.info(f"Executing single report: {report_name}")
        
        # Check if report exists
        if report_name not in self.aparavi_reports:
            available_reports = ", ".join(self.aparavi_reports.keys())
            error_msg = f"Report '{report_name}' not found. Available reports: {available_reports}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
        
        try:
            report_config = self.aparavi_reports[report_name]
            aql_query = report_config["query"]
            description = report_config.get("description", "")
            
            self.logger.info(f"Executing AQL query for {report_name}")
            
            # Execute the AQL query
            result = await self.aparavi_client.execute_query(aql_query, format_type="json")
            
            if isinstance(result, dict) and result.get("status") == "OK":
                # Return raw JSON response for the agent to interpret
                import json
                json_response = json.dumps(result, indent=2)
                self.logger.info(f"Report {report_name} executed successfully")
                
                return {
                    "content": [{
                        "type": "text", 
                        "text": f"# Aparavi Data Suite Report: {report_name}\n\n{description}\n\nRaw JSON Response:\n```json\n{json_response}\n```"
                    }]
                }
            else:
                # Handle error response
                error_msg = f"Failed to execute report '{report_name}'"
                if isinstance(result, str):
                    error_msg += f": {result}"
                elif isinstance(result, dict):
                    error_msg += f": {result.get('message', 'Unknown error')}"
                
                self.logger.error(error_msg)
                return {
                    "content": [{"type": "text", "text": error_msg}],
                    "isError": True
                }
                
        except Exception as e:
            error_msg = f"Error executing report '{report_name}': {format_error_message(e)}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
    
    async def _execute_analysis_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Execute an analysis workflow (multiple related reports)."""
        self.logger.info(f"Executing analysis workflow: {workflow_name}")
        
        # Check if workflow exists
        if workflow_name not in self.analysis_workflows:
            available_workflows = ", ".join(self.analysis_workflows.keys())
            error_msg = f"Workflow '{workflow_name}' not found. Available workflows: {available_workflows}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
        
        try:
            workflow_config = self.analysis_workflows[workflow_name]
            workflow_description = workflow_config.get("description", "")
            report_names = workflow_config.get("reports", [])
            
            if not report_names:
                error_msg = f"Workflow '{workflow_name}' has no reports defined"
                self.logger.error(error_msg)
                return {
                    "content": [{"type": "text", "text": error_msg}],
                    "isError": True
                }
            
            # Execute all reports in the workflow
            workflow_results = []
            workflow_results.append(f"# Aparavi Data Suite Analysis Workflow: {workflow_name}\n")
            workflow_results.append(f"{workflow_description}\n")
            workflow_results.append(f"Executing {len(report_names)} reports...\n\n")
            
            for i, report_name in enumerate(report_names, 1):
                self.logger.info(f"Executing workflow report {i}/{len(report_names)}: {report_name}")
                
                # Check if report exists
                if report_name not in self.aparavi_reports:
                    workflow_results.append(f"## Report {i}: {report_name} (SKIPPED - Not Found)\n\n")
                    continue
                
                try:
                    report_config = self.aparavi_reports[report_name]
                    aql_query = report_config["query"]
                    report_description = report_config.get("description", "")
                    
                    # Execute the AQL query
                    result = await self.aparavi_client.execute_query(aql_query, format_type="json")
                    
                    if isinstance(result, dict) and result.get("status") == "OK":
                        import json
                        json_response = json.dumps(result, indent=2)
                        workflow_results.append(f"## Report {i}: {report_name}\n")
                        workflow_results.append(f"{report_description}\n\n")
                        workflow_results.append(f"```json\n{json_response}\n```\n\n")
                    else:
                        error_info = result.get('message', 'Unknown error') if isinstance(result, dict) else str(result)
                        workflow_results.append(f"## Report {i}: {report_name} (ERROR)\n")
                        workflow_results.append(f"Error: {error_info}\n\n")
                        
                except Exception as e:
                    workflow_results.append(f"## Report {i}: {report_name} (ERROR)\n")
                    workflow_results.append(f"Error: {format_error_message(e)}\n\n")
            
            self.logger.info(f"Workflow {workflow_name} completed")
            
            return {
                "content": [{"type": "text", "text": "".join(workflow_results)}]
            }
            
        except Exception as e:
            error_msg = f"Error executing workflow '{workflow_name}': {format_error_message(e)}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
    
    async def _handle_validate_aql_query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validate_aql_query tool request."""
        query = arguments.get("query")
        
        if not query:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: 'query' parameter is required"
                    }
                ],
                "isError": True
            }
        
        if not isinstance(query, str) or not query.strip():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: 'query' must be a non-empty string"
                    }
                ],
                "isError": True
            }
        
        try:
            self.logger.info(f"Validating AQL query: {query[:100]}...")
            
            # Use the Aparavi Data Suite client to validate the query
            result = await self.aparavi_client.execute_query(
                query=query.strip(),
                format_type="json",
                use_cache=False,  # Don't cache validation requests
                validate_only=True
            )
            
            # Check if validation was successful
            if isinstance(result, dict):
                if result.get("status") == "OK" and result.get("data", {}).get("valid") == True:
                    validation_result = {
                        "valid": True,
                        "message": "AQL query syntax is valid",
                        "query": query.strip()
                    }
                    self.logger.info("AQL query validation successful")
                elif result.get("status") == "error":
                    # Extract error information from the response
                    error_msg = result.get("message", "Unknown validation error")
                    validation_result = {
                        "valid": False,
                        "message": f"AQL query validation failed: {error_msg}",
                        "query": query.strip(),
                        "error_details": result
                    }
                    self.logger.warning(f"AQL query validation failed: {error_msg}")
                else:
                    # Handle unexpected status
                    status = result.get("status", "unknown")
                    validation_result = {
                        "valid": False,
                        "message": f"Unexpected validation response status: {status}",
                        "query": query.strip(),
                        "error_details": result
                    }
                    self.logger.warning(f"Unexpected validation response: {result}")
            else:
                # Handle unexpected response format
                validation_result = {
                    "valid": False,
                    "message": "Unexpected response format from validation",
                    "query": query.strip(),
                    "raw_response": str(result)
                }
                self.logger.warning("Unexpected validation response format")
            
            # Format the response as markdown
            if validation_result["valid"]:
                response_text = f"""# AQL Query Validation Result

**Status:** VALID

**Query:**
```sql
{validation_result['query']}
```

**Result:** The AQL query syntax is valid and can be executed against the Aparavi Data Suite API.
"""
            else:
                response_text = f"""# AQL Query Validation Result

**Status:** INVALID

**Query:**
```sql
{validation_result['query']}
```

**Error:** {validation_result['message']}

**Recommendation:** Please check the AQL syntax and ensure all field names, functions, and clauses are correct according to Aparavi Data Suite AQL documentation.
"""
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": response_text
                    }
                ]
            }
            
        except Exception as e:
            error_msg = f"Failed to validate AQL query: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"""# AQL Query Validation Result

**Status:** ERROR

**Query:**
```sql
{query.strip()}
```

**Error:** {error_msg}

**Note:** This may indicate a connection issue with the Aparavi Data Suite API or an internal server error.
"""
                    }
                ],
                "isError": True
            }
    
    async def _handle_execute_custom_aql_query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execute_custom_aql_query tool request - validate then execute if valid."""
        query = arguments.get("query")
        
        if not query:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: 'query' parameter is required"
                    }
                ],
                "isError": True
            }
        
        if not isinstance(query, str) or not query.strip():
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Error: 'query' must be a non-empty string"
                    }
                ],
                "isError": True
            }
        
        try:
            self.logger.info(f"Validating and executing AQL query: {query[:100]}...")
            
            # Step 1: Validate the query first
            validation_result = await self.aparavi_client.execute_query(
                query=query.strip(),
                format_type="json",
                use_cache=False,
                validate_only=True
            )
            
            # Check validation result
            if isinstance(validation_result, dict):
                if validation_result.get("status") == "OK" and validation_result.get("data", {}).get("valid") == True:
                    self.logger.info("AQL query validation successful, proceeding with execution")
                    
                    # Step 2: Execute the validated query
                    execution_result = await self.aparavi_client.execute_query(
                        query=query.strip(),
                        format_type="json",
                        use_cache=False,
                        validate_only=False
                    )
                    
                    # Return raw JSON results for LLM interpretation
                    if isinstance(execution_result, dict) and execution_result.get("status") == "OK":
                        response_text = f"""# AQL Query Execution Result

**Status:** SUCCESS

**Query:**
```sql
{query.strip()}
```

**Raw JSON Results:**
```json
{json.dumps(execution_result, indent=2)}
```

**Note:** The above JSON contains the raw query results for LLM interpretation and analysis."""
                        
                        self.logger.info("AQL query executed successfully")
                        return {
                            "content": [{
                                "type": "text",
                                "text": response_text
                            }]
                        }
                    else:
                        # Execution failed
                        error_msg = execution_result.get("message", "Unknown execution error") if isinstance(execution_result, dict) else str(execution_result)
                        response_text = f"""# AQL Query Execution Result

**Status:** EXECUTION_FAILED

**Query:**
```sql
{query.strip()}
```

**Error:** {error_msg}

**Raw Error Response:**
```json
{json.dumps(execution_result, indent=2) if isinstance(execution_result, dict) else str(execution_result)}
```

**Note:** The query syntax is valid but execution failed. Check the error details above."""
                        
                        self.logger.warning(f"AQL query execution failed: {error_msg}")
                        return {
                            "content": [{
                                "type": "text",
                                "text": response_text
                            }],
                            "isError": True
                        }
                        
                elif validation_result.get("status") == "error":
                    # Validation failed - return validation error
                    error_msg = validation_result.get("message", "Unknown validation error")
                    response_text = f"""# AQL Query Execution Result

**Status:** VALIDATION_FAILED

**Query:**
```sql
{query.strip()}
```

**Validation Error:** {error_msg}

**Raw Validation Response:**
```json
{json.dumps(validation_result, indent=2)}
```

**Recommendation:** Please fix the AQL syntax errors before attempting execution."""
                    
                    self.logger.warning(f"AQL query validation failed: {error_msg}")
                    return {
                        "content": [{
                            "type": "text",
                            "text": response_text
                        }],
                        "isError": True
                    }
                else:
                    # Unexpected validation response
                    status = validation_result.get("status", "unknown")
                    response_text = f"""# AQL Query Execution Result

**Status:** VALIDATION_ERROR

**Query:**
```sql
{query.strip()}
```

**Error:** Unexpected validation response status: {status}

**Raw Response:**
```json
{json.dumps(validation_result, indent=2)}
```

**Note:** This may indicate an issue with the Aparavi Data Suite API or server configuration."""
                    
                    self.logger.warning(f"Unexpected validation response: {validation_result}")
                    return {
                        "content": [{
                            "type": "text",
                            "text": response_text
                        }],
                        "isError": True
                    }
            else:
                # Unexpected validation response format
                response_text = f"""# AQL Query Execution Result

**Status:** VALIDATION_ERROR

**Query:**
```sql
{query.strip()}
```

**Error:** Unexpected response format from validation

**Raw Response:** {str(validation_result)}

**Note:** This may indicate a connection issue with the Aparavi Data Suite API."""
                
                self.logger.warning("Unexpected validation response format")
                return {
                    "content": [{
                        "type": "text",
                        "text": response_text
                    }],
                    "isError": True
                }
                
        except Exception as e:
            error_msg = f"Failed to validate and execute AQL query: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            response_text = f"""# AQL Query Execution Result

**Status:** ERROR

**Query:**
```sql
{query.strip()}
```

**Error:** {error_msg}

**Note:** This may indicate a connection issue with the Aparavi Data Suite API or an internal server error."""
            
            return {
                "content": [{
                    "type": "text",
                    "text": response_text
                }],
                "isError": True
            }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        self.logger.debug(f"Handling request: {method}")
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_list_tools(params)
            elif method == "tools/call":
                result = await self.handle_call_tool(params)
            elif method == "notifications/initialized":
                # Handle initialization notification (no response needed)
                self.logger.debug("Received initialization notification")
                return None  # No response for notifications
            elif method == "resources/list":
                # We don't provide resources, return empty list
                result = {"resources": []}
            elif method == "prompts/list":
                # We don't provide prompts, return empty list
                result = {"prompts": []}
            else:
                raise ValueError(f"Unknown method: {method}")
            
            # Don't send response for notifications
            if method.startswith("notifications/"):
                return None
                
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            error_msg = format_error_message(e, f"Request handling failed for {method}")
            self.logger.error(error_msg)
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": error_msg
                }
            }
        
        return response
    
    async def run(self) -> None:
        """Run the MCP server."""
        self.logger.info("Starting Aparavi Data Suite MCP Server")
        
        try:
            # Initialize Aparavi Data Suite client connection
            await self.aparavi_client.initialize()
            
            # Read from stdin and write to stdout
            while True:
                try:
                    # Read JSON-RPC request from stdin
                    line = await asyncio.to_thread(sys.stdin.readline)
                    if not line:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse JSON request
                    request = json.loads(line)
                    
                    # Handle request
                    response = await self.handle_request(request)
                    
                    # Send JSON response to stdout
                    if response is not None:
                        response_json = json.dumps(response)
                        try:
                            print(response_json, flush=True)
                        except (OSError, IOError, UnicodeEncodeError) as e:
                            # Handle case where stdout is closed (e.g., when Claude Desktop disconnects)
                            self.logger.debug(f"Stdout write failed (connection closed): {e}")
                            break
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON received: {e}")
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing request: {e}")
                    continue
                    
        except KeyboardInterrupt:
            self.logger.info("Server shutdown requested")
        except Exception as e:
            self.logger.error(f"Server error: {format_error_message(e)}")
            raise
        finally:
            # Ensure proper cleanup
            try:
                await self.aparavi_client.close()
            except Exception as e:
                self.logger.warning(f"Error during cleanup: {e}")
            self.logger.info("Aparavi Data Suite MCP Server stopped")


async def async_main() -> None:
    """Async main entry point for the Aparavi Data Suite MCP server."""
    try:
        server = AparaviMCPServer()
        await server.run()
    except Exception as e:
        logging.error(f"Failed to start server: {e}")
        raise


def main() -> None:
    """Main entry point for the Aparavi Data Suite MCP server."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Server failed to start: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
