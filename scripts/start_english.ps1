# ClawAI Startup Script (English - Simple Version)
# Usage: Right-click this file and select "Run with PowerShell"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ClawAI Penetration Testing System" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get current directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Working directory: $scriptDir" -ForegroundColor Gray

# Check Python
Write-Host "[1/3] Checking Python..." -ForegroundColor Gray
try {
    python --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Python found" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Python not found" -ForegroundColor Red
        Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Red
        pause
        exit 1
    }
} catch {
    Write-Host "[ERROR] Python not found" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Red
    pause
    exit 1
}

# Check Node.js
Write-Host "[2/3] Checking Node.js..." -ForegroundColor Gray
try {
    node --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Node.js found" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Node.js not found" -ForegroundColor Red
        Write-Host "Please install Node.js 16+ and try again" -ForegroundColor Red
        pause
        exit 1
    }
} catch {
    Write-Host "[ERROR] Node.js not found" -ForegroundColor Red
    Write-Host "Please install Node.js 16+ and try again" -ForegroundColor Red
    pause
    exit 1
}

# Check project structure
Write-Host "[3/3] Checking project structure..." -ForegroundColor Gray
if (Test-Path "$scriptDir\backend") {
    Write-Host "[OK] Backend folder found" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Backend folder not found" -ForegroundColor Yellow
}

if (Test-Path "$scriptDir\frontend") {
    Write-Host "[OK] Frontend folder found" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Frontend folder not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Starting Services" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Backend
Write-Host "Starting Backend API (port 5000)..." -ForegroundColor Magenta
$backendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$scriptDir\backend`" && python api_server.py" -PassThru -WindowStyle Normal
Start-Sleep -Seconds 2

# Start Frontend
Write-Host "Starting Frontend Dev Server (port 3000)..." -ForegroundColor Magenta
$frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$scriptDir\frontend`" && npm run dev -- --host 0.0.0.0" -PassThru -WindowStyle Normal
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Service Status" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API: http://localhost:5000" -ForegroundColor Green
Write-Host "Frontend UI: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "APIs available:" -ForegroundColor Blue
Write-Host "- POST /attack   Generate attack chain" -ForegroundColor Gray
Write-Host "- GET /health    Health check" -ForegroundColor Gray
Write-Host ""
Write-Host "How to use:" -ForegroundColor Blue
Write-Host "1. Open browser to http://localhost:3000" -ForegroundColor Gray
Write-Host "2. Enter target IP or domain" -ForegroundColor Gray
Write-Host "3. Click 'Start Attack'" -ForegroundColor Gray
Write-Host "4. View attack visualization" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Startup Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Process IDs:" -ForegroundColor Blue
Write-Host "Backend: $($backendProcess.Id)" -ForegroundColor Gray
Write-Host "Frontend: $($frontendProcess.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop services, close both terminal windows" -ForegroundColor Yellow

# Ask to open browser
$choice = Read-Host "Open browser to frontend? (y/n)"
if ($choice -eq 'y' -or $choice -eq 'Y') {
    Start-Process "http://localhost:3000"
    Write-Host "Browser opened" -ForegroundColor Green
}

Write-Host ""
Write-Host "Services are running in background." -ForegroundColor Green
Write-Host "Close terminal windows to stop services." -ForegroundColor Yellow
Write-Host ""
pause