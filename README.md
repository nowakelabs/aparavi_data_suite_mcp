# Aparavi Data Suite MCP Server

**Talk to your enterprise data using natural language with Claude Desktop.**

This MCP server connects Claude Desktop to your Aparavi Data Suite, enabling you to:
- 💬 Ask questions about your data in plain English
- 📊 Run compliance and analytics reports
- 🔍 Find files, duplicates, and sensitive data
- 🏷️ Manage data classification and tagging

## 🚀 Quick Start

**Ready to get started?** Follow these 3 simple steps:

1. **Install Aparavi Data Suite** (see Prerequisites below)
2. **Choose your deployment method** (Docker recommended)
3. **Configure Claude Desktop** (copy provided config file)

**That's it!** Start asking Claude questions about your data.

## 📋 Prerequisites

### Step 1: Install Aparavi Data Suite

**⚠️ Required:** You need Aparavi Data Suite running before using this MCP server.

👉 **[Download Aparavi Data Suite Baseline](https://aparavi.com/download-aparavi-data-suite-baseline/)** 👈

**What is Aparavi Data Suite?**
A comprehensive data intelligence platform for enterprise data discovery, classification, governance, and compliance reporting.

**Setup Checklist:**
1. ✅ Install Aparavi Data Suite from the link above
2. ✅ Configure your data sources
3. ✅ Verify it's running at `http://localhost:80`
4. ✅ Note your login credentials (default: root/root)

---

## 🚀 What You Can Do

**Ask Claude questions like:**
- "Show me all duplicate files in our system"
- "Find sensitive data that needs classification"
- "What's our storage usage by department?"
- "Tag all Excel files from Q4 2024 as 'financial'"

**Available Tools:**
- 📊 **20+ Pre-built Reports** - Compliance, storage, duplicates, and more
- 🔍 **Custom Queries** - Ask anything about your data in natural language
- 🏷️ **File Tagging** - Organize and classify your data
- ✅ **Health Monitoring** - Check system status and connectivity

**New to this?** Just ask Claude "Help me get started with Aparavi" and it will guide you!

## 🛠️ Step 2: Choose Your Deployment Method

### Option A: Docker (Recommended) 🐳

**Easiest setup - works on Windows, Mac, and Linux:**

1. **Install Docker Desktop**
2. **Copy the config file:**
   ```bash
   # Download this repo
   git clone https://github.com/nowakelabs/aparavi_data_suite_mcp.git
   
   # Copy Docker config to Claude Desktop
   cp claudedesktop/claude_desktop_config_docker.json ~/.config/Claude/claude_desktop_config.json
   ```
3. **Restart Claude Desktop** - That's it!

### Option B: Local Development 💻

**For developers who want to modify the code:**

1. **Install Python 3.11+** and **UV package manager**
2. **Clone and setup:**
   ```bash
   git clone https://github.com/nowakelabs/aparavi_data_suite_mcp.git
   cd aparavi_data_suite_mcp
   uv sync
   ```
3. **Copy the appropriate config:**
   - **Windows:** `claudedesktop/claude_desktop_config_windows.json`
   - **Mac:** `claudedesktop/claude_desktop_config_mac.json`
## 🎯 Step 3: Configure Claude Desktop

**Copy the right config file for your setup:**

- **Docker:** Copy `claudedesktop/claude_desktop_config_docker.json`
- **Windows Local:** Copy `claudedesktop/claude_desktop_config_windows.json`
- **Mac Local:** Copy `claudedesktop/claude_desktop_config_mac.json`

**To your Claude Desktop config location:**
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/.config/Claude/claude_desktop_config.json`

**Restart Claude Desktop** and you're ready to go!

---

## 💬 Using the MCP Server

**Once everything is set up, just talk to Claude naturally:**

- "Show me duplicate files in our system"
- "What's our storage usage by department?"
- "Find all Excel files created last month"
- "Help me tag sensitive documents"
- "Run a compliance report"

**Need help getting started?** Ask Claude: *"Help me get started with Aparavi"*

---

## 🔧 Troubleshooting

**Common Issues:**

1. **"Can't connect to Aparavi"**
   - Make sure Aparavi Data Suite is running at `http://localhost:80`
   - Check your username/password (default: root/root)

2. **"MCP server won't start"**
   - For Docker: Make sure Docker Desktop is running
   - For Local: Make sure Python 3.11+ and UV are installed

3. **"Claude doesn't see the server"**
   - Check that you copied the config file to the right location
   - Restart Claude Desktop after copying the config

**Still having issues?** Contact: ask@nowakelabs.com

---

## 📚 Advanced Documentation

For detailed technical information:
- **Docker Deployment:** See `DOCKER.md`
- **API Reference:** Check the source code documentation
- **Custom Development:** Review the development setup in the repository

**Sample Config:** `claudedesktop/claude_desktop_config_docker.json`

```json
{
  "mcpServers": {
    "aparavi-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e", "APARAVI_HOST=host.docker.internal",
        "-e", "APARAVI_PORT=80",
        "-e", "APARAVI_USERNAME=root",
        "-e", "APARAVI_PASSWORD=root",
        "-e", "APARAVI_API_VERSION=v3",
        "-e", "LOG_LEVEL=INFO",
        "nowakelabs/aparavi-mcp-server:latest",
        "python", "/app/scripts/start_server.py"
      ]
    }
  }
}
```

##### Option 2: Local Windows Development

Uses local Python virtual environment on Windows.

**Sample Config:** `claudedesktop/claude_desktop_config_windows.json`

```json
{
  "mcpServers": {
    "aparavi-mcp-server": {
      "command": "c:\\path\\to\\aparavi_reporting_mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "c:\\path\\to\\aparavi_reporting_mcp\\scripts\\start_server.py"
      ],
      "cwd": "c:\\path\\to\\aparavi_reporting_mcp",
      "env": {
        "APARAVI_HOST": "localhost",
        "APARAVI_PORT": "80",
        "APARAVI_API_VERSION": "v3",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

##### Option 3: Local macOS Development

Uses local Python virtual environment on macOS.

**Sample Config:** `claudedesktop/claude_desktop_config_mac.json`

```json
{
  "mcpServers": {
    "aparavi-mcp-server": {
      "command": "~/Documents/GitHub/aparavi_reporting_mcp/.venv/bin/python",
      "args": [
        "~/Documents/GitHub/aparavi_reporting_mcp/scripts/start_server.py"
      ],
      "cwd": "~/Documents/GitHub/aparavi_reporting_mcp",
      "env": {
        "APARAVI_HOST": "localhost",
        "APARAVI_PORT": "80",
        "APARAVI_API_VERSION": "v3",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

##### Configuration Setup Instructions

1. **Choose your deployment method** from the three options above
2. **Copy the appropriate sample config** from the `claudedesktop/` directory
3. **Update the configuration** with your specific paths and credentials
4. **Place the config file** in the correct Claude Desktop location:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`
5. **Restart Claude Desktop** to load the new configuration

##### Configuration Notes by Deployment Type

**Docker Deployment:**
- ✅ Uses `host.docker.internal` to connect to Aparavi server on host machine
- ✅ Runs container with `--rm` flag for automatic cleanup
- ✅ Interactive mode (`-i`) for MCP protocol communication
- ✅ All credentials passed as environment variables
- ✅ No need for local Python/UV installation
- ✅ Uses pre-built `nowakelabs/aparavi-mcp-server:latest` image

**Local Development (Windows/Mac):**
- ⚠️ Requires local Python environment setup with UV
- ⚠️ Must update file paths to match your local installation
- ⚠️ Uses `localhost` to connect to local Aparavi server
- ✅ Direct access to code for debugging and development
- ✅ Faster iteration for code changes

#### Docker vs Local Deployment

| Feature | Local (UV/Python) | Docker |
|---------|-------------------|--------|
| **Setup Complexity** | Medium (requires UV, Python, venv) | Low (just Docker) |
| **Isolation** | Uses local Python environment | Fully containerized |
| **Networking** | Direct localhost connection | Uses Docker networking |
| **Updates** | `uv sync` to update deps | Rebuild Docker image |
| **Debugging** | Direct access to logs/code | Container logs via Docker |
| **Portability** | Requires Python setup | Runs anywhere with Docker |

**Choose Docker if:**
- You prefer containerized deployments
- Want to avoid local Python environment setup
- Need consistent deployment across environments
- Already using Docker for other services

**Choose Local if:**
- You want direct access to code for debugging
- Prefer faster iteration during development
- Don't want Docker overhead
- Need to modify code frequently

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

#### 1. `guide_start_here`
**Purpose:** 🌟 **START HERE** - Intelligent entry point and routing assistant  
**Parameters:**
- `user_experience` (optional): "new", "intermediate", "advanced", or "unknown"
- `query_goal` (optional): "duplicates", "growth", "security", "exploration", "custom", "troubleshooting", or "unknown"
- `preferred_approach` (optional): "reports", "custom_queries", "guided", or "unknown"
- `context_window` (optional): "small", "medium", "large", or "unknown"
- `specific_question` (optional): Describe your specific data analysis question or challenge

**Features:**
- Assesses your experience level and analysis goals
- Provides personalized step-by-step workflows
- Adapts response complexity to your preferences
- Routes you to the optimal tool sequence
- Perfect for new users or complex analysis planning

#### 2. `health_check`
**Purpose:** Comprehensive server health monitoring  
**Parameters:** None  
**Features:**
- API connectivity testing
- AQL query validation for all configured reports
- Configuration validation
- Detailed status reporting

#### 3. `server_info`
**Purpose:** Detailed server configuration and capabilities  
**Parameters:** None  
**Returns:** Server version, configuration, loaded reports count

#### 4. `run_aparavi_report`
**Purpose:** Execute predefined reports and analysis workflows  
**Parameters:**
- `report_name` (optional): Specific report name or "list"
- `workflow_name` (optional): Workflow name or "list"

#### 5. `validate_aql_query`
**Purpose:** Validate custom AQL queries without execution  
**Parameters:**
- `query` (required): AQL query string to validate
**Returns:** Validation status, syntax errors, recommendations

#### 6. `execute_custom_aql_query`
**Purpose:** Validate and execute custom AQL queries  
**Parameters:**
- `query` (required): AQL query string to validate and execute
**Returns:** Raw JSON results for LLM interpretation

#### 7. `generate_aql_query`
**Purpose:** Intelligent AQL query builder for custom analysis  
**Parameters:**
- `business_question` (required): The specific business question or data analysis need
- `desired_fields` (optional): Specific fields/columns desired in the output
- `filters` (optional): Specific filter conditions
- `complexity_preference` (optional): "simple" or "comprehensive" approach
**Features:**
- Generates valid AQL syntax from natural language
- Prevents common syntax errors (DISTINCT, DATEADD, invalid fields)
- Provides detailed explanations and field validation
- Recommends query chaining for complex analysis

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
