# Q# Integration Guide

This guide shows how to integrate the Zero-Trust AI Defense System with Q# (Q Sharp) quantum computing web applications.

## Overview

Q# applications typically expose quantum operations through REST APIs using Python host programs. The defense middleware integrates seamlessly with these architectures.

## Architecture

```
┌─────────────────────────────────────────┐
│  Q# Quantum Operations (.qs files)      │
│  - Bell States                           │
│  - Grover's Algorithm                    │
│  - Quantum Random Generation             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Python Host (FastAPI/Flask)             │
│  - Exposes Q# via REST API               │
│  - Handles HTTP requests                 │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Zero-Trust Defense Middleware           │
│  - Detects attack patterns               │
│  - Serves fake quantum data              │
│  - Tracks adversaries                    │
└─────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```powershell
# Install Q# for Python
pip install qsharp

# Install FastAPI and Uvicorn
pip install fastapi uvicorn

# Install defense system
cd C:\Users\redgh\zero-trust-ai-defense
poetry install
```

### 2. Add Middleware (One Line!)

```python
from fastapi import FastAPI
from integrations.qsharp_middleware import create_qsharp_defense_middleware

app = FastAPI()

# This single line adds full defense capabilities
create_qsharp_defense_middleware(app, enable_quantum=True)
```

### 3. Run Example

```powershell
cd C:\Users\redgh\zero-trust-ai-defense\examples
python qsharp_app_example.py
```

Visit http://localhost:8000/docs for interactive API documentation.

## Features

### 1. Q#-Specific Threat Detection

The middleware understands quantum computing attack patterns:

- **Quantum Circuit Probing**: Detects systematic exploration of quantum circuits
- **Algorithm Extraction**: Identifies attempts to reverse-engineer quantum algorithms
- **State Exfiltration**: Catches bulk extraction of quantum state data
- **Oracle Queries**: Monitors excessive queries to quantum oracles (e.g., Grover's algorithm)

### 2. Q#-Specific Countermeasures

When threats are detected, fake quantum data is served:

**For Model Extraction Attacks:**
```json
{
  "quantum_results": {
    "measurements": [0, 1, 0, 1, 1, 0, 0, 1],
    "success_probability": 0.8723,
    "fidelity": 0.9456,
    "tracking_token": "abc123def456"
  }
}
```

**For Data Exfiltration:**
```json
{
  "quantum_states": [
    {"state": "|0⟩", "amplitude": 0.707, "phase": 0},
    {"state": "|1⟩", "amplitude": 0.707, "phase": 3.14159}
  ],
  "tracking_token": "xyz789"
}
```

### 3. Quantum-Enhanced Security (Optional)

Enable quantum random number generation for tracking tokens:

```python
create_qsharp_defense_middleware(
    app, 
    enable_quantum=True  # Use quantum RNG
)
```

This provides **provably random** tracking tokens using quantum superposition.

## Complete Integration Example

### Step 1: Create Q# Operations

Create `QuantumOperations.qs`:

```qsharp
namespace QuantumDefense {
    open Microsoft.Quantum.Intrinsic;
    open Microsoft.Quantum.Canon;
    
    /// Generate quantum random bits
    operation GenerateRandomBits(numBits : Int) : Int[] {
        mutable results = new Int[numBits];
        
        use qubits = Qubit[numBits];
        
        for i in 0..numBits-1 {
            H(qubits[i]);  // Superposition
            let result = M(qubits[i]);  // Measure
            set results w/= i <- result == One ? 1 | 0;
            Reset(qubits[i]);
        }
        
        return results;
    }
    
    /// Run Bell state circuit
    operation RunBellState() : (Int, Int) {
        use (q1, q2) = (Qubit(), Qubit());
        
        H(q1);
        CNOT(q1, q2);
        
        let m1 = M(q1);
        let m2 = M(q2);
        
        Reset(q1);
        Reset(q2);
        
        return (m1 == Zero ? 0 | 1, m2 == Zero ? 0 | 1);
    }
}
```

### Step 2: Create Python Host with Defense

Create `quantum_api.py`:

```python
from fastapi import FastAPI
from integrations.qsharp_middleware import create_qsharp_defense_middleware
import qsharp

# Import Q# operations
qsharp.reload()
from QuantumDefense import GenerateRandomBits, RunBellState

app = FastAPI()

# Add defense middleware
defense = create_qsharp_defense_middleware(app, enable_quantum=True)

@app.post("/quantum/bell-state")
async def bell_state():
    """Run Bell state circuit"""
    result = RunBellState.simulate()
    return {"measurement": result}

@app.post("/quantum/random")
async def random_bits(num_bits: int = 128):
    """Generate quantum random bits"""
    bits = GenerateRandomBits.simulate(num_bits=num_bits)
    return {"bits": bits, "num_bits": num_bits}

@app.get("/defense/status")
async def defense_status():
    """Check defense system status"""
    return defense.middleware.orchestrator.get_status()
```

### Step 3: Run the Protected API

```powershell
uvicorn quantum_api:app --reload
```

## Testing the Defense

### Test 1: Normal Request (Allowed)

```powershell
curl -X POST http://localhost:8000/quantum/bell-state
```

**Response:** Real quantum data
```json
{
  "measurement": [0, 0]
}
```

### Test 2: Attack Pattern (Blocked)

```powershell
# SQL injection attempt
curl -X POST http://localhost:8000/quantum/random `
  -H "Content-Type: application/json" `
  -d '{"num_bits": "1000 OR 1=1"}'
```

**Response:** Fake data with tracking token
```json
{
  "quantum_operation": "generic",
  "result": [1, 0, 1, 1, 0, 1, 0, 0],
  "tracking_token": "a1b2c3d4e5f6g7h8",
  "note": "This is poisoned data for security purposes"
}
```

### Test 3: Systematic Probing (Detected)

```python
# This pattern will be detected
import requests

for i in range(100):
    # Systematic parameter exploration
    response = requests.post(
        "http://localhost:8000/quantum/random",
        json={"num_bits": i * 10}
    )
```

**Defense Action:** After detecting the pattern:
- Risk score increases
- Fake data served
- Counter-agents deployed
- All requests logged

## Monitoring Q# Operations

### Get Defense Statistics

```python
@app.get("/defense/qsharp-stats")
async def qsharp_stats():
    return defense.middleware.get_qsharp_stats()
```

**Response:**
```json
{
  "total_operations": 1523,
  "threats_detected": 47,
  "threat_percentage": 3.08,
  "quantum_enhanced": true
}
```

### View Threat History

```python
@app.get("/defense/threats")
async def threat_history():
    history = defense.middleware.qsharp_operation_history[-50:]
    threats = [h for h in history if h["threat_detected"]]
    return {"threats": threats}
```

## Advanced Configuration

### Custom Q# Threat Patterns

Add to `config/rules.yaml`:

```yaml
detection_rules:
  qsharp_patterns:
    - name: "quantum_circuit_probing"
      description: "Systematic exploration of quantum circuits"
      threshold: 0.8
      risk_score: 85
      
    - name: "oracle_abuse"
      description: "Excessive queries to quantum oracle"
      threshold: 100  # queries per minute
      risk_score: 80
```

### Custom Q# Countermeasures

Add to `config/policies.yaml`:

```yaml
scenarios:
  quantum_circuit_extraction:
    description: "Quantum algorithm extraction attempt"
    environment_requirements:
      - qsharp
      - numpy
      - scipy
    cake_template: "quantum_defense.cake"
    counter_strategy: "quantum_poisoning"
    isolation_level: "critical"
```

## Q# Quantum RNG Integration

For truly random tracking tokens, implement the Q# RNG:

```qsharp
namespace QuantumDefense {
    operation GenerateTrackingToken() : String {
        // Generate 128 quantum random bits
        let bits = GenerateRandomBits(128);
        
        // Convert to hex string
        mutable token = "";
        for i in 0..4..127 {
            let nibble = bits[i] * 8 + bits[i+1] * 4 + 
                        bits[i+2] * 2 + bits[i+3];
            set token += IntAsHex(nibble);
        }
        
        return token;
    }
}
```

Then update the middleware to use it:

```python
def _quantum_random_token(self) -> Optional[str]:
    try:
        from QuantumDefense import GenerateTrackingToken
        return GenerateTrackingToken.simulate()
    except:
        return None  # Fallback to classical
```

## Performance Considerations

### Overhead

- **Pattern Detection**: ~2-5ms per request
- **Safety Filter**: ~1-3ms per request
- **Countermeasure Deployment**: ~100-500ms (only when threat detected)

For quantum operations that take seconds/minutes, this overhead is negligible.

### Optimization Tips

1. **Cache Q# compilation**: Reuse compiled Q# operations
2. **Async processing**: Defense runs asynchronously
3. **Lazy countermeasures**: Only deploy when confidence > threshold
4. **Rate limiting**: Reduce load from bot attacks

## Security Best Practices

### 1. Monitor Quantum-Specific Patterns

```python
# Track quantum circuit complexity
if request.circuit_depth > 1000:
    log_suspicious_activity(request)
```

### 2. Validate Quantum Parameters

```python
# Prevent resource exhaustion
if request.num_qubits > MAX_QUBITS:
    return error_response()
```

### 3. Rate Limit Expensive Operations

```python
# Limit quantum simulations
@app.post("/quantum/simulate")
@rate_limit(requests_per_minute=10)
async def simulate(...):
    ...
```

## Troubleshooting

### "qsharp module not found"

```powershell
pip install qsharp
```

### "Q# compilation failed"

Ensure Q# operations are in the Python working directory:

```powershell
# Check Q# files
ls *.qs

# Reload Q# runtime
python -c "import qsharp; qsharp.reload()"
```

### Defense not triggering

Check configuration thresholds in `config/rules.yaml`:

```yaml
detection_rules:
  timing_patterns:
    - threshold: 0.95  # Lower for more sensitivity
```

## Production Checklist

- [ ] Test with legitimate quantum workloads
- [ ] Tune detection thresholds for your use case
- [ ] Set up monitoring and alerting
- [ ] Configure proper rate limits
- [ ] Enable quantum-enhanced RNG in production
- [ ] Review logs regularly
- [ ] Test countermeasure effectiveness
- [ ] Document false positive handling

## Next Steps

1. **Run the example**: `python examples/qsharp_app_example.py`
2. **Add to your Q# app**: Just 3 lines of code
3. **Customize detection**: Tune for your quantum algorithms
4. **Monitor effectiveness**: Track threats and false positives
5. **Enhance with Q# RNG**: Use quantum randomness

## Support

For issues specific to Q# integration, check:
- Q# documentation: https://learn.microsoft.com/en-us/azure/quantum/
- This project's README.md
- examples/qsharp_app_example.py

## License

Same as main project - use responsibly and ethically for defensive purposes only.
