"""
Pattern Detector - Identifies AI/ML attack behavioral patterns
"""
import re
import time
import hashlib
from typing import Dict, List, Any, Tuple
from collections import deque, defaultdict
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass, field


@dataclass
class RequestMetadata:
    """Metadata for a single request"""
    timestamp: float
    source_ip: str
    user_agent: str
    endpoint: str
    query_params: Dict[str, Any]
    headers: Dict[str, str]
    content: str
    session_id: str = ""
    
    def fingerprint(self) -> str:
        """Generate unique fingerprint for this request"""
        data = f"{self.source_ip}{self.user_agent}{self.session_id}"
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class DetectionResult:
    """Result of pattern detection"""
    is_suspicious: bool
    confidence: float
    detected_patterns: List[str]
    risk_score: float
    evidence: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class PatternDetector:
    """Detects bot and AI/ML attack patterns"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.request_history = defaultdict(lambda: deque(maxlen=1000))
        self.timing_windows = defaultdict(lambda: deque(maxlen=100))
        self.fingerprint_cache = {}
        
    def analyze_request(self, request: RequestMetadata) -> DetectionResult:
        """
        Analyze a request for suspicious patterns
        """
        detected_patterns = []
        evidence = {}
        risk_score = 0.0
        
        # Store request in history
        fingerprint = request.fingerprint()
        self.request_history[fingerprint].append(request)
        self.timing_windows[fingerprint].append(request.timestamp)
        
        # Run detection checks
        timing_result = self._check_timing_patterns(fingerprint)
        if timing_result[0]:
            detected_patterns.append("timing_anomaly")
            evidence["timing"] = timing_result[1]
            risk_score += timing_result[2]
            
        behavioral_result = self._check_behavioral_patterns(fingerprint)
        if behavioral_result[0]:
            detected_patterns.append("behavioral_anomaly")
            evidence["behavioral"] = behavioral_result[1]
            risk_score += behavioral_result[2]
            
        content_result = self._check_content_patterns(request)
        if content_result[0]:
            detected_patterns.extend(content_result[1])
            evidence["content"] = content_result[2]
            risk_score += content_result[3]
            
        ml_attack_result = self._check_ml_attack_patterns(fingerprint, request)
        if ml_attack_result[0]:
            detected_patterns.extend(ml_attack_result[1])
            evidence["ml_attack"] = ml_attack_result[2]
            risk_score += ml_attack_result[3]
        
        # Determine if suspicious
        is_suspicious = risk_score > 30  # Threshold from config
        confidence = min(risk_score / 100.0, 1.0)
        
        return DetectionResult(
            is_suspicious=is_suspicious,
            confidence=confidence,
            detected_patterns=detected_patterns,
            risk_score=risk_score,
            evidence=evidence
        )
    
    def _check_timing_patterns(self, fingerprint: str) -> Tuple[bool, Dict, float]:
        """Check for suspicious timing patterns"""
        timestamps = list(self.timing_windows[fingerprint])
        
        if len(timestamps) < 5:
            return False, {}, 0.0
        
        # Calculate inter-request intervals
        intervals = np.diff(timestamps)
        
        # Check for suspiciously consistent timing
        if len(intervals) > 0:
            mean_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            
            # Coefficient of variation
            cv = std_interval / mean_interval if mean_interval > 0 else 0
            
            # Bots have very consistent timing (low CV)
            if cv < 0.1:  # Very consistent
                evidence = {
                    "pattern": "consistent_timing",
                    "coefficient_of_variation": float(cv),
                    "mean_interval": float(mean_interval),
                    "std_deviation": float(std_interval)
                }
                return True, evidence, 60.0
            
            # Check for burst activity
            recent_timestamps = [t for t in timestamps if t > time.time() - 60]
            requests_per_second = len(recent_timestamps) / 60.0
            
            if requests_per_second > 5.0:
                evidence = {
                    "pattern": "burst_activity",
                    "requests_per_second": requests_per_second
                }
                return True, evidence, 70.0
        
        return False, {}, 0.0
    
    def _check_behavioral_patterns(self, fingerprint: str) -> Tuple[bool, Dict, float]:
        """Check for bot-like behavioral patterns"""
        requests = list(self.request_history[fingerprint])
        
        if len(requests) < 10:
            return False, {}, 0.0
        
        # Check for perfect patterns (no human errors)
        endpoints = [r.endpoint for r in requests]
        
        # Systematic enumeration detection
        if self._is_systematic_enumeration(endpoints):
            evidence = {
                "pattern": "systematic_enumeration",
                "endpoints_count": len(set(endpoints)),
                "sequential": True
            }
            return True, evidence, 75.0
        
        # Check for token abuse (same token, multiple IPs)
        session_ids = [r.session_id for r in requests if r.session_id]
        source_ips = [r.source_ip for r in requests]
        
        if session_ids and len(set(source_ips)) > 3:
            evidence = {
                "pattern": "token_abuse",
                "unique_ips": len(set(source_ips)),
                "same_session": session_ids[0] if session_ids else None
            }
            return True, evidence, 80.0
        
        return False, {}, 0.0
    
    def _check_content_patterns(self, request: RequestMetadata) -> Tuple[bool, List[str], Dict, float]:
        """Check request content for attack patterns"""
        patterns_detected = []
        evidence = {}
        risk_score = 0.0
        
        content = request.content + " ".join(str(v) for v in request.query_params.values())
        
        # SQL Injection patterns
        sql_patterns = [
            r"(?i)(union|select|insert|update|delete|drop|alter).*(?i)(from|where|table)",
            r"(?i)('\s*or\s*'1'\s*=\s*'1)",
            r"(?i)(exec|execute|xp_cmdshell)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, content):
                patterns_detected.append("sql_injection")
                evidence["sql_injection"] = {"matched_pattern": pattern}
                risk_score += 90.0
                break
        
        # XSS patterns
        xss_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"onerror\s*=",
            r"onload\s*="
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                patterns_detected.append("xss_attempt")
                evidence["xss"] = {"matched_pattern": pattern}
                risk_score += 85.0
                break
        
        # Directory traversal
        if re.search(r"\.\./|\.\.\\", content):
            patterns_detected.append("directory_traversal")
            evidence["directory_traversal"] = {"detected": True}
            risk_score += 80.0
        
        return len(patterns_detected) > 0, patterns_detected, evidence, risk_score
    
    def _check_ml_attack_patterns(self, fingerprint: str, request: RequestMetadata) -> Tuple[bool, List[str], Dict, float]:
        """Detect ML-specific attack patterns"""
        patterns_detected = []
        evidence = {}
        risk_score = 0.0
        
        requests = list(self.request_history[fingerprint])
        
        if len(requests) < 10:
            return False, [], {}, 0.0
        
        # Model inversion - probing for confidence scores
        if self._detect_model_inversion(requests):
            patterns_detected.append("model_inversion")
            evidence["model_inversion"] = {
                "confidence_probing": True,
                "boundary_exploration": True
            }
            risk_score += 90.0
        
        # Membership inference - repeated similar queries
        if self._detect_membership_inference(requests):
            patterns_detected.append("membership_inference")
            evidence["membership_inference"] = {
                "repeated_queries": True,
                "differential_analysis": True
            }
            risk_score += 85.0
        
        # Model extraction - systematic I/O collection
        if self._detect_model_extraction(requests):
            patterns_detected.append("model_extraction")
            evidence["model_extraction"] = {
                "systematic_collection": True,
                "coverage": len(set(r.query_params for r in requests))
            }
            risk_score += 95.0
        
        return len(patterns_detected) > 0, patterns_detected, evidence, risk_score
    
    def _is_systematic_enumeration(self, endpoints: List[str]) -> bool:
        """Detect if endpoints are being accessed systematically"""
        # Check for sequential patterns (e.g., /api/user/1, /api/user/2, ...)
        numeric_suffixes = []
        for endpoint in endpoints:
            match = re.search(r'/(\d+)/?$', endpoint)
            if match:
                numeric_suffixes.append(int(match.group(1)))
        
        if len(numeric_suffixes) > 5:
            # Check if numbers are sequential
            sorted_nums = sorted(numeric_suffixes)
            diffs = np.diff(sorted_nums)
            if np.all(diffs <= 2):  # Sequential or close to sequential
                return True
        
        return False
    
    def _detect_model_inversion(self, requests: List[RequestMetadata]) -> bool:
        """Detect model inversion attacks"""
        # Look for patterns that suggest boundary exploration
        # or confidence score probing
        
        # Check if queries are exploring decision boundaries
        query_variations = []
        for req in requests[-20:]:  # Last 20 requests
            query_str = str(req.query_params)
            query_variations.append(query_str)
        
        # High variation suggests boundary exploration
        unique_ratio = len(set(query_variations)) / len(query_variations)
        return unique_ratio > 0.8
    
    def _detect_membership_inference(self, requests: List[RequestMetadata]) -> bool:
        """Detect membership inference attacks"""
        # Look for repeated similar queries with slight variations
        query_hashes = []
        for req in requests[-20:]:
            query_str = str(sorted(req.query_params.items()))
            query_hashes.append(hashlib.md5(query_str.encode()).hexdigest())
        
        # Check for duplicate or near-duplicate queries
        unique_queries = len(set(query_hashes))
        total_queries = len(query_hashes)
        
        # Low unique ratio suggests repeated queries
        return unique_queries < total_queries * 0.5
    
    def _detect_model_extraction(self, requests: List[RequestMetadata]) -> bool:
        """Detect model extraction attempts"""
        # Systematic input/output collection patterns
        
        # Check if requests cover a wide parameter space systematically
        all_params = set()
        for req in requests:
            for key in req.query_params.keys():
                all_params.add(key)
        
        # Wide parameter coverage suggests extraction
        return len(all_params) > 10 and len(requests) > 50
