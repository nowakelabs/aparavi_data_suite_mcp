# APARAVI MCP Server

A Model Context Protocol (MCP) server that enables Claude Desktop users to query APARAVI data management systems through natural language. The server exposes 20 predefined APARAVI AQL (APARAVI Query Language) reports as MCP tools for seamless integration.

## 🚀 Features

- **Natural Language Queries**: Query APARAVI data using conversational language through Claude Desktop
- **20 Predefined Reports**: Access comprehensive data analysis reports including storage, optimization, and governance insights
- **Secure Authentication**: HTTP Basic Auth integration with APARAVI API
- **Intelligent Caching**: Built-in query result caching for improved performance
- **Error Handling**: Robust error handling with retry logic and detailed logging
- **Modern Python**: Built with Python 3.11+ using UV for fast dependency management

## 📋 Prerequisites

- Python 3.11 or higher
- UV package manager
- Access to an APARAVI data management system
- Claude Desktop (for MCP integration)

## 🛠️ Installation

### 1. Install UV (if not already installed)

**Windows:**
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

### 3. Configuration

Copy the environment template and configure your APARAVI connection:

```bash
cp .env.example .env
```

Edit `.env` with your APARAVI credentials:

```bash
APARAVI_HOST=your-aparavi-server
APARAVI_PORT=80
APARAVI_USERNAME=your_username
APARAVI_PASSWORD=your_password
```

Alternatively, use a YAML configuration file:

```bash
cp config/config.example.yaml config/config.yaml
# Edit config/config.yaml with your settings
```

## 🚀 Quick Start

### Start the MCP Server

```bash
# Using the startup script
python scripts/start_server.py

# Or directly
python -m aparavi_mcp.server

# With custom configuration
python scripts/start_server.py --config config/config.yaml --log-level DEBUG
```

### Test Server Health

The server provides basic health check and info tools for Phase 1:

- `health_check`: Verify server and APARAVI API connectivity
- `server_info`: Display server configuration information

## 🔧 Development

### Project Structure

```
aparavi_reporting_mcp/
├── src/aparavi_mcp/           # Main package
│   ├── server.py              # MCP server implementation
│   ├── aparavi_client.py      # APARAVI API client
│   ├── config.py              # Configuration management
│   ├── utils.py               # Utility functions
│   └── tools/                 # MCP tool definitions (Phase 2)
├── tests/                     # Test suite
├── config/                    # Configuration files
├── scripts/                   # Utility scripts
└── pyproject.toml            # Project configuration
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=aparavi_mcp

# Run specific test file
uv run pytest tests/test_server.py
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run flake8 src/ tests/

# Type checking
uv run mypy src/
```

## 📊 Available Reports (Phase 2)

The following APARAVI AQL reports will be available as MCP tools:

### Storage Analysis
1. Data Sources Overview
2. Subfolder Overview  
3. File Type/Extension Summary
4. Yearly Data Growth Report
5. Data Owner Summary

### Optimization
6. Duplicate File Summary
7. Duplicate File Summary - DETAILED
8. Large Files Report
9. Old Files Report
10. File Type/Extension Activity

### Governance & Compliance
11. Classification Summary by Data Source
12. Classifications by Age
13. Simple Classification Summary
14. PII Files Report
15. Sensitive Data Location Analysis

### Advanced Analytics
16. Storage Trend Analysis
17. Access Pattern Analysis
18. Data Lifecycle Insights
19. Compliance Risk Assessment
20. Custom Query Builder

## 🔐 Security

- HTTP Basic Authentication with APARAVI API
- Environment variable configuration for sensitive data
- Input sanitization and query validation
- Secure credential handling

## 📝 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APARAVI_HOST` | localhost | APARAVI server hostname |
| `APARAVI_PORT` | 80 | APARAVI server port |
| `APARAVI_USERNAME` | - | Authentication username |
| `APARAVI_PASSWORD` | - | Authentication password |
| `APARAVI_API_VERSION` | v3 | API version |
| `LOG_LEVEL` | INFO | Logging level |
| `CACHE_ENABLED` | true | Enable query caching |
| `CACHE_TTL` | 300 | Cache TTL in seconds |

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify APARAVI username/password in `.env`
   - Check APARAVI server accessibility

2. **Connection Refused**
   - Confirm APARAVI host/port settings
   - Verify network connectivity

3. **Module Import Errors**
   - Ensure virtual environment is activated
   - Run `uv pip install -e .` to install in development mode

### Debug Mode

Run with debug logging for detailed information:

```bash
python scripts/start_server.py --log-level DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

[License information to be added]

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review server logs for error details
- Contact the APARAVI support team

---

**Phase 1 Status**: ✅ Complete - Basic MCP server with health checks and configuration
**Phase 2 Status**: 🚧 In Development - APARAVI API integration and report tools
