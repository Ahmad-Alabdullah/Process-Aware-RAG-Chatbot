<#
.SYNOPSIS
    NeuralPath RAG Chatbot - Start Production Stack
.DESCRIPTION
    Starts all Docker containers for production deployment.
#>

param(
    [switch]$Pull,      # Pull latest images before starting
    [switch]$Detach,    # Run in detached mode (default)
    [switch]$Logs       # Follow logs after starting
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path $PSScriptRoot -Parent

Write-Host @"

 _   _                      ____       _   _     
| \ | | ___ _   _ _ __ __ _|  _ \ __ _| |_| |__  
|  \| |/ _ \ | | | '__/ _` | |_) / _` | __| '_ \ 
| |\  |  __/ |_| | | | (_| |  __/ (_| | |_| | | |
|_| \_|\___|\__,_|_|  \__,_|_|   \__,_|\__|_| |_|
                                                 
              Starting Production Stack...

"@ -ForegroundColor Cyan

# Change to project root
Push-Location $projectRoot

try {
    # Check for .env.production
    if (-not (Test-Path ".env.production")) {
        Write-Host "Error: .env.production not found!" -ForegroundColor Red
        Write-Host "Run .\deploy\setup-windows.ps1 first" -ForegroundColor Yellow
        exit 1
    }

    # Create external volumes if they don't exist
    Write-Host "`nCreating Docker volumes if needed..." -ForegroundColor Yellow
    $volumes = @("server_pgdata", "server_osdata", "server_qdrant", "server_neo4j", "server_ollama")
    foreach ($vol in $volumes) {
        $exists = docker volume ls --format "{{.Name}}" | Where-Object { $_ -eq $vol }
        if (-not $exists) {
            Write-Host "  Creating volume: $vol" -ForegroundColor Gray
            docker volume create $vol | Out-Null
        }
    }
    Write-Host "  ✓ Volumes ready" -ForegroundColor Green

    # Pull latest images if requested
    if ($Pull) {
        Write-Host "`nPulling latest images..." -ForegroundColor Yellow
        docker compose -f docker-compose.prod.yml --env-file .\.env.production pull
    }

    # Start the stack
    Write-Host "`nStarting containers..." -ForegroundColor Yellow
    docker compose -f docker-compose.prod.yml --env-file .\.env.production up -d

    Write-Host "`n" + "="*50 -ForegroundColor Green
    Write-Host "Stack started successfully!" -ForegroundColor Green
    Write-Host "="*50 -ForegroundColor Green

    # Show status
    Write-Host "`nContainer Status:" -ForegroundColor Cyan
    docker compose -f docker-compose.prod.yml ps

    Write-Host @"

Access Points:
  - Local Frontend: http://localhost
  - Local API:      http://localhost:8080
  - External:       https://neurapath.de (after Cloudflare setup)

Useful commands:
  - View logs:      docker compose -f docker-compose.prod.yml logs -f
  - Stop stack:     docker compose -f docker-compose.prod.yml down
  - Restart:        docker compose -f docker-compose.prod.yml restart

"@ -ForegroundColor White

    # Follow logs if requested
    if ($Logs) {
        Write-Host "Following logs... (Ctrl+C to exit)" -ForegroundColor Yellow
        docker compose -f docker-compose.prod.yml logs -f
    }

} finally {
    Pop-Location
}
