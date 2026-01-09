<#
.SYNOPSIS
    NeuralPath RAG Chatbot - Windows Setup Script
.DESCRIPTION
    Validates prerequisites and prepares the system for production deployment.
#>

param(
    [switch]$SkipDocker,
    [switch]$SkipGPU
)

$ErrorActionPreference = "Stop"

Write-Host @"

 _   _                      ____       _   _     
| \ | | ___ _   _ _ __ __ _|  _ \ __ _| |_| |__  
|  \| |/ _ \ | | | '__/ _` | |_) / _` | __| '_ \ 
| |\  |  __/ |_| | | | (_| |  __/ (_| | |_| | | |
|_| \_|\___|\__,_|_|  \__,_|_|   \__,_|\__|_| |_|
                                                 
              Production Setup Script

"@ -ForegroundColor Cyan

# ============================================
# Check Docker Desktop
# ============================================
Write-Host "`n[1/4] Checking Docker Desktop..." -ForegroundColor Yellow

if (-not $SkipDocker) {
    try {
        $dockerVersion = docker --version
        Write-Host "  ✓ Docker found: $dockerVersion" -ForegroundColor Green
        
        # Check if Docker is running
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
            exit 1
        }
        Write-Host "  ✓ Docker is running" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Docker not found. Please install Docker Desktop from https://docker.com/products/docker-desktop" -ForegroundColor Red
        exit 1
    }
}

# ============================================
# Check NVIDIA GPU
# ============================================
Write-Host "`n[2/4] Checking NVIDIA GPU..." -ForegroundColor Yellow

if (-not $SkipGPU) {
    try {
        $nvidiaSmi = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ GPU found: $nvidiaSmi" -ForegroundColor Green
            
            # Check Docker GPU support
            $dockerGpu = docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ Docker GPU passthrough working" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ Docker GPU passthrough not configured. Ollama will use CPU." -ForegroundColor Yellow
                Write-Host "    Enable WSL2 GPU support in Docker Desktop settings." -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "  ⚠ nvidia-smi not found. GPU features may be limited." -ForegroundColor Yellow
    }
}

# ============================================
# Check existing Docker volumes
# ============================================
Write-Host "`n[3/4] Checking existing data volumes..." -ForegroundColor Yellow

$volumes = @("server_pgdata", "server_osdata", "server_qdrant", "server_neo4j", "server_ollama")
$existingVolumes = docker volume ls --format "{{.Name}}" 2>&1

foreach ($vol in $volumes) {
    if ($existingVolumes -contains $vol) {
        Write-Host "  ✓ Found existing volume: $vol" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Volume not found: $vol (will be created)" -ForegroundColor Yellow
    }
}

# ============================================
# Check environment file
# ============================================
Write-Host "`n[4/4] Checking environment configuration..." -ForegroundColor Yellow

$envPath = Join-Path $PSScriptRoot "..\.env.production"
$envExamplePath = Join-Path $PSScriptRoot "..\.env.production.example"

if (Test-Path $envPath) {
    Write-Host "  ✓ .env.production exists" -ForegroundColor Green
    
    # Check for placeholder values
    $envContent = Get-Content $envPath -Raw
    if ($envContent -match "your_tunnel_token_here") {
        Write-Host "  ⚠ CLOUDFLARE_TUNNEL_TOKEN not configured!" -ForegroundColor Yellow
        Write-Host "    Get your token from: Cloudflare Zero Trust > Networks > Tunnels" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ .env.production not found" -ForegroundColor Red
    if (Test-Path $envExamplePath) {
        Write-Host "    Creating from template..." -ForegroundColor Yellow
        Copy-Item $envExamplePath $envPath
        Write-Host "  ✓ Created .env.production - please edit with your values" -ForegroundColor Green
    }
}

# ============================================
# Summary
# ============================================
Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "Setup complete! Next steps:" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan
Write-Host @"

1. Configure Cloudflare Tunnel:
   - Go to: https://one.dash.cloudflare.com
   - Zero Trust > Networks > Tunnels
   - Create tunnel and copy token to .env.production

2. Start the application:
   .\deploy\start.ps1

3. Access the app:
   - Local: http://localhost
   - External: https://neurapath.de (after DNS propagation)

"@ -ForegroundColor White
