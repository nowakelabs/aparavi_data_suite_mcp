# Docker Support for Aparavi MCP Server

This document describes how to run the Aparavi MCP Server in Docker containers while maintaining the local implementation as the gold standard.

## Overview

The Docker implementation provides three deployment modes:

1. **Local Mode** (`aparavi-mcp-local`) - Stdio-based MCP protocol (default, matches local behavior)
2. **HTTP Mode** (`aparavi-mcp-http`) - HTTP-based MCP protocol for remote access
3. **Development Mode** (`aparavi-mcp-dev`) - Live code mounting for development

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Aparavi Data Suite server accessible from Docker containers

### Basic Setup

1. **Copy environment configuration:**
   ```bash
   cp .env.docker .env
   # Edit .env with your Aparavi server details
   ```

2. **Build and run in local mode:**
   ```bash
   docker-compose up --build aparavi-mcp-local
   ```

3. **For HTTP mode (remote access):**
   ```bash
   docker-compose --profile http up --build aparavi-mcp-http
   ```

## Deployment Modes

### Local Mode (Default)

This mode preserves the original stdio-based MCP protocol, maintaining full compatibility with the local implementation.

```bash
# Run local mode
docker-compose up aparavi-mcp-local

# Run in background
docker-compose up -d aparavi-mcp-local
```

**Use Cases:**
- Direct replacement for local server
- Testing containerized deployment
- Consistent behavior with local gold standard

### HTTP Mode

Provides HTTP-based MCP protocol for remote access and web integration.

```bash
# Run HTTP mode
docker-compose --profile http up aparavi-mcp-http

# Access endpoints
curl http://localhost:8080/health
curl http://localhost:8080/info
```

**Available Endpoints:**
- `GET /health` - Health check
- `GET /info` - Server information
- `GET /docs` - API documentation
- `POST /mcp/tools/list` - List available tools
- `POST /mcp/tools/call` - Call specific tool
- `POST /mcp/resources/list` - List resources
- `POST /mcp/resources/read` - Read resource
- `POST /mcp/prompts/list` - List prompts
- `POST /mcp/prompts/get` - Get prompt

**Use Cases:**
- Remote MCP server access
- Web application integration
- API-based tool calling

### Development Mode

Mounts source code for live development and debugging.

```bash
# Run development mode
docker-compose --profile dev up aparavi-mcp-dev

# Code changes are immediately reflected
```

**Features:**
- Live code mounting
- Debug logging enabled
- Caching disabled for development
- Full development dependencies

## Configuration

### Environment Variables

The Docker deployment uses the same environment variables as the local version:

```bash
# Aparavi API Configuration
APARAVI_HOST=host.docker.internal  # Use this for local Aparavi server
APARAVI_PORT=80
APARAVI_USERNAME=root
APARAVI_PASSWORD=root
APARAVI_API_VERSION=v3
APARAVI_TIMEOUT=30
APARAVI_MAX_RETRIES=3
APARAVI_CLIENT_OBJECT_ID=your-client-id

# MCP Server Configuration
MCP_SERVER_NAME=aparavi-mcp-server-docker
MCP_SERVER_VERSION=0.1.0
LOG_LEVEL=INFO
CACHE_ENABLED=true
CACHE_TTL=300

# Docker-specific settings
MCP_HTTP_PORT=8080
MCP_SERVER_MODE=local
```

### Network Configuration

The Docker setup includes:
- Custom bridge network (`aparavi-mcp-network`)
- Host networking support for local Aparavi server access
- Port mapping for HTTP mode

### Volume Mounts

- `./logs:/app/logs` - Log files
- `./data:/app/data` - Data persistence
- `./.env:/app/.env:ro` - Environment configuration (read-only)

## PowerShell Scripts

### Build Script

```powershell
# Build Docker image
.\scripts\docker-build.ps1

# Build without cache
.\scripts\docker-build.ps1 -NoBuildCache

# Build development image
.\scripts\docker-build.ps1 -Development
```

### Run Script

```powershell
# Run in local mode
.\scripts\docker-run.ps1 -Mode local

# Run in HTTP mode
.\scripts\docker-run.ps1 -Mode http

# Run in development mode
.\scripts\docker-run.ps1 -Mode dev

# Build and run in background
.\scripts\docker-run.ps1 -Mode http -Build -Detached

# View logs
.\scripts\docker-run.ps1 -Mode local -Logs
```

## Networking Considerations

### Local Aparavi Server Access

When running Aparavi Data Suite locally, use `host.docker.internal` as the hostname:

```bash
APARAVI_HOST=host.docker.internal
```

### Remote Aparavi Server Access

For remote Aparavi servers, use the actual hostname or IP:

```bash
APARAVI_HOST=aparavi.company.com
```

### Port Mapping

- HTTP mode exposes port 8080 by default
- Customize with `MCP_HTTP_PORT` environment variable
- Local and dev modes use stdio (no port exposure needed)

## Comparison with Local Implementation

| Feature | Local (Gold Standard) | Docker Local Mode | Docker HTTP Mode |
|---------|----------------------|-------------------|------------------|
| Protocol | stdio MCP | stdio MCP | HTTP MCP |
| Performance | Native | Near-native | HTTP overhead |
| Networking | Direct | Container network | HTTP endpoints |
| Deployment | Local Python | Container | Container |
| Development | Direct editing | Volume mounts | Volume mounts |
| Claude Integration | Direct | Via container | Via HTTP calls |

## Health Monitoring

### Health Checks

The Docker image includes built-in health checks:

```bash
# Check container health
docker-compose ps

# View health check logs
docker inspect aparavi-mcp-local --format='{{.State.Health.Status}}'
```

### Logging

Logs are available through Docker and mounted volumes:

```bash
# View container logs
docker-compose logs -f aparavi-mcp-local

# View log files
tail -f logs/aparavi-mcp-server.log
```

## Troubleshooting

### Common Issues

1. **Connection to Aparavi server fails:**
   - Check `APARAVI_HOST` setting
   - Verify network connectivity
   - Use `host.docker.internal` for local servers

2. **Permission errors:**
   - Ensure log and data directories are writable
   - Check user permissions in container

3. **Port conflicts:**
   - Change `MCP_HTTP_PORT` if 8080 is in use
   - Check for other services using the same port

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set debug level
LOG_LEVEL=DEBUG docker-compose up aparavi-mcp-local

# Or edit .env file
echo "LOG_LEVEL=DEBUG" >> .env
```

## Security Considerations

- Container runs as non-root user (`aparavi`)
- Environment files should not be committed with secrets
- Use Docker secrets for production deployments
- Configure CORS appropriately for HTTP mode
- Limit network access as needed

## Production Deployment

For production use:

1. Use specific image tags (not `latest`)
2. Configure proper secrets management
3. Set up log rotation
4. Monitor container health
5. Use orchestration platform (Kubernetes, Docker Swarm)
6. Configure backup for data volumes

## Migration from Local

To migrate from local to Docker deployment:

1. Export current configuration to `.env`
2. Test with local mode first
3. Verify all tools work correctly
4. Switch to HTTP mode if remote access needed
5. Update Claude Desktop configuration if necessary

The Docker implementation maintains full compatibility with the local gold standard while providing additional deployment flexibility.
