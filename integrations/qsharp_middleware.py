"""
Q# Web Framework Middleware Integration
Integrates zero-trust AI defense with Q# quantum computing applications
"""
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Callable, Optional
import asyncio

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import DefenseOrchestrator


class QSharpDefenseMiddleware:
    """
    Middleware for Q# web frameworks
    Compatible with Q# quantum computing applications hosted in Python
    """
    
    def __init__(self, config_dir: str, base_dir: str, 
                 enable_quantum_enhanced: bool = False):
        """
        Initialize Q# defense middleware
        
        Args:
            config_dir: Path to config directory
            base_dir: Base directory for the defense system
            enable_quantum_enhanced: Use quantum randomness for tracking tokens
        """
        self.orchestrator = DefenseOrchestrator(config_dir, base_dir)
        self.enable_quantum_enhanced = enable_quantum_enhanced
        
        # Track Q# operations for pattern analysis
        self.qsharp_operation_history = []
        
    async def __call__(self, request: Any, call_next: Callable) -> Any:
        """
        ASGI middleware interface for Q# web frameworks
        Compatible with FastAPI, Starlette, and other ASGI frameworks
        """
        # Extract request metadata
        request_data = await self._extract_request_data(request)
        
        # Add Q# specific metadata
        request_data["qsharp_operation"] = getattr(request, "qsharp_op", None)
        request_data["quantum_circuit"] = getattr(request, "quantum_circuit", None)
        
        # Process through defense system
        defense_response = self.orchestrator.process_request(request_data)
        
        # Handle response based on threat level
        if defense_response["action"] == "countermeasures":
            # Deploy countermeasures
            return await self._handle_threat(request, defense_response)
        
        # Log Q# operations for pattern analysis
        self._log_qsharp_operation(request_data, defense_response)
        
        # Allow request to proceed
        return await call_next(request)
    
    async def _extract_request_data(self, request: Any) -> Dict[str, Any]:
        """Extract relevant data from Q# web request"""
        
        # Handle different request types
        if hasattr(request, "client"):
            # ASGI request (FastAPI/Starlette)
            client_host = request.client.host if request.client else "unknown"
            
            # Read body safely
            body = b""
            if hasattr(request, "body"):
                if asyncio.iscoroutine(request.body):
                    body = await request.body()
                else:
                    body = request.body()
            
            return {
                "timestamp": time.time(),
                "ip": client_host,
                "user_agent": request.headers.get("user-agent", ""),
                "endpoint": str(request.url.path),
                "params": dict(request.query_params) if hasattr(request, "query_params") else {},
                "headers": dict(request.headers),
                "content": body.decode("utf-8", errors="ignore"),
                "session_id": request.cookies.get("session_id", ""),
                "method": request.method
            }
        else:
            # Generic request object
            return {
                "timestamp": time.time(),
                "ip": getattr(request, "remote_addr", "unknown"),
                "user_agent": "",
                "endpoint": getattr(request, "path", ""),
                "params": {},
                "headers": {},
                "content": "",
                "session_id": ""
            }
    
    async def _handle_threat(self, request: Any, defense_response: Dict[str, Any]) -> Any:
        """
        Handle detected threat by serving poisoned data
        
        For Q# applications, we can:
        1. Serve fake quantum circuit results
        2. Return incorrect quantum state measurements
        3. Provide misleading quantum algorithm outputs
        """
        from starlette.responses import JSONResponse
        
        threat_category = defense_response.get("threat_category", "unknown")
        tracking_token = self._generate_tracking_token(defense_response)
        
        # Generate Q# specific fake data
        fake_data = self._generate_qsharp_fake_data(threat_category, tracking_token)
        
        # Return fake response with tracking
        return JSONResponse({
            "status": "success",
            "data": fake_data,
            "tracking_token": tracking_token,
            "quantum_enhanced": self.enable_quantum_enhanced
        })
    
    def _generate_qsharp_fake_data(self, threat_category: str, 
                                   tracking_token: str) -> Dict[str, Any]:
        """
        Generate Q# specific fake data based on threat type
        """
        
        if threat_category == "model_extraction":
            # Fake quantum circuit results
            return {
                "quantum_results": {
                    "measurements": [0, 1, 0, 1, 1, 0, 0, 1],  # Random but plausible
                    "success_probability": 0.8723,
                    "fidelity": 0.9456,
                    "circuit_depth": 42,
                    "gate_count": 128,
                    "tracking_token": tracking_token
                },
                "simulation_time_ms": 234,
                "backend": "quantum_simulator_v2"
            }
        
        elif threat_category == "data_exfiltration":
            # Fake quantum state data
            return {
                "quantum_states": [
                    {"state": "|0⟩", "amplitude": 0.707, "phase": 0},
                    {"state": "|1⟩", "amplitude": 0.707, "phase": 3.14159}
                ],
                "entanglement_entropy": 0.693,
                "bell_state_fidelity": 0.99,
                "tracking_token": tracking_token
            }
        
        else:
            # Generic fake quantum data
            return {
                "quantum_operation": "generic",
                "result": [1, 0, 1, 1, 0, 1, 0, 0],
                "iterations": 1000,
                "tracking_token": tracking_token,
                "note": "This is poisoned data for security purposes"
            }
    
    def _generate_tracking_token(self, defense_response: Dict[str, Any]) -> str:
        """
        Generate tracking token
        Optionally use quantum random number generation if available
        """
        if self.enable_quantum_enhanced:
            try:
                # Attempt to use Q# quantum RNG
                token = self._quantum_random_token()
                if token:
                    return token
            except:
                pass
        
        # Fallback to classical RNG
        import hashlib
        data = f"{json.dumps(defense_response)}{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _quantum_random_token(self) -> Optional[str]:
        """
        Generate truly random token using quantum randomness
        Requires Q# quantum random number generator
        """
        try:
            # This would call a Q# operation for quantum RNG
            # Placeholder for actual Q# integration
            
            # Example Q# operation (would need actual implementation):
            # import qsharp
            # from MyQuantumNamespace import GenerateRandomBits
            # bits = GenerateRandomBits.simulate(num_bits=128)
            # return ''.join(str(b) for b in bits)
            
            return None  # Return None to use fallback
        except:
            return None
    
    def _log_qsharp_operation(self, request_data: Dict[str, Any], 
                              defense_response: Dict[str, Any]):
        """Log Q# operations for pattern analysis"""
        log_entry = {
            "timestamp": time.time(),
            "qsharp_operation": request_data.get("qsharp_operation"),
            "quantum_circuit": request_data.get("quantum_circuit"),
            "threat_detected": defense_response["action"] == "countermeasures",
            "risk_score": defense_response.get("risk_score", 0)
        }
        
        self.qsharp_operation_history.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.qsharp_operation_history) > 1000:
            self.qsharp_operation_history = self.qsharp_operation_history[-1000:]
    
    def get_qsharp_stats(self) -> Dict[str, Any]:
        """Get statistics about Q# operations and threats"""
        if not self.qsharp_operation_history:
            return {"total_operations": 0}
        
        total = len(self.qsharp_operation_history)
        threats = sum(1 for log in self.qsharp_operation_history if log["threat_detected"])
        
        return {
            "total_operations": total,
            "threats_detected": threats,
            "threat_percentage": (threats / total * 100) if total > 0 else 0,
            "quantum_enhanced": self.enable_quantum_enhanced
        }


# FastAPI specific integration
class FastAPIQSharpDefense:
    """
    FastAPI-specific middleware for Q# applications
    """
    
    def __init__(self, config_dir: str = "config", base_dir: str = ".",
                 enable_quantum_enhanced: bool = False):
        self.middleware = QSharpDefenseMiddleware(config_dir, base_dir, 
                                                   enable_quantum_enhanced)
    
    async def dispatch(self, request, call_next):
        """FastAPI middleware dispatch method"""
        return await self.middleware(request, call_next)


# Example Q# quantum RNG operation (would be in separate .qs file)
QSHARP_RNG_EXAMPLE = """
namespace QuantumDefense {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
    open Microsoft.Quantum.Convert;
    
    /// Generate quantum random bits for tracking tokens
    operation GenerateRandomBits(numBits : Int) : Int[] {
        mutable results = new Int[numBits];
        
        use qubits = Qubit[numBits];
        
        for i in 0..numBits-1 {
            // Put qubit in superposition
            H(qubits[i]);
            
            // Measure (collapses to random 0 or 1)
            let result = M(qubits[i]);
            set results w/= i <- result == One ? 1 | 0;
            
            // Reset qubit
            Reset(qubits[i]);
        }
        
        return results;
    }
    
    /// Generate tracking token using quantum randomness
    operation GenerateTrackingToken() : String {
        let bits = GenerateRandomBits(128);
        // Convert to hex string
        return BitsToHex(bits);
    }
}
"""


def create_qsharp_defense_middleware(app, config_dir: str = "config", 
                                     base_dir: str = ".",
                                     enable_quantum: bool = False):
    """
    Helper function to easily add defense middleware to Q# web apps
    
    Usage:
        from fastapi import FastAPI
        from integrations.qsharp_middleware import create_qsharp_defense_middleware
        
        app = FastAPI()
        create_qsharp_defense_middleware(app)
    """
    middleware = FastAPIQSharpDefense(config_dir, base_dir, enable_quantum)
    app.middleware("http")(middleware.dispatch)
    return middleware
