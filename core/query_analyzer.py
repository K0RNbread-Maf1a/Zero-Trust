"""
Query Analyzer - Multi-stage safety filter and attack pattern analyzer
Filters out legitimate queries before triggering defensive responses
"""
import re
import hashlib
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
import time


@dataclass
class SafetyCheckResult:
    """Result of safety verification"""
    is_safe: bool
    confidence: float
    stage: int
    reasons: List[str]
    indicators: Dict[str, Any]


class QueryAnalyzer:
    """
    Analyzes attacker queries and generates appropriate countermeasures
    Includes multi-stage safety filter to avoid false positives
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.safety_config = config.get("safety_filters", {})
        self.verification_stages = self.safety_config.get("verification_stages", [])
        self.whitelist_patterns = self.safety_config.get("whitelist_patterns", [])
        
        # Track user behavior for safety assessment
        self.user_history = defaultdict(list)
        self.reputation_scores = defaultdict(lambda: 0.5)  # Start neutral
        
    def analyze_query(self, query: str, metadata: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Analyze a query and determine if it's safe or suspicious
        Returns: (is_safe, analysis_details)
        """
        user_id = metadata.get("user_id", metadata.get("ip", "unknown"))
        
        # Multi-stage safety verification
        safety_result = self._multi_stage_safety_check(query, metadata, user_id)
        
        if safety_result.is_safe:
            # Update positive reputation
            self._update_reputation(user_id, positive=True)
            return True, {
                "safe": True,
                "stage": safety_result.stage,
                "reasons": safety_result.reasons,
                "confidence": safety_result.confidence
            }
        
        # Query appears suspicious - do deep analysis
        attack_analysis = self._analyze_attack_pattern(query, metadata)
        
        # Final safety check - could still be legitimate
        final_check = self._final_safety_verification(query, metadata, attack_analysis)
        
        if final_check.is_safe:
            return True, {
                "safe": True,
                "stage": "final_verification",
                "reasons": final_check.reasons
            }
        
        # Confirmed suspicious - update negative reputation
        self._update_reputation(user_id, positive=False)
        
        return False, {
            "safe": False,
            "attack_analysis": attack_analysis,
            "confidence": safety_result.confidence
        }
    
    def _multi_stage_safety_check(self, query: str, metadata: Dict[str, Any], 
                                   user_id: str) -> SafetyCheckResult:
        """
        Multi-stage verification process
        Each stage has increasing scrutiny
        """
        
        for stage_config in self.verification_stages:
            stage_num = stage_config.get("stage", 0)
            checks = stage_config.get("checks", [])
            threshold = stage_config.get("pass_threshold", 0.5)
            
            # Run checks for this stage
            safety_score = 0.0
            reasons = []
            indicators = {}
            
            if "ip_reputation" in checks:
                ip_score, ip_reasons = self._check_ip_reputation(metadata)
                safety_score += ip_score
                reasons.extend(ip_reasons)
                indicators["ip_reputation"] = ip_score
            
            if "rate_limit" in checks:
                rate_score, rate_reasons = self._check_rate_limit(user_id)
                safety_score += rate_score
                reasons.extend(rate_reasons)
                indicators["rate_limit"] = rate_score
            
            if "timing_patterns" in checks:
                timing_score, timing_reasons = self._check_timing_safety(user_id)
                safety_score += timing_score
                reasons.extend(timing_reasons)
                indicators["timing"] = timing_score
            
            if "content_analysis" in checks:
                content_score, content_reasons = self._check_content_safety(query)
                safety_score += content_score
                reasons.extend(content_reasons)
                indicators["content"] = content_score
            
            if "ml_pattern_detection" in checks:
                ml_score, ml_reasons = self._check_ml_safety(query, metadata)
                safety_score += ml_score
                reasons.extend(ml_reasons)
                indicators["ml_pattern"] = ml_score
            
            if "fingerprinting" in checks:
                fp_score, fp_reasons = self._check_fingerprint_safety(metadata)
                safety_score += fp_score
                reasons.extend(fp_reasons)
                indicators["fingerprint"] = fp_score
            
            # Normalize score
            num_checks = len(checks)
            normalized_score = safety_score / num_checks if num_checks > 0 else 0.0
            
            # If passed this stage, query is considered safe
            if normalized_score >= threshold:
                return SafetyCheckResult(
                    is_safe=True,
                    confidence=normalized_score,
                    stage=stage_num,
                    reasons=reasons,
                    indicators=indicators
                )
        
        # Failed all stages
        return SafetyCheckResult(
            is_safe=False,
            confidence=0.0,
            stage=len(self.verification_stages),
            reasons=["Failed all safety verification stages"],
            indicators={}
        )
    
    def _check_ip_reputation(self, metadata: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Check IP reputation"""
        ip = metadata.get("ip", "")
        
        # Check if internal IP
        if self._is_internal_ip(ip):
            return 0.9, ["Internal IP address"]
        
        # Check reputation score
        reputation = self.reputation_scores.get(ip, 0.5)
        
        if reputation > 0.7:
            return 0.8, [f"Good IP reputation: {reputation:.2f}"]
        elif reputation > 0.4:
            return 0.5, [f"Neutral IP reputation: {reputation:.2f}"]
        else:
            return 0.2, [f"Poor IP reputation: {reputation:.2f}"]
    
    def _check_rate_limit(self, user_id: str) -> Tuple[float, List[str]]:
        """Check if within reasonable rate limits"""
        recent_requests = [r for r in self.user_history[user_id] 
                          if r["timestamp"] > time.time() - 60]
        
        requests_per_minute = len(recent_requests)
        
        if requests_per_minute < 10:
            return 0.9, ["Normal request rate"]
        elif requests_per_minute < 30:
            return 0.6, ["Elevated request rate"]
        else:
            return 0.2, ["Excessive request rate"]
    
    def _check_timing_safety(self, user_id: str) -> Tuple[float, List[str]]:
        """Check for human-like timing patterns"""
        history = self.user_history[user_id]
        
        if len(history) < 5:
            return 0.7, ["Insufficient history"]
        
        # Check for human errors (backtracking, hesitation)
        has_backtracking = any(r.get("backtrack", False) for r in history[-10:])
        has_hesitation = any(r.get("hesitation", False) for r in history[-10:])
        
        if has_backtracking or has_hesitation:
            return 0.9, ["Human-like behavior detected (errors, hesitation)"]
        
        # Check timing variance
        timestamps = [r["timestamp"] for r in history[-20:]]
        if len(timestamps) > 1:
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            variance = sum((x - sum(intervals)/len(intervals))**2 for x in intervals) / len(intervals)
            
            if variance > 1.0:  # High variance = human
                return 0.8, ["Variable timing suggests human user"]
        
        return 0.5, ["Timing patterns inconclusive"]
    
    def _check_content_safety(self, query: str) -> Tuple[float, List[str]]:
        """Check if content suggests legitimate use"""
        reasons = []
        score = 0.5
        
        # Check for typos (humans make typos)
        if self._has_typos(query):
            score += 0.2
            reasons.append("Contains typos (human indicator)")
        
        # Check for natural language
        if self._is_natural_language(query):
            score += 0.2
            reasons.append("Natural language detected")
        
        # Check for obvious malicious patterns
        if self._has_obvious_attack_patterns(query):
            score -= 0.4
            reasons.append("Contains attack patterns")
        
        return min(max(score, 0.0), 1.0), reasons
    
    def _check_ml_safety(self, query: str, metadata: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Check if query is safe from ML attack perspective"""
        # Look for legitimate ML/AI usage vs attack
        
        if "research" in metadata.get("purpose", "").lower():
            return 0.8, ["Declared research purpose"]
        
        if metadata.get("authenticated", False) and metadata.get("internal", False):
            return 0.9, ["Authenticated internal user"]
        
        return 0.5, ["ML safety check inconclusive"]
    
    def _check_fingerprint_safety(self, metadata: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Check device fingerprint for legitimacy"""
        user_agent = metadata.get("user_agent", "")
        
        # Real browsers have complex user agents
        if len(user_agent) > 50 and "Mozilla" in user_agent:
            return 0.7, ["Standard browser user agent"]
        
        # Check for bot-like user agents
        bot_indicators = ["bot", "crawler", "spider", "scraper", "curl", "wget"]
        if any(indicator in user_agent.lower() for indicator in bot_indicators):
            return 0.2, ["Bot-like user agent"]
        
        return 0.5, ["User agent check inconclusive"]
    
    def _final_safety_verification(self, query: str, metadata: Dict[str, Any], 
                                   attack_analysis: Dict[str, Any]) -> SafetyCheckResult:
        """
        Final safety check before triggering countermeasures
        Last chance to avoid false positive
        """
        reasons = []
        is_safe = False
        
        # Check whitelist patterns
        for pattern_config in self.whitelist_patterns:
            pattern_name = pattern_config.get("name", "")
            indicators = pattern_config.get("indicators", [])
            conditions = pattern_config.get("conditions", [])
            
            # Check if matches whitelist pattern
            if self._matches_whitelist(query, metadata, indicators, conditions):
                reasons.append(f"Matches whitelist pattern: {pattern_name}")
                is_safe = True
                break
        
        # Check if attack confidence is low
        if attack_analysis.get("confidence", 1.0) < 0.5:
            reasons.append("Low confidence in attack detection")
            is_safe = True
        
        return SafetyCheckResult(
            is_safe=is_safe,
            confidence=1.0 if is_safe else 0.0,
            stage=999,  # Final stage
            reasons=reasons,
            indicators={}
        )
    
    def _analyze_attack_pattern(self, query: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Deep analysis of potential attack pattern"""
        analysis = {
            "query": query,
            "attack_type": None,
            "confidence": 0.0,
            "indicators": []
        }
        
        # Determine attack type
        if re.search(r"(?i)(select|union|insert)", query):
            analysis["attack_type"] = "sql_injection"
            analysis["confidence"] = 0.9
            analysis["indicators"].append("SQL keywords detected")
        
        elif re.search(r"\.\./|\.\.\\", query):
            analysis["attack_type"] = "directory_traversal"
            analysis["confidence"] = 0.85
            analysis["indicators"].append("Path traversal detected")
        
        elif self._looks_like_ml_probing(query, metadata):
            analysis["attack_type"] = "ml_attack"
            analysis["confidence"] = 0.75
            analysis["indicators"].append("ML probing patterns")
        
        else:
            analysis["attack_type"] = "unknown"
            analysis["confidence"] = 0.5
        
        return analysis
    
    def _update_reputation(self, user_id: str, positive: bool):
        """Update user reputation score"""
        current = self.reputation_scores[user_id]
        
        if positive:
            self.reputation_scores[user_id] = min(current + 0.05, 1.0)
        else:
            self.reputation_scores[user_id] = max(current - 0.1, 0.0)
    
    def _is_internal_ip(self, ip: str) -> bool:
        """Check if IP is internal"""
        internal_ranges = ["127.", "10.", "192.168.", "172.16."]
        return any(ip.startswith(prefix) for prefix in internal_ranges)
    
    def _has_typos(self, query: str) -> bool:
        """Simple typo detection"""
        # Check for common typos: double letters, missing spaces, etc.
        common_typos = [r"(\w)\1{2,}", r"\w{15,}"]  # Triple letters, very long words
        return any(re.search(pattern, query) for pattern in common_typos)
    
    def _is_natural_language(self, query: str) -> bool:
        """Check if query looks like natural language"""
        # Simple heuristic: presence of common words and sentence structure
        common_words = ["the", "is", "are", "what", "how", "can", "please", "help"]
        words = query.lower().split()
        common_count = sum(1 for word in words if word in common_words)
        return common_count > 0 and len(words) > 3
    
    def _has_obvious_attack_patterns(self, query: str) -> bool:
        """Check for obvious attack patterns"""
        attack_patterns = [
            r"<script",
            r"javascript:",
            r"(?i)drop\s+table",
            r"(?i)exec\s*\(",
            r"\.\./"
        ]
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in attack_patterns)
    
    def _looks_like_ml_probing(self, query: str, metadata: Dict[str, Any]) -> bool:
        """Check if query looks like ML model probing"""
        # Systematic parameter exploration
        has_many_params = len(metadata.get("params", {})) > 5
        has_numeric_params = any(isinstance(v, (int, float)) 
                                for v in metadata.get("params", {}).values())
        
        return has_many_params and has_numeric_params
    
    def _matches_whitelist(self, query: str, metadata: Dict[str, Any], 
                          indicators: List[str], conditions: List[str]) -> bool:
        """Check if query matches whitelist criteria"""
        
        # Check indicators
        for indicator in indicators:
            if indicator == "typos_present" and self._has_typos(query):
                return True
            elif indicator == "backtracking":
                # Would need more context from session history
                pass
            elif indicator == "mouse_movement" and metadata.get("has_mouse_events", False):
                return True
        
        # Check conditions
        for condition in conditions:
            if "valid_session" in condition and metadata.get("session_valid", False):
                return True
            elif "internal_ip" in condition and self._is_internal_ip(metadata.get("ip", "")):
                return True
        
        return False
