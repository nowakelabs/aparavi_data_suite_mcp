# Docker build script for Aparavi MCP Server (HTTP Mode Only)
# PowerShell script with Buildx multi-platform support

param(
    [string]$Tag = "nowakelabs/aparavi-mcp-server:latest",
    [switch]$NoBuildCache = $false,
    [switch]$MultiPlatform = $false,
    [switch]$Push = $false,
    [string]$Registry = ""
)

Write-Host "Building Aparavi MCP Server Docker image (HTTP Mode)..." -ForegroundColor Green

# Set build context to project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Initialize Buildx if not already done
Write-Host "Checking Docker Buildx setup..." -ForegroundColor Yellow
try {
    $BuilderExists = docker buildx ls | Select-String "aparavi-builder"
    if (-not $BuilderExists) {
        Write-Host "Creating Buildx builder instance..." -ForegroundColor Yellow
        docker buildx create --name aparavi-builder --use
        docker buildx inspect --bootstrap
    } else {
        Write-Host "Using existing Buildx builder..." -ForegroundColor Green
        docker buildx use aparavi-builder
    }
} catch {
    Write-Host "Warning: Could not set up Buildx builder, using default" -ForegroundColor Yellow
}

# Build arguments
$BuildArgs = @()
if ($NoBuildCache) {
    $BuildArgs += "--no-cache"
}

# Multi-platform support
if ($MultiPlatform) {
    $BuildArgs += "--platform", "linux/amd64,linux/arm64"
    Write-Host "Building for multiple platforms: linux/amd64, linux/arm64" -ForegroundColor Cyan
}

# Registry and push support
$FinalTag = $Tag
if ($Registry) {
    $FinalTag = "$Registry/$Tag"
    Write-Host "Using registry: $Registry" -ForegroundColor Cyan
}

if ($Push) {
    $BuildArgs += "--push"
    Write-Host "Will push to registry after build" -ForegroundColor Cyan
} else {
    $BuildArgs += "--load"
}

# Build the Docker image using Buildx
$BuildCommand = @(
    "docker", "buildx", "build"
    $BuildArgs
    "-t", $FinalTag
    "-f", "Dockerfile"
    $ProjectRoot
)

Write-Host "Running: $($BuildCommand -join ' ')" -ForegroundColor Yellow

try {
    & $BuildCommand[0] $BuildCommand[1..($BuildCommand.Length-1)]
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Successfully built Docker image: $FinalTag" -ForegroundColor Green
        
        if (-not $Push) {
            # Show image info for local builds
            Write-Host "`nImage information:" -ForegroundColor Cyan
            docker images $FinalTag --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        }
        
        Write-Host "`nUsage Examples:" -ForegroundColor Yellow
        Write-Host "# Local single-platform build:" -ForegroundColor Gray
        Write-Host ".\scripts\docker-build.ps1" -ForegroundColor White
        Write-Host "# Multi-platform build:" -ForegroundColor Gray
        Write-Host ".\scripts\docker-build.ps1 -MultiPlatform" -ForegroundColor White
        Write-Host "# Build and push to registry:" -ForegroundColor Gray
        Write-Host ".\scripts\docker-build.ps1 -MultiPlatform -Push -Registry 'your-registry.com'" -ForegroundColor White
        
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
