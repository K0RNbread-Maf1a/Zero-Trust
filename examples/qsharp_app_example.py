"""
Example Q# Web Application with Zero-Trust Defense Middleware

This demonstrates how to integrate the defense system with a Q# quantum computing web app.
Q# applications typically expose quantum operations via REST APIs.
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Import the Q# defense middleware
from integrations.qsharp_middleware import create_qsharp_defense_middleware


# Initialize FastAPI app
app = FastAPI(
    title="Quantum Computing API with Zero-Trust Defense",
    description="Q# quantum operations protected by AI defense system"
)

# Add defense middleware - this line is all you need!
defense_middleware = create_qsharp_defense_middleware(
    app,
    config_dir="../config",
    base_dir="..",
    enable_quantum=True  # Use quantum RNG for tracking tokens
)


# Pydantic models for Q# operations
class QuantumCircuitRequest(BaseModel):
    """Request to run a quantum circuit"""
    circuit_name: str
    qubits: int
    parameters: Optional[dict] = None
    shots: int = 1000


class QuantumMeasurement(BaseModel):
    """Quantum measurement result"""
    state: str
    count: int
    probability: float


class QuantumCircuitResponse(BaseModel):
    """Response from quantum circuit execution"""
    circuit_name: str
    measurements: List[QuantumMeasurement]
    total_shots: int
    execution_time_ms: float


# Example Q# quantum operations
@app.post("/api/quantum/run-circuit", response_model=QuantumCircuitResponse)
async def run_quantum_circuit(request: QuantumCircuitRequest):
    """
    Execute a quantum circuit
    
    This endpoint is protected by the defense middleware.
    Suspicious requests will receive fake quantum data instead.
    """
    
    # In a real app, this would call Q# operations like:
    # import qsharp
    # from MyQuantumNamespace import MyQuantumOperation
    # result = MyQuantumOperation.simulate(...)
    
    # For this example, simulate some quantum results
    if request.circuit_name == "bell_state":
        # Bell state should produce |00⟩ and |11⟩ with equal probability
        return QuantumCircuitResponse(
            circuit_name="bell_state",
            measurements=[
                QuantumMeasurement(state="|00⟩", count=487, probability=0.487),
                QuantumMeasurement(state="|11⟩", count=513, probability=0.513)
            ],
            total_shots=request.shots,
            execution_time_ms=234.5
        )
    
    elif request.circuit_name == "grover_search":
        # Grover's algorithm results
        return QuantumCircuitResponse(
            circuit_name="grover_search",
            measurements=[
                QuantumMeasurement(state="|101⟩", count=876, probability=0.876),
                QuantumMeasurement(state="|000⟩", count=42, probability=0.042),
                QuantumMeasurement(state="|111⟩", count=82, probability=0.082)
            ],
            total_shots=request.shots,
            execution_time_ms=567.3
        )
    
    raise HTTPException(status_code=404, detail="Circuit not found")


@app.post("/api/quantum/generate-random")
async def generate_quantum_random(num_bits: int = 128):
    """
    Generate truly random bits using quantum mechanics
    
    Protected by defense middleware - attackers trying to extract
    the quantum RNG will receive fake but plausible random data.
    """
    
    # In real implementation:
    # from QuantumDefense import GenerateRandomBits
    # bits = GenerateRandomBits.simulate(num_bits=num_bits)
    
    import random
    bits = [random.randint(0, 1) for _ in range(num_bits)]
    
    return {
        "num_bits": num_bits,
        "bits": bits,
        "source": "quantum_hardware",
        "entropy": 1.0  # Perfect entropy from quantum source
    }


@app.get("/api/quantum/simulate-entanglement")
async def simulate_entanglement(num_qubits: int = 2):
    """
    Simulate quantum entanglement
    
    Defense middleware monitors for systematic probing of quantum states,
    which could indicate model extraction attacks on quantum algorithms.
    """
    
    if num_qubits < 2 or num_qubits > 10:
        raise HTTPException(status_code=400, detail="Must use 2-10 qubits")
    
    # Simulate entanglement results
    return {
        "num_qubits": num_qubits,
        "entanglement_entropy": 0.693 * (num_qubits - 1),
        "bell_inequality_violation": 2.828,  # Violates classical limit of 2
        "fidelity": 0.9945
    }


# Defense monitoring endpoints
@app.get("/api/defense/status")
async def get_defense_status():
    """Get current defense system status"""
    status = defense_middleware.middleware.orchestrator.get_status()
    qsharp_stats = defense_middleware.middleware.get_qsharp_stats()
    
    return {
        "defense_system": status,
        "qsharp_specific": qsharp_stats
    }


@app.get("/api/defense/threats")
async def get_threat_history():
    """Get recent threat detections"""
    history = defense_middleware.middleware.qsharp_operation_history[-50:]
    threats = [h for h in history if h["threat_detected"]]
    
    return {
        "recent_threats": threats,
        "total_threats": len(threats)
    }


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "defense_active": True}


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Quantum Computing API with Zero-Trust Defense",
        "version": "1.0.0",
        "defense": "active",
        "endpoints": [
            "/api/quantum/run-circuit",
            "/api/quantum/generate-random",
            "/api/quantum/simulate-entanglement",
            "/api/defense/status",
            "/api/defense/threats"
        ]
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Starting Q# Web Application with Zero-Trust Defense")
    print("=" * 60)
    print()
    print("Defense Middleware: ACTIVE")
    print("Quantum Enhanced: ENABLED")
    print()
    print("Try these endpoints:")
    print("  POST http://localhost:8000/api/quantum/run-circuit")
    print("  POST http://localhost:8000/api/quantum/generate-random")
    print("  GET  http://localhost:8000/api/defense/status")
    print()
    print("To test defense system, try sending malicious requests:")
    print("  curl -X POST http://localhost:8000/api/quantum/run-circuit \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"circuit_name\": \"SELECT * FROM circuits\"}'")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
