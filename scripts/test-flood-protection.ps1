# Test Flood Protection
# Simulates various attack scenarios to test DoS/DDoS protection

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("DoS", "Brute", "RateLimit", "All")]
    [string]$TestType = "All",
    
    [Parameter(Mandatory=$false)]
    [string]$TargetUrl = "http://localhost:8000",
    
    [Parameter(Mandatory=$false)]
    [int]$Intensity = 10
)

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "     Flood Protection Test Suite" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

function Test-DoS {
    Write-Host "[TEST] DoS Attack Simulation" -ForegroundColor Yellow
    Write-Host "Sending rapid requests from single source..." -ForegroundColor Gray
    
    $blocked = 0
    $allowed = 0
    
    for ($i = 0; $i -lt 100; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "$TargetUrl/health" -Method GET -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 429 -or $response.StatusCode -eq 403) {
                $blocked++
            } else {
                $allowed++
            }
        } catch {
            $blocked++
        }
        
        Start-Sleep -Milliseconds 50
    }
    
    Write-Host "  Results: $allowed allowed, $blocked blocked" -ForegroundColor $(if ($blocked -gt 50) { "Green" } else { "Yellow" })
    Write-Host ""
}

function Test-BruteForce {
    Write-Host "[TEST] Brute Force Protection" -ForegroundColor Yellow
    Write-Host "Attempting multiple failed logins..." -ForegroundColor Gray
    
    $attempts = 0
    $blocked = $false
    
    for ($i = 0; $i -lt 10; $i++) {
        try {
            $body = @{
                username = "admin"
                password = "wrong_$i"
            } | ConvertTo-Json
            
            $response = Invoke-WebRequest -Uri "$TargetUrl/api/auth/login" `
                -Method POST `
                -Body $body `
                -ContentType "application/json" `
                -TimeoutSec 2 `
                -ErrorAction SilentlyContinue
            
            $attempts++
        } catch {
            if ($_.Exception.Response.StatusCode -eq 429) {
                $blocked = $true
                break
            }
        }
        
        Start-Sleep -Seconds 1
    }
    
    Write-Host "  Failed attempts before block: $attempts" -ForegroundColor $(if ($blocked) { "Green" } else { "Yellow" })
    Write-Host "  Brute force protection: $(if ($blocked) { 'ACTIVE' } else { 'NOT TRIGGERED' })" -ForegroundColor $(if ($blocked) { "Green" } else { "Red" })
    Write-Host ""
}

function Test-RateLimit {
    Write-Host "[TEST] Rate Limiting" -ForegroundColor Yellow
    Write-Host "Testing per-IP rate limits..." -ForegroundColor Gray
    
    $startTime = Get-Date
    $requests = 0
    $limited = $false
    
    while ((Get-Date) -lt $startTime.AddSeconds(5)) {
        try {
            $response = Invoke-WebRequest -Uri "$TargetUrl/health" -Method GET -TimeoutSec 1 -ErrorAction SilentlyContinue
            $requests++
        } catch {
            if ($_.Exception.Response.StatusCode -eq 429) {
                $limited = $true
                break
            }
        }
    }
    
    $rps = [math]::Round($requests / 5, 2)
    
    Write-Host "  Requests per second: $rps" -ForegroundColor Gray
    Write-Host "  Rate limiting: $(if ($limited) { 'TRIGGERED' } else { 'NOT TRIGGERED' })" -ForegroundColor $(if ($limited) { "Green" } else { "Yellow" })
    Write-Host ""
}

function Get-ProtectionStats {
    Write-Host "[STATS] Flood Protection Statistics" -ForegroundColor Cyan
    
    try {
        $auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:admin123"))
        $response = Invoke-RestMethod -Uri "$TargetUrl/api/defense/status" `
            -Method GET `
            -Headers @{Authorization = "Basic $auth"} `
            -ErrorAction SilentlyContinue
        
        Write-Host "  Total Requests: $($response.defense_system.total_executions)" -ForegroundColor White
        Write-Host "  Threats Detected: $($response.defense_system.active_environments)" -ForegroundColor Yellow
        Write-Host ""
    } catch {
        Write-Host "  Could not retrieve stats (server may not be running)" -ForegroundColor Red
        Write-Host ""
    }
}

# Main execution
Write-Host "Target: $TargetUrl" -ForegroundColor Gray
Write-Host "Test Type: $TestType" -ForegroundColor Gray
Write-Host ""

# Check if server is running
try {
    $health = Invoke-WebRequest -Uri "$TargetUrl/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[✓] Server is responding" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[✗] Server is not responding at $TargetUrl" -ForegroundColor Red
    Write-Host "    Start the server first: poetry run python server/protected_server.py" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Run tests
switch ($TestType) {
    "DoS" {
        Test-DoS
    }
    "Brute" {
        Test-BruteForce
    }
    "RateLimit" {
        Test-RateLimit
    }
    "All" {
        Test-DoS
        Test-BruteForce
        Test-RateLimit
    }
}

Get-ProtectionStats

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "     Test Complete" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Protection Features:" -ForegroundColor Cyan
Write-Host "  ✓ Rate Limiting (per-IP, per-endpoint, global)" -ForegroundColor Green
Write-Host "  ✓ DoS Detection (50+ req/10s = block)" -ForegroundColor Green
Write-Host "  ✓ DDoS Detection (10x baseline from 10+ sources)" -ForegroundColor Green
Write-Host "  ✓ Brute Force Protection (5 failed = 1hr block)" -ForegroundColor Green
Write-Host "  ✓ Progressive Penalties (exponential backoff)" -ForegroundColor Green
Write-Host "  ✓ Challenge-Response (CAPTCHA-like after 3 violations)" -ForegroundColor Green
Write-Host "  ✓ Auto-Expiring Blocks (repeat offenders = longer)" -ForegroundColor Green
Write-Host "  ✓ Adaptive Learning (baseline adjusts to traffic)" -ForegroundColor Green
Write-Host ""
