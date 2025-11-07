"""
Risk Scorer - Calculates and categorizes threat levels
"""
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Risk level categories"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAssessment:
    """Complete risk assessment for a request"""
    risk_level: RiskLevel
    risk_score: float
    threat_category: str
    recommended_actions: List[str]
    confidence: float
    evidence_summary: Dict[str, Any]


class RiskScorer:
    """Calculates risk scores and determines appropriate responses"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thresholds = config.get("response_policies", {}).get("risk_thresholds", {
            "low": 30,
            "medium": 60,
            "high": 80,
            "critical": 95
        })
        self.response_strategies = config.get("response_policies", {}).get("response_strategies", {})
        
    def assess_risk(self, risk_score: float, detected_patterns: List[str], 
                   evidence: Dict[str, Any]) -> RiskAssessment:
        """
        Assess overall risk and determine response strategy
        """
        # Determine risk level
        risk_level = self._calculate_risk_level(risk_score)
        
        # Categorize threat
        threat_category = self._categorize_threat(detected_patterns)
        
        # Get recommended actions
        recommended_actions = self._get_recommended_actions(risk_level, threat_category)
        
        # Calculate confidence based on evidence strength
        confidence = self._calculate_confidence(evidence, detected_patterns)
        
        # Summarize evidence
        evidence_summary = self._summarize_evidence(evidence, detected_patterns)
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_score=risk_score,
            threat_category=threat_category,
            recommended_actions=recommended_actions,
            confidence=confidence,
            evidence_summary=evidence_summary
        )
    
    def _calculate_risk_level(self, risk_score: float) -> RiskLevel:
        """Convert numeric risk score to risk level"""
        if risk_score >= self.thresholds.get("critical", 95):
            return RiskLevel.CRITICAL
        elif risk_score >= self.thresholds.get("high", 80):
            return RiskLevel.HIGH
        elif risk_score >= self.thresholds.get("medium", 60):
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _categorize_threat(self, detected_patterns: List[str]) -> str:
        """Categorize the type of threat based on detected patterns"""
        
        # Priority-based categorization
        if any(p in detected_patterns for p in ["model_extraction", "model_inversion"]):
            return "ml_attack"
        elif "sql_injection" in detected_patterns:
            return "sql_injection"
        elif "directory_traversal" in detected_patterns:
            return "directory_traversal"
        elif any(p in detected_patterns for p in ["timing_anomaly", "behavioral_anomaly"]):
            return "bot_activity"
        elif "xss_attempt" in detected_patterns:
            return "xss_attack"
        elif "membership_inference" in detected_patterns:
            return "ml_attack"
        else:
            return "general_suspicious"
    
    def _get_recommended_actions(self, risk_level: RiskLevel, threat_category: str) -> List[str]:
        """Get recommended response actions based on risk level"""
        
        base_actions = []
        
        if risk_level == RiskLevel.LOW:
            base_actions = self.response_strategies.get("monitor", {}).get("actions", ["log", "track"])
        elif risk_level == RiskLevel.MEDIUM:
            base_actions = self.response_strategies.get("honeypot", {}).get("actions", 
                ["log", "track", "serve_fake_data"])
        elif risk_level == RiskLevel.HIGH:
            base_actions = self.response_strategies.get("active_defense", {}).get("actions",
                ["log", "track", "serve_fake_data", "deploy_counter_agents", "rate_limit"])
        elif risk_level == RiskLevel.CRITICAL:
            base_actions = self.response_strategies.get("full_countermeasures", {}).get("actions",
                ["log", "track", "serve_fake_data", "deploy_counter_agents", 
                 "aggressive_rate_limit", "set_traps", "reverse_tracking"])
        
        # Add threat-specific actions
        threat_specific = self._get_threat_specific_actions(threat_category)
        
        return list(set(base_actions + threat_specific))
    
    def _get_threat_specific_actions(self, threat_category: str) -> List[str]:
        """Get actions specific to the threat type"""
        
        threat_actions = {
            "ml_attack": ["deploy_model_poisoning", "inject_adversarial_examples"],
            "sql_injection": ["deploy_sql_honeypot", "inject_fake_database"],
            "directory_traversal": ["deploy_fake_filesystem"],
            "bot_activity": ["deploy_timing_traps", "increase_complexity"],
            "xss_attack": ["sanitize_output", "deploy_xss_trap"]
        }
        
        return threat_actions.get(threat_category, [])
    
    def _calculate_confidence(self, evidence: Dict[str, Any], 
                            detected_patterns: List[str]) -> float:
        """Calculate confidence in the risk assessment"""
        
        # Base confidence on amount and quality of evidence
        confidence = 0.0
        
        # More evidence types = higher confidence
        evidence_types = len(evidence.keys())
        confidence += min(evidence_types * 0.15, 0.5)
        
        # Multiple detected patterns = higher confidence
        pattern_count = len(detected_patterns)
        confidence += min(pattern_count * 0.1, 0.3)
        
        # Specific high-confidence indicators
        if "timing" in evidence:
            timing_data = evidence["timing"]
            if "coefficient_of_variation" in timing_data:
                cv = timing_data["coefficient_of_variation"]
                if cv < 0.05:  # Very consistent = high confidence
                    confidence += 0.2
        
        if "content" in evidence:
            # Direct pattern matches are high confidence
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _summarize_evidence(self, evidence: Dict[str, Any], 
                           detected_patterns: List[str]) -> Dict[str, Any]:
        """Create a concise summary of evidence for reporting"""
        
        summary = {
            "patterns_detected": detected_patterns,
            "evidence_categories": list(evidence.keys()),
            "key_indicators": []
        }
        
        # Extract key indicators from evidence
        if "timing" in evidence:
            timing = evidence["timing"]
            if "pattern" in timing:
                summary["key_indicators"].append(f"Timing: {timing['pattern']}")
        
        if "behavioral" in evidence:
            behavioral = evidence["behavioral"]
            if "pattern" in behavioral:
                summary["key_indicators"].append(f"Behavioral: {behavioral['pattern']}")
        
        if "content" in evidence:
            content = evidence["content"]
            for attack_type in content.keys():
                summary["key_indicators"].append(f"Content: {attack_type}")
        
        if "ml_attack" in evidence:
            ml_attack = evidence["ml_attack"]
            for attack_type in ml_attack.keys():
                summary["key_indicators"].append(f"ML Attack: {attack_type}")
        
        return summary
    
    def should_deploy_countermeasures(self, risk_assessment: RiskAssessment) -> bool:
        """Determine if active countermeasures should be deployed"""
        return risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def get_scenario_for_threat(self, threat_category: str) -> str:
        """Map threat category to scenario configuration"""
        
        scenario_mapping = {
            "ml_attack": "model_extraction",
            "sql_injection": "sql_injection",
            "directory_traversal": "directory_traversal",
            "bot_activity": "api_scraping",
            "xss_attack": "reconnaissance",
            "general_suspicious": "reconnaissance"
        }
        
        return scenario_mapping.get(threat_category, "api_scraping")
