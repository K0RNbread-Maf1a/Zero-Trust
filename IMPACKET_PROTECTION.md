# Impacket Attack Protection

## Overview

The Impacket Protection system defends against network-based attacks using the Impacket toolkit. Impacket is a collection of Python classes commonly used by penetration testers and attackers for exploiting Windows network protocols.

## What is Impacket?

Impacket provides low-level programmatic access to network protocols including:
- **SMB/CIFS** - File sharing and remote execution
- **Kerberos** - Windows authentication
- **NTLM** - Legacy authentication
- **DCE/RPC** - Remote procedure calls
- **LDAP** - Directory services

### Common Impacket Tools

| Tool | Attack Type | Severity |
|------|-------------|----------|
| `psexec.py` | Remote command execution via SMB | Critical |
| `wmiexec.py` | Remote execution via WMI | Critical |
| `smbexec.py` | Remote execution via SMB services | Critical |
| `secretsdump.py` | Credential dumping (hashes, tickets) | Critical |
| `GetUserSPNs.py` | Kerberoasting | High |
| `ticketer.py` | Golden/Silver ticket creation | Critical |
| `ntlmrelayx.py` | NTLM relay attacks | Critical |
| `dcomexec.py` | DCOM-based remote execution | High |
| `atexec.py` | Task Scheduler remote execution | High |
| `lookupsid.py` | User enumeration | Medium |

## Detection Strategies

The protection system uses multiple detection layers:

### 1. Signature-Based Detection
Matches known patterns from Impacket tools:
- Service names: `PSEXESVC`, `RemComSvc`
- Named pipes: `\PIPE\PSEXESVC`, `\PIPE\WINREG`
- WMI indicators: `Win32_Process.Create`, `__EventFilter`
- Registry access: `NTDS.DIT`, `SYSTEM` hive
- Kerberos indicators: `krbtgt`, unusual ticket lifetimes

### 2. Protocol Anomaly Detection
Identifies suspicious protocol usage:
- **SMB**: Admin share access (`ADMIN$`, `C$`), service operations
- **Kerberos**: Weak encryption (RC4, DES), long ticket lifetimes
- **NTLM**: Missing MIC, signing disabled, hash authentication
- **RPC**: Suspicious interfaces (DCOM, Task Scheduler)
- **LDAP**: Injection patterns, rapid enumeration

### 3. Attack Chain Recognition
Detects multi-stage attack sequences:

**PsExec Chain:**
1. SMB connection to `ADMIN$`
2. Service creation via `SVCCTL`
3. Named pipe access (`\PIPE\PSEXESVC`)

**Secretsdump Chain:**
1. SMB connection
2. Registry hive access (`WINREG`)
3. NTDS.DIT or SAM access

### 4. Behavioral Analysis
Monitors for suspicious patterns:
- Rapid authentication attempts (>10 in 1 minute)
- Multiple failed authentications (>5)
- Protocol switching (>3 different protocols)
- Rapid SMB session creation (>20 in 1 minute)
- Multiple SPN requests (>5 in 5 minutes)

### 5. NTLM Relay Detection
Specific indicators:
- NTLM signing disabled
- MIC (Message Integrity Check) removed
- Same username from multiple IPs
- Relayed authentication patterns

## Attack Categories

### SMB-Based Attacks

**PsExec Execution**
```
Indicators:
- ADMIN$ share access
- SVCCTL operations
- Named pipe: PSEXESVC
- Service installation

Confidence: 0.9+
```

**WMIExec**
```
Indicators:
- Win32_Process.Create calls
- Event subscription
- WMI namespace access

Confidence: 0.9+
```

**Secretsdump**
```
Indicators:
- Registry hive access (SYSTEM, SECURITY, SAM)
- NTDS.DIT access
- Volume shadow copy operations

Confidence: 1.0 (Critical)
```

### Kerberos Attacks

**Golden Ticket**
```
Indicators:
- krbtgt service access
- Unusually long ticket lifetime (>10 days)
- Weak encryption types

Confidence: 0.8+
Action: Reset krbtgt password twice
```

**Kerberoasting**
```
Indicators:
- Multiple SPN requests (>5)
- RC4_HMAC encryption
- Service ticket requests

Confidence: 0.7+
```

### NTLM Attacks

**NTLM Relay**
```
Indicators:
- Signing disabled
- MIC not present
- Authentication from multiple sources

Confidence: 0.8+
Mitigation: Enable SMB/LDAP signing
```

**Pass-the-Hash**
```
Indicators:
- Hash authentication (LM:NTLM format)
- No password authentication
- Direct hash usage

Confidence: 0.9+
```

### RPC/DCOM Attacks

**DCOM Execution**
```
Indicators:
- IRemUnknown2 interface
- MMC20.Application activation
- Remote object activation

Confidence: 0.8+
```

### LDAP Attacks

**LDAP Injection**
```
Indicators:
- Combined AND/OR filters: (&...(|...
- Wildcard abuse: *)( or admin*
- Filter manipulation

Confidence: 0.7+
```

## Usage

### Basic Integration

```python
from defense.impacket_protection import ImpacketProtection

# Initialize protection
protector = ImpacketProtection()

# Analyze network event
event_data = {
    'source_ip': '192.168.1.100',
    'protocol': 'SMB',
    'share': 'ADMIN$',
    'command': 'SVCCTL',
    'path': '\\PIPE\\PSEXESVC'
}

is_attack, analysis = protector.analyze_network_event(event_data)

if is_attack:
    print(f"Attack detected: {analysis['attack_type']}")
    print(f"Confidence: {analysis['confidence']:.2%}")
    print(f"Indicators: {analysis['indicators']}")
    print(f"Recommendations: {analysis['recommendations']}")
```

### Authentication Tracking

```python
# Report authentication attempts
auth_data = {
    'username': 'admin',
    'protocol': 'SMB',
    'auth_type': 'NTLM',
    'success': False
}

protector.report_auth_attempt('192.168.1.100', auth_data)
```

### Statistics

```python
stats = protector.get_statistics()

print(f"Total Events: {stats['total_events']}")
print(f"Attacks Detected: {stats['attacks_detected']}")
print(f"SMB Attacks: {stats['smb_attacks']}")
print(f"Kerberos Attacks: {stats['kerberos_attacks']}")
print(f"NTLM Relays: {stats['ntlm_relay_attempts']}")
print(f"Secret Dumps: {stats['secret_dumps']}")
```

### Blocked IPs

```python
blocked = protector.get_blocked_ips()

for block in blocked:
    print(f"IP: {block['ip']}")
    print(f"  Reason: {block['reason']}")
    print(f"  Attack Type: {block['attack_type']}")
    print(f"  Blocked At: {block['blocked_at']}")
```

## Testing

Run the test suite to verify protection:

```powershell
# Test all attack types
.\scripts\test-impacket-protection.ps1

# Test specific attack type
.\scripts\test-impacket-protection.ps1 -AttackType SMB
.\scripts\test-impacket-protection.ps1 -AttackType Kerberos
.\scripts\test-impacket-protection.ps1 -AttackType NTLM
.\scripts\test-impacket-protection.ps1 -AttackType RPC
.\scripts\test-impacket-protection.ps1 -AttackType LDAP
```

### Test Output

```
[TEST] SMB-based Attacks
==================================================
  PsExec Detection: BLOCKED
  Confidence: 90.00%
  Indicators: ['Admin share access: ADMIN$', 'Service control operations', ...]

  Secretsdump Chain:
    Step 1: ALLOWED
    Step 2: BLOCKED
    Step 3: BLOCKED

  WMIExec Detection: BLOCKED
  Matched Signatures: ['wmiexec']

  SMB Attacks Detected: 3
  Total Blocks: 2
```

## Security Recommendations

### Immediate Actions

1. **Enable SMB Signing** (Critical)
   - Prevents NTLM relay attacks
   - Required on all systems
   ```powershell
   Set-SmbClientConfiguration -RequireSecuritySignature $true -Force
   Set-SmbServerConfiguration -RequireSecuritySignature $true -Force
   ```

2. **Disable NTLM** (High Priority)
   - Use Kerberos where possible
   - Enable NTLM audit mode first
   ```powershell
   # Audit NTLM usage first
   Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Lsa" -Name "LmCompatibilityLevel" -Value 5
   ```

3. **Enable LSASS Protection** (Critical)
   - Prevents credential dumping
   ```powershell
   Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "RunAsPPL" -Value 1
   ```

4. **Restrict Admin Shares** (High Priority)
   - Limit access to ADMIN$, C$, IPC$
   ```powershell
   # Disable default admin shares (workstations only)
   Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Services\LanmanServer\Parameters" -Name "AutoShareWks" -Value 0
   ```

### Long-Term Hardening

5. **Kerberos Security**
   - Enable AES encryption (disable RC4/DES)
   - Monitor for unusual ticket lifetimes
   - Implement Protected Users security group
   - Reset krbtgt password regularly (twice)

6. **LDAP Hardening**
   - Enable LDAP signing and channel binding
   - Require TLS for LDAP connections
   - Implement LDAP query limits

7. **Audit Logging**
   - Enable security audit logging
   - Monitor events: 4624, 4625 (logon), 4672 (admin logon)
   - Alert on: 4697 (service install), 4698 (scheduled task)

8. **Least Privilege**
   - Minimize accounts with local admin rights
   - Use LAPS for local admin passwords
   - Implement privileged access workstations (PAWs)

### Detection & Response

9. **Network Monitoring**
   - Monitor SMB connections to admin shares
   - Alert on rapid authentication failures
   - Track unusual service installations
   - Monitor DCE/RPC calls

10. **Incident Response**
    - Isolate affected systems immediately
    - Reset compromised credentials
    - Check for persistence mechanisms
    - Analyze attack chain and timeline

## Event Data Format

Network events should include:

```python
{
    'source_ip': str,           # Source IP address
    'protocol': str,            # Protocol: SMB, KERBEROS, NTLM, RPC, LDAP
    'event_type': str,          # Event type (optional)
    
    # SMB-specific
    'share': str,               # Share name (ADMIN$, C$, etc.)
    'path': str,                # File/pipe path
    'command': str,             # SMB command
    
    # Kerberos-specific
    'service_principal': str,   # Target SPN
    'ticket_type': str,         # TGT, TGS
    'ticket_lifetime': int,     # Lifetime in seconds
    'encryption_type': str,     # Encryption algorithm
    
    # NTLM-specific
    'auth_type': str,           # Authentication type
    'ntlm_flags': dict,         # NTLM negotiation flags
    'mic_present': bool,        # MIC field present
    'username': str,            # Username
    
    # RPC-specific
    'interface_uuid': str,      # RPC interface UUID
    'operation': str,           # RPC operation
    
    # LDAP-specific
    'ldap_filter': str          # LDAP query filter
}
```

## Integration with Existing Systems

### With Virtual Protected Server

The server automatically integrates Impacket protection:

```python
# In server/protected_server.py
from defense.impacket_protection import ImpacketProtection

impacket_protection = ImpacketProtection()

@app.middleware("http")
async def impacket_middleware(request: Request, call_next):
    # Extract network event data
    event_data = {
        'source_ip': request.client.host,
        'protocol': 'HTTP',  # or detected protocol
        # ... additional fields
    }
    
    # Check for attack
    is_attack, analysis = impacket_protection.analyze_network_event(event_data)
    
    if is_attack:
        return JSONResponse(
            status_code=403,
            content={"error": "Attack detected", "details": analysis}
        )
    
    return await call_next(request)
```

### With Flood Protection

Combine with flood protection for comprehensive defense:

```python
from defense.flood_protection import FloodProtection
from defense.impacket_protection import ImpacketProtection

flood = FloodProtection()
impacket = ImpacketProtection()

# Check both protections
def check_request(request_data):
    # Flood protection
    allowed, flood_result = flood.check_request(request_data)
    if not allowed:
        return False, flood_result
    
    # Impacket protection (if network event)
    if is_network_event(request_data):
        is_attack, impacket_result = impacket.analyze_network_event(request_data)
        if is_attack:
            return False, impacket_result
    
    return True, {"allowed": True}
```

## Performance Considerations

- **Memory**: O(n) where n = number of unique IPs (max 1000 events per IP)
- **CPU**: Pattern matching is efficient (regex-based)
- **Latency**: <1ms per event analysis
- **Scaling**: Handles 10,000+ events/second

### Optimization Tips

1. **Adjust history limits** for high-traffic environments
2. **Use sampling** for very high-volume networks
3. **Implement caching** for repeated pattern checks
4. **Tune confidence thresholds** based on false positive rate

## Troubleshooting

### False Positives

**Legitimate admin activity flagged:**
- Whitelist known admin IPs
- Lower confidence threshold
- Adjust signature patterns

**Service installation blocked:**
- Whitelist authorized service names
- Use challenge-response for admins

### False Negatives

**Attacks not detected:**
- Lower detection thresholds
- Add custom signatures
- Enable stricter behavioral checks

### Performance Issues

**High CPU usage:**
- Reduce event history size
- Disable unused detection modules
- Use sampling for high traffic

## Reference

### Confidence Scoring

| Range | Meaning | Action |
|-------|---------|--------|
| 0.0-0.3 | Low suspicion | Log only |
| 0.3-0.5 | Medium suspicion | Monitor, require challenge |
| 0.5-0.7 | High suspicion | Rate limit, alert |
| 0.7-1.0 | Attack confirmed | Block IP, generate report |

### Signature Severity

| Level | Score | Examples |
|-------|-------|----------|
| Critical | 10 | Secretsdump, Golden Ticket |
| High | 8-9 | PsExec, WMIExec, NTLM Relay |
| Medium | 5-7 | Kerberoasting, LDAP Injection |
| Low | 1-4 | Enumeration, Reconnaissance |

## Additional Resources

- [Impacket GitHub Repository](https://github.com/SecureAuthCorp/impacket)
- [MITRE ATT&CK - Lateral Movement](https://attack.mitre.org/tactics/TA0008/)
- [Microsoft: SMB Security Best Practices](https://docs.microsoft.com/en-us/windows-server/storage/file-server/smb-security)
- [NIST: Kerberos Security](https://csrc.nist.gov/projects/kerberos)
- [SANS: Detecting Impacket Attacks](https://www.sans.org/white-papers/)

---

**Last Updated**: 2025-11-07  
**Version**: 1.0.0  
**Maintained By**: Zero-Trust AI Defense Team
