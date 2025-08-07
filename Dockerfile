# Multi-stage build for Aparavi MCP Server
# Stage 1: Build stage with all dependencies
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Stage 2: Runtime stage
FROM python:3.11-slim as runtime

# Set runtime arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r aparavi && useradd -r -g aparavi -s /bin/bash aparavi

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY references/ ./references/
COPY scripts/ ./scripts/

# Copy configuration files
COPY .env.example ./
COPY pyproject.toml ./

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data && \
    chown -R aparavi:aparavi /app

# Switch to non-root user
USER aparavi

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose port for HTTP mode (if implemented)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); from aparavi_mcp.server import AparaviMCPServer; print('Health check passed')" || exit 1

# Default command - can be overridden for different modes
CMD ["python", "-m", "aparavi_mcp.server"]
