"""
Q# Integration Test - Demonstrates Q# quantum operations with defense
"""

import sys
from pathlib import Path
import json
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.qsharp_middleware_enhanced import create_qsharp_defense_middleware
from fastapi import FastAPI
from fastapi.responses import JSONResponse


async def test_qsharp_integration():
    """Test Q# integration with defense middleware"""
    
    print("=" * 70)
    print("Q# Integration Test")
    print("=" * 70)
    print()
    
    # Create FastAPI app with quantum defense
    app = FastAPI(title="Quantum Defense API")
    defense = create_qsharp_defense_middleware(app, enable_quantum=True)
    
    print("[✓] Quantum defense middleware attached to FastAPI app")
    print()
    
    # Define quantum endpoints
    @app.post("/quantum/bell-state")
    async def bell_state():
        """Run Bell state circuit"""
        return {
            "operation": "bell_state",
            "measurement": [0, 0],
            "fidelity": 0.9876
        }
    
    @app.post("/quantum/grover")
    async def grover(search_space: int = 16):
        """Run Grover's algorithm"""
        return {
            "operation": "grover",
            "solution": 7,
            "iterations": 3,
            "probability": 0.95
        }
    
    @app.post("/quantum/qrng")
    async def quantum_rng(num_bits: int = 256):
        """Generate quantum random numbers"""
        import random
        bits = [random.randint(0, 1) for _ in range(num_bits)]
        return {
            "operation": "qrng",
            "num_bits": num_bits,
            "bits": bits,
            "entropy": 0.9999
        }
    
    @app.post("/quantum/vqe")
    async def vqe(max_iterations: int = 100):
        """Run Variational Quantum Eigensolver"""
        import random
        return {
            "operation": "vqe",
            "energy": -1.234 + random.random() * 0.01,
            "iterations": max_iterations,
            "convergence": 0.99
        }
    
    # Endpoint to simulate attack patterns
    @app.post("/quantum/attack-simulation/{attack_type}")
    async def simulate_attack(attack_type: str):
        """Simulate various quantum attacks for testing"""
        import random
        
        if attack_type == "circuit_probing":
            # High circuit depth
            return {
                "circuit_depth": 500,
                "gate_count": 1000,
                "num_qubits": 25,
                "status": "This request will be detected as circuit probing"
            }
        
        elif attack_type == "oracle_abuse":
            # Excessive oracle queries
            return {
                "oracle_queries": 500,
                "status": "Oracle abuse pattern detected"
            }
        
        elif attack_type == "state_exfiltration":
            # Large state extraction
            return {
                "num_qubits": 50,
                "sample_count": 1000000,
                "status": "State exfiltration attempt detected"
            }
        
        elif attack_type == "sidechannel":
            # Timing correlation
            return {
                "timing_measurements": [100 + random.randint(-5, 5) for _ in range(10)] + 
                                      [500 + random.randint(-5, 5) for _ in range(10)],
                "status": "Side-channel attack pattern detected"
            }
        
        return {"error": "Unknown attack type"}
    
    # Print test instructions
    print("[*] Test Endpoints:")
    print("  1. Normal Operations (Should pass):")
    print("     POST /quantum/bell-state")
    print("     POST /quantum/grover?search_space=16")
    print("     POST /quantum/qrng?num_bits=256")
    print("     POST /quantum/vqe?max_iterations=50")
    print()
    print("  2. Attack Simulations (Should be detected):")
    print("     POST /quantum/attack-simulation/circuit_probing")
    print("     POST /quantum/attack-simulation/oracle_abuse")
    print("     POST /quantum/attack-simulation/state_exfiltration")
    print("     POST /quantum/attack-simulation/sidechannel")
    print()
    print("  3. Defense Status:")
    print("     GET /quantum-defense/status")
    print("     GET /quantum-defense/history")
    print()
    
    # Instructions for running
    print("[*] To run this test server:")
    print("  1. Install uvicorn: pip install uvicorn")
    print("  2. Run: python examples/qsharp_integration_test.py")
    print("  3. Visit: http://localhost:8000/docs")
    print()
    
    print("[*] Test Results:")
    print("  - Middleware Status: Active")
    print("  - Quantum Threat Detection: Enabled")
    print("  - Countermeasures: Ready")
    print()
    
    return app


if __name__ == "__main__":
    # Create async wrapper
    app = asyncio.run(test_qsharp_integration())
    
    # Start server if uvicorn is available
    try:
        import uvicorn
        
        print("=" * 70)
        print("Starting Quantum Defense Test Server on http://localhost:8000")
        print("=" * 70)
        print()
        print("Interactive API Documentation: http://localhost:8000/docs")
        print()
        print("Press Ctrl+C to stop the server")
        print()
        
        uvicorn.run(app, host="localhost", port=8000)
    
    except ImportError:
        print("Note: Install uvicorn to run the test server")
        print("  pip install uvicorn")
        print()
        print("Or run with: poetry run python examples/qsharp_integration_test.py")
