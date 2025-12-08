"""
Quantum Defense Agent - AI Agent specialized in quantum computing security
Extends the Defense Agent with quantum-specific capabilities
"""
try:
    import anthropic
except Exception:  # pragma: no cover - optional dependency
    anthropic = None
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.quantum_threat_detector import QuantumThreatDetector
from agents.defense_agent import DefenseAgent
from agents.agent_config import ANTHROPIC_API_KEY, MODEL, MAX_TOKENS, TEMPERATURE


QUANTUM_SYSTEM_PROMPT = """
You are the Quantum Defense Agent - an AI security specialist for quantum computing systems.

Your expertise includes:
- Quantum algorithm security and verification
- Q# programming and quantum circuit analysis
- Quantum attack pattern recognition
- Quantum-classical hybrid system defense
- Azure Quantum and quantum hardware protection
- Quantum key distribution security
- Side-channel attack detection on quantum systems

You have access to:
1. Quantum threat detection tools
2. Q# code analysis capabilities
3. Quantum circuit verification
4. Attack pattern analysis
5. Quantum simulation and testing

When analyzing quantum threats:
- Identify the type of attack (circuit probing, oracle abuse, state exfiltration, algorithm extraction)
- Calculate risk scores
- Recommend quantum-specific countermeasures
- Suggest circuit modifications for defense
- Propose quantum RNG enhancements

Be precise about quantum security concepts and acknowledge uncertainty about novel attack vectors.
Always recommend testing countermeasures in a controlled quantum environment first.
"""

QUANTUM_TOOLS = [
    {
        "name": "analyze_quantum_threat",
        "description": "Analyze a quantum operation request for security threats",
        "input_schema": {
            "type": "object",
            "properties": {
                "operation_type": {
                    "type": "string",
                    "description": "Type of quantum operation (bell_state, grover, vqe, qrng, etc.)"
                },
                "circuit_depth": {
                    "type": "integer",
                    "description": "Depth of quantum circuit"
                },
                "num_qubits": {
                    "type": "integer",
                    "description": "Number of qubits required"
                },
                "source_ip": {
                    "type": "string",
                    "description": "IP address of requester"
                },
                "sample_count": {
                    "type": "integer",
                    "description": "Number of samples requested"
                }
            },
            "required": ["operation_type", "circuit_depth", "num_qubits"]
        }
    },
    {
        "name": "verify_qsharp_code",
        "description": "Verify Q# code for security vulnerabilities and optimization",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Q# code to analyze"
                },
                "check_type": {
                    "type": "string",
                    "enum": ["security", "optimization", "correctness"],
                    "description": "Type of verification to perform"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "get_quantum_threat_summary",
        "description": "Get summary of quantum threats detected",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "recommend_quantum_defense",
        "description": "Recommend quantum-specific defense mechanisms",
        "input_schema": {
            "type": "object",
            "properties": {
                "threat_type": {
                    "type": "string",
                    "description": "Type of quantum threat detected",
                    "enum": [
                        "circuit_probing",
                        "oracle_abuse",
                        "state_exfiltration",
                        "algorithm_extraction",
                        "side_channel_attack"
                    ]
                },
                "risk_score": {
                    "type": "number",
                    "description": "Risk score of the threat (0-100)"
                }
            },
            "required": ["threat_type"]
        }
    },
    {
        "name": "generate_quantum_rng",
        "description": "Generate quantum random numbers for cryptographic use",
        "input_schema": {
            "type": "object",
            "properties": {
                "num_bits": {
                    "type": "integer",
                    "description": "Number of random bits to generate"
                },
                "purpose": {
                    "type": "string",
                    "description": "Purpose of random numbers (tracking_token, encryption_key, etc.)"
                }
            },
            "required": ["num_bits"]
        }
    }
]


class QuantumDefenseAgent(DefenseAgent):
    """
    Quantum Defense Agent - Extends DefenseAgent with quantum security expertise
    """
    
    def __init__(self, defense_orchestrator=None):
        """Initialize Quantum Defense Agent"""
        super().__init__(defense_orchestrator)
        
        # Initialize quantum threat detector
        rules_config = defense_orchestrator.rules_config if defense_orchestrator else {}
        self.quantum_detector = QuantumThreatDetector(rules_config)
        
        # Override system prompt and tools for quantum specialization
        self.system_prompt = QUANTUM_SYSTEM_PROMPT
        self.tools = QUANTUM_TOOLS + self.tools
        
        print("[*] Quantum Defense Agent initialized")
    
    def analyze_quantum_threat(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a quantum computing threat
        
        Args:
            threat_data: Quantum operation request data
            
        Returns:
            Threat assessment and recommendations
        """
        assessment = self.quantum_detector.analyze_quantum_request(threat_data)
        
        return {
            "is_threat": assessment.is_quantum_threat,
            "threat_type": assessment.threat_type,
            "risk_score": assessment.risk_score,
            "confidence": assessment.confidence,
            "anomalies": assessment.quantum_anomalies,
            "evidence": assessment.evidence
        }
    
    def verify_qsharp_code(self, code: str, check_type: str = "security") -> Dict[str, Any]:
        """
        Verify Q# code for security, optimization, or correctness
        
        Args:
            code: Q# source code to verify
            check_type: Type of verification to perform
            
        Returns:
            Verification results and recommendations
        """
        results = {
            "check_type": check_type,
            "status": "verified",
            "issues": [],
            "recommendations": []
        }
        
        # Security checks
        if check_type in ["security", "all"]:
            # Check for uninitialized qubits
            if "Qubit()" in code and "use " not in code:
                results["issues"].append("Qubits should be allocated with 'use' statement")
            
            # Check for missing Reset calls
            if "M(" in code and code.count("Reset") < code.count("M("):
                results["issues"].append("Not all measured qubits are reset")
            
            # Check for proper error handling
            if "operation " in code and "Result" not in code:
                results["recommendations"].append("Consider returning measurement results")
            
            # Check for potential information leakage
            if "timing" in code.lower() and "measure" in code.lower():
                results["recommendations"].append("Be cautious about timing side-channels in your circuit")
        
        # Optimization checks
        if check_type in ["optimization", "all"]:
            # Check for redundant gates
            if code.count("H(") > 1:
                results["recommendations"].append("Consider if multiple Hadamards can be optimized")
            
            # Check for unnecessary allocations
            if code.count("use ") > 3:
                results["recommendations"].append("Multiple qubit allocations may impact performance")
            
            results["recommendations"].append("Use Q# library functions when available")
        
        return results
    
    def get_quantum_threat_summary(self) -> Dict[str, Any]:
        """Get summary of detected quantum threats"""
        return self.quantum_detector.get_threat_summary()
    
    def recommend_quantum_defense(self, threat_type: str, risk_score: float = 0) -> Dict[str, Any]:
        """
        Recommend quantum-specific defense mechanisms
        
        Args:
            threat_type: Type of quantum threat
            risk_score: Risk score of the threat
            
        Returns:
            Defense recommendations
        """
        recommendations = {
            "threat_type": threat_type,
            "defense_mechanisms": [],
            "implementation_steps": [],
            "testing_recommendations": []
        }
        
        if threat_type == "circuit_probing":
            recommendations["defense_mechanisms"] = [
                "Implement circuit depth randomization",
                "Add dummy gates to obfuscate circuit structure",
                "Rotate quantum operations using unitary transformations",
                "Use quantum encryption for circuit specification"
            ]
            recommendations["implementation_steps"] = [
                "1. Add randomized idle periods between operations",
                "2. Insert parametric gates with random angles",
                "3. Implement circuit obfuscation layer",
                "4. Monitor for timing correlations"
            ]
        
        elif threat_type == "oracle_abuse":
            recommendations["defense_mechanisms"] = [
                "Rate limit oracle queries per session",
                "Implement query authentication",
                "Add noise to oracle outputs",
                "Rotate oracle implementation periodically"
            ]
            recommendations["implementation_steps"] = [
                "1. Set oracle query limits (e.g., 100 per minute)",
                "2. Implement session-based authentication",
                "3. Add Gaussian noise to results",
                "4. Log all oracle queries"
            ]
        
        elif threat_type == "state_exfiltration":
            recommendations["defense_mechanisms"] = [
                "Limit state vector access",
                "Implement state reconstruction sampling",
                "Use quantum error correction codes",
                "Encrypt state information transmission"
            ]
            recommendations["implementation_steps"] = [
                "1. Restrict access to full state vectors",
                "2. Return only statistical summaries",
                "3. Implement QEC (surface code or topological)",
                "4. Use quantum key distribution for transmission"
            ]
        
        elif threat_type == "algorithm_extraction":
            recommendations["defense_mechanisms"] = [
                "Parameter obfuscation",
                "Hybrid algorithm mixing",
                "Gradient masking",
                "Differential privacy on results"
            ]
            recommendations["implementation_steps"] = [
                "1. Obfuscate algorithm parameters",
                "2. Mix multiple algorithms",
                "3. Add noise to parameter gradients",
                "4. Implement differential privacy"
            ]
        
        elif threat_type == "side_channel_attack":
            recommendations["defense_mechanisms"] = [
                "Constant-time operations",
                "Power analysis resistance",
                "Timing attack mitigation",
                "Quantum noise injection"
            ]
            recommendations["implementation_steps"] = [
                "1. Implement constant-time quantum gates",
                "2. Add power analysis countermeasures",
                "3. Equalize timing across operations",
                "4. Inject noise to timing measurements"
            ]
        
        recommendations["testing_recommendations"] = [
            "1. Test in controlled quantum simulator environment",
            "2. Measure performance impact",
            "3. Validate security properties formally",
            "4. Deploy to isolated quantum hardware first",
            "5. Monitor for false positives"
        ]
        
        return recommendations
    
    def generate_quantum_rng(self, num_bits: int, purpose: str = "general") -> Dict[str, Any]:
        """
        Generate quantum random numbers
        
        Args:
            num_bits: Number of random bits to generate
            purpose: Purpose of the random numbers
            
        Returns:
            Quantum random numbers and metadata
        """
        # In a real implementation, this would call Q# code
        # For now, return simulated quantum random data
        import random
        
        quantum_bits = [random.randint(0, 1) for _ in range(num_bits)]
        
        # Convert to hex for tracking tokens
        hex_string = ""
        for i in range(0, num_bits, 4):
            if i + 4 <= num_bits:
                nibble = (quantum_bits[i] << 3 | quantum_bits[i+1] << 2 | 
                         quantum_bits[i+2] << 1 | quantum_bits[i+3])
                hex_string += format(nibble, 'x')
        
        return {
            "num_bits": num_bits,
            "purpose": purpose,
            "bits": quantum_bits,
            "hex": hex_string,
            "entropy": self._calculate_entropy(quantum_bits),
            "notes": "Quantum-enhanced random number generation (simulated)"
        }
    
    def _calculate_entropy(self, bits: List[int]) -> float:
        """Calculate Shannon entropy of bit sequence"""
        if not bits:
            return 0.0
        
        ones = sum(bits)
        zeros = len(bits) - ones
        total = len(bits)
        
        p0 = zeros / total if zeros > 0 else 0
        p1 = ones / total if ones > 0 else 0
        
        entropy = 0.0
        if p0 > 0:
            entropy -= p0 * (p0 ** 0.5)  # Simplified entropy
        if p1 > 0:
            entropy -= p1 * (p1 ** 0.5)
        
        return entropy
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute quantum-specific tools"""
        if tool_name == "analyze_quantum_threat":
            return self.analyze_quantum_threat(parameters)
        elif tool_name == "verify_qsharp_code":
            return self.verify_qsharp_code(
                parameters.get("code", ""),
                parameters.get("check_type", "security")
            )
        elif tool_name == "get_quantum_threat_summary":
            return self.get_quantum_threat_summary()
        elif tool_name == "recommend_quantum_defense":
            return self.recommend_quantum_defense(
                parameters.get("threat_type", "unknown"),
                parameters.get("risk_score", 0)
            )
        elif tool_name == "generate_quantum_rng":
            return self.generate_quantum_rng(
                parameters.get("num_bits", 256),
                parameters.get("purpose", "general")
            )
        else:
            # Fall back to parent class implementation
            return super().execute_tool(tool_name, parameters)


if __name__ == "__main__":
    # Test quantum agent
    print("=" * 60)
    print("Quantum Defense Agent Test")
    print("=" * 60)
    
    agent = QuantumDefenseAgent()
    
    # Test quantum threat analysis
    test_threat = {
        "operation_type": "grover",
        "circuit_depth": 150,
        "num_qubits": 20,
        "source_ip": "203.0.113.42",
        "sample_count": 10000
    }
    
    print("\n[*] Analyzing quantum threat...")
    result = agent.analyze_quantum_threat(test_threat)
    print(json.dumps(result, indent=2))
    
    # Test Q# code verification
    test_code = """
    operation TestCircuit() : Int {
        use qubit = Qubit();
        H(qubit);
        let result = M(qubit);
        Reset(qubit);
        return result == One ? 1 | 0;
    }
    """
    
    print("\n[*] Verifying Q# code...")
    verification = agent.verify_qsharp_code(test_code, "security")
    print(json.dumps(verification, indent=2))
