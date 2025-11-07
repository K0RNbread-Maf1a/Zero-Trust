"""
Flood Protection - Advanced DoS/DDoS and brute-force attack prevention

Features:
- Rate limiting (per IP, per endpoint, global)
- Progressive penalties (exponential backoff)
- Distributed attack detection (DDoS)
- Brute-force prevention (login attempts, API abuse)
- Adaptive thresholds (learns normal traffic)
- Automatic IP blocking with auto-expiry
- Challenge-response systems (CAPTCHA-like)
- Connection throttling
- Resource exhaustion prevention
"""
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import secrets


@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests: int  # Number of requests
    window: int    # Time window in seconds
    penalty: int   # Penalty duration in seconds


@dataclass
class BlockedIP:
    """Blocked IP information"""
    ip: str
    reason: str
    blocked_at: float
    expires_at: float
    block_count: int = 1
    auto_expires: bool = True


@dataclass
class ConnectionInfo:
    """Connection tracking information"""
    ip: str
    first_request: float
    last_request: float
    request_count: int = 0
    failed_attempts: int = 0
    challenge_required: bool = False
    challenge_token: Optional[str] = None
    penalty_level: int = 0


class FloodProtection:
    """
    Advanced flood protection system
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Rate limiting configurations
        self.rate_limits = {
            "global": RateLimit(1000, 60, 60),      # 1000 req/min globally
            "per_ip": RateLimit(100, 60, 300),      # 100 req/min per IP
            "per_endpoint": RateLimit(20, 60, 60),  # 20 req/min per endpoint
            "login": RateLimit(5, 300, 3600),       # 5 login attempts per 5 min
            "api_key": RateLimit(1000, 3600, 7200), # 1000 API calls per hour
        }
        
        # Tracking
        self.request_history = defaultdict(lambda: deque(maxlen=1000))
        self.connections = {}  # ip -> ConnectionInfo
        self.blocked_ips = {}  # ip -> BlockedIP
        self.failed_logins = defaultdict(lambda: deque(maxlen=100))
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "dos_detected": 0,
            "ddos_detected": 0,
            "brute_force_blocked": 0,
            "ips_blocked": 0
        }
        
        # Adaptive thresholds
        self.baseline_rps = 10.0  # Requests per second baseline
        self.learning = True
        
    def check_request(self, request_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request should be allowed
        Returns: (allowed, response_data)
        """
        self.stats["total_requests"] += 1
        
        ip = request_data.get("ip", "unknown")
        endpoint = request_data.get("endpoint", "/")
        timestamp = time.time()
        
        # Clean up expired blocks
        self._cleanup_expired_blocks()
        
        # Check if IP is blocked
        if ip in self.blocked_ips:
            block_info = self.blocked_ips[ip]
            if timestamp < block_info.expires_at:
                self.stats["blocked_requests"] += 1
                return False, {
                    "blocked": True,
                    "reason": block_info.reason,
                    "expires_in": int(block_info.expires_at - timestamp),
                    "message": f"IP blocked for {block_info.reason}. Expires in {int(block_info.expires_at - timestamp)}s"
                }
        
        # Get or create connection info
        if ip not in self.connections:
            self.connections[ip] = ConnectionInfo(
                ip=ip,
                first_request=timestamp,
                last_request=timestamp
            )
        
        conn = self.connections[ip]
        conn.last_request = timestamp
        conn.request_count += 1
        
        # Check if challenge is required
        if conn.challenge_required:
            challenge_response = request_data.get("challenge_response")
            if not challenge_response or challenge_response != conn.challenge_token:
                return False, {
                    "challenge_required": True,
                    "message": "Complete challenge to continue",
                    "challenge": self._generate_challenge()
                }
            else:
                # Challenge passed
                conn.challenge_required = False
                conn.challenge_token = None
                conn.penalty_level = max(0, conn.penalty_level - 1)
        
        # Apply penalty delay if needed
        if conn.penalty_level > 0:
            penalty_delay = 2 ** conn.penalty_level  # Exponential backoff
            if timestamp - conn.last_request < penalty_delay:
                return False, {
                    "rate_limited": True,
                    "retry_after": int(penalty_delay),
                    "message": f"Rate limited. Retry after {penalty_delay}s"
                }
        
        # Check rate limits
        rate_check = self._check_rate_limits(ip, endpoint, timestamp)
        if not rate_check["allowed"]:
            self._apply_penalty(ip, rate_check["violation"])
            return False, rate_check
        
        # Check for DoS/DDoS patterns
        dos_check = self._check_dos_patterns(ip, timestamp)
        if dos_check["is_attack"]:
            self._block_ip(ip, dos_check["attack_type"], duration=3600)
            return False, {
                "blocked": True,
                "reason": dos_check["attack_type"],
                "message": "Attack pattern detected. IP blocked."
            }
        
        # Check for brute force on login endpoints
        if self._is_auth_endpoint(endpoint):
            brute_check = self._check_brute_force(ip, endpoint)
            if not brute_check["allowed"]:
                return False, brute_check
        
        # Request allowed
        self._record_request(ip, endpoint, timestamp)
        return True, {"allowed": True}
    
    def report_failed_auth(self, ip: str, endpoint: str):
        """Report a failed authentication attempt"""
        timestamp = time.time()
        self.failed_logins[ip].append({
            "endpoint": endpoint,
            "timestamp": timestamp
        })
        
        # Check for brute force
        recent_failures = [
            f for f in self.failed_logins[ip]
            if timestamp - f["timestamp"] < 300  # Last 5 minutes
        ]
        
        if len(recent_failures) >= 5:
            # Brute force detected
            self.stats["brute_force_blocked"] += 1
            self._block_ip(ip, "brute_force_auth", duration=3600)
            
            if ip in self.connections:
                self.connections[ip].failed_attempts += 1
    
    def report_successful_auth(self, ip: str):
        """Report successful authentication (resets counters)"""
        if ip in self.failed_logins:
            self.failed_logins[ip].clear()
        
        if ip in self.connections:
            self.connections[ip].failed_attempts = 0
            self.connections[ip].penalty_level = 0
    
    def manually_block_ip(self, ip: str, reason: str, duration: int = 86400):
        """Manually block an IP address"""
        self._block_ip(ip, f"manual: {reason}", duration, auto_expires=False)
    
    def unblock_ip(self, ip: str):
        """Manually unblock an IP address"""
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
    
    def get_blocked_ips(self) -> List[BlockedIP]:
        """Get all currently blocked IPs"""
        return list(self.blocked_ips.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get protection statistics"""
        active_blocks = len(self.blocked_ips)
        active_connections = len(self.connections)
        
        # Calculate current RPS
        now = time.time()
        recent_requests = sum(
            1 for history in self.request_history.values()
            for ts in history
            if now - ts < 60
        )
        current_rps = recent_requests / 60.0
        
        return {
            **self.stats,
            "active_blocks": active_blocks,
            "active_connections": active_connections,
            "current_rps": round(current_rps, 2),
            "baseline_rps": round(self.baseline_rps, 2)
        }
    
    def get_connection_info(self, ip: str) -> Optional[ConnectionInfo]:
        """Get connection info for an IP"""
        return self.connections.get(ip)
    
    # ==================== Private Methods ====================
    
    def _check_rate_limits(self, ip: str, endpoint: str, timestamp: float) -> Dict[str, Any]:
        """Check all rate limits"""
        
        # Global rate limit
        global_history = self.request_history["global"]
        recent_global = sum(1 for ts in global_history if timestamp - ts < self.rate_limits["global"].window)
        
        if recent_global >= self.rate_limits["global"].requests:
            return {
                "allowed": False,
                "violation": "global_rate_limit",
                "message": "Global rate limit exceeded",
                "retry_after": self.rate_limits["global"].penalty
            }
        
        # Per-IP rate limit
        ip_history = self.request_history[f"ip:{ip}"]
        recent_ip = sum(1 for ts in ip_history if timestamp - ts < self.rate_limits["per_ip"].window)
        
        if recent_ip >= self.rate_limits["per_ip"].requests:
            return {
                "allowed": False,
                "violation": "ip_rate_limit",
                "message": "Per-IP rate limit exceeded",
                "retry_after": self.rate_limits["per_ip"].penalty
            }
        
        # Per-endpoint rate limit
        endpoint_key = f"endpoint:{ip}:{endpoint}"
        endpoint_history = self.request_history[endpoint_key]
        recent_endpoint = sum(1 for ts in endpoint_history if timestamp - ts < self.rate_limits["per_endpoint"].window)
        
        if recent_endpoint >= self.rate_limits["per_endpoint"].requests:
            return {
                "allowed": False,
                "violation": "endpoint_rate_limit",
                "message": f"Rate limit for {endpoint} exceeded",
                "retry_after": self.rate_limits["per_endpoint"].penalty
            }
        
        return {"allowed": True}
    
    def _check_dos_patterns(self, ip: str, timestamp: float) -> Dict[str, Any]:
        """Check for DoS/DDoS attack patterns"""
        
        # Get request history for this IP
        ip_history = self.request_history[f"ip:{ip}"]
        
        if len(ip_history) < 10:
            return {"is_attack": False}
        
        # Calculate requests in last 10 seconds
        recent_10s = sum(1 for ts in ip_history if timestamp - ts < 10)
        
        # Check for DoS (single source flooding)
        if recent_10s > 50:  # More than 50 requests in 10 seconds
            self.stats["dos_detected"] += 1
            return {
                "is_attack": True,
                "attack_type": "dos_flood",
                "requests_per_10s": recent_10s
            }
        
        # Check for distributed attack patterns
        global_history = self.request_history["global"]
        global_recent = sum(1 for ts in global_history if timestamp - ts < 10)
        
        # If global traffic is way above baseline
        if global_recent > self.baseline_rps * 10 * 10:  # 10x baseline for 10 seconds
            # Check how many unique IPs
            unique_ips = set()
            for key, history in self.request_history.items():
                if key.startswith("ip:"):
                    recent = sum(1 for ts in history if timestamp - ts < 10)
                    if recent > 5:
                        unique_ips.add(key)
            
            # DDoS if many sources
            if len(unique_ips) > 10:
                self.stats["ddos_detected"] += 1
                return {
                    "is_attack": True,
                    "attack_type": "ddos_flood",
                    "attack_sources": len(unique_ips)
                }
        
        return {"is_attack": False}
    
    def _check_brute_force(self, ip: str, endpoint: str) -> Dict[str, Any]:
        """Check for brute force attacks on authentication endpoints"""
        
        recent_failures = [
            f for f in self.failed_logins[ip]
            if time.time() - f["timestamp"] < 300
        ]
        
        if len(recent_failures) >= 3:
            # Require challenge after 3 failures
            if ip in self.connections:
                conn = self.connections[ip]
                if not conn.challenge_required:
                    conn.challenge_required = True
                    conn.challenge_token = secrets.token_urlsafe(16)
            
            return {
                "allowed": False,
                "brute_force_detected": True,
                "challenge_required": True,
                "message": "Multiple failed attempts. Complete challenge to continue."
            }
        
        return {"allowed": True}
    
    def _apply_penalty(self, ip: str, violation: str):
        """Apply progressive penalty to an IP"""
        if ip in self.connections:
            conn = self.connections[ip]
            conn.penalty_level += 1
            
            # After 3 violations, require challenge
            if conn.penalty_level >= 3:
                conn.challenge_required = True
                conn.challenge_token = secrets.token_urlsafe(16)
            
            # After 5 violations, block temporarily
            if conn.penalty_level >= 5:
                duration = 2 ** conn.penalty_level  # Exponential
                self._block_ip(ip, f"repeated_{violation}", duration)
    
    def _block_ip(self, ip: str, reason: str, duration: int, auto_expires: bool = True):
        """Block an IP address"""
        timestamp = time.time()
        
        if ip in self.blocked_ips:
            # Increase block duration for repeat offenders
            existing = self.blocked_ips[ip]
            existing.block_count += 1
            existing.expires_at = timestamp + (duration * existing.block_count)
            existing.reason = f"{reason} (x{existing.block_count})"
        else:
            self.blocked_ips[ip] = BlockedIP(
                ip=ip,
                reason=reason,
                blocked_at=timestamp,
                expires_at=timestamp + duration,
                auto_expires=auto_expires
            )
            self.stats["ips_blocked"] += 1
    
    def _cleanup_expired_blocks(self):
        """Remove expired IP blocks"""
        timestamp = time.time()
        expired = [
            ip for ip, block in self.blocked_ips.items()
            if block.auto_expires and timestamp >= block.expires_at
        ]
        
        for ip in expired:
            del self.blocked_ips[ip]
    
    def _record_request(self, ip: str, endpoint: str, timestamp: float):
        """Record a request in history"""
        self.request_history["global"].append(timestamp)
        self.request_history[f"ip:{ip}"].append(timestamp)
        self.request_history[f"endpoint:{ip}:{endpoint}"].append(timestamp)
        
        # Update baseline (simple moving average)
        if self.learning:
            global_history = self.request_history["global"]
            if len(global_history) > 100:
                recent_window = 60  # 1 minute
                recent_count = sum(1 for ts in global_history if timestamp - ts < recent_window)
                rps = recent_count / recent_window
                
                # Update baseline with exponential moving average
                alpha = 0.1
                self.baseline_rps = (alpha * rps) + ((1 - alpha) * self.baseline_rps)
    
    def _is_auth_endpoint(self, endpoint: str) -> bool:
        """Check if endpoint is authentication-related"""
        auth_patterns = [
            "/login", "/auth", "/signin", "/api/auth",
            "/oauth", "/token", "/session"
        ]
        return any(pattern in endpoint.lower() for pattern in auth_patterns)
    
    def _generate_challenge(self) -> Dict[str, Any]:
        """Generate a simple challenge for suspected bots"""
        # In production, this could be a CAPTCHA, proof-of-work, etc.
        a = secrets.randbelow(10)
        b = secrets.randbelow(10)
        
        return {
            "type": "math",
            "question": f"What is {a} + {b}?",
            "expected": str(a + b)
        }


class ConnectionThrottler:
    """
    Connection-level throttling for resource exhaustion prevention
    """
    
    def __init__(self, max_concurrent: int = 1000):
        self.max_concurrent = max_concurrent
        self.active_connections = {}
        self.connection_counts = defaultdict(int)
        
    def acquire_connection(self, ip: str) -> Tuple[bool, Optional[str]]:
        """Try to acquire a connection slot"""
        
        # Check global limit
        if len(self.active_connections) >= self.max_concurrent:
            return False, "Server at capacity"
        
        # Check per-IP limit (max 10 concurrent per IP)
        if self.connection_counts[ip] >= 10:
            return False, "Too many concurrent connections from your IP"
        
        # Acquire connection
        conn_id = secrets.token_urlsafe(16)
        self.active_connections[conn_id] = {
            "ip": ip,
            "acquired_at": time.time()
        }
        self.connection_counts[ip] += 1
        
        return True, conn_id
    
    def release_connection(self, conn_id: str):
        """Release a connection slot"""
        if conn_id in self.active_connections:
            ip = self.active_connections[conn_id]["ip"]
            del self.active_connections[conn_id]
            self.connection_counts[ip] -= 1
    
    def get_connection_count(self, ip: str) -> int:
        """Get number of active connections for an IP"""
        return self.connection_counts[ip]
