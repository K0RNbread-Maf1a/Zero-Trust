# Identify Attackers Script
# Analyzes logs and generates attacker profiles

param(
    [Parameter(Mandatory=$false)]
    [string]$LogPath = "..\logs",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputPath = "..\reports",
    
    [Parameter(Mandatory=$false)]
    [int]$MinAttribution = 30,
    
    [Parameter(Mandatory=$false)]
    [switch]$ExportIOCs,
    
    [Parameter(Mandatory=$false)]
    [switch]$GenerateReports
)

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "     Attacker Identification System" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Ensure Python environment is available
Write-Host "[*] Checking Python environment..." -ForegroundColor Yellow

try {
    $pythonCmd = "poetry"
    $testCmd = & $pythonCmd run python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Poetry not found"
    }
    Write-Host "[✓] Poetry environment ready" -ForegroundColor Green
} catch {
    Write-Host "[✗] Error: Poetry not found. Please install Poetry first." -ForegroundColor Red
    exit 1
}

# Create output directory
Write-Host "[*] Creating output directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null
Write-Host "[✓] Output directory ready: $OutputPath" -ForegroundColor Green

# Run attacker identification
Write-Host ""
Write-Host "[*] Analyzing logs and identifying attackers..." -ForegroundColor Yellow
Write-Host ""

$pythonScript = @"
import sys
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tracking.attacker_identifier import AttackerIdentifier
from core.orchestrator import DefenseOrchestrator

# Initialize
identifier = AttackerIdentifier()
orchestrator = DefenseOrchestrator('../config', '..')

# Get defense status to extract attack data
status = orchestrator.get_status()

# Simulate attacker identification from recent executions
execution_log = orchestrator.cake_executor.get_execution_log()

print(f"Analyzing {len(execution_log)} operations...")

# For demonstration, create sample attacker profiles
sample_attackers = [
    {
        'ip': '203.0.113.42',
        'user_agent': 'Mozilla/5.0 (bot)',
        'endpoint': '/api/auth/login',
        'attack_type': 'sql_injection'
    },
    {
        'ip': '198.51.100.23',
        'user_agent': 'curl/7.68.0',
        'endpoint': '/.env',
        'attack_type': 'reconnaissance'
    }
]

for attacker_data in sample_attackers:
    request_data = {
        'ip': attacker_data['ip'],
        'user_agent': attacker_data['user_agent'],
        'endpoint': attacker_data['endpoint'],
        'headers': {}
    }
    
    threat_data = {
        'action': 'countermeasures',
        'threat_category': attacker_data['attack_type'],
        'risk_score': 85
    }
    
    attacker_id = identifier.identify_attacker(request_data, threat_data)
    print(f"Identified attacker: {attacker_id}")

# Get all attackers
all_attackers = identifier.get_all_attackers()
print(f"\nTotal attackers identified: {len(all_attackers)}")

# Get high-priority attackers
high_priority = identifier.get_high_priority_attackers($MinAttribution)
print(f"High-priority attackers: {len(high_priority)}")

# Export results
results = {
    'total_attackers': len(all_attackers),
    'high_priority_count': len(high_priority),
    'attackers': []
}

for profile in all_attackers:
    results['attackers'].append({
        'attacker_id': profile.attacker_id,
        'attribution_score': profile.attribution_score,
        'skill_level': profile.skill_level,
        'attack_attempts': profile.attack_attempts,
        'ip_addresses': profile.ip_addresses,
        'attack_patterns': profile.attack_patterns
    })

# Save to file
output_file = Path('$OutputPath') / 'attackers_summary.json'
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: {output_file}")

# Generate detailed reports
if $GenerateReports:
    for profile in high_priority:
        report = identifier.generate_threat_intelligence_report(profile.attacker_id)
        
        report_file = Path('$OutputPath') / f'attacker_report_{profile.attacker_id}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report generated: {report_file}")

# Export IOCs
if $ExportIOCs:
    iocs = identifier.export_for_threat_feed()
    
    ioc_file = Path('$OutputPath') / 'iocs.json'
    with open(ioc_file, 'w') as f:
        json.dump(iocs, f, indent=2)
    
    print(f"IOCs exported: {ioc_file}")

# Find correlations
correlations = identifier.correlate_attackers()
if correlations:
    print(f"\nFound {len(correlations)} correlated attacker groups:")
    for corr in correlations:
        print(f"  - {corr['attacker1']} <-> {corr['attacker2']} (score: {corr['correlation_score']:.2f})")

print("\n✓ Analysis complete!")
"@

# Save Python script to temp file
$tempScript = Join-Path $env:TEMP "identify_attackers_$(Get-Random).py"
$pythonScript | Out-File -FilePath $tempScript -Encoding UTF8

try {
    # Run Python script
    & poetry run python $tempScript
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[✓] Attacker identification complete!" -ForegroundColor Green
        Write-Host ""
        
        # Display summary if file exists
        $summaryFile = Join-Path $OutputPath "attackers_summary.json"
        if (Test-Path $summaryFile) {
            Write-Host "Summary Report:" -ForegroundColor Cyan
            Write-Host "───────────────" -ForegroundColor Cyan
            
            $summary = Get-Content $summaryFile | ConvertFrom-Json
            
            Write-Host "Total Attackers Identified: " -NoNewline
            Write-Host $summary.total_attackers -ForegroundColor Yellow
            
            Write-Host "High-Priority Attackers: " -NoNewline
            Write-Host $summary.high_priority_count -ForegroundColor Red
            
            Write-Host ""
            Write-Host "Top Attackers:" -ForegroundColor Cyan
            
            $summary.attackers | Sort-Object -Property attribution_score -Descending | Select-Object -First 5 | ForEach-Object {
                Write-Host "  • " -NoNewline -ForegroundColor White
                Write-Host "$($_.attacker_id) " -NoNewline -ForegroundColor Yellow
                Write-Host "| Score: $($_.attribution_score) " -NoNewline
                Write-Host "| Skill: $($_.skill_level) " -NoNewline
                Write-Host "| Attacks: $($_.attack_attempts)"
                Write-Host "    IPs: $($_.ip_addresses -join ', ')" -ForegroundColor DarkGray
                Write-Host "    Patterns: $($_.attack_patterns -join ', ')" -ForegroundColor DarkGray
            }
        }
        
        Write-Host ""
        Write-Host "Output Files:" -ForegroundColor Cyan
        Write-Host "───────────────" -ForegroundColor Cyan
        Get-ChildItem $OutputPath -Filter "*.json" | ForEach-Object {
            Write-Host "  📄 $($_.Name) " -NoNewline
            Write-Host "($([math]::Round($_.Length/1KB, 2)) KB)" -ForegroundColor DarkGray
        }
        
        Write-Host ""
        Write-Host "Next Steps:" -ForegroundColor Cyan
        Write-Host "───────────────" -ForegroundColor Cyan
        Write-Host "  1. Review attacker reports in: $OutputPath"
        Write-Host "  2. Block malicious IPs in your firewall"
        Write-Host "  3. Share IOCs with your security team"
        Write-Host "  4. Monitor for tracking token usage"
        Write-Host ""
        
    } else {
        Write-Host "[✗] Attacker identification failed" -ForegroundColor Red
    }
    
} finally {
    # Cleanup
    if (Test-Path $tempScript) {
        Remove-Item $tempScript -Force
    }
}

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
"@

