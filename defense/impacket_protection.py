"""
Impacket Attack Prevention - Network protocol attack detection and prevention

Impacket is a collection of Python classes for working with network protocols,
commonly used by attackers for:
- SMB/CIFS attacks (PsExec, WMIExec, SMBExec)
- Kerberos attacks (Golden/Silver tickets, Pass-the-Hash, Pass-the-Ticket)
- NTLM relay attacks
- DCE/RPC exploitation
- LDAP exploitation
- Secret dumping (secretsdump.py)

This module detects and blocks these attack patterns.
"""
import re
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta


@dataclass
class ImpacketSignature:
    """Signature for identifying Impacket-based attacks"""
    name: str
    pattern: str
    category: str
    severity: int  # 1-10
    description: str
    indicators: List[str] = field(default_factory=list)


@dataclass
class NetworkEvent:
    """Network event tracking"""
    ip: str
    timestamp: float
    event_type: str
    protocol: str
    details: Dict[str, Any]
    matched_signatures: List[str] = field(default_factory=list)


class ImpacketProtection:
    """
    Advanced protection against Impacket-based network attacks
    
    Detection strategies:
    1. Protocol anomaly detection (malformed SMB/Kerberos/LDAP packets)
    2. Attack tool signatures (Impacket user-agents, tool fingerprints)
    3. Behavioral patterns (rapid auth attempts, unusual protocol sequences)
    4. Known attack chains (PsExec execution flow, secretsdump patterns)
    5. Network-level indicators (suspicious ports, protocol mismatches)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize attack signatures
        self.signatures = self._initialize_signatures()
        
        # Event tracking
        self.network_events = defaultdict(lambda: deque(maxlen=1000))
        self.auth_attempts = defaultdict(lambda: deque(maxlen=100))
        self.smb_sessions = {}
        self.kerberos_tickets = {}
        self.suspicious_ips = set()
        self.blocked_ips = {}
        
        # Attack chain tracking
        self.attack_chains = defaultdict(list)
        
        # Statistics
        self.stats = {
            "total_events": 0,
            "attacks_detected": 0,
            "smb_attacks": 0,
            "kerberos_attacks": 0,
            "ntlm_relay_attempts": 0,
            "rpc_exploits": 0,
            "ldap_attacks": 0,
            "secret_dumps": 0,
            "ips_blocked": 0
        }
        
    def analyze_network_event(self, event_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Analyze network event for Impacket attack patterns
        Returns: (is_attack, analysis_result)
        """
        self.stats["total_events"] += 1
        
        ip = event_data.get("source_ip", "unknown")
        protocol = event_data.get("protocol", "").upper()
        timestamp = time.time()
        
        # Check if IP is already blocked
        if ip in self.blocked_ips:
            return True, {
                "blocked": True,
                "reason": self.blocked_ips[ip]["reason"],
                "blocked_at": self.blocked_ips[ip]["timestamp"]
            }
        
        # Create network event
        event = NetworkEvent(
            ip=ip,
            timestamp=timestamp,
            event_type=event_data.get("event_type", "unknown"),
            protocol=protocol,
            details=event_data
        )
        
        # Run detection checks
        analysis = {
            "is_attack": False,
            "matched_signatures": [],
            "attack_type": None,
            "confidence": 0.0,
            "indicators": [],
            "recommendations": []
        }
        
        # Check for signature matches
        signature_matches = self._check_signatures(event_data)
        if signature_matches:
            analysis["matched_signatures"] = signature_matches
            analysis["is_attack"] = True
            analysis["confidence"] += 0.4
        
        # Protocol-specific checks
        if protocol == "SMB":
            smb_analysis = self._analyze_smb_traffic(ip, event_data)
            if smb_analysis["suspicious"]:
                analysis["is_attack"] = True
                analysis["attack_type"] = smb_analysis["attack_type"]
                analysis["confidence"] += smb_analysis["confidence"]
                analysis["indicators"].extend(smb_analysis["indicators"])
        
        elif protocol == "KERBEROS":
            krb_analysis = self._analyze_kerberos_traffic(ip, event_data)
            if krb_analysis["suspicious"]:
                analysis["is_attack"] = True
                analysis["attack_type"] = krb_analysis["attack_type"]
                analysis["confidence"] += krb_analysis["confidence"]
                analysis["indicators"].extend(krb_analysis["indicators"])
        
        elif protocol == "LDAP":
            ldap_analysis = self._analyze_ldap_traffic(ip, event_data)
            if ldap_analysis["suspicious"]:
                analysis["is_attack"] = True
                analysis["attack_type"] = ldap_analysis["attack_type"]
                analysis["confidence"] += ldap_analysis["confidence"]
                analysis["indicators"].extend(ldap_analysis["indicators"])
        
        elif protocol == "RPC" or protocol == "DCERPC":
            rpc_analysis = self._analyze_rpc_traffic(ip, event_data)
            if rpc_analysis["suspicious"]:
                analysis["is_attack"] = True
                analysis["attack_type"] = rpc_analysis["attack_type"]
                analysis["confidence"] += rpc_analysis["confidence"]
                analysis["indicators"].extend(rpc_analysis["indicators"])
        
        # Check for NTLM relay patterns
        ntlm_analysis = self._check_ntlm_relay(ip, event_data)
        if ntlm_analysis["is_relay"]:
            analysis["is_attack"] = True
            analysis["attack_type"] = "ntlm_relay"
            analysis["confidence"] += 0.3
            analysis["indicators"].extend(ntlm_analysis["indicators"])
        
        # Check attack chains
        chain_analysis = self._check_attack_chains(ip, event_data)
        if chain_analysis["chain_detected"]:
            analysis["is_attack"] = True
            analysis["attack_type"] = chain_analysis["chain_type"]
            analysis["confidence"] += 0.3
            analysis["indicators"].append(f"Attack chain: {chain_analysis['chain_type']}")
        
        # Check behavioral anomalies
        behavior_analysis = self._check_behavioral_anomalies(ip)
        if behavior_analysis["anomalous"]:
            analysis["confidence"] += behavior_analysis["confidence_boost"]
            analysis["indicators"].extend(behavior_analysis["anomalies"])
        
        # Normalize confidence to 0-1
        analysis["confidence"] = min(1.0, analysis["confidence"])
        
        # Store event
        event.matched_signatures = analysis["matched_signatures"]
        self.network_events[ip].append(event)
        
        # Take action if attack detected with high confidence
        if analysis["is_attack"] and analysis["confidence"] >= 0.7:
            self._handle_attack(ip, analysis)
            analysis["action_taken"] = "ip_blocked"
            analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis["is_attack"], analysis
    
    def report_auth_attempt(self, ip: str, auth_data: Dict[str, Any]):
        """Report authentication attempt for tracking"""
        timestamp = time.time()
        self.auth_attempts[ip].append({
            "timestamp": timestamp,
            "username": auth_data.get("username"),
            "protocol": auth_data.get("protocol"),
            "success": auth_data.get("success", False),
            "auth_type": auth_data.get("auth_type")  # NTLM, Kerberos, etc.
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get protection statistics"""
        return {
            **self.stats,
            "suspicious_ips": len(self.suspicious_ips),
            "active_smb_sessions": len(self.smb_sessions),
            "tracked_kerberos_tickets": len(self.kerberos_tickets),
            "blocked_ips": len(self.blocked_ips)
        }
    
    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get list of blocked IPs"""
        return [
            {
                "ip": ip,
                "reason": data["reason"],
                "blocked_at": data["timestamp"],
                "attack_type": data["attack_type"]
            }
            for ip, data in self.blocked_ips.items()
        ]
    
    def unblock_ip(self, ip: str):
        """Manually unblock an IP"""
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
        if ip in self.suspicious_ips:
            self.suspicious_ips.remove(ip)
    
    # ==================== Private Methods ====================
    
    def _initialize_signatures(self) -> Dict[str, ImpacketSignature]:
        """Initialize Impacket attack signatures"""
        signatures = {
            # SMB-based attacks
            "psexec": ImpacketSignature(
                name="PsExec Execution",
                pattern=r"(PSEXESVC|RemComSvc|__output)",
                category="smb",
                severity=9,
                description="PsExec remote command execution",
                indicators=["Named pipe creation", "Service installation", "ADMIN$ share access"]
            ),
            "wmiexec": ImpacketSignature(
                name="WMIExec",
                pattern=r"(Win32_Process\.Create|__EventFilter|__EventConsumer)",
                category="smb",
                severity=9,
                description="WMI-based remote execution",
                indicators=["WMI process creation", "Event subscription"]
            ),
            "smbexec": ImpacketSignature(
                name="SMBExec",
                pattern=r"(__output|BTOBTO|ADMIN\$)",
                category="smb",
                severity=9,
                description="SMB-based remote execution",
                indicators=["Temporary service", "Command output redirection"]
            ),
            "secretsdump": ImpacketSignature(
                name="Secretsdump",
                pattern=r"(NTDS\.DIT|SYSTEM|SECURITY|SAM|\\Registry\\Machine)",
                category="smb",
                severity=10,
                description="Credential dumping attempt",
                indicators=["Registry hive access", "NTDS.DIT access", "SYSTEM hive copy"]
            ),
            
            # Kerberos attacks
            "golden_ticket": ImpacketSignature(
                name="Golden Ticket",
                pattern=r"(krbtgt|TGT|KRB_TGT)",
                category="kerberos",
                severity=10,
                description="Golden ticket attack (forged TGT)",
                indicators=["Unusual TGT lifetime", "krbtgt encryption"]
            ),
            "silver_ticket": ImpacketSignature(
                name="Silver Ticket",
                pattern=r"(KRB_TGS|service ticket|forged.*ticket)",
                category="kerberos",
                severity=9,
                description="Silver ticket attack (forged service ticket)",
                indicators=["Forged service ticket", "Unusual encryption type"]
            ),
            "kerberoasting": ImpacketSignature(
                name="Kerberoasting",
                pattern=r"(GetUserSPNs|RC4_HMAC|TGS.*REQ.*SPN)",
                category="kerberos",
                severity=8,
                description="Kerberoasting attack",
                indicators=["Multiple SPN requests", "RC4 encryption requests"]
            ),
            
            # NTLM attacks
            "ntlm_relay": ImpacketSignature(
                name="NTLM Relay",
                pattern=r"(ntlmrelayx|NTLMSSP|AUTHENTICATE.*relay)",
                category="ntlm",
                severity=9,
                description="NTLM relay attack",
                indicators=["Relayed authentication", "MIC removed", "Signing disabled"]
            ),
            "pass_the_hash": ImpacketSignature(
                name="Pass-the-Hash",
                pattern=r"(NTLM hash|LM:NTLM|pass.*hash)",
                category="ntlm",
                severity=9,
                description="Pass-the-hash attack",
                indicators=["Hash authentication", "No password authentication"]
            ),
            
            # DCE/RPC attacks
            "dcomexec": ImpacketSignature(
                name="DCOM Execution",
                pattern=r"(DCOM|IRemUnknown2|MMC20\.Application)",
                category="rpc",
                severity=9,
                description="DCOM-based remote execution",
                indicators=["DCOM object activation", "Remote MMC execution"]
            ),
            "atexec": ImpacketSignature(
                name="AT Exec",
                pattern=r"(atsvc|ITaskSchedulerService|scheduled.*task)",
                category="rpc",
                severity=8,
                description="Task Scheduler remote execution",
                indicators=["Remote task creation", "ATSVC RPC calls"]
            ),
            
            # LDAP attacks
            "ldap_injection": ImpacketSignature(
                name="LDAP Injection",
                pattern=r"(\(\&|\(\||\*\)|\)\(|admin\*)",
                category="ldap",
                severity=7,
                description="LDAP injection attempt",
                indicators=["Malformed LDAP filter", "Wildcard abuse"]
            )
        }
        
        return signatures
    
    def _check_signatures(self, event_data: Dict[str, Any]) -> List[str]:
        """Check event against known signatures"""
        matches = []
        
        # Convert event data to searchable string
        search_string = str(event_data).lower()
        
        for sig_id, signature in self.signatures.items():
            if re.search(signature.pattern, search_string, re.IGNORECASE):
                matches.append(sig_id)
                
                # Update stats
                if signature.category == "smb":
                    self.stats["smb_attacks"] += 1
                elif signature.category == "kerberos":
                    self.stats["kerberos_attacks"] += 1
                elif signature.category == "rpc":
                    self.stats["rpc_exploits"] += 1
                elif signature.category == "ldap":
                    self.stats["ldap_attacks"] += 1
        
        return matches
    
    def _analyze_smb_traffic(self, ip: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze SMB traffic for attacks"""
        analysis = {
            "suspicious": False,
            "attack_type": None,
            "confidence": 0.0,
            "indicators": []
        }
        
        # Check for common attack indicators
        command = str(event_data.get("command", "")).upper()
        path = str(event_data.get("path", "")).upper()
        share = str(event_data.get("share", "")).upper()
        
        # Admin share access
        if share in ["ADMIN$", "C$", "IPC$"]:
            analysis["suspicious"] = True
            analysis["indicators"].append(f"Admin share access: {share}")
            analysis["confidence"] += 0.3
        
        # Registry access
        if "WINREG" in path or "REGISTRY" in path:
            analysis["suspicious"] = True
            analysis["indicators"].append("Registry access via SMB")
            analysis["confidence"] += 0.2
        
        # Service operations
        if any(svc in command for svc in ["SVCCTL", "SCMR", "SERVICE"]):
            analysis["suspicious"] = True
            analysis["indicators"].append("Service control operations")
            analysis["attack_type"] = "smb_exec"
            analysis["confidence"] += 0.3
        
        # Named pipe abuse
        if "\\PIPE\\" in path:
            pipe_name = path.split("\\PIPE\\")[-1]
            suspicious_pipes = ["PSEXESVC", "REMCOMSVC", "WINREG", "SAMR", "LSARPC"]
            if any(p in pipe_name for p in suspicious_pipes):
                analysis["suspicious"] = True
                analysis["indicators"].append(f"Suspicious named pipe: {pipe_name}")
                analysis["confidence"] += 0.3
        
        # Rapid SMB session creation
        recent_sessions = [
            e for e in self.network_events[ip]
            if e.protocol == "SMB" and time.time() - e.timestamp < 60
        ]
        if len(recent_sessions) > 20:
            analysis["suspicious"] = True
            analysis["indicators"].append("Rapid SMB session creation")
            analysis["confidence"] += 0.2
        
        return analysis
    
    def _analyze_kerberos_traffic(self, ip: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Kerberos traffic for attacks"""
        analysis = {
            "suspicious": False,
            "attack_type": None,
            "confidence": 0.0,
            "indicators": []
        }
        
        ticket_type = event_data.get("ticket_type", "")
        encryption = event_data.get("encryption_type", "")
        service = str(event_data.get("service_principal", ""))
        
        # Check for weak encryption (often used in attacks)
        if "RC4" in encryption or "DES" in encryption:
            analysis["suspicious"] = True
            analysis["indicators"].append(f"Weak encryption: {encryption}")
            analysis["confidence"] += 0.2
        
        # Multiple SPN requests (Kerberoasting)
        recent_spn_requests = [
            e for e in self.network_events[ip]
            if "SPN" in str(e.details) and time.time() - e.timestamp < 300
        ]
        if len(recent_spn_requests) > 5:
            analysis["suspicious"] = True
            analysis["attack_type"] = "kerberoasting"
            analysis["indicators"].append(f"Multiple SPN requests: {len(recent_spn_requests)}")
            analysis["confidence"] += 0.4
        
        # Unusual ticket lifetime
        lifetime = event_data.get("ticket_lifetime", 0)
        if lifetime > 864000:  # > 10 days
            analysis["suspicious"] = True
            analysis["indicators"].append("Unusually long ticket lifetime")
            analysis["confidence"] += 0.3
        
        # krbtgt access
        if "krbtgt" in service.lower():
            analysis["suspicious"] = True
            analysis["attack_type"] = "golden_ticket"
            analysis["indicators"].append("krbtgt service access")
            analysis["confidence"] += 0.5
        
        return analysis
    
    def _analyze_ldap_traffic(self, ip: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze LDAP traffic for attacks"""
        analysis = {
            "suspicious": False,
            "attack_type": None,
            "confidence": 0.0,
            "indicators": []
        }
        
        query = str(event_data.get("ldap_filter", ""))
        
        # LDAP injection patterns
        injection_patterns = [
            r"\(\&.*\(\|",  # Combined AND/OR
            r"\*\)\(",      # Wildcard tricks
            r"admin\*",     # Admin wildcards
            r"\)\)\(",      # Parenthesis manipulation
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                analysis["suspicious"] = True
                analysis["attack_type"] = "ldap_injection"
                analysis["indicators"].append("LDAP injection pattern detected")
                analysis["confidence"] += 0.4
                break
        
        # Enumeration attempts
        if any(attr in query.lower() for attr in ["*", "objectclass=*", "cn=*"]):
            recent_queries = [
                e for e in self.network_events[ip]
                if e.protocol == "LDAP" and time.time() - e.timestamp < 60
            ]
            if len(recent_queries) > 10:
                analysis["suspicious"] = True
                analysis["indicators"].append("LDAP enumeration detected")
                analysis["confidence"] += 0.3
        
        return analysis
    
    def _analyze_rpc_traffic(self, ip: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze RPC traffic for attacks"""
        analysis = {
            "suspicious": False,
            "attack_type": None,
            "confidence": 0.0,
            "indicators": []
        }
        
        interface = str(event_data.get("interface_uuid", ""))
        operation = str(event_data.get("operation", ""))
        
        # Suspicious RPC interfaces
        suspicious_interfaces = {
            "ITaskSchedulerService": "scheduled_task_exec",
            "IRemUnknown2": "dcom_exec",
            "DCOM": "dcom_exec",
            "SVCCTL": "service_exec"
        }
        
        for iface, attack in suspicious_interfaces.items():
            if iface.lower() in interface.lower():
                analysis["suspicious"] = True
                analysis["attack_type"] = attack
                analysis["indicators"].append(f"Suspicious RPC interface: {iface}")
                analysis["confidence"] += 0.4
        
        # WMI-based execution
        if "Win32_Process" in operation and "Create" in operation:
            analysis["suspicious"] = True
            analysis["attack_type"] = "wmi_exec"
            analysis["indicators"].append("WMI process creation")
            analysis["confidence"] += 0.4
        
        return analysis
    
    def _check_ntlm_relay(self, ip: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for NTLM relay attacks"""
        analysis = {
            "is_relay": False,
            "indicators": []
        }
        
        auth_type = str(event_data.get("auth_type", ""))
        
        if "NTLM" in auth_type.upper():
            # Check for relay indicators
            flags = event_data.get("ntlm_flags", {})
            
            # Signing disabled (common in relays)
            if not flags.get("signing_enabled", True):
                analysis["is_relay"] = True
                analysis["indicators"].append("NTLM signing disabled")
            
            # MIC removed (relay indicator)
            if not event_data.get("mic_present", True):
                analysis["is_relay"] = True
                analysis["indicators"].append("MIC not present (relay indicator)")
                self.stats["ntlm_relay_attempts"] += 1
            
            # Same authentication from multiple IPs
            username = event_data.get("username")
            if username:
                recent_auths = [
                    e for e in self.auth_attempts.values()
                    for attempt in e
                    if attempt["username"] == username and time.time() - attempt["timestamp"] < 60
                ]
                
                unique_ips = len(set(self.auth_attempts.keys()))
                if unique_ips > 3 and len(recent_auths) > 5:
                    analysis["is_relay"] = True
                    analysis["indicators"].append(f"Same user from {unique_ips} IPs")
        
        return analysis
    
    def _check_attack_chains(self, ip: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for known attack chains"""
        analysis = {
            "chain_detected": False,
            "chain_type": None
        }
        
        # Get recent events from this IP
        recent_events = [
            e for e in self.network_events[ip]
            if time.time() - e.timestamp < 300  # Last 5 minutes
        ]
        
        # PsExec chain: SMB connection → Service creation → Named pipe
        psexec_chain = [
            any("ADMIN$" in str(e.details) for e in recent_events),
            any("SERVICE" in str(e.details) for e in recent_events),
            any("PIPE" in str(e.details) for e in recent_events)
        ]
        if all(psexec_chain):
            analysis["chain_detected"] = True
            analysis["chain_type"] = "psexec_execution"
        
        # Secretsdump chain: SMB → Registry access → NTDS access
        secretsdump_chain = [
            any("SMB" in e.protocol for e in recent_events),
            any("REGISTRY" in str(e.details) or "WINREG" in str(e.details) for e in recent_events),
            any("NTDS" in str(e.details) or "SAM" in str(e.details) for e in recent_events)
        ]
        if all(secretsdump_chain):
            analysis["chain_detected"] = True
            analysis["chain_type"] = "credential_dumping"
            self.stats["secret_dumps"] += 1
        
        return analysis
    
    def _check_behavioral_anomalies(self, ip: str) -> Dict[str, Any]:
        """Check for behavioral anomalies"""
        analysis = {
            "anomalous": False,
            "confidence_boost": 0.0,
            "anomalies": []
        }
        
        # Rapid authentication attempts
        recent_auth = [
            a for a in self.auth_attempts[ip]
            if time.time() - a["timestamp"] < 60
        ]
        if len(recent_auth) > 10:
            analysis["anomalous"] = True
            analysis["anomalies"].append("Rapid authentication attempts")
            analysis["confidence_boost"] += 0.2
        
        # Multiple failed authentications
        failed_auth = [a for a in recent_auth if not a.get("success", False)]
        if len(failed_auth) > 5:
            analysis["anomalous"] = True
            analysis["anomalies"].append("Multiple failed authentications")
            analysis["confidence_boost"] += 0.2
        
        # Protocol switching (sign of automated tools)
        recent_events = [
            e for e in self.network_events[ip]
            if time.time() - e.timestamp < 60
        ]
        protocols = set(e.protocol for e in recent_events)
        if len(protocols) > 3:
            analysis["anomalous"] = True
            analysis["anomalies"].append(f"Rapid protocol switching: {', '.join(protocols)}")
            analysis["confidence_boost"] += 0.1
        
        return analysis
    
    def _handle_attack(self, ip: str, analysis: Dict[str, Any]):
        """Handle detected attack"""
        self.stats["attacks_detected"] += 1
        
        # Block IP
        self.blocked_ips[ip] = {
            "timestamp": time.time(),
            "reason": f"Impacket attack: {analysis['attack_type']}",
            "attack_type": analysis["attack_type"],
            "confidence": analysis["confidence"],
            "indicators": analysis["indicators"]
        }
        
        self.stats["ips_blocked"] += 1
        self.suspicious_ips.add(ip)
        
        # Log attack
        print(f"[IMPACKET ATTACK] Blocked {ip} - {analysis['attack_type']} (confidence: {analysis['confidence']:.2f})")
        print(f"  Indicators: {', '.join(analysis['indicators'])}")
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on attack type"""
        recommendations = []
        
        attack_type = analysis.get("attack_type", "")
        
        if "smb" in attack_type or "psexec" in attack_type:
            recommendations.extend([
                "Enable SMB signing on all systems",
                "Restrict ADMIN$ and C$ share access",
                "Monitor for service installation events",
                "Implement least-privilege access"
            ])
        
        if "kerberos" in attack_type or "ticket" in attack_type:
            recommendations.extend([
                "Reset krbtgt password twice (if Golden Ticket suspected)",
                "Enable Kerberos encryption downgrade detection",
                "Monitor for unusual ticket lifetimes",
                "Implement Protected Users security group"
            ])
        
        if "ntlm" in attack_type or "relay" in attack_type:
            recommendations.extend([
                "Enable NTLM signing and EPA (Extended Protection for Authentication)",
                "Disable NTLM where possible, use Kerberos",
                "Enable SMB signing enforcement",
                "Implement LDAP signing and channel binding"
            ])
        
        if "secret" in attack_type or "dump" in attack_type:
            recommendations.extend([
                "Audit access to NTDS.DIT and registry hives",
                "Implement credential rotation policy",
                "Enable LSASS protection (RunAsPPL)",
                "Monitor for volume shadow copy operations"
            ])
        
        return recommendations
