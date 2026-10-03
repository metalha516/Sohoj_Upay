# Sohoj Financial Coach — Clean Clone Automated Setup Script for Windows PowerShell
[CmdletBinding()]
param (
    [switch]$SkipFrontend,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "     SOHOJ FINANCIAL COACH — REPRODUCIBLE SETUP           " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Environment Check
Write-Host "`n[*] Checking system dependencies..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Python 3.12+ is required but not found in PATH."
    exit 1
}
Write-Host "    Found $pythonVersion" -ForegroundColor Green

if (-not $SkipFrontend) {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Node.js not detected. Skipping frontend installation."
        $SkipFrontend = $true
    } else {
        Write-Host "    Found Node $nodeVersion" -ForegroundColor Green
    }
}

# 2. Environment Configuration
Write-Host "`n[*] Configuring environment variables..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "    Created .env from .env.example" -ForegroundColor Green
} else {
    Write-Host "    .env already exists, keeping existing file." -ForegroundColor DarkGray
}

# 3. Backend Dependencies
Write-Host "`n[*] Installing Python backend packages..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -e backend/.[dev]
python -m pip install locust

# 4. Frontend Dependencies
if (-not $SkipFrontend) {
    Write-Host "`n[*] Installing Frontend dependencies..." -ForegroundColor Yellow
    Push-Location "frontend"
    try {
        npm install
    } finally {
        Pop-Location
    }
}

# 5. Execute Disaster Recovery Verification Drill
Write-Host "`n[*] Executing Disaster Recovery & Backup Integrity Drill..." -ForegroundColor Yellow
python scripts/drill_backup_restore.py

# 6. Verification Test Suite
if (-not $SkipTests) {
    Write-Host "`n[*] Running backend test suite..." -ForegroundColor Yellow
    python -m pytest backend/tests -q
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   SOHOJ SETUP COMPLETED SUCCESSFULLY!                   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "To start the development stack:"
Write-Host "  Backend API:  python -m uvicorn app.main:app --app-dir backend --port 8000"
Write-Host "  Frontend:     cd frontend && npm run dev"
Write-Host "  Production:   docker compose -f docker-compose.prod.yml up -d --build"
