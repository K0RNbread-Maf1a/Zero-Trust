"""
Quantum Defense Examples
Demonstrates quantum threat detection and defense mechanisms
"""

import sys
from pathlib import Path
import json
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.quantum_defense_agent import QuantumDefenseAgent
from core.orchestrator import DefenseOrchestrator


def main():
    print("=" * 70)
    print("Quantum Defense Agent Examples")
    print("=" * 70)
    print()
    
    # Initialize systems
    print("[*] Initializing Quantum Defense System...")
    base_dir = Path(__file__).parent.parent
    config_dir = base_dir / "config"
    
    try:
        orchestrator = DefenseOrchestrator(str(config_dir), str(base_dir))
        agent = QuantumDefenseAgent(defense_orchestrator=orchestrator)
        print("✓ Quantum Defense Agent initialized\n")
    except Exception as e:
        print(f"✗ Error initializing: {e}")
        return
    
    # Example 1: Analyze Normal Quantum Operation
    print("-" * 70)
    print("Example 1: Normal Bell State Circuit")
    print("-" * 70)
    
    normal_bell = {
        "operation_type": "bell_state",
        "circuit_depth": 3,
        "num_qubits": 2,
        "source_ip": "192.168.1.100",
        "sample_count": 100,
        "gate_count": 2
    }
    
    print(f"Request: {json.dumps(normal_bell, indent=2)}")
    result = agent.analyze_quantum_threat(normal_bell)
    print(f"\nThreat Assessment:")
    print(f"  - Is Threat: {result['is_threat']}")
    print(f"  - Risk Score: {result['risk_score']}")
    print(f"  - Confidence: {result['confidence']:.2%}\n")
    
    # Example 2: Detect Circuit Probing Attack
    print("-" * 70)
    print("Example 2: Circuit Probing Attack Detection")
    print("-" * 70)
    
    circuit_probing = {
        "operation_type": "grover",
        "circuit_depth": 250,  # Unusually high
        "num_qubits": 15,
        "source_ip": "203.0.113.42",
        "sample_count": 10000,
        "gate_count": 500,
        "parameters": {
            "variations": list(range(100))  # Systematic variation
        }
    }
    
    print(f"Request: Circuit depth={circuit_probing['circuit_depth']}, " 
          f"gate_count={circuit_probing['gate_count']}")
    result = agent.analyze_quantum_threat(circuit_probing)
    print(f"\nThreat Assessment:")
    print(f"  - Is Threat: {result['is_threat']}")
    print(f"  - Threat Type: {result['threat_type']}")
    print(f"  - Risk Score: {result['risk_score']}")
    print(f"  - Anomalies: {result['anomalies']}\n")
    
    # Example 3: Detect Oracle Abuse
    print("-" * 70)
    print("Example 3: Oracle Query Abuse Detection")
    print("-" * 70)
    
    # Simulate multiple oracle queries
    oracle_abuser_ip = "192.168.99.99"
    for i in range(120):
        oracle_query = {
            "operation_type": "oracle",
            "circuit_depth": 10,
            "num_qubits": 5,
            "source_ip": oracle_abuser_ip,
            "sample_count": 10,
            "gate_count": 5
        }
        agent.analyze_quantum_threat(oracle_query)
    
    # Now analyze one more to trigger detection
    print(f"Simulated {120} oracle queries from {oracle_abuser_ip}")
    final_query = {
        "operation_type": "oracle",
        "circuit_depth": 10,
        "num_qubits": 5,
        "source_ip": oracle_abuser_ip,
        "sample_count": 10
    }
    result = agent.analyze_quantum_threat(final_query)
    print(f"\nThreat Assessment:")
    print(f"  - Is Threat: {result['is_threat']}")
    print(f"  - Threat Type: {result['threat_type']}")
    print(f"  - Risk Score: {result['risk_score']}")
    print(f"  - Anomalies: {result['anomalies']}\n")
    
    # Example 4: Detect State Exfiltration
    print("-" * 70)
    print("Example 4: Quantum State Exfiltration Detection")
    print("-" * 70)
    
    exfiltration_attack = {
        "operation_type": "state_dump",
        "circuit_depth": 50,
        "num_qubits": 35,  # High dimensional
        "source_ip": "203.0.113.99",
        "sample_count": 100000,  # Excessive samples
        "request_size_bytes": 50000000  # 50MB request
    }
    
    print(f"Request: {exfiltration_attack['num_qubits']} qubits, "
          f"{exfiltration_attack['sample_count']} samples, "
          f"{exfiltration_attack['request_size_bytes']/1000000:.1f}MB")
    result = agent.analyze_quantum_threat(exfiltration_attack)
    print(f"\nThreat Assessment:")
    print(f"  - Is Threat: {result['is_threat']}")
    print(f"  - Threat Type: {result['threat_type']}")
    print(f"  - Risk Score: {result['risk_score']}")
    print(f"  - Anomalies: {result['anomalies']}\n")
    
    # Example 5: Verify Q# Code
    print("-" * 70)
    print("Example 5: Q# Code Security Verification")
    print("-" * 70)
    
    qsharp_code = """
    operation QuantumRandomBits(numBits : Int) : Int[] {
        mutable results = new Int[numBits];
        
        use qubits = Qubit[numBits] {
            for i in 0..numBits-1 {
                H(qubits[i]);
                let measurement = M(qubits[i]);
                set results w/= i <- measurement == One ? 1 | 0;
                Reset(qubits[i]);
            }
        }
        
        return results;
    }
    """
    
    print("Verifying Q# code...")
    verification = agent.verify_qsharp_code(qsharp_code, "security")
    print(f"\nVerification Results:")
    print(f"  - Check Type: {verification['check_type']}")
    print(f"  - Status: {verification['status']}")
    if verification['issues']:
        print(f"  - Issues: {verification['issues']}")
    if verification['recommendations']:
        print(f"  - Recommendations:")
        for rec in verification['recommendations']:
            print(f"    * {rec}")
    print()
    
    # Example 6: Get Threat Summary
    print("-" * 70)
    print("Example 6: Quantum Threat Summary")
    print("-" * 70)
    
    summary = agent.get_quantum_threat_summary()
    print(f"Total Operations Analyzed: {summary['total_operations']}")
    print(f"Threats Detected: {summary['threats_detected']}")
    print(f"Threat Percentage: {summary['threat_percentage']:.2f}%")
    if summary['threat_types']:
        print(f"Threat Types Detected:")
        for ttype, count in summary['threat_types'].items():
            print(f"  - {ttype}: {count}")
    print()
    
    # Example 7: Get Defense Recommendations
    print("-" * 70)
    print("Example 7: Defense Recommendations for Circuit Probing")
    print("-" * 70)
    
    defense = agent.recommend_quantum_defense("circuit_probing", risk_score=85)
    print(f"Threat Type: {defense['threat_type']}")
    print(f"\nDefense Mechanisms:")
    for mechanism in defense['defense_mechanisms']:
        print(f"  • {mechanism}")
    print(f"\nImplementation Steps:")
    for step in defense['implementation_steps']:
        print(f"  {step}")
    print(f"\nTesting Recommendations:")
    for rec in defense['testing_recommendations']:
        print(f"  {rec}")
    print()
    
    # Example 8: Generate Quantum RNG
    print("-" * 70)
    print("Example 8: Quantum Random Number Generation")
    print("-" * 70)
    
    rng = agent.generate_quantum_rng(256, "tracking_token")
    print(f"Generated {rng['num_bits']} quantum random bits")
    print(f"Purpose: {rng['purpose']}")
    print(f"Entropy: {rng['entropy']:.6f}")
    print(f"Hex Token (32 chars): {rng['hex'][:32]}")
    print(f"Full Hex: {rng['hex']}\n")
    
    # Example 9: Side-Channel Attack Detection
    print("-" * 70)
    print("Example 9: Side-Channel Attack Detection")
    print("-" * 70)
    
    # Simulate timing measurements showing correlation
    timing_measurements = [100, 102, 101, 103, 100, 500, 502, 501, 503, 500] + \
                         [100, 101, 102, 100, 101] + \
                         [500, 499, 501, 500, 499]
    
    sidechannel_attack = {
        "operation_type": "vqe",
        "circuit_depth": 100,
        "num_qubits": 10,
        "source_ip": "203.0.113.88",
        "execution_times": timing_measurements,
        "timing_measurements": timing_measurements
    }
    
    print(f"Timing measurements showing bimodal distribution:")
    print(f"  Low timing group: ~100-103 μs")
    print(f"  High timing group: ~500-502 μs")
    result = agent.analyze_quantum_threat(sidechannel_attack)
    print(f"\nThreat Assessment:")
    print(f"  - Is Threat: {result['is_threat']}")
    print(f"  - Threat Type: {result['threat_type']}")
    print(f"  - Risk Score: {result['risk_score']}")
    print()
    
    print("=" * 70)
    print("Examples Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
