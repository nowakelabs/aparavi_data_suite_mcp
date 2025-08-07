# Docker run script for Aparavi MCP Server
# PowerShell script for Windows environments

param(
    [ValidateSet("local", "http", "dev")]
    [string]$Mode = "local",
    [string]$EnvFile = ".env",
    [switch]$Build = $false,
    [switch]$Detached = $false,
    [switch]$Logs = $false
)

Write-Host "Running Aparavi MCP Server in Docker..." -ForegroundColor Green

# Set project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Change to project directory
Push-Location $ProjectRoot

try {
    # Check if .env file exists
    if (-not (Test-Path $EnvFile)) {
        Write-Host "Environment file '$EnvFile' not found. Creating from template..." -ForegroundColor Yellow
        
        if (Test-Path ".env.docker") {
            Copy-Item ".env.docker" $EnvFile
            Write-Host "Copied .env.docker to $EnvFile" -ForegroundColor Green
        } elseif (Test-Path ".env.example") {
            Copy-Item ".env.example" $EnvFile
            Write-Host "Copied .env.example to $EnvFile" -ForegroundColor Green
        } else {
            Write-Host "No template environment file found. Please create $EnvFile manually." -ForegroundColor Red
            exit 1
        }
    }

    # Build command arguments
    $ComposeArgs = @("docker-compose")
    
    # Add environment file
    $ComposeArgs += "--env-file", $EnvFile
    
    # Add profile for specific modes
    if ($Mode -eq "http") {
        $ComposeArgs += "--profile", "http"
    } elseif ($Mode -eq "dev") {
        $ComposeArgs += "--profile", "dev"
    }
    
    # Build if requested
    if ($Build) {
        Write-Host "Building Docker images..." -ForegroundColor Yellow
        $BuildCommand = $ComposeArgs + @("build")
        & $BuildCommand[0] $BuildCommand[1..($BuildCommand.Length-1)]
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Docker build failed" -ForegroundColor Red
            exit $LASTEXITCODE
        }
    }
    
    # Show logs if requested
    if ($Logs) {
        $ServiceName = switch ($Mode) {
            "local" { "aparavi-mcp-local" }
            "http" { "aparavi-mcp-http" }
            "dev" { "aparavi-mcp-dev" }
        }
        
        Write-Host "Showing logs for $ServiceName..." -ForegroundColor Yellow
        $LogsCommand = $ComposeArgs + @("logs", "-f", $ServiceName)
        & $LogsCommand[0] $LogsCommand[1..($LogsCommand.Length-1)]
        return
    }
    
    # Run the appropriate service
    $ServiceName = switch ($Mode) {
        "local" { "aparavi-mcp-local" }
        "http" { "aparavi-mcp-http" }
        "dev" { "aparavi-mcp-dev" }
    }
    
    $RunArgs = @("up")
    if ($Detached) {
        $RunArgs += "-d"
    }
    $RunArgs += $ServiceName
    
    $RunCommand = $ComposeArgs + $RunArgs
    
    Write-Host "Starting service: $ServiceName" -ForegroundColor Yellow
    Write-Host "Command: $($RunCommand -join ' ')" -ForegroundColor Gray
    
    & $RunCommand[0] $RunCommand[1..($RunCommand.Length-1)]
    
    if ($LASTEXITCODE -eq 0 -and $Detached) {
        Write-Host "`nService started successfully in detached mode" -ForegroundColor Green
        Write-Host "To view logs: docker-compose logs -f $ServiceName" -ForegroundColor Yellow
        Write-Host "To stop: docker-compose down" -ForegroundColor Yellow
        
        if ($Mode -eq "http") {
            $Port = (Get-Content $EnvFile | Where-Object { $_ -match "^MCP_HTTP_PORT=" }) -replace "MCP_HTTP_PORT=", ""
            if (-not $Port) { $Port = "8080" }
            Write-Host "HTTP server available at: http://localhost:$Port" -ForegroundColor Cyan
            Write-Host "API docs at: http://localhost:$Port/docs" -ForegroundColor Cyan
        }
    }
    
} catch {
    Write-Host "Error running Docker container: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}
