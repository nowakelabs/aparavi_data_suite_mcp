# Docker build script for Aparavi MCP Server (HTTP Mode Only)
# PowerShell script for Windows environments

param(
    [string]$Tag = "aparavi-mcp-server:latest",
    [switch]$NoBuildCache = $false
)

Write-Host "Building Aparavi MCP Server Docker image (HTTP Mode)..." -ForegroundColor Green

# Set build context to project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Build arguments
$BuildArgs = @()
if ($NoBuildCache) {
    $BuildArgs += "--no-cache"
}

# Build the Docker image
$BuildCommand = @(
    "docker", "build"
    $BuildArgs
    "-t", $Tag
    "-f", "Dockerfile"
    $ProjectRoot
)

Write-Host "Running: $($BuildCommand -join ' ')" -ForegroundColor Yellow

try {
    & $BuildCommand[0] $BuildCommand[1..($BuildCommand.Length-1)]
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Successfully built Docker image: $Tag" -ForegroundColor Green
        
        # Show image info
        Write-Host "`nImage information:" -ForegroundColor Cyan
        docker images $Tag --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        
        Write-Host "`nTo run the container:" -ForegroundColor Yellow
        Write-Host "docker-compose up aparavi-mcp-server" -ForegroundColor White
        Write-Host "# Server will be available at http://localhost:8080" -ForegroundColor Gray
        
    } else {
        Write-Host "Docker build failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "Error during Docker build: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
