"""
Q# Middleware Wrapper - Integrates Q# quantum defense with FastAPI
Enhanced version with quantum threat detection
"""
from fastapi import FastAPI, Request
from typing import Optional, Dict, Any, Callable
import json
import time
import hashlib
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.quantum_threat_detector import QuantumThreatDetector
from core.orchestrator import DefenseOrchestrator


class QuantumDefenseMiddleware:
    """Middleware for integrating quantum defense with FastAPI"""
    
    def __init__(self, orchestrator: DefenseOrchestrator, enable_quantum: bool = True):
        """
        Initialize quantum defense middleware
        
        Args:
            orchestrator: Defense orchestrator instance
            enable_quantum: Enable quantum-specific threat detection
        """
        self.orchestrator = orchestrator
        self.enable_quantum = enable_quantum
        self.quantum_detector = QuantumThreatDetector(orchestrator.rules_config)
        self.qsharp_operation_history = []
        self.quantum_stats = {
            "total_operations": 0,
            "threats_detected": 0,
            "countermeasures_deployed": 0
        }
    
    async def __call__(self, request: Request, call_next: Callable) -> Any:
        """
        Process request through quantum defense middleware
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/handler
            
        Returns:
            Response with defense applied
        """
        start_time = time.time()
        
        # Extract request data
        request_data = await self._extract_request_data(request)
        
        # Check if this is a quantum operation
        is_quantum_op = self._is_quantum_operation(request)
        
        if is_quantum_op and self.enable_quantum:
            # Apply quantum-specific threat detection
            quantum_request = self._build_quantum_request(request_data, request)
            threat_assessment = self.quantum_detector.analyze_quantum_request(quantum_request)
            
            # Record operation
            self.quantum_stats["total_operations"] += 1
            
            if threat_assessment.is_quantum_threat:
                self.quantum_stats["threats_detected"] += 1
                
                # Store threat in history
                self.qsharp_operation_history.append({
                    "timestamp": time.time(),
                    "path": request.url.path,
                    "threat_type": threat_assessment.threat_type,
                    "risk_score": threat_assessment.risk_score,
                    "confidence": threat_assessment.confidence
                })
                
                # Deploy countermeasures if risk is high
                if threat_assessment.risk_score >= 80:
                    self.quantum_stats["countermeasures_deployed"] += 1
                    return await self._deploy_quantum_countermeasures(
                        request, threat_assessment
                    )
        
        # Process through standard defense pipeline
        standard_request_data = {
            "timestamp": time.time(),
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
            "endpoint": request.url.path,
            "params": dict(request.query_params),
            "headers": dict(request.headers),
            "content": request_data.get("body", ""),
            "session_id": request.cookies.get("session_id", "")
        }
        
        response = self.orchestrator.process_request(standard_request_data)
        
        if response["action"] == "countermeasures":
            return await self._serve_fake_quantum_data(request, response, threat_assessment)
        
        # Normal processing
        return await call_next(request)
    
    async def _extract_request_data(self, request: Request) -> Dict[str, Any]:
        """Extract full request data including body"""
        try:
            body = await request.body()
            body_str = body.decode("utf-8") if body else ""
        except:
            body_str = ""
        
        return {
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "headers": dict(request.headers),
            "body": body_str
        }
    
    def _is_quantum_operation(self, request: Request) -> bool:
        """
        Check if request is a quantum operation
        
        Heuristics:
        - Path contains 'quantum', 'qsharp', 'bell', 'grover', etc.
        - Headers indicate quantum operation
        - Body contains quantum-specific parameters
        """
        path = request.url.path.lower()
        quantum_keywords = [
            "quantum", "qsharp", "bell", "grover", "vqe", "qaoa", "hhl", 
            "teleport", "entangle", "superposition", "qrng", "qiskit"
        ]
        
        for keyword in quantum_keywords:
            if keyword in path:
                return True
        
        # Check headers
        content_type = request.headers.get("content-type", "").lower()
        if "quantum" in content_type or "qsharp" in content_type:
            return True
        
        # Check for quantum-specific parameters
        if any(kw in request.url.query for kw in ["qubits", "circuit_depth", "oracle"]):
            return True
        
        return False
    
    def _build_quantum_request(self, request_data: Dict[str, Any], 
                              request: Request) -> Dict[str, Any]:
        """Build quantum request for threat detector"""
        query_params = dict(request.query_params)
        body = {}
        
        try:
            if request_data.get("body"):
                body = json.loads(request_data["body"])
        except:
            pass
        
        return {
            "ip": request.client.host if request.client else "unknown",
            "operation_type": body.get("operation_type") or self._infer_operation_type(request.url.path),
            "circuit_depth": int(body.get("circuit_depth", 0)) or int(query_params.get("depth", 0)),
            "num_qubits": int(body.get("num_qubits", 0)) or int(query_params.get("qubits", 0)),
            "gate_count": int(body.get("gate_count", 0)),
            "sample_count": int(body.get("sample_count", 1)),
            "parameters": body.get("parameters", {}),
            "execution_times": body.get("execution_times", []),
            "timing_measurements": body.get("timing_measurements", []),
            "request_size_bytes": len(request_data.get("body", ""))
        }
    
    def _infer_operation_type(self, path: str) -> str:
        """Infer quantum operation type from path"""
        path_lower = path.lower()
        
        if "bell" in path_lower:
            return "bell_state"
        elif "grover" in path_lower:
            return "grover"
        elif "vqe" in path_lower:
            return "vqe"
        elif "qaoa" in path_lower:
            return "qaoa"
        elif "teleport" in path_lower:
            return "teleportation"
        elif "qrng" in path_lower or "random" in path_lower:
            return "qrng"
        elif "oracle" in path_lower:
            return "oracle"
        else:
            return "generic"
    
    async def _deploy_quantum_countermeasures(self, request: Request, 
                                             threat_assessment: Any) -> Any:
        """Deploy quantum-specific countermeasures"""
        from fastapi.responses import JSONResponse
        
        # Generate fake quantum data based on threat type
        fake_data = self._generate_fake_quantum_data(
            threat_assessment.threat_type,
            request.url.path
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "data": fake_data,
                "message": "Quantum operation completed",
                "tracking_token": self._generate_tracking_token(),
                "_defense_note": "Countermeasures active"
            }
        )
    
    async def _serve_fake_quantum_data(self, request: Request, 
                                      defense_response: Dict, 
                                      threat_assessment: Any) -> Any:
        """Serve fake quantum data to attacker"""
        from fastapi.responses import JSONResponse
        
        operation_type = self._infer_operation_type(request.url.path)
        fake_data = self._generate_fake_quantum_data(operation_type, request.url.path)
        
        return JSONResponse(
            status_code=200,
            content={
                "result": fake_data,
                "quantum_metrics": {
                    "fidelity": 0.95,
                    "success_probability": 0.87,
                    "execution_time_ms": 123
                },
                "tracking_token": self._generate_tracking_token()
            }
        )
    
    def _generate_fake_quantum_data(self, operation_type: str, path: str) -> Dict[str, Any]:
        """Generate realistic fake quantum data"""
        import random
        
        if operation_type == "bell_state":
            return {
                "measurements": [random.randint(0, 1) for _ in range(100)],
                "entanglement": 0.999,
                "fidelity": 0.96
            }
        elif operation_type == "grover":
            return {
                "solution": random.randint(0, 15),
                "iterations": 3,
                "probability": 0.95
            }
        elif operation_type == "qrng":
            bits = [random.randint(0, 1) for _ in range(256)]
            return {
                "bits": bits,
                "entropy": 0.999,
                "min_entropy": 0.998
            }
        elif operation_type == "vqe":
            return {
                "energy": -1.234 + random.random() * 0.01,
                "iterations": 50,
                "convergence": 0.99
            }
        else:
            return {
                "status": "success",
                "result": [random.random() for _ in range(10)],
                "execution_time_us": random.randint(100, 10000)
            }
    
    def _generate_tracking_token(self) -> str:
        """Generate unique tracking token"""
        token_data = f"{time.time()}{hashlib.urandom(16).hex()}"
        return hashlib.sha256(token_data.encode()).hexdigest()[:32]
    
    def get_quantum_stats(self) -> Dict[str, Any]:
        """Get quantum defense statistics"""
        return {
            **self.quantum_stats,
            "recent_operations": self.qsharp_operation_history[-20:]
        }
    
    def get_operation_history(self) -> list:
        """Get full operation history"""
        return self.qsharp_operation_history


def create_qsharp_defense_middleware(app: FastAPI, enable_quantum: bool = True) -> Any:
    """
    Create and attach Q# quantum defense middleware to FastAPI app
    
    Usage:
        from fastapi import FastAPI
        from integrations.qsharp_middleware import create_qsharp_defense_middleware
        
        app = FastAPI()
        defense = create_qsharp_defense_middleware(app, enable_quantum=True)
    
    Args:
        app: FastAPI application instance
        enable_quantum: Enable quantum-specific threat detection
        
    Returns:
        Middleware instance with defense capabilities
    """
    from core.orchestrator import DefenseOrchestrator
    
    # Initialize orchestrator
    base_dir = Path(__file__).parent.parent
    config_dir = base_dir / "config"
    orchestrator = DefenseOrchestrator(str(config_dir), str(base_dir))
    
    # Create middleware
    middleware = QuantumDefenseMiddleware(orchestrator, enable_quantum)
    
    # Add middleware to app
    app.middleware("http")(middleware)
    
    # Add status endpoint
    @app.get("/quantum-defense/status")
    async def quantum_defense_status() -> Dict[str, Any]:
        """Get quantum defense middleware status"""
        return middleware.get_quantum_stats()
    
    # Add history endpoint
    @app.get("/quantum-defense/history")
    async def quantum_operation_history() -> Dict[str, Any]:
        """Get quantum operation history"""
        return {
            "operations": middleware.get_operation_history()
        }
    
    return type('MiddlewareWrapper', (), {
        'middleware': middleware,
        'orchestrator': orchestrator
    })()


if __name__ == "__main__":
    # Test middleware
    from fastapi import FastAPI
    import uvicorn
    
    app = FastAPI()
    defense = create_qsharp_defense_middleware(app)
    
    @app.post("/quantum/bell-state")
    async def bell_state():
        """Run Bell state circuit"""
        return {"measurement": [0, 0]}
    
    @app.post("/quantum/grover")
    async def grover():
        """Run Grover's algorithm"""
        return {"solution": 5}
    
    print("Starting Quantum Defense Middleware Test Server...")
    uvicorn.run(app, host="localhost", port=8000)
