# Attacker Identification & Tracking

Advanced system for identifying, profiling, and tracking attackers who interact with your defense system.

## Overview

The attacker identification system automatically:
- **Identifies** unique attackers from request patterns
- **Profiles** their skills, tactics, and infrastructure
- **Tracks** stolen data usage via tracking tokens
- **Correlates** related attacks and attacker groups
- **Generates** threat intelligence reports and IOCs

## How It Works

### 1. Automatic Identification

Every request is analyzed for:
- **IP addresses** - Direct identification
- **User agents** - Browser/tool fingerprinting  
- **Behavioral fingerprint** - Unique request characteristics
- **Timing patterns** - Automated vs human behavior

### 2. Profile Building

Each identified attacker gets a comprehensive profile:

```python
AttackerProfile {
    attacker_id: "ATK-a1b2c3d4e5f6"
    first_seen: 2025-01-06 10:30:00
    last_seen: 2025-01-06 15:45:23
    
    # Identity
    ip_addresses: ["203.0.113.42", "198.51.100.23"]
    user_agents: ["Mozilla/5.0 (bot)", "curl/7.68.0"]
    fingerprints: ["abc123...", "def456..."]
    
    # Behavior
    attack_patterns: ["sql_injection", "directory_traversal"]
    timing_signature: {is_automated: true, mean_interval: 0.15s}
    targeted_endpoints: ["/api/auth/login", "/.env"]
    
    # Attribution
    attribution_score: 85.0  # 0-100 confidence
    skill_level: "advanced"
    
    # Evidence
    tracked_tokens_used: ["token_abc123", "token_def456"]
    stolen_data_usage: [...]  # Where/when tokens were used
    
    # Geolocation
    countries: ["Unknown"]  # Add real geolocation service
    isp: "Example ISP"
    asn: "AS12345"
}
```

### 3. Tracking Token Monitoring

When an attacker receives fake data with tracking tokens:

```
1. Attacker hits /admin/config
2. Defense serves fake credentials with token: "abc123def456"
3. System links token to attacker profile: ATK-a1b2c3d4e5f6
4. Later, token seen being used at external service
5. Attribution score increases by 20 points
6. Confirms data exfiltration
```

### 4. Attacker Correlation

Finds related attackers based on:
- **Shared infrastructure** (IPs, ASN)
- **Similar tactics** (attack patterns)
- **Timing proximity** (active at same time)
- **Common targets** (same endpoints)

## Quick Start

### Run Identification Script

```powershell
cd C:\Users\redgh\zero-trust-ai-defense\scripts
.\identify-attackers.ps1 -GenerateReports -ExportIOCs
```

**Output:**
```
===============================================
     Attacker Identification System
===============================================

[✓] Poetry environment ready
[✓] Output directory ready: ..\reports

[*] Analyzing logs and identifying attackers...

Identified attacker: ATK-a1b2c3d4e5f6
Identified attacker: ATK-f7e8d9c0b1a2

Total attackers identified: 2
High-priority attackers: 2

Results saved to: ..\reports\attackers_summary.json
Report generated: ..\reports\attacker_report_ATK-a1b2c3d4e5f6.json
IOCs exported: ..\reports\iocs.json

✓ Analysis complete!

Summary Report:
───────────────
Total Attackers Identified: 2
High-Priority Attackers: 2

Top Attackers:
  • ATK-a1b2c3d4e5f6 | Score: 85 | Skill: advanced | Attacks: 15
    IPs: 203.0.113.42, 198.51.100.23
    Patterns: sql_injection, directory_traversal

Output Files:
───────────────
  📄 attackers_summary.json (2.3 KB)
  📄 attacker_report_ATK-a1b2c3d4e5f6.json (5.7 KB)
  📄 iocs.json (3.1 KB)

Next Steps:
───────────────
  1. Review attacker reports in: ..\reports
  2. Block malicious IPs in your firewall
  3. Share IOCs with your security team
  4. Monitor for tracking token usage
```

### Programmatic Usage

```python
from tracking.attacker_identifier import AttackerIdentifier

# Initialize
identifier = AttackerIdentifier()

# Identify attacker from request
attacker_id = identifier.identify_attacker(request_data, threat_data)

# Get profile
profile = identifier.get_attacker_profile(attacker_id)
print(f"Skill level: {profile.skill_level}")
print(f"Attribution score: {profile.attribution_score}")

# Track token usage (when you detect your tracking token elsewhere)
identifier.track_token_usage("abc123def456", {
    "location": "external_service.com",
    "context": "API request"
})

# Get high-priority attackers
threats = identifier.get_high_priority_attackers(min_score=70.0)

# Find correlated attacks
correlations = identifier.correlate_attackers()

# Generate threat intelligence report
report = identifier.generate_threat_intelligence_report(attacker_id)

# Export IOCs for SIEM/firewall
iocs = identifier.export_for_threat_feed()
```

## Threat Intelligence Report

The system generates comprehensive reports:

```json
{
  "attacker_id": "ATK-a1b2c3d4e5f6",
  "report_generated": "2025-01-06T15:45:23Z",
  
  "summary": {
    "first_seen": "2025-01-06T10:30:00Z",
    "last_seen": "2025-01-06T15:45:23Z",
    "duration_days": 0.22,
    "total_attacks": 15,
    "skill_level": "advanced",
    "attribution_confidence": 85.0
  },
  
  "identity": {
    "likely_identity": null,
    "organization": null,
    "motivation": null,
    "unique_ips": 2,
    "unique_fingerprints": 3
  },
  
  "infrastructure": {
    "ip_addresses": ["203.0.113.42", "198.51.100.23"],
    "user_agents": ["Mozilla/5.0 (bot)", "curl/7.68.0"],
    "countries": ["Unknown"],
    "cities": [],
    "isp": null,
    "asn": null
  },
  
  "tactics": {
    "attack_patterns": ["sql_injection", "directory_traversal"],
    "targeted_endpoints": ["/api/auth/login", "/.env", "/admin/config"],
    "timing_signature": {
      "mean_interval": 0.15,
      "stdev_interval": 0.02,
      "is_automated": true
    },
    "honeypot_interactions": 2
  },
  
  "evidence": {
    "tracked_tokens": ["abc123def456", "xyz789abc123"],
    "data_exfiltration": true,
    "exfiltration_events": [
      {
        "token": "abc123def456",
        "timestamp": 1704551723.5,
        "usage": {"location": "external_service.com"},
        "location": "external_service.com"
      }
    ],
    "related_attackers": []
  },
  
  "iocs": [
    {
      "type": "ipv4",
      "value": "203.0.113.42",
      "confidence": "high",
      "first_seen": "2025-01-06T10:30:00Z",
      "last_seen": "2025-01-06T15:45:23Z"
    },
    {
      "type": "user-agent",
      "value": "curl/7.68.0",
      "confidence": "medium"
    },
    {
      "type": "tracking-token",
      "value": "abc123def456",
      "confidence": "high",
      "indicates": "data_exfiltration"
    }
  ],
  
  "recommendations": [
    "BLOCK: All IP addresses (203.0.113.42, 198.51.100.23...)",
    "MONITOR: Watch for tracking token usage (evidence of stolen data)",
    "RESPOND: Data exfiltration detected - initiate incident response",
    "INVESTIGATE: Advanced attacker - conduct thorough investigation"
  ]
}
```

## Attribution Scoring

The system calculates an **attribution confidence score** (0-100):

| Score | Meaning | Actions Taken |
|-------|---------|---------------|
| 0-30  | Low confidence - possible false positive | Monitor only |
| 30-50 | Medium confidence - suspicious activity | Log, track |
| 50-70 | High confidence - likely attacker | Generate reports |
| 70-85 | Very high confidence - confirmed attacker | Block IPs, alert |
| 85-100 | Definitive - proven data exfiltration | Incident response |

**Score increases from:**
- Each attack attempt: +5 points
- Using multiple tactics: +10 points per tactic
- Multiple infrastructure: +5 points per IP
- **Tracking token usage: +20 points** (strongest evidence)
- Honeypot access: +10 points
- Systematic behavior: +15 points

## Skill Level Assessment

Automatically classifies attacker sophistication:

### Script Kiddie (< 20 points)
- Single attack type
- Single IP address
- Falls for honeypots
- No evasion techniques

### Intermediate (20-50 points)
- 2-3 attack types
- Basic automation
- Some infrastructure rotation

### Advanced (50-80 points)
- Multiple attack vectors
- Sophisticated automation
- Multiple IPs/infrastructure
- Some honeypot avoidance

### Expert (80+ points)
- Many attack types
- Complex infrastructure
- Honeypot avoidance
- Advanced persistence
- Potential APT (Advanced Persistent Threat)

## Attacker Correlation

Finds related attackers that might be part of same campaign:

```json
{
  "attacker1": "ATK-a1b2c3d4e5f6",
  "attacker2": "ATK-f7e8d9c0b1a2",
  "correlation_score": 0.85,
  "shared_characteristics": [
    "Shared IPs: 1",
    "Shared patterns: {'sql_injection'}",
    "Same ASN: AS12345",
    "Temporal proximity"
  ],
  "likelihood": "same_group"
}
```

**Correlation score > 0.8** = Likely same group/campaign  
**Correlation score > 0.6** = Possibly related

## IOC Export

Exports in standard threat intelligence format:

```json
[
  {
    "type": "threat-actor",
    "id": "ATK-a1b2c3d4e5f6",
    "created": "2025-01-06T10:30:00Z",
    "modified": "2025-01-06T15:45:23Z",
    "labels": ["apt", "multi-vector", "automated", "data-theft"],
    "indicators": [
      {"type": "ipv4", "value": "203.0.113.42"}
    ],
    "attack_patterns": [
      {"type": "attack-pattern", "name": "sql_injection"}
    ],
    "confidence": 85,
    "description": "Threat actor ATK-a1b2c3d4e5f6 (advanced level)..."
  }
]
```

Import into:
- **SIEM** (Splunk, ELK, QRadar)
- **Firewalls** (block IPs)
- **Threat Intel Platforms** (MISP, ThreatConnect)
- **Security Tools** (IDS/IPS)

## Integration with Geolocation

To enable real IP geolocation, uncomment in `tracking/attacker_identifier.py`:

```python
def _enrich_geolocation(self, profile: AttackerProfile, ip: str):
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            country = data.get("country_name")
            if country and country not in profile.countries:
                profile.countries.append(country)
            
            city = data.get("city")
            if city and city not in profile.cities:
                profile.cities.append(city)
            
            profile.asn = data.get("asn")
            profile.isp = data.get("org")
    except:
        pass
```

**Free services:**
- ipapi.co (1000 requests/day free)
- ipinfo.io (50k requests/month free)
- ip-api.com (45 requests/minute free)

## Tracking Token Monitoring

### How to Monitor for Token Usage

**1. Web Application Firewall (WAF)**
```python
# Add to your WAF rules
if tracking_token_pattern in request:
    identifier.track_token_usage(token, {
        "location": request.host,
        "source_ip": request.ip
    })
```

**2. API Gateway**
```python
# Monitor outgoing API calls
if stolen_api_key in request.headers:
    identifier.track_token_usage(api_key, {
        "service": "external_api",
        "endpoint": request.url
    })
```

**3. Database Triggers**
```sql
-- Detect queries with tracked credentials
CREATE TRIGGER detect_tracked_tokens
AFTER SELECT ON sensitive_table
FOR EACH ROW
WHEN (SELECT value FROM tokens WHERE tracked = true)
    CALL log_token_usage(token_id);
```

## Best Practices

### 1. Regular Analysis
```powershell
# Run daily
.\identify-attackers.ps1 -GenerateReports -ExportIOCs

# Review high-priority attackers
# Block confirmed malicious IPs
# Share IOCs with team
```

### 2. Attribution Thresholds

- **Score > 30**: Start collecting evidence
- **Score > 50**: Generate detailed report
- **Score > 70**: Consider IP blocking
- **Score > 85**: Initiate incident response

### 3. Evidence Collection

Strong evidence in order of weight:
1. **Tracking token usage** (+20) - Proves data theft
2. **Multiple attack types** (+10 each) - Shows intent
3. **Automated patterns** (+15) - Indicates tooling
4. **Honeypot access** (+10) - Confirms reconnaissance

### 4. False Positive Mitigation

- Don't block on first attack (could be scan)
- Require attribution score > 50 for action
- Whitelist known security scanners
- Review automated blocks weekly

## Advanced Usage

### Custom Attacker Labels

```python
# Add custom classification
profile.organization = "Suspected APT Group X"
profile.motivation = "espionage"
profile.likely_identity = "Known threat actor alias"
```

### Export for Different Formats

```python
# STIX format
stix_data = convert_to_stix(profile)

# CSV for Excel
csv_data = export_to_csv(identifier.get_all_attackers())

# Markdown report
markdown = generate_markdown_report(profile)
```

### Real-time Alerting

```python
# Hook into alerting system
if profile.attribution_score > 80:
    send_alert({
        "severity": "high",
        "attacker_id": profile.attacker_id,
        "iocs": profile.ip_addresses,
        "recommendation": "Block immediately"
    })
```

## Troubleshooting

### No Attackers Identified

- Check if defense system is active
- Verify attacks are being logged
- Lower `MinAttribution` threshold: `-MinAttribution 20`

### Low Attribution Scores

- Scores increase with more evidence
- Single attacks won't score high (by design)
- Wait for pattern to emerge

### Missing Geolocation Data

- Uncomment geolocation code
- Add API key if required
- Check rate limits

## Legal & Ethical Considerations

### ⚠️ Important

- **Defensive use only** - Identify attackers targeting you
- **No offensive action** - Don't attack back
- **Legal compliance** - Follow local laws
- **Data retention** - Have clear retention policy
- **Privacy** - Handle attacker data responsibly
- **Disclosure** - Consider responsible disclosure

### Documentation

- Log all identification actions
- Document response decisions
- Keep audit trail
- Prepare for legal requests

## Next Steps

1. **Run identification script** to see current attackers
2. **Review threat intelligence reports** for high-priority threats
3. **Block confirmed malicious IPs** in firewall
4. **Set up tracking token monitoring** in production
5. **Share IOCs with security team** and threat feeds
6. **Tune attribution thresholds** based on your environment

## Support

For advanced scenarios:
- Multiple defense deployments
- Cross-organization threat sharing
- Custom attribution models
- SIEM integration

See main README.md for contact information.
