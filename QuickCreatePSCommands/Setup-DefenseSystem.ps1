# Quick Setup Script for Zero-Trust AI Defense System

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Zero-Trust AI Defense - Quick Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Check Poetry
try {
    $poetryVersion = poetry --version
    Write-Host "✓ Poetry found: $poetryVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Poetry not found. Installing..." -ForegroundColor Yellow
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
}

# Check .NET
try {
    $dotnetVersion = dotnet --version
    Write-Host "✓ .NET found: $dotnetVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ .NET not found. Please install .NET SDK 6.0+" -ForegroundColor Red
    exit 1
}

# Install Python dependencies
Write-Host "`n[2/6] Installing Python dependencies..." -ForegroundColor Yellow
poetry install

# Check Cake tool
Write-Host "`n[3/6] Checking Cake tool..." -ForegroundColor Yellow
try {
    dotnet cake --version | Out-Null
    Write-Host "✓ Cake tool found" -ForegroundColor Green
} catch {
    Write-Host "Installing Cake tool..." -ForegroundColor Yellow
    dotnet tool install -g Cake.Tool
}

# Create necessary directories
Write-Host "`n[4/6] Creating directories..." -ForegroundColor Yellow
$dirs = @("logs", "environments")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✓ Created $dir/" -ForegroundColor Green
    }
}

# Check API key
Write-Host "`n[5/6] Checking API key..." -ForegroundColor Yellow
if ($env:ANTHROPIC_API_KEY) {
    Write-Host "✓ ANTHROPIC_API_KEY is set" -ForegroundColor Green
} else {
    Write-Host "⚠ ANTHROPIC_API_KEY not set (needed for Defense Agent)" -ForegroundColor Yellow
    Write-Host "  Set it with: `$env:ANTHROPIC_API_KEY='your_key'" -ForegroundColor Gray
}

# Test installation
Write-Host "`n[6/6] Testing installation..." -ForegroundColor Yellow
poetry run python -c "import core.orchestrator; print('✓ Defense system imports successful')"

Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "`nQuick Start Commands:" -ForegroundColor Cyan
Write-Host "  poetry run python main.py          # Test defense system"
Write-Host "  poetry run defense-agent            # Run AI agent"
Write-Host "  poetry run python server/protected_server.py  # Start server"
Write-Host ""
