"""
Quantum Defense Detector - Detects quantum-specific attacks
Extends pattern detection for quantum computing scenarios
"""
import json
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import time


@dataclass
class QuantumThreatAssessment:
    """Assessment of quantum-specific threats"""
    is_quantum_threat: bool
    threat_type: str  # "circuit_probing", "oracle_abuse", "state_exfiltration", etc.
    risk_score: float
    confidence: float
    quantum_anomalies: Dict[str, Any]
    evidence: Dict[str, Any]
    timestamp: float


class QuantumThreatDetector:
    """Detects attacks on quantum computing systems"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize quantum threat detector with configuration
        
        Args:
            config: Detection rules configuration from config/rules.yaml
        """
        self.config = config
        self.quantum_operation_history = []
        self.circuit_patterns = {}
        self.oracle_query_log = {}
        
    def analyze_quantum_request(self, request: Dict[str, Any]) -> QuantumThreatAssessment:
        """
        Analyze a quantum operation request for threats
        
        Args:
            request: Quantum operation request with metadata
            
        Returns:
            QuantumThreatAssessment with threat analysis
        """
        threat_type = ""
        risk_score = 0.0
        anomalies = {}
        evidence = {}
        
        # Check for quantum circuit probing
        circuit_result = self._detect_circuit_probing(request)
        if circuit_result[0]:
            threat_type = "circuit_probing"
            risk_score += circuit_result[1]
            evidence["circuit_probing"] = circuit_result[2]
            anomalies["circuit_depth_variance"] = circuit_result[2].get("depth_variance", 0)
        
        # Check for oracle abuse
        oracle_result = self._detect_oracle_abuse(request)
        if oracle_result[0]:
            threat_type = "oracle_abuse"
            risk_score += oracle_result[1]
            evidence["oracle_abuse"] = oracle_result[2]
            anomalies["oracle_queries_per_minute"] = oracle_result[2].get("qpm", 0)
        
        # Check for state exfiltration
        state_result = self._detect_state_exfiltration(request)
        if state_result[0]:
            threat_type = "state_exfiltration"
            risk_score += state_result[1]
            evidence["state_exfiltration"] = state_result[2]
            anomalies["bulk_extraction"] = state_result[2].get("extraction_size", 0)
        
        # Check for algorithm extraction
        algo_result = self._detect_algorithm_extraction(request)
        if algo_result[0]:
            threat_type = "algorithm_extraction"
            risk_score += algo_result[1]
            evidence["algorithm_extraction"] = algo_result[2]
            anomalies["systematic_exploration"] = algo_result[2].get("exploration_pattern", [])
        
        # Check for side-channel attacks
        sideChannel_result = self._detect_side_channel_attack(request)
        if sideChannel_result[0]:
            threat_type = "side_channel_attack"
            risk_score += sideChannel_result[1]
            evidence["side_channel"] = sideChannel_result[2]
            anomalies["timing_variance"] = sideChannel_result[2].get("timing_variance", 0)
        
        # Store in history
        self.quantum_operation_history.append({
            "timestamp": time.time(),
            "threat_type": threat_type,
            "risk_score": risk_score,
            "request": request
        })
        
        confidence = min(1.0, risk_score / 100.0) if risk_score > 0 else 0.0
        
        return QuantumThreatAssessment(
            is_quantum_threat=risk_score >= 60,
            threat_type=threat_type,
            risk_score=risk_score,
            confidence=confidence,
            quantum_anomalies=anomalies,
            evidence=evidence,
            timestamp=time.time()
        )
    
    def _detect_circuit_probing(self, request: Dict[str, Any]) -> Tuple[bool, float, Dict]:
        """
        Detect systematic exploration of quantum circuits
        
        Indicators:
        - Progressive increase in circuit depth
        - Systematic variation of parameters
        - Unusual gate patterns
        """
        circuit_depth = request.get("circuit_depth", 0)
        gate_count = request.get("gate_count", 0)
        parameters = request.get("parameters", {})
        
        # Track circuit patterns
        ip = request.get("ip", "unknown")
        if ip not in self.circuit_patterns:
            self.circuit_patterns[ip] = []
        
        self.circuit_patterns[ip].append({
            "depth": circuit_depth,
            "gates": gate_count,
            "timestamp": time.time()
        })
        
        # Keep only recent history
        cutoff_time = time.time() - 3600  # Last hour
        self.circuit_patterns[ip] = [p for p in self.circuit_patterns[ip] 
                                     if p["timestamp"] > cutoff_time]
        
        is_detected = False
        risk_score = 0.0
        evidence = {}
        
        # Check for progressive depth increase
        if len(self.circuit_patterns[ip]) > 5:
            depths = [p["depth"] for p in self.circuit_patterns[ip][-10:]]
            if len(depths) > 1:
                depth_increase = max(depths) - min(depths)
                depth_variance = sum((d - sum(depths)/len(depths))**2 for d in depths) / len(depths)
                
                if depth_variance > 100 or depth_increase > 50:
                    is_detected = True
                    risk_score = min(100, 50 + depth_variance / 10)
                    evidence = {
                        "depth_variance": depth_variance,
                        "depth_increase": depth_increase,
                        "pattern_count": len(self.circuit_patterns[ip])
                    }
        
        return (is_detected, risk_score, evidence)
    
    def _detect_oracle_abuse(self, request: Dict[str, Any]) -> Tuple[bool, float, Dict]:
        """
        Detect excessive queries to quantum oracle
        
        Indicators:
        - High query rate
        - Systematic query patterns
        - Parameter sweep across oracle inputs
        """
        ip = request.get("ip", "unknown")
        is_oracle_query = request.get("operation_type") == "oracle"
        
        if ip not in self.oracle_query_log:
            self.oracle_query_log[ip] = []
        
        if is_oracle_query:
            self.oracle_query_log[ip].append(time.time())
        
        # Clean old entries
        cutoff_time = time.time() - 60  # Last minute
        self.oracle_query_log[ip] = [t for t in self.oracle_query_log[ip] 
                                     if t > cutoff_time]
        
        is_detected = False
        risk_score = 0.0
        evidence = {}
        
        queries_per_minute = len(self.oracle_query_log[ip])
        if queries_per_minute > 100:  # Threshold
            is_detected = True
            risk_score = min(100, 50 + (queries_per_minute - 100) / 2)
            evidence = {
                "qpm": queries_per_minute,
                "threshold": 100,
                "recent_queries": len([t for t in self.oracle_query_log[ip] 
                                      if t > time.time() - 10])
            }
        
        return (is_detected, risk_score, evidence)
    
    def _detect_state_exfiltration(self, request: Dict[str, Any]) -> Tuple[bool, float, Dict]:
        """
        Detect bulk extraction of quantum state data
        
        Indicators:
        - Large number of qubits requested
        - High sampling rate
        - Extraction of complete state vector
        """
        num_qubits = request.get("num_qubits", 0)
        sample_count = request.get("sample_count", 1)
        request_size = request.get("request_size_bytes", 0)
        
        is_detected = False
        risk_score = 0.0
        evidence = {}
        
        # Check for excessive data extraction
        extraction_size = num_qubits * sample_count * 8  # Approximate bytes
        
        if extraction_size > 10000000:  # 10MB threshold
            is_detected = True
            risk_score = min(100, 60 + (extraction_size - 10000000) / 100000)
            evidence = {
                "extraction_size": extraction_size,
                "num_qubits": num_qubits,
                "sample_count": sample_count
            }
        
        # Check for high-dimensional state extraction
        if num_qubits > 30:
            is_detected = True
            risk_score = max(risk_score, min(100, 40 + (num_qubits - 30) * 2))
            evidence["high_dimensional"] = True
        
        return (is_detected, risk_score, evidence)
    
    def _detect_algorithm_extraction(self, request: Dict[str, Any]) -> Tuple[bool, float, Dict]:
        """
        Detect attempts to reverse-engineer quantum algorithms
        
        Indicators:
        - Systematic parameter exploration
        - Boundary testing
        - Edge case analysis
        """
        parameters = request.get("parameters", {})
        operation_type = request.get("operation_type", "")
        
        is_detected = False
        risk_score = 0.0
        evidence = {}
        
        # Check for parameter sweep
        if isinstance(parameters, dict):
            param_variations = len(parameters.get("variations", []))
            if param_variations > 50:
                is_detected = True
                risk_score = min(100, 50 + param_variations / 2)
                evidence = {
                    "exploration_pattern": "parameter_sweep",
                    "parameter_variations": param_variations
                }
        
        # Check for sequential algorithm testing
        ip = request.get("ip", "unknown")
        if operation_type in ["grover", "vqe", "qaoa", "hhl"]:
            risk_score = max(risk_score, 40)
            evidence["algorithm_tested"] = operation_type
        
        return (is_detected, risk_score, evidence)
    
    def _detect_side_channel_attack(self, request: Dict[str, Any]) -> Tuple[bool, float, Dict]:
        """
        Detect side-channel attacks through timing analysis
        
        Indicators:
        - Timing variance in quantum operations
        - Correlation between timing and results
        - Statistical deviation
        """
        timing_measurements = request.get("timing_measurements", [])
        execution_times = request.get("execution_times", [])
        
        is_detected = False
        risk_score = 0.0
        evidence = {}
        
        if len(execution_times) > 10:
            # Calculate variance
            mean_time = sum(execution_times) / len(execution_times)
            variance = sum((t - mean_time)**2 for t in execution_times) / len(execution_times)
            stddev = variance ** 0.5
            
            # Coefficient of variation
            cv = stddev / mean_time if mean_time > 0 else 0
            
            # High CV indicates timing side-channel vulnerability
            if cv > 0.5:  # 50% variance threshold
                is_detected = True
                risk_score = min(100, 40 + cv * 100)
                evidence = {
                    "timing_variance": variance,
                    "coefficient_of_variation": cv,
                    "measurements_count": len(execution_times)
                }
        
        return (is_detected, risk_score, evidence)
    
    def get_threat_summary(self) -> Dict[str, Any]:
        """Get summary of quantum threats detected"""
        if not self.quantum_operation_history:
            return {
                "total_operations": 0,
                "threats_detected": 0,
                "threat_percentage": 0.0,
                "threat_types": {}
            }
        
        total = len(self.quantum_operation_history)
        threats = [op for op in self.quantum_operation_history if op["risk_score"] >= 60]
        
        threat_types = {}
        for threat in threats:
            ttype = threat["threat_type"]
            threat_types[ttype] = threat_types.get(ttype, 0) + 1
        
        return {
            "total_operations": total,
            "threats_detected": len(threats),
            "threat_percentage": (len(threats) / total * 100) if total > 0 else 0.0,
            "threat_types": threat_types,
            "avg_risk_score": sum(op["risk_score"] for op in self.quantum_operation_history) / total
        }
