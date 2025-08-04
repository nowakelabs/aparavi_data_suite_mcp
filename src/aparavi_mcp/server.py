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
        
        # Log the initialization parameters for debugging
        self.logger.debug(f"Initialize params: {params}")
        
        return {
            "protocolVersion": "2025-06-18",
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
                "name": "guide_start_here",
                "description": "**START HERE**: Intelligent entry point and routing assistant for the Aparavi Data Suite MCP Server. Assesses your experience level, goals, and preferences to provide personalized guidance on which tools to use and in what sequence. **PERFECT FOR**: New users, complex analysis planning, tool selection guidance, workflow optimization, and when you're unsure which of the 6 available tools best fits your needs. **SAVES TIME**: Prevents trial-and-error by recommending the optimal path forward based on your specific situation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_experience": {
                            "type": "string",
                            "enum": ["new", "intermediate", "advanced", "unknown"],
                            "description": "Your experience level with AQL/Aparavi Data Suite (leave empty if unsure)"
                        },
                        "query_goal": {
                            "type": "string",
                            "enum": ["duplicates", "growth", "security", "exploration", "custom", "troubleshooting", "unknown"],
                            "description": "Your primary analysis goal (leave empty if unsure)"
                        },
                        "preferred_approach": {
                            "type": "string",
                            "enum": ["reports", "custom_queries", "guided", "unknown"],
                            "description": "Your preferred working style (leave empty if unsure)"
                        },
                        "context_window": {
                            "type": "string",
                            "enum": ["small", "medium", "large", "unknown"],
                            "description": "Your context/attention preference - small=focused steps, large=comprehensive guidance (leave empty if unsure)"
                        },
                        "specific_question": {
                            "type": "string",
                            "description": "Optional: Describe your specific data analysis question or challenge"
                        }
                    },
                    "required": []
                }
            },
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
                "description": "Validate and execute a custom AQL query against the Aparavi Data Suite API. First validates syntax, then executes if valid, returning raw JSON results.",
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
            },
            {
                "name": "generate_aql_query",
                "description": "**USE THIS TOOL WHEN**: User asks for custom data analysis NOT covered by the 20 predefined reports. Intelligent AQL query builder that generates valid, syntactically correct AQL queries from natural language business questions. Prevents common syntax errors (DISTINCT, DATEADD, invalid fields) that cause execute_custom_aql_query to fail. **WHEN TO USE**: Custom analysis requests, specific field combinations, unique filter requirements, or when predefined reports don't match the user's exact needs. **WORKFLOW**: Use this first to generate proper syntax, then validate_aql_query, then execute_custom_aql_query.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "business_question": {
                            "type": "string",
                            "description": "The specific business question or data analysis need (e.g., 'Find large PDF files created in the last 30 days by department')"
                        },
                        "desired_fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional: Specific fields/columns desired in the output (will be validated against available Aparavi fields)"
                        },
                        "filters": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional: Specific filter conditions (e.g., 'file size > 100MB', 'created last 30 days', 'PDF files only')"
                        },
                        "complexity_preference": {
                            "type": "string",
                            "enum": ["simple", "comprehensive"],
                            "description": "Whether to generate a simple focused query or a more comprehensive analysis",
                            "default": "simple"
                        }
                    },
                    "required": ["business_question"]
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
            if tool_name == "guide_start_here":
                return await self._handle_guide_start_here(arguments)
            elif tool_name == "health_check":
                return await self._handle_health_check()
            elif tool_name == "server_info":
                return await self._handle_server_info()
            elif tool_name == "run_aparavi_report":
                return await self._handle_run_aparavi_report(arguments)
            elif tool_name == "validate_aql_query":
                return await self._handle_validate_aql_query(arguments)
            elif tool_name == "execute_custom_aql_query":
                return await self._handle_execute_custom_aql_query(arguments)
            elif tool_name == "generate_aql_query":
                return await self._handle_generate_aql_query(arguments)
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
    
    def _format_focused_response(self, assessment: Dict[str, str], guidance: Dict[str, Any]) -> str:
        """Format a focused, concise response for users who prefer small context windows."""
        
        experience = assessment["detected_experience"]
        goal = assessment["detected_goal"]
        
        response = f"# Quick Start Guide\n\n"
        response += f"**Detected:** {experience.title()} user seeking {goal} analysis\n\n"
        
        if guidance["next_steps"]:
            response += f"## Next Step\n\n"
            first_step = guidance["next_steps"][0]
            response += f"**Tool:** `{first_step['tool']}`\n"
            response += f"**Parameters:** {first_step['parameters']}\n"
            response += f"**Purpose:** {first_step['purpose']}\n\n"
        
        response += f"## Key Tip\n"
        if guidance["helpful_context"]["success_tips"]:
            response += f"{guidance['helpful_context']['success_tips'][0]}\n\n"
        
        response += f"*Need more guidance? Call guide_start_here again with context_window='large'*"
        
        return response
    
    def _format_comprehensive_response(self, assessment: Dict[str, str], guidance: Dict[str, Any]) -> str:
        """Format a comprehensive response for users who prefer detailed guidance."""
        
        experience = assessment["detected_experience"]
        goal = assessment["detected_goal"]
        approach = assessment["recommended_approach"]
        
        response = f"# Comprehensive Aparavi Data Suite Guide\n\n"
        
        # Assessment Summary
        response += f"## Your Profile Assessment\n\n"
        response += f"- **Experience Level:** {experience.title()}\n"
        response += f"- **Analysis Goal:** {goal.title()}\n"
        response += f"- **Recommended Approach:** {approach.replace('_', ' ').title()}\n\n"
        
        # Detailed Next Steps
        if guidance["next_steps"]:
            response += f"## Recommended Workflow\n\n"
            for i, step in enumerate(guidance["next_steps"], 1):
                response += f"### Step {step['step']}: {step['tool']}\n\n"
                response += f"**Parameters:** `{step['parameters']}`\n\n"
                response += f"**Purpose:** {step['purpose']}\n\n"
                response += f"**Expected Outcome:** {step['expected_outcome']}\n\n"
        
        # Alternative Paths
        if guidance["alternative_paths"]:
            response += f"## Alternative Approaches\n\n"
            for alt in guidance["alternative_paths"]:
                response += f"**If:** {alt['if']}\n"
                response += f"**Then:** {alt['then']}\n"
                response += f"**Tools:** {', '.join(alt['tools'])}\n\n"
        
        # Recommended Resources
        if guidance["recommended_reports"]:
            response += f"## Relevant Reports\n\n"
            for report in guidance["recommended_reports"][:3]:  # Show top 3
                response += f"- `{report}`\n"
            response += f"\n"
        
        if guidance["recommended_workflows"]:
            response += f"## Relevant Workflows\n\n"
            for workflow in guidance["recommended_workflows"]:
                response += f"- `{workflow}`\n"
            response += f"\n"
        
        # Comprehensive Context
        response += f"## Important Limitations\n\n"
        for limitation in guidance["helpful_context"]["key_limitations"]:
            response += f"- {limitation}\n"
        response += f"\n"
        
        response += f"## Common Pitfalls to Avoid\n\n"
        for pitfall in guidance["helpful_context"]["common_pitfalls"]:
            response += f"- {pitfall}\n"
        response += f"\n"
        
        response += f"## Success Tips\n\n"
        for tip in guidance["helpful_context"]["success_tips"]:
            response += f"- {tip}\n"
        response += f"\n"
        
        response += f"## All Available Tools\n\n"
        response += f"1. **guide_start_here** - This intelligent routing assistant\n"
        response += f"2. **health_check** - System health and connectivity verification\n"
        response += f"3. **server_info** - Configuration and capabilities overview\n"
        response += f"4. **run_aparavi_report** - 20 predefined reports + 5 workflows\n"
        response += f"5. **validate_aql_query** - Syntax validation without execution\n"
        response += f"6. **execute_custom_aql_query** - Validate and execute custom queries\n"
        response += f"7. **generate_aql_query** - Intelligent AQL query builder\n\n"
        
        response += f"*Ready to proceed? Execute the recommended Step 1 above to get started!*"
        
        return response
    
    def _format_balanced_response(self, assessment: Dict[str, str], guidance: Dict[str, Any]) -> str:
        """Format a balanced response with essential information without overwhelming detail."""
        
        experience = assessment["detected_experience"]
        goal = assessment["detected_goal"]
        approach = assessment["recommended_approach"]
        
        response = f"# Aparavi Data Suite - Your Personalized Guide\n\n"
        
        # Quick Assessment
        response += f"**Profile:** {experience.title()} user → {goal.title()} analysis → {approach.replace('_', ' ').title()} approach\n\n"
        
        # Primary Workflow
        if guidance["next_steps"]:
            response += f"## Recommended Steps\n\n"
            for step in guidance["next_steps"][:2]:  # Show first 2 steps
                response += f"**{step['step']}.** `{step['tool']}` - {step['purpose']}\n"
                response += f"   Parameters: `{step['parameters']}`\n\n"
        
        # Key Alternative
        if guidance["alternative_paths"]:
            response += f"## If That Doesn't Fit\n\n"
            primary_alt = guidance["alternative_paths"][0]
            response += f"**{primary_alt['if']}**\n"
            response += f"{primary_alt['then']}\n\n"
        
        # Essential Context
        response += f"## Key Things to Know\n\n"
        response += f"**Limitations:** {guidance['helpful_context']['key_limitations'][0]}\n\n"
        response += f"**Success Tip:** {guidance['helpful_context']['success_tips'][0]}\n\n"
        
        # Quick Tool Reference
        response += f"## Tool Quick Reference\n\n"
        response += f"- **Predefined Analysis:** `run_aparavi_report` (20 reports, 5 workflows)\n"
        response += f"- **Custom Analysis:** `generate_aql_query` → `validate_aql_query` → `execute_custom_aql_query`\n"
        response += f"- **System Check:** `health_check` or `server_info`\n\n"
        
        response += f"*Want more detail? Call guide_start_here with context_window='large'*\n"
        response += f"*Want just the essentials? Use context_window='small'*"
        
        return response
    
    async def _handle_generate_aql_query(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generate_aql_query tool requests - optimized for LLM efficiency."""
        self.logger.debug("Handling generate_aql_query request")
        
        try:
            # Extract and validate inputs
            business_question = arguments.get("business_question", "").strip()
            desired_fields = arguments.get("desired_fields", [])
            filters = arguments.get("filters", [])
            complexity_preference = arguments.get("complexity_preference", "simple")
            
            if not business_question:
                return {
                    "content": [{
                        "type": "text", 
                        "text": "Please provide a business_question describing what you want to analyze."
                    }],
                    "isError": True
                }
            
            # Use optimized pipeline approach
            concepts = self._detect_query_concepts(business_question)
            query_info = self._generate_query_template(concepts, filters, business_question, complexity_preference)
            response_text = self._format_response(business_question, concepts, query_info, desired_fields)
            
            return {
                "content": [{
                    "type": "text",
                    "text": response_text
                }]
            }
            
        except Exception as e:
            error_msg = f"Error in generate_aql_query: {format_error_message(e)}"
            self.logger.error(error_msg)
            return {
                "content": [{"type": "text", "text": error_msg}],
                "isError": True
            }
    
    # Cache for AQL reference data to avoid repeated file I/O
    _aql_reference_cache = None
    _aql_reference_cache_time = None
    
    def _load_aql_reference(self) -> Dict[str, Any]:
        """Load and cache AQL reference data for performance."""
        import time
        
        # Cache for 5 minutes to balance performance and freshness
        if (self._aql_reference_cache is not None and 
            self._aql_reference_cache_time is not None and
            time.time() - self._aql_reference_cache_time < 300):
            return self._aql_reference_cache
            
        aql_ref_path = Path(__file__).parent.parent.parent / "references" / "aql_ref.json"
        try:
            with open(aql_ref_path, 'r', encoding='utf-8') as f:
                self._aql_reference_cache = json.load(f)
                self._aql_reference_cache_time = time.time()
                return self._aql_reference_cache
        except Exception as e:
            self.logger.warning(f"Could not load AQL reference: {e}")
            return {}
    
    def _detect_query_concepts(self, business_question: str) -> Dict[str, Any]:
        """Detect key concepts from business question using optimized pattern matching."""
        question_lower = business_question.lower()
        
        # Optimized concept detection with weighted scoring
        concept_patterns = {
            'duplicates': ['duplicate', 'duplicates', 'duplicate files', 'same file', 'identical'],
            'file_size': ['large', 'big', 'size', 'storage', 'space', 'gb', 'mb', 'bytes'],
            'time_recent': ['recent', 'new', 'created', 'last', 'latest', 'today', 'yesterday'],
            'time_old': ['old', 'stale', 'unused', 'accessed', 'ancient', 'outdated'],
            'data_source': ['department', 'folder', 'location', 'source', 'path', 'directory'],
            'file_type': ['type', 'extension', 'pdf', 'doc', 'excel', 'format', 'kind'],
            'classification': ['classification', 'sensitive', 'pii', 'classified', 'confidential', 'private']
        }
        
        detected = {}
        for concept, patterns in concept_patterns.items():
            score = sum(1 for pattern in patterns if pattern in question_lower)
            if score > 0:
                detected[concept] = score
                
        return detected
    
    def _build_select_fields(self, concepts: Dict[str, Any]) -> List[str]:
        """Build SELECT clause fields based on detected concepts."""
        fields = []
        
        # Template-based field selection for consistency
        field_templates = {
            'data_source': 'COMPONENTS(parentPath, 3) AS "Data Source"',
            'file_type': 'extension AS "File Type"',
            'file_size': [
                'SUM(size)/1073741824 AS "Total Size (GB)"',
                'COUNT(name) AS "File Count"',
                'AVG(size)/1048576 AS "Average Size (MB)"'
            ],
            'duplicates': [
                'SUM(CASE WHEN dupCount > 1 THEN 1 ELSE 0 END) AS "Files with Duplicates"',
                'SUM(CASE WHEN dupCount > 1 THEN dupCount - 1 ELSE 0 END) AS "Duplicate Instances"'
            ],
            'time_recent': 'SUM(CASE WHEN (cast(NOW() as number) - createTime) < (30 * 24 * 60 * 60) THEN 1 ELSE 0 END) AS "Recent Files (30 days)"',
            'classification': ['classification AS "Classification"', 'COUNT(*) AS "Count"']
        }
        
        for concept in concepts:
            if concept in field_templates:
                template = field_templates[concept]
                if isinstance(template, list):
                    fields.extend(template)
                else:
                    fields.append(template)
        
        # Default fields if none detected
        return fields if fields else ['COUNT(name) AS "File Count"', 'SUM(size)/1073741824 AS "Total Size (GB)"']
    
    def _build_where_conditions(self, concepts: Dict[str, Any], filters: List[str], business_question: str) -> List[str]:
        """Build WHERE clause conditions based on concepts and filters."""
        conditions = ['ClassID = \'idxobject\'']  # Always required
        
        # Concept-based conditions
        condition_templates = {
            'duplicates': 'dupCount > 1',
            'time_recent': '(cast(NOW() as number) - createTime) < (30 * 24 * 60 * 60)',
            'time_old': '(cast(NOW() as number) - accessTime) > (365 * 24 * 60 * 60)',
            'classification': 'classification IS NOT NULL AND classification != \'Unclassified\''
        }
        
        for concept in concepts:
            if concept in condition_templates:
                conditions.append(condition_templates[concept])
        
        # Special handling for file size with context
        if 'file_size' in concepts and 'large' in business_question.lower():
            conditions.append('size > 104857600')  # > 100MB
        
        # Process user filters with templates
        filter_templates = {
            'pdf': 'extension = \'pdf\'',
            'excel': 'extension IN (\'xlsx\', \'xls\')',
            'word': 'extension IN (\'docx\', \'doc\')',
            'large': 'size > 104857600'
        }
        
        for filter_condition in filters:
            filter_lower = filter_condition.lower()
            for key, template in filter_templates.items():
                if key in filter_lower:
                    conditions.append(template)
                    break
        
        return conditions
    
    def _build_group_by_fields(self, concepts: Dict[str, Any]) -> List[str]:
        """Build GROUP BY clause fields based on concepts."""
        group_fields = []
        
        group_templates = {
            'data_source': 'COMPONENTS(parentPath, 3)',
            'file_type': 'extension',
            'classification': 'classification'
        }
        
        for concept in concepts:
            if concept in group_templates:
                group_fields.append(group_templates[concept])
        
        return group_fields
    
    def _generate_query_template(self, concepts: Dict[str, Any], filters: List[str], 
                                business_question: str, complexity: str) -> Dict[str, str]:
        """Generate AQL query using template-based approach."""
        select_fields = self._build_select_fields(concepts)
        where_conditions = self._build_where_conditions(concepts, filters, business_question)
        group_fields = self._build_group_by_fields(concepts)
        
        # Build query components
        select_clause = f"SELECT {', '.join(select_fields)}"
        from_clause = "FROM STORE('/')"
        where_clause = f"WHERE {' AND '.join(where_conditions)}"
        group_clause = f"GROUP BY {', '.join(group_fields)}" if group_fields else ""
        
        # Smart ordering based on concepts
        if 'file_size' in concepts:
            order_clause = "ORDER BY \"Total Size (GB)\" DESC"
        elif 'duplicates' in concepts:
            order_clause = "ORDER BY \"Files with Duplicates\" DESC"
        else:
            order_clause = "ORDER BY \"File Count\" DESC"
            
        limit_clause = "LIMIT 50" if complexity == "simple" else ""
        
        # Construct final query
        query_parts = [select_clause, from_clause, where_clause]
        if group_clause:
            query_parts.append(group_clause)
        query_parts.append(order_clause)
        if limit_clause:
            query_parts.append(limit_clause)
        
        return {
            'query': " ".join(query_parts),
            'select_fields': select_fields,
            'where_conditions': where_conditions,
            'group_fields': group_fields,
            'order_clause': order_clause
        }
    
    def _format_response(self, business_question: str, concepts: Dict[str, Any], 
                        query_info: Dict[str, str], desired_fields: List[str]) -> str:
        """Format the response using templates for consistency."""
        parts = []
        
        # Header
        parts.append(f"# AQL Query Builder for: {business_question}\n")
        
        # Concepts
        concept_names = list(concepts.keys()) if concepts else ['General file analysis']
        parts.append(f"**Detected Concepts**: {', '.join(concept_names)}\n")
        
        # Query
        parts.append("## Generated AQL Query\n")
        parts.append(f"```sql\n{query_info['query']}\n```\n")
        
        # Explanation
        parts.append("### Query Explanation\n")
        field_names = [f.split(' AS ')[1].strip('"') if ' AS ' in f else f for f in query_info['select_fields']]
        parts.append(f"- **SELECT**: Returns {', '.join(field_names)}\n")
        parts.append(f"- **WHERE**: Filters for {', '.join(query_info['where_conditions'])}\n")
        if query_info['group_fields']:
            parts.append(f"- **GROUP BY**: Groups results by {', '.join(query_info['group_fields'])}\n")
        
        # Field validation if requested
        if desired_fields:
            aql_ref = self._load_aql_reference()
            core_fields = aql_ref.get("aql_reference_guide", {}).get("core_fields_reference", [])
            valid_fields = [field.get('field', '') for field in core_fields if isinstance(field, dict)]
            
            parts.append("\n### Field Validation\n")
            for field in desired_fields:
                if field in valid_fields:
                    parts.append(f"✓ **{field}**: Valid Aparavi field\n")
                else:
                    parts.append(f"✗ **{field}**: Invalid field. Try: {', '.join(valid_fields[:3])}...\n")
        
        # Best practices
        parts.append("\n### Next Steps\n")
        parts.append("1. **Validate**: Use `validate_aql_query` to check syntax\n")
        parts.append("2. **Execute**: Use `execute_custom_aql_query` to run the query\n")
        parts.append("3. **Refine**: Adjust based on results\n")
        
        return "".join(parts)

    async def _handle_guide_start_here(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle guide_start_here tool - intelligent entry point and routing assistant."""
        self.logger.info("Processing guide_start_here request")
        
        try:
            # Extract parameters with defaults
            user_experience = arguments.get("user_experience", "unknown")
            query_goal = arguments.get("query_goal", "unknown")
            preferred_approach = arguments.get("preferred_approach", "unknown")
            context_window = arguments.get("context_window", "unknown")
            specific_question = arguments.get("specific_question", "").strip()
            
            # Load available reports and workflows for intelligent routing
            available_reports = list(self.aparavi_reports.keys())
            available_workflows = list(self.analysis_workflows.keys())
            
            # Assessment logic
            assessment = self._assess_user_context(
                user_experience, query_goal, preferred_approach, specific_question
            )
            
            # Generate personalized guidance
            guidance = self._generate_personalized_guidance(
                assessment, context_window, specific_question, available_reports, available_workflows
            )
            
            # Format response based on context window preference
            if context_window == "small":
                response = self._format_focused_response(assessment, guidance)
            elif context_window == "large":
                response = self._format_comprehensive_response(assessment, guidance)
            else:
                response = self._format_balanced_response(assessment, guidance)
            
            self.logger.info(f"Guide provided for {assessment['detected_experience']} user with {assessment['detected_goal']} goal")
            
            return {
                "content": [{
                    "type": "text",
                    "text": response
                }]
            }
            
        except Exception as e:
            self.logger.error(f"Error in guide_start_here: {e}")
            return {
                "isError": True,
                "content": [{
                    "type": "text",
                    "text": f"# Guide Start Here Failed\n\nError: {str(e)}\n\nPlease try again or contact support@aparavi.com"
                }]
            }
    
    def _assess_user_context(self, user_experience: str, query_goal: str, preferred_approach: str, specific_question: str) -> Dict[str, str]:
        """Assess user context and detect patterns from their input."""
        
        # Experience level detection
        detected_experience = user_experience
        if user_experience == "unknown" and specific_question:
            question_lower = specific_question.lower()
            if any(term in question_lower for term in ["aql", "query", "select", "where", "group by"]):
                detected_experience = "intermediate"
            elif any(term in question_lower for term in ["syntax", "validation", "optimize", "performance"]):
                detected_experience = "advanced"
            elif any(term in question_lower for term in ["how do i", "getting started", "new to", "don't know"]):
                detected_experience = "new"
            else:
                detected_experience = "new"  # Default to safest assumption
        elif user_experience == "unknown":
            detected_experience = "new"  # Default to safest assumption
        
        # Goal detection from specific question
        detected_goal = query_goal
        if query_goal == "unknown" and specific_question:
            question_lower = specific_question.lower()
            if any(term in question_lower for term in ["duplicate", "dedup", "same file", "copies"]):
                detected_goal = "duplicates"
            elif any(term in question_lower for term in ["growth", "trend", "over time", "monthly", "yearly"]):
                detected_goal = "growth"
            elif any(term in question_lower for term in ["classification", "sensitive", "pii", "security", "permission"]):
                detected_goal = "security"
            elif any(term in question_lower for term in ["overview", "summary", "explore", "what data", "show me"]):
                detected_goal = "exploration"
            elif any(term in question_lower for term in ["custom", "specific", "complex", "advanced analysis"]):
                detected_goal = "custom"
            elif any(term in question_lower for term in ["error", "failed", "not working", "help", "troubleshoot"]):
                detected_goal = "troubleshooting"
            else:
                detected_goal = "exploration"  # Default to safest assumption
        elif query_goal == "unknown":
            detected_goal = "exploration"  # Default to safest assumption
        
        # Approach recommendation
        recommended_approach = preferred_approach
        if preferred_approach == "unknown":
            if detected_experience == "new":
                recommended_approach = "guided"
            elif detected_experience == "advanced" and detected_goal == "custom":
                recommended_approach = "custom_queries"
            else:
                recommended_approach = "reports"
        
        return {
            "detected_experience": detected_experience,
            "detected_goal": detected_goal,
            "recommended_approach": recommended_approach
        }
    
    def _generate_personalized_guidance(self, assessment: Dict[str, str], context_window: str, 
                                      specific_question: str, available_reports: list, available_workflows: list) -> Dict[str, Any]:
        """Generate personalized guidance based on assessment."""
        
        experience = assessment["detected_experience"]
        goal = assessment["detected_goal"]
        approach = assessment["recommended_approach"]
        
        # Goal-specific report recommendations
        goal_report_mapping = {
            "duplicates": ["duplicate_file_summary", "duplicate_file_summary_detailed"],
            "growth": ["yearly_data_growth", "monthly_data_growth", "data_sources_created"],
            "security": ["classifications_by_permissions", "classifications_by_owner", "simple_classification_summary"],
            "exploration": ["data_sources_overview", "file_type_extension_summary", "simple_classification_summary"],
            "custom": [],  # Will use generate_aql_query
            "troubleshooting": []  # Will use health_check first
        }
        
        # Workflow recommendations
        goal_workflow_mapping = {
            "duplicates": ["storage_audit"],
            "growth": ["growth_analysis", "data_lifecycle"],
            "security": ["security_review", "compliance_check"],
            "exploration": ["storage_audit", "compliance_check"],
            "custom": [],
            "troubleshooting": []
        }
        
        # Generate next steps based on experience and goal
        next_steps = []
        
        if goal == "troubleshooting":
            next_steps = [
                {
                    "step": 1,
                    "tool": "health_check",
                    "parameters": "No parameters needed",
                    "purpose": "Verify system connectivity and identify any configuration issues",
                    "expected_outcome": "System status report with API connectivity and AQL validation results"
                }
            ]
        elif experience == "new":
            if goal in goal_report_mapping and goal_report_mapping[goal]:
                primary_report = goal_report_mapping[goal][0]
                next_steps = [
                    {
                        "step": 1,
                        "tool": "run_aparavi_report",
                        "parameters": f'report_name="{primary_report}"',
                        "purpose": "Get immediate insights for {goal} analysis without needing AQL knowledge",
                        "expected_outcome": "Formatted report with key metrics and insights"
                    },
                    {
                        "step": 2,
                        "tool": "run_aparavi_report",
                        "parameters": 'report_name="list"',
                        "purpose": "Discover other relevant reports for deeper analysis",
                        "expected_outcome": "Complete list of 20 available reports with descriptions"
                    }
                ]
            else:
                next_steps = [
                    {
                        "step": 1,
                        "tool": "server_info",
                        "parameters": "No parameters needed",
                        "purpose": "Understand available capabilities and get oriented",
                        "expected_outcome": "Server configuration and feature overview"
                    },
                    {
                        "step": 2,
                        "tool": "run_aparavi_report",
                        "parameters": 'report_name="list"',
                        "purpose": "See all available pre-built analyses",
                        "expected_outcome": "Complete catalog of reports and workflows"
                    }
                ]
        elif experience == "intermediate":
            if goal == "custom":
                next_steps = [
                    {
                        "step": 1,
                        "tool": "generate_aql_query",
                        "parameters": f'business_question="{specific_question or "Your specific analysis question"}"',
                        "purpose": "Generate syntactically correct AQL for your custom analysis",
                        "expected_outcome": "Valid AQL query with explanation and field validation"
                    },
                    {
                        "step": 2,
                        "tool": "validate_aql_query",
                        "parameters": "query=\"[generated query]\"",
                        "purpose": "Verify the generated query syntax before execution",
                        "expected_outcome": "Validation confirmation or detailed error information"
                    }
                ]
            elif goal in goal_workflow_mapping and goal_workflow_mapping[goal]:
                primary_workflow = goal_workflow_mapping[goal][0]
                next_steps = [
                    {
                        "step": 1,
                        "tool": "run_aparavi_report",
                        "parameters": f'workflow_name="{primary_workflow}"',
                        "purpose": f"Execute comprehensive {goal} analysis workflow",
                        "expected_outcome": "Multi-report analysis with integrated insights"
                    }
                ]
        elif experience == "advanced":
            if goal == "custom":
                next_steps = [
                    {
                        "step": 1,
                        "tool": "validate_aql_query",
                        "parameters": "query=\"[your AQL query]\"",
                        "purpose": "Validate your custom AQL syntax against Aparavi limitations",
                        "expected_outcome": "Syntax validation with specific error details if needed"
                    },
                    {
                        "step": 2,
                        "tool": "execute_custom_aql_query",
                        "parameters": "query=\"[validated query]\"",
                        "purpose": "Execute your validated query and get raw JSON results",
                        "expected_outcome": "Raw JSON data for further analysis or visualization"
                    }
                ]
            else:
                # Advanced users might want to see the query behind reports
                if goal in goal_report_mapping and goal_report_mapping[goal]:
                    primary_report = goal_report_mapping[goal][0]
                    next_steps = [
                        {
                            "step": 1,
                            "tool": "run_aparavi_report",
                            "parameters": f'report_name="{primary_report}"',
                            "purpose": "Execute optimized report to see results and understand query patterns",
                            "expected_outcome": "Report results plus insight into proven AQL patterns"
                        }
                    ]
        
        # Generate alternative paths
        alternative_paths = []
        
        if goal != "custom":
            alternative_paths.append({
                "if": "The predefined reports don't match your exact needs",
                "then": "Use generate_aql_query → validate_aql_query → execute_custom_aql_query",
                "tools": ["generate_aql_query", "validate_aql_query", "execute_custom_aql_query"]
            })
        
        if experience != "new":
            alternative_paths.append({
                "if": "You want to explore all available options first",
                "then": "Start with run_aparavi_report('list') to see all 20 reports and 5 workflows",
                "tools": ["run_aparavi_report"]
            })
        
        if goal != "troubleshooting":
            alternative_paths.append({
                "if": "You encounter errors or unexpected results",
                "then": "Run health_check to verify system status and connectivity",
                "tools": ["health_check"]
            })
        
        # Context-aware helpful information
        helpful_context = {
            "key_limitations": [
                "AQL doesn't support DISTINCT (use GROUP BY instead)",
                "No DATEADD function (use time arithmetic: cast(NOW() as number) - createTime)",
                "Always include ClassID = 'idxobject' for file analysis",
                "Handle NULL values explicitly in WHERE clauses"
            ],
            "common_pitfalls": [
                "Don't write AQL manually - use generate_aql_query for custom analysis",
                "Always validate queries before execution to avoid API errors",
                "Check predefined reports first - they cover 90% of common use cases",
                "Use workflows for multi-report analysis instead of running reports individually"
            ],
            "success_tips": [
                "Start with predefined reports, then move to custom queries if needed",
                "Use the 3-step workflow: generate → validate → execute for custom analysis",
                "Break complex questions into smaller, focused queries",
                "Leverage report combinations and workflows for comprehensive analysis"
            ]
        }
        
        return {
            "next_steps": next_steps,
            "alternative_paths": alternative_paths,
            "helpful_context": helpful_context,
            "recommended_reports": goal_report_mapping.get(goal, []),
            "recommended_workflows": goal_workflow_mapping.get(goal, [])
        }
    
    def _format_focused_response(self, assessment: Dict[str, str], guidance: Dict[str, Any]) -> str:
        """Format a focused, concise response for users who prefer small context windows."""
        
        experience = assessment["detected_experience"]
        goal = assessment["detected_goal"]
        
        response = f"# Quick Start Guide\n\n"
        response += f"**Detected:** {experience.title()} user seeking {goal} analysis\n\n"
        
        if guidance["next_steps"]:
            response += f"## Next Step\n\n"
            first_step = guidance["next_steps"][0]
            response += f"**Tool:** `{first_step['tool']}`\n"
            response += f"**Parameters:** {first_step['parameters']}\n"
            response += f"**Purpose:** {first_step['purpose']}\n\n"
        
        response += f"## Key Tip\n"
        if guidance["helpful_context"]["success_tips"]:
            response += f"{guidance['helpful_context']['success_tips'][0]}\n\n"
        
        response += f"*Need more guidance? Call guide_start_here again with context_window='large'*"
        
        return response
    
    def _format_comprehensive_response(self, assessment: Dict[str, str], guidance: Dict[str, Any]) -> str:
        """Format a comprehensive response for users who prefer detailed guidance."""
        
        experience = assessment["detected_experience"]
        goal = assessment["detected_goal"]
        approach = assessment["recommended_approach"]
        
        response = f"# Comprehensive Aparavi Data Suite Guide\n\n"
        
        # Assessment Summary
        response += f"## Your Profile Assessment\n\n"
        response += f"- **Experience Level:** {experience.title()}\n"
        response += f"- **Analysis Goal:** {goal.title()}\n"
        response += f"- **Recommended Approach:** {approach.replace('_', ' ').title()}\n\n"
        
        # Detailed Next Steps
        if guidance["next_steps"]:
            response += f"## Recommended Workflow\n\n"
            for i, step in enumerate(guidance["next_steps"], 1):
                response += f"### Step {step['step']}: {step['tool']}\n\n"
                response += f"**Parameters:** `{step['parameters']}`\n\n"
                response += f"**Purpose:** {step['purpose']}\n\n"
                response += f"**Expected Outcome:** {step['expected_outcome']}\n\n"
        
        # Alternative Paths
        if guidance["alternative_paths"]:
            response += f"## Alternative Approaches\n\n"
            for alt in guidance["alternative_paths"]:
                response += f"**If:** {alt['if']}\n"
                response += f"**Then:** {alt['then']}\n"
                response += f"**Tools:** {', '.join(alt['tools'])}\n\n"
        
        # Recommended Resources
        if guidance["recommended_reports"]:
            response += f"## Relevant Reports\n\n"
            for report in guidance["recommended_reports"][:3]:  # Show top 3
                response += f"- `{report}`\n"
            response += f"\n"
        
        if guidance["recommended_workflows"]:
            response += f"## Relevant Workflows\n\n"
            for workflow in guidance["recommended_workflows"]:
                response += f"- `{workflow}`\n"
            response += f"\n"
        
        # Comprehensive Context
        response += f"## Important Limitations\n\n"
        for limitation in guidance["helpful_context"]["key_limitations"]:
            response += f"- {limitation}\n"
        response += f"\n"
        
        response += f"## Common Pitfalls to Avoid\n\n"
        for pitfall in guidance["helpful_context"]["common_pitfalls"]:
            response += f"- {pitfall}\n"
        response += f"\n"
        
        response += f"## Success Tips\n\n"
        for tip in guidance["helpful_context"]["success_tips"]:
            response += f"- {tip}\n"
        response += f"\n"
        
        response += f"## All Available Tools\n\n"
        response += f"1. **guide_start_here** - This intelligent routing assistant\n"
        response += f"2. **health_check** - System health and connectivity verification\n"
        response += f"3. **server_info** - Configuration and capabilities overview\n"
        response += f"4. **run_aparavi_report** - 20 predefined reports + 5 workflows\n"
        response += f"5. **validate_aql_query** - Syntax validation without execution\n"
        response += f"6. **execute_custom_aql_query** - Validate and execute custom queries\n"
        response += f"7. **generate_aql_query** - Intelligent AQL query builder\n\n"
        
        response += f"*Ready to proceed? Execute the recommended Step 1 above to get started!*"
        
        return response
    
    def _format_balanced_response(self, assessment: Dict[str, str], guidance: Dict[str, Any]) -> str:
        """Format a balanced response with essential information without overwhelming detail."""
        
        experience = assessment["detected_experience"]
        goal = assessment["detected_goal"]
        approach = assessment["recommended_approach"]
        
        response = f"# Aparavi Data Suite - Your Personalized Guide\n\n"
        
        # Quick Assessment
        response += f"**Profile:** {experience.title()} user → {goal.title()} analysis → {approach.replace('_', ' ').title()} approach\n\n"
        
        # Primary Workflow
        if guidance["next_steps"]:
            response += f"## Recommended Steps\n\n"
            for step in guidance["next_steps"][:2]:  # Show first 2 steps
                response += f"**{step['step']}.** `{step['tool']}` - {step['purpose']}\n"
                response += f"   Parameters: `{step['parameters']}`\n\n"
        
        # Key Alternative
        if guidance["alternative_paths"]:
            response += f"## If That Doesn't Fit\n\n"
            primary_alt = guidance["alternative_paths"][0]
            response += f"**{primary_alt['if']}**\n"
            response += f"{primary_alt['then']}\n\n"
        
        # Essential Context
        response += f"## Key Things to Know\n\n"
        response += f"**Limitations:** {guidance['helpful_context']['key_limitations'][0]}\n\n"
        response += f"**Success Tip:** {guidance['helpful_context']['success_tips'][0]}\n\n"
        
        # Quick Tool Reference
        response += f"## Tool Quick Reference\n\n"
        response += f"- **Predefined Analysis:** `run_aparavi_report` (20 reports, 5 workflows)\n"
        response += f"- **Custom Analysis:** `generate_aql_query` → `validate_aql_query` → `execute_custom_aql_query`\n"
        response += f"- **System Check:** `health_check` or `server_info`\n\n"
        
        response += f"*Want more detail? Call guide_start_here with context_window='large'*\n"
        response += f"*Want just the essentials? Use context_window='small'*"
        
        return response
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests and route to appropriate handlers."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        self.logger.debug(f"Handling request: {method} (id: {request_id})")
        
        # Handle missing method
        if not method:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: missing method"
                }
            }
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_list_tools(params)
            elif method == "tools/call":
                result = await self.handle_call_tool(params)
            elif method == "resources/list":
                result = await self.handle_list_resources(params)
            elif method == "prompts/list":
                result = await self.handle_list_prompts(params)
            elif method == "notifications/initialized":
                # Handle the initialized notification - no response needed
                self.logger.info("Received initialized notification")
                return None
            else:
                error_msg = f"Method not found: {method}"
                self.logger.error(error_msg)
                
                # For notifications (no id), don't send a response
                if request_id is None:
                    return None
                    
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": error_msg
                    }
                }
            
            # For notifications (no id), don't send a response
            if request_id is None:
                return None
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            error_msg = f"Internal error handling {method}: {format_error_message(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            # For notifications (no id), don't send a response
            if request_id is None:
                return None
                
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": error_msg
                }
            }
    
    async def handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request."""
        self.logger.debug("Listing available resources")
        
        resources = [
            {
                "name": "Aparavi Data Suite API Documentation",
                "description": "Official API documentation for Aparavi Data Suite",
                "url": "https://aparavi.com/docs/api"
            },
            {
                "name": "Aparavi Data Suite Community Forum",
                "description": "Community forum for discussing Aparavi Data Suite and related topics",
                "url": "https://community.aparavi.com"
            }
        ]
        
        return {
            "resources": resources
        }
    
    async def handle_list_prompts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request."""
        self.logger.debug("Listing available prompts")
        
        prompts = [
            {
                "name": "Get started with Aparavi Data Suite",
                "description": "Begin your journey with Aparavi Data Suite",
                "prompt": "What do you want to do with Aparavi Data Suite?"
            },
            {
                "name": "Explore Aparavi Data Suite features",
                "description": "Learn about the features of Aparavi Data Suite",
                "prompt": "What features of Aparavi Data Suite are you interested in?"
            }
        ]
        
        return {
            "prompts": prompts
        }
    
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
                    try:
                        request = json.loads(line)
                        self.logger.debug(f"Received request: {request}")
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Invalid JSON received: {line[:100]}... Error: {e}")
                        continue
                    
                    # Handle request
                    try:
                        response = await self.handle_request(request)
                        self.logger.debug(f"Generated response: {response}")
                    except Exception as e:
                        self.logger.error(f"Error handling request: {e}", exc_info=True)
                        continue
                    
                    # Send JSON response to stdout (only if response is not None)
                    if response is not None:
                        try:
                            # Ensure clean JSON output without extra whitespace
                            response_json = json.dumps(response, separators=(',', ':'))
                            print(response_json, flush=True)
                            self.logger.debug(f"Sent response: {response_json}")
                        except (OSError, IOError, UnicodeEncodeError) as e:
                            # Handle case where stdout is closed (e.g., when Claude Desktop disconnects)
                            self.logger.debug(f"Stdout write failed (connection closed): {e}")
                            break
                        except Exception as e:
                            self.logger.error(f"Error serializing response: {e}")
                            continue
                    else:
                        self.logger.debug("No response sent (notification or null response)")
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
