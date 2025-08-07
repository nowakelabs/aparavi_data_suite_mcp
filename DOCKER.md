# Docker Deployment for Aparavi Data Suite MCP Server

This document describes how to deploy the Aparavi Data Suite MCP Server using Docker for cross-platform compatibility and easy deployment.

## Overview

The Docker deployment provides a streamlined HTTP-based MCP server that can be easily integrated with Claude Desktop and other MCP clients. The Docker approach offers:

- **Cross-platform compatibility** (Windows, macOS, Linux)
- **Simplified deployment** with pre-built images
- **Consistent environment** across different systems
- **Easy integration** with Claude Desktop

## Quick Start

### Prerequisites

- Docker installed on your system
- Aparavi Data Suite server running and accessible
- [Download Aparavi Data Suite Baseline](https://aparavi.com/download-aparavi-data-suite-baseline/) if not already installed

### Using Pre-built Docker Image

**Run the MCP server directly:**
```bash
docker run --rm -i \
  -e APARAVI_HOST=host.docker.internal \
  -e APARAVI_PORT=80 \
  -e APARAVI_USERNAME=root \
  -e APARAVI_PASSWORD=root \
  -e APARAVI_CLIENT_OBJECT_ID=43225572-pltf-4336-af95-2aed2eb00810 \
  -e LOG_LEVEL=INFO \
  nowakelabs/aparavi-mcp-server:latest \
  python /app/scripts/start_server.py
```

### Using Docker Compose

**Run with docker-compose:**
```bash
docker-compose up aparavi-mcp-server
```

## Claude Desktop Integration

The Docker deployment is designed to work seamlessly with Claude Desktop. Use the provided configuration file:

**Copy the Docker configuration:**
```bash
cp claudedesktop/claude_desktop_config_docker.json ~/.config/Claude/claude_desktop_config.json
```

**Or manually add to your Claude Desktop config:**
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
        "-e", "APARAVI_CLIENT_OBJECT_ID=43225572-pltf-4336-af95-2aed2eb00810",
        "-e", "LOG_LEVEL=INFO",
        "nowakelabs/aparavi-mcp-server:latest",
        "python", "/app/scripts/start_server.py"
      ]
    }
  }
}
```

## Building from Source

### Local Build

**Build the Docker image:**
```bash
.\scripts\docker-build.ps1
```

**Build with custom tag:**
```bash
.\scripts\docker-build.ps1 -Tag "my-aparavi-mcp:v1.0"
```

### Multi-Platform Build

**Build for multiple platforms:**
```bash
.\scripts\docker-build.ps1 -MultiPlatform
```

**Build and push to registry:**
```bash
.\scripts\docker-build.ps1 -MultiPlatform -Push -Registry "myregistry.com"
```
## Configuration

### Environment Variables

The Docker deployment uses these essential environment variables:

```bash
# Aparavi API Configuration
APARAVI_HOST=host.docker.internal  # Use this for local Aparavi server
APARAVI_PORT=80
APARAVI_USERNAME=root
APARAVI_PASSWORD=root
APARAVI_CLIENT_OBJECT_ID=43225572-pltf-4336-af95-2aed2eb00810

# Logging Configuration
LOG_LEVEL=INFO
```

### Customizing Configuration

**For different Aparavi servers:**
```bash
# Remote Aparavi server
APARAVI_HOST=your-aparavi-server.com
APARAVI_PORT=443

# Different credentials
APARAVI_USERNAME=your-username
APARAVI_PASSWORD=your-password

# Your specific Client Object ID
APARAVI_CLIENT_OBJECT_ID=your-client-object-id
```

## Networking

### Local Aparavi Server Access

When running Aparavi Data Suite locally, use `host.docker.internal` as the hostname:

```bash
APARAVI_HOST=host.docker.internal
```

### Remote Aparavi Server Access

For remote Aparavi servers, use the actual hostname or IP:

```bash
APARAVI_HOST=aparavi.company.com
APARAVI_PORT=443  # Use HTTPS port for remote servers
```

## Troubleshooting

### Common Issues

1. **Connection to Aparavi server fails:**
   - Check `APARAVI_HOST` setting
   - Verify network connectivity
   - Use `host.docker.internal` for local servers
   - Ensure Aparavi Data Suite is running

2. **Authentication errors:**
   - Verify `APARAVI_USERNAME` and `APARAVI_PASSWORD`
   - Check that credentials work with Aparavi Data Suite directly

3. **Claude Desktop integration issues:**
   - Ensure Docker is running and accessible
   - Check that the Docker image is available
   - Verify environment variables in Claude Desktop config

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Run with debug logging
docker run --rm -i \
  -e APARAVI_HOST=host.docker.internal \
  -e APARAVI_PORT=80 \
  -e APARAVI_USERNAME=root \
  -e APARAVI_PASSWORD=root \
  -e APARAVI_CLIENT_OBJECT_ID=43225572-pltf-4336-af95-2aed2eb00810 \
  -e LOG_LEVEL=DEBUG \
  nowakelabs/aparavi-mcp-server:latest \
  python /app/scripts/start_server.py
```

## Platform-Specific Notes

### Windows
- Use the provided `claude_desktop_config_windows.json` for local development
- Docker Desktop must be running for Docker deployment
- Use `%USERPROFILE%\Documents\GitHub\aparavi_data_suite_mcp` paths

### macOS
- Use the provided `claude_desktop_config_mac.json` for local development
- Docker Desktop must be running for Docker deployment
- Use `~/Documents/GitHub/aparavi_data_suite_mcp` paths

### Linux
- Docker deployment works out of the box
- Adjust paths in local configs as needed for your distribution

## Support

For issues and support:
- Check the main README.md for comprehensive setup instructions
- Ensure Aparavi Data Suite is properly installed and configured
- Verify all environment variables are correctly set
- Contact: support@aparavi.com

The Docker implementation maintains full compatibility with the local gold standard while providing additional deployment flexibility.
