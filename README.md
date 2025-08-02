# Aparavi Data Suite MCP Server

A comprehensive Model Context Protocol (MCP) server that enables Claude Desktop and other MCP clients to interact with Aparavi Data Suite systems through natural language. The server provides a unified interface for executing AQL (Aparavi Data Suite Query Language) queries, running predefined reports, and validating custom queries.

## 🚀 Features

### Core MCP Tools
- **`health_check`**: Comprehensive server health monitoring with API connectivity and AQL validation
- **`server_info`**: Detailed server configuration and capability information
- **`run_aparavi_report`**: Execute 20 predefined Aparavi Data Suite reports and 5 analysis workflows
- **`validate_aql_query`**: Validate custom AQL queries without execution
- **`execute_custom_aql_query`**: Validate and execute custom AQL queries with raw JSON output

### Advanced Capabilities
- **20 Predefined Reports**: Comprehensive data analysis covering storage, duplicates, classifications, and more
- **5 Analysis Workflows**: Pre-configured multi-report analysis for common business scenarios
- **Smart Query Validation**: Real-time AQL syntax validation using Aparavi Data Suite API
- **Raw JSON Output**: Unformatted results for flexible LLM interpretation and analysis
- **Intelligent Report Discovery**: Natural language report selection with keyword matching
- **Secure Authentication**: HTTP Basic Auth integration with environment-based credentials
- **Robust Error Handling**: Comprehensive error reporting and recovery mechanisms
- **Modern Architecture**: Python 3.11+ with async/await and UV package management

## 📋 Prerequisites

- **Python 3.11+**: Required for modern async features
- **UV Package Manager**: Fast dependency management
- **Aparavi Data Suite System**: Access to Aparavi Data Suite API
- **Claude Desktop**: For MCP integration (or any MCP-compatible client)

## 🛠️ Installation

### 1. Install UV Package Manager

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd aparavi_reporting_mcp

# Create virtual environment and install dependencies
uv venv
uv pip install -e .

# Install development dependencies (optional)
uv pip install -e ".[dev]"
```

### 3. Environment Configuration

Copy the environment template and configure your Aparavi Data Suite connection:

```bash
cp .env.template .env
```

Edit `.env` with your Aparavi Data Suite credentials:

```env
# Aparavi Data Suite API Configuration
APARAVI_BASE_URL=http://localhost
APARAVI_PORT=80
APARAVI_USERNAME=your_username
APARAVI_PASSWORD=your_password

# Server Configuration
SERVER_NAME=Aparavi Data Suite MCP Server
SERVER_VERSION=1.0.0
LOG_LEVEL=INFO
```

### 4. Claude Desktop Integration

Add the MCP server to your Claude Desktop configuration:

**Location:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "aparavi-reporting": {
      "command": "python",
      "args": [
        "C:\\path\\to\\aparavi_reporting_mcp\\scripts\\start_server_claude.py"
      ],
      "cwd": "C:\\path\\to\\aparavi_reporting_mcp"
    }
  }
}
```

## 📖 Usage

### Starting the Server

**For Claude Desktop (recommended):**
The server starts automatically when Claude Desktop loads. Check the MCP section for available tools.

**For standalone testing:**
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Start server
python scripts/start_server.py
```

### 🔧 Available MCP Tools

#### 1. `health_check`
**Purpose:** Comprehensive server health monitoring  
**Parameters:** None  
**Features:**
- API connectivity testing
- AQL query validation for all configured reports
- Configuration validation
- Detailed status reporting

#### 2. `server_info`
**Purpose:** Detailed server configuration and capabilities  
**Parameters:** None  
**Returns:** Server version, configuration, loaded reports count

#### 3. `run_aparavi_report`
**Purpose:** Execute predefined reports and analysis workflows  
**Parameters:**
- `report_name` (optional): Specific report name or "list"
- `workflow_name` (optional): Workflow name or "list"

#### 4. `validate_aql_query`
**Purpose:** Validate custom AQL queries without execution  
**Parameters:**
- `query` (required): AQL query string to validate
**Returns:** Validation status, syntax errors, recommendations

#### 5. `execute_custom_aql_query`
**Purpose:** Validate and execute custom AQL queries  
**Parameters:**
- `query` (required): AQL query string to validate and execute
**Returns:** Raw JSON results for LLM interpretation

### 📊 Available Reports (20 Total)

**Storage & Optimization:**
- `data_sources_overview` - Storage overview by data source
- `subfolder_overview` - Storage breakdown by subfolder
- `file_type_analysis` - File type distribution and sizes
- `large_files_analysis` - Files over 100MB
- `storage_optimization` - Storage optimization opportunities
- `archive_candidates` - Files suitable for archiving
- `cleanup_opportunities` - Data cleanup recommendations

**Data Quality & Duplicates:**
- `duplicate_files_analysis` - Duplicate file detection
- `version_control_analysis` - File versioning patterns

**Security & Compliance:**
- `classification_overview` - Data classification summary
- `sensitive_data_analysis` - Sensitive data identification
- `retention_analysis` - Data retention compliance
- `compliance_summary` - Compliance status overview
- `risk_assessment` - Data risk evaluation

**Analytics & Insights:**
- `data_growth_analysis` - Historical data growth trends
- `user_activity_analysis` - User access patterns
- `metadata_analysis` - File metadata insights
- `access_patterns` - File access analytics
- `collaboration_insights` - File sharing analytics
- `performance_metrics` - System performance data

### 🔄 Analysis Workflows (5 Total)

- **`storage_optimization`** - Complete storage analysis and recommendations
- **`data_governance`** - Governance and compliance review
- **`security_assessment`** - Security-focused analysis
- **`cleanup_analysis`** - Data cleanup recommendations
- **`performance_review`** - Performance optimization insights

### 💬 Example Queries

**Natural Language Examples:**
```sql
"Show me the health status of the server"
"Run a storage optimization analysis"
"What are the largest files in the system?"
"Show me duplicate files that could be cleaned up"
"Run the data governance workflow"
"List all available reports"
"Validate this AQL query: SELECT name WHERE ClassID = 'idxobject' LIMIT 5"
"Execute this query and show results: SELECT extension, COUNT(*) WHERE ClassID = 'idxobject' GROUP BY extension"
```

## 🧪 Development & Testing

### Project Structure

```bash
aparavi_reporting_mcp/
├── src/aparavi_mcp/           # Main source code
│   ├── server.py              # MCP server implementation
│   ├── aparavi_client.py      # Aparavi Data Suite API client
│   ├── config.py              # Configuration management
│   └── utils.py               # Utility functions
├── config/                    # Configuration files
│   └── aparavi_reports.json   # Report and workflow definitions
├── scripts/                   # Utility scripts
│   ├── start_server.py        # Standalone server starter
│   ├── start_server_claude.py # Claude Desktop wrapper
│   ├── test_mcp_manual.py     # Manual MCP testing
│   ├── test_aql_validation.py # AQL validation testing
│   └── test_execute_custom_aql.py # Custom query testing
├── references/                # Documentation
│   └── aparavi_aql_reports.md # Comprehensive AQL reference
└── tests/                     # Test suite
```

### Running Tests

```bash
# Manual MCP server testing
python scripts/test_mcp_manual.py

# Test AQL validation functionality
python scripts/test_aql_validation.py

# Test custom query execution
python scripts/test_execute_custom_aql.py

# Simple validation test
python scripts/simple_mcp_test.py
```

## 🔧 Troubleshooting

### Common Issues

1. **Server Won't Start**
   - Check Python version (3.11+ required)
   - Verify virtual environment activation: `uv venv` then activate
   - Check `.env` file exists and has correct values

2. **Authentication Failed**
   - Verify Aparavi Data Suite credentials in `.env`
   - Test connectivity: `curl -u username:password http://localhost:80/server/api/v3/database/query`
   - Ensure Aparavi Data Suite server is running and accessible

3. **Claude Desktop Integration Issues**
   - Verify `claude_desktop_config.json` syntax is valid JSON
   - Use absolute paths in configuration
   - Restart Claude Desktop after config changes
   - Check Windows path escaping: `C:\\path\\to\\file`

4. **Query Execution Errors**
   - Use `validate_aql_query` tool to check syntax first
   - Remember: always include `ClassID = 'idxobject'` for file queries
   - No `COUNT(DISTINCT)` - use proper AQL syntax
   - Check Aparavi Data Suite server logs for detailed errors

5. **Unicode/Encoding Errors**
   - This project avoids Unicode emojis for Windows compatibility
   - If you see encoding errors, check for Unicode characters in logs

### Debug Mode

**Enable Debug Logging:**
```env
LOG_LEVEL=DEBUG
```

**Test Health Check:**
```bash
python -c "import asyncio; from src.aparavi_mcp.server import AparaviMCPServer; asyncio.run(AparaviMCPServer()._handle_health_check())"
```

## 📚 AQL Reference

### Core AQL Syntax Rules

The server uses Aparavi Data Suite Query Language (AQL) for data queries. Key syntax rules:

- **Always include:** `ClassID = 'idxobject'` for file queries
- **Field names:** `name`, `path`, `parentPath`, `size`, `extension`, `createTime`, `modifyTime`
- **Metadata filtering:** `metadata LIKE '%"Field":"Value"%'`
- **Size units:** 1073741824 = 1GB, 1048576 = 1MB
- **No SQL functions:** Avoid `COUNT(DISTINCT)`, use AQL-specific syntax
- **Classification:** `classification != 'Unclassified'` to exclude unclassified

### Example AQL Queries

**Basic file listing:**
```sql
SELECT name, size, extension 
WHERE ClassID = 'idxobject' 
LIMIT 10
```

**Large files analysis:**
```sql
SELECT name, size/1048576 AS "Size (MB)", path
WHERE ClassID = 'idxobject' 
  AND size > 104857600
ORDER BY size DESC
LIMIT 20
```

**File type distribution:**
```sql
SELECT extension, COUNT(*) AS "File Count", SUM(size)/1073741824 AS "Total Size (GB)"
WHERE ClassID = 'idxobject'
GROUP BY extension
ORDER BY "Total Size (GB)" DESC
```

**Metadata search:**
```sql
SELECT name, path
WHERE ClassID = 'idxobject'
  AND metadata LIKE '%"Author":"John Doe"%'
LIMIT 50
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch:** `git checkout -b feature/amazing-feature`
3. **Follow coding standards:**
   - Python 3.11+ syntax and type hints
   - Async/await for I/O operations
   - No Unicode emojis (Windows compatibility)
   - Comprehensive error handling
4. **Add tests** for new functionality
5. **Test thoroughly** with provided test scripts
6. **Commit changes:** `git commit -m 'Add amazing feature'`
7. **Push and create Pull Request**

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues:** [GitHub Issues](https://github.com/your-org/aparavi_reporting_mcp/issues)
- **Documentation:** [AQL Reference Guide](references/aparavi_aql_reports.md)
- **Testing:** Use provided test scripts in `scripts/` directory

---

**Built for seamless Aparavi Data Suite management through Claude Desktop** 🚀
