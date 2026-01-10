<#
.SYNOPSIS
    NeuralPath RAG Chatbot - Stop Production Stack
.DESCRIPTION
    Stops all Docker containers gracefully.
#>

param(
    [switch]$RemoveVolumes  # Also remove volumes (CAUTION: deletes data!)
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "Stopping NeuralPath production stack..." -ForegroundColor Yellow

Push-Location $projectRoot

try {
    if ($RemoveVolumes) {
        Write-Host "WARNING: This will delete all data!" -ForegroundColor Red
        $confirm = Read-Host "Type 'DELETE' to confirm"
        if ($confirm -ne "DELETE") {
            Write-Host "Aborted." -ForegroundColor Yellow
            exit 0
        }
        docker compose -f docker-compose.prod.yml --env-file .\.env.production down -v
    } else {
        docker compose -f docker-compose.prod.yml --env-file .\.env.production down
    }

    Write-Host "`n✓ Stack stopped successfully" -ForegroundColor Green

} finally {
    Pop-Location
}
