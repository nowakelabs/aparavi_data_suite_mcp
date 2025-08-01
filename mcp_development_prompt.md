# APARAVI MCP Server Development Plan

## **Context & Objective**

I'm building an MCP (Model Context Protocol) server that enables Claude Desktop users to query APARAVI data management systems through natural language. The server will expose 20 predefined APARAVI AQL (APARAVI Query Language) reports as MCP tools that Claude can discover and execute.

**Key Requirements:**
- Python-based MCP server using Anthropic's MCP SDK with UV for fast dependency management
- Integration with APARAVI API endpoints for data queries
- 20 tools corresponding to specific AQL reports (Data Sources Overview, Duplicate Analysis, Classification Reports, etc.)
- Natural language query support with intelligent parameter mapping
- Secure authentication and error handling
- Native Python deployment using UV's modern toolchain (no Docker required - can be added later for enterprise use)

## **Technical Architecture**

```
Claude Desktop ←→ MCP Server ←→ APARAVI API
                     ↓
                 Tool Registry
                 Query Engine
                 Response Formatter
                 Cache Layer
```

## **Development Phases - Follow This Order**

### **Phase 1: Project Foundation**
Create the basic project structure and MCP server skeleton.

**Tasks:**
1. Set up UV environment and project structure
2. Install and configure MCP Python SDK dependencies using UV
3. Create basic MCP server that can start/stop and respond to health checks
4. Implement configuration management for APARAVI connection settings
5. Add logging framework and basic error handling

**Setup Instructions:**
```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create project directory
mkdir aparavi-mcp-server
cd aparavi-mcp-server

# Initialize UV project with pyproject.toml
uv init --package aparavi-mcp-server

# Create virtual environment
uv venv

# Add core dependencies
uv add mcp anthropic-mcp-sdk requests pydantic pyyaml python-dotenv

# Add development dependencies
uv add --dev pytest pytest-asyncio black flake8 mypy

# Create the project structure (see File Structure above)
mkdir -p src/aparavi_mcp/tools tests config scripts
touch src/aparavi_mcp/__init__.py
# ... create other files
```

**File Structure:**
```
aparavi-mcp-server/
├── src/
│   ├── aparavi_mcp/
│   │   ├── __init__.py
│   │   ├── server.py           # Main MCP server
│   │   ├── aparavi_client.py   # APARAVI API client
│   │   ├── tools/              # MCP tool definitions
│   │   │   ├── __init__.py
│   │   │   ├── storage_tools.py
│   │   │   ├── optimization_tools.py
│   │   │   └── governance_tools.py
│   │   ├── config.py           # Configuration management
│   │   └── utils.py            # Utilities and helpers
├── tests/
│   ├── __init__.py
│   ├── test_aparavi_client.py
│   ├── test_tools.py
│   └── test_server.py
├── config/
│   ├── config.yaml
│   └── config.example.yaml
├── scripts/
│   ├── start_server.py
│   └── setup_dev.py
├── pyproject.toml              # UV project configuration
├── uv.lock                     # UV lockfile (auto-generated)
├── README.md
└── .env.example
```

**Validation:** MCP server starts without errors and Claude Desktop can discover it

---

### **Phase 2: APARAVI API Integration**
Build the core APARAVI API client and query execution engine.

**APARAVI API Details:**
- **Endpoint**: `http://localhost/server/api/v3/database/query`
- **Method**: GET
- **Parameters**: 
  - `select`: URL-encoded AQL query string
  - `options`: JSON string with format, stream, validate flags
- **Authentication**: HTTP Basic Auth
- **Response Formats**: JSON or CSV

**AQL Queries to Implement:**
1. Data Sources Overview - Storage distribution and activity analysis
2. Duplicate File Summary - Infrastructure-wide duplicate analysis  
3. Classification Summary by Data Source - Sensitive data location analysis
4. File Type/Extension Summary - File format and storage analysis
5. Subfolder Overview - Directory structure analysis
6. Classifications by Age - Data aging patterns
7. Classifications by Access Permissions - Security risk analysis
8. Classifications by Owner - Data ownership patterns
9. Monthly Data Growth by Category - Growth trend analysis
10. User/Owner File Categories Summary - User activity patterns
11. Access/Permissions File Categories Summary - Permission analysis
12. Data Sources Overview - Last Modified - Modification patterns
13. Data Sources Overview - Created - Creation patterns  
14. Data Sources Overview - Last Accessed - Access patterns
15. File Type/Extension Activity - Format usage analysis
16. Duplicate File Summary - DETAILED - Age-based duplicate analysis
17. Yearly Data Growth Report - Historical growth analysis
18. Data Owner Summary - Top storage consumers
19. Simple Classification Summary - Basic classification overview
20. File Type/Category Summary DETAILED - Comprehensive category analysis

**Tasks:**
1. Implement APARAVI API client with authentication
2. Create query execution engine with timeout and retry logic
3. Add response parsing and data normalization
4. Implement caching mechanism for frequently accessed data
5. Add comprehensive error handling and logging

**Validation:** All 20 AQL queries execute successfully and return properly formatted data

---

### **Phase 3: MCP Tool Implementation**
Create MCP tools for each APARAVI report with rich descriptions and parameter schemas.

**Tool Design Pattern:**
```python
{
    "name": "aparavi_storage_overview",
    "description": "Analyze storage distribution across data sources with activity indicators and optimization opportunities",
    "parameters": {
        "type": "object",
        "properties": {
            "business_question": {
                "type": "string", 
                "description": "The business question you're trying to answer"
            },
            "scope": {
                "type": "string",
                "enum": ["all", "top_sources", "specific_path"],
                "description": "Analysis scope"
            },
            "include_stale_analysis": {
                "type": "boolean",
                "description": "Include analysis of stale/unused files"
            }
        }
    }
}
```

**Tool Categories:**
- **Storage Analysis** (6 tools): overview, growth, capacity, activity
- **Optimization** (4 tools): duplicates, cleanup, efficiency  
- **Governance** (6 tools): classification, permissions, ownership
- **Reporting** (4 tools): trends, summaries, compliance

**Tasks:**
1. Define MCP tool schemas for all 20 reports
2. Implement tool execution handlers that map to AQL queries  
3. Create intelligent parameter inference and validation
4. Add business-friendly descriptions and use case examples
5. Implement response formatting for Claude consumption

**Validation:** Claude can discover all tools and execute them with natural language queries

---

### **Phase 4: Advanced Features**
Add sophisticated capabilities like query chaining, context awareness, and data insights.

**Tasks:**
1. **Query Chaining**: Enable multi-step analysis workflows
2. **Context Awareness**: Use conversation history to enhance queries
3. **Smart Suggestions**: Recommend follow-up analyses based on results
4. **Data Insights**: Automatically identify key findings and trends
5. **Resource Exposure**: Expose APARAVI schema as MCP resources

**Advanced Features:**
- Session state management for conversation context  
- Intelligent follow-up query suggestions
- Data trend detection and anomaly identification
- Comparative analysis capabilities
- Executive summary generation

**Validation:** Users can conduct sophisticated multi-step analyses through natural conversation

---

### **Phase 5: Production Readiness**
Add security, monitoring, performance optimization, and deployment capabilities.

**Tasks:**
1. **Security**: Implement secure credential management, rate limiting, audit logging
2. **Performance**: Add query optimization, connection pooling, result compression
3. **Monitoring**: Implement health checks, metrics collection, alerting
4. **Deployment**: Create installation scripts, service management, configuration templates
5. **Testing**: Comprehensive test suite including unit, integration, and end-to-end tests

**Production Features:**
- Environment-based configuration management (.env files)
- Encrypted credential storage using system keyring
- Request rate limiting and throttling  
- Comprehensive audit logging with rotation
- Performance metrics and health monitoring
- Graceful error handling and recovery
- System service integration (systemd/Windows Service)
- Multiple deployment options (standalone, service, cloud)

**Deployment Options:**
```bash
# Option 1: Direct UV execution
uv run src/aparavi_mcp/server.py

# Option 2: As a module with UV
uv run -m aparavi_mcp.server

# Option 3: Install and run as package
uv pip install -e .
uv run aparavi-mcp-server

# Option 4: System service (Linux)
sudo systemctl enable aparavi-mcp
sudo systemctl start aparavi-mcp

# Option 5: Windows Service
uv run scripts/install_service.py

# Option 6: Cloud deployment (PM2, supervisor, etc.)
pm2 start ecosystem.config.js
```

**Validation:** System passes security audit and performs well under load

---

## **Implementation Guidelines for AI Assistant**

### **Code Quality Standards**
- Use type hints throughout Python code
- Follow PEP 8 style guidelines
- Include comprehensive docstrings
- Implement proper error handling with specific exception types
- Use logging instead of print statements
- Write defensive code with input validation

### **MCP Integration Best Practices**
- Follow MCP protocol specifications exactly
- Use proper JSON schema for tool definitions
- Implement graceful connection handling
- Add comprehensive error responses Claude can interpret
- Include metadata in responses (data freshness, scope, confidence)

### **APARAVI Integration Requirements**
- Always URL-encode AQL queries before sending
- Include proper authentication headers
- Handle API rate limits gracefully  
- Parse responses consistently regardless of format
- Log all queries for audit purposes

### **Testing Strategy**
- Mock APARAVI API responses for unit tests
- Create integration tests with real APARAVI instance
- Test error scenarios (network failures, invalid queries, auth issues)
- Validate MCP protocol compliance
- Test Claude Desktop integration end-to-end

### **Configuration Management**
- Use environment variables for sensitive data (.env files)
- Support multiple deployment environments (dev/test/prod)
- Validate configuration on startup with clear error messages
- Provide example configuration files (.env.example, config.example.yaml)
- Use pydantic for configuration validation and type safety

### **Dependency Management with UV**
UV uses `pyproject.toml` for dependency management instead of requirements.txt:

```toml
# pyproject.toml
[project]
name = "aparavi-mcp-server"
version = "0.1.0"
description = "APARAVI MCP Server for Claude Desktop integration"
requires-python = ">=3.9"
dependencies = [
    "mcp>=0.1.0",
    "anthropic-mcp-sdk>=0.1.0",
    "requests>=2.31.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project.scripts]
aparavi-mcp-server = "aparavi_mcp.server:main"
```

**UV Commands:**
```bash
# Add new dependency
uv add requests

# Add development dependency  
uv add --dev pytest

# Install all dependencies
uv sync

# Update dependencies
uv lock --upgrade

# Run with dependencies
uv run python src/aparavi_mcp/server.py
```

### **Virtual Environment Best Practices**
- Always activate venv before development: `source venv/bin/activate`
- Keep requirements.txt updated: `pip freeze > requirements.txt`
- Use separate requirements-dev.txt for development tools
- Test in clean environment periodically to catch missing dependencies
- Document Python version requirements (3.9+ recommended)

### **Performance Considerations**
- Implement query result caching with TTL
- Use connection pooling for APARAVI API
- Add query timeout handling
- Optimize large result set handling
- Monitor and log performance metrics

## **Development Workflow**

### **Step-by-Step Process**
1. **Start with Phase 1**: Get basic MCP server running first
2. **Test Early and Often**: Validate each component before moving forward
3. **Incremental Development**: Add one tool at a time and test thoroughly
4. **Claude Integration**: Test with Claude Desktop at each major milestone
5. **Document as You Go**: Keep README and documentation updated

### **Validation Checkpoints**
- [ ] Phase 1: MCP server starts and Claude Desktop can connect
- [ ] Phase 2: All 20 AQL queries execute and return valid data
- [ ] Phase 3: Claude can discover and execute all tools via natural language
- [ ] Phase 4: Multi-step analysis workflows work smoothly
- [ ] Phase 5: System is production-ready with proper security and monitoring

### **Common Issues to Watch For**
- **UV Installation**: Ensure UV is properly installed and in PATH
- **Dependencies**: Use `uv add` instead of pip install to maintain pyproject.toml
- **Environment**: Always use `uv run` for command execution to ensure correct environment
- **Python Versions**: UV handles Python version management - specify in pyproject.toml
- **MCP Protocol**: JSON formatting errors in tool definitions or responses
- **APARAVI API**: Authentication failures and connection timeouts
- **Environment Variables**: Missing or incorrect .env configuration
- **Path Issues**: Import errors due to incorrect PYTHONPATH or project structure
- **Claude Desktop**: Connection stability and MCP server discovery issues
- **Lock File**: Commit uv.lock for reproducible deployments

## **Success Criteria**

### **Technical Goals**
- All 20 APARAVI reports accessible as MCP tools
- Sub-5 second response times for 90% of queries
- Proper error handling for all failure scenarios
- Claude Desktop integration works seamlessly
- Production-ready security and monitoring

### **User Experience Goals**
- Natural language queries work intuitively
- Claude provides actionable business insights
- Multi-step analysis flows feel conversational
- Error messages are helpful and actionable
- System provides proactive recommendations

## **Getting Started Instructions**

### **Environment Setup with UV**
```bash
# 1. Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Create project and initialize
mkdir aparavi-mcp-server && cd aparavi-mcp-server
uv init --package aparavi-mcp-server

# 3. Create virtual environment and install dependencies
uv venv
uv add mcp anthropic-mcp-sdk requests pydantic pyyaml python-dotenv
uv add --dev pytest pytest-asyncio black flake8 mypy

# 4. Create basic project structure
mkdir -p src/aparavi_mcp/tools tests config scripts
touch src/aparavi_mcp/__init__.py src/aparavi_mcp/server.py
```

### **Development Workflow**
1. **Begin with Phase 1**: Focus only on getting the basic MCP server structure working
2. **Use Official MCP SDK**: Follow Anthropic's MCP Python SDK documentation
3. **Test Incrementally**: Validate each component before adding complexity  
4. **Start Simple**: Implement 3-5 core tools first, then expand
5. **Document Everything**: Keep clear notes on what works and what doesn't

### **Daily Development Process**
```bash
# No need to manually activate - UV handles environment automatically

# Install new dependencies (when needed)
uv add new-package
uv add --dev dev-package

# Run the server
uv run src/aparavi_mcp/server.py

# Run tests
uv run pytest tests/

# Format code
uv run black src/

# Type checking
uv run mypy src/

# Sync dependencies (like pip install -r requirements.txt)
uv sync
```

Remember: The goal is to create a conversational interface to APARAVI data that feels natural and provides genuine business value to users through Claude Desktop.

---

**Ready to start? Let's begin with Phase 1 - setting up the basic project structure and MCP server foundation.**