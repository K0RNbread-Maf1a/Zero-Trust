# Zero-Trust AI Defense System

A sophisticated zero-trust security agent model designed to detect and counter AI/ML attacks using a "fight fire with fire" approach. The system detects attack patterns, serves poisoned data to mislead attackers, and deploys counter-agents to confuse and trap malicious bots and AI models.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Incoming Request                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   Multi-Stage Safety       │
        │   Filter (QueryAnalyzer)   │◄─── Whitelists, Reputation
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   Pattern Detection        │
        │   (Detector)               │◄─── ML Attack Patterns
        └────────────┬───────────────┘     Bot Signatures
                     │
                     ▼
        ┌────────────────────────────┐
        │   Risk Assessment          │
        │   (RiskScorer)             │◄─── Rules, Thresholds
        └────────────┬───────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
    LOW/MEDIUM                 HIGH/CRITICAL
        │                         │
        ▼                         ▼
  ┌────────┐         ┌───────────────────────┐
  │  Log & │         │  Deploy Counter-      │
  │  Track │         │  measures             │
  └────────┘         └───────────┬───────────┘
                                 │
                     ┌───────────┴───────────┐
                     │                       │
                     ▼                       ▼
        ┌────────────────────┐  ┌──────────────────────┐
        │  Poetry Creates    │  │  Cake Script         │
        │  Isolated Env      │  │  Generated           │
        │  (scenario-based)  │  │  (attack-specific)   │
        └──────────┬─────────┘  └──────────┬───────────┘
                   │                       │
                   └───────────┬───────────┘
                               ▼
                   ┌───────────────────────┐
                   │  Cake Executor        │
                   │  Runs in Isolated Env │
                   └───────────┬───────────┘
                               │
                   ┌───────────┴───────────┐
                   │                       │
                   ▼                       ▼
        ┌────────────────┐     ┌────────────────────┐
        │  Serve Fake    │     │  Deploy Counter-   │
        │  Data with     │     │  Agents (flood,    │
        │  Tracking      │     │  confuse, trap)    │
        └────────────────┘     └────────────────────┘
```

## Key Features

### 1. **Multi-Stage Safety Filter**
- Filters out legitimate queries before triggering defenses
- Prevents false positives through:
  - IP reputation checks
  - Rate limit analysis
  - Human behavior detection (typos, timing variance)
  - Content analysis
  - Whitelist patterns

### 2. **Pattern Detection**
- **Timing Analysis**: Detects bot-like consistent request patterns
- **Behavioral Analysis**: Identifies systematic enumeration, token abuse
- **Content Analysis**: SQL injection, XSS, directory traversal
- **ML Attack Detection**: Model inversion, membership inference, model extraction

### 3. **Scenario-Based Response**
- **SQL Injection** → Deploy fake database with tracking tokens
- **API Scraping** → Flood attacker with false data
- **Model Extraction** → Serve adversarial examples, poisoned data
- **Directory Traversal** → Generate fake filesystem
- **Credential Stuffing** → Create honeypot accounts

### 4. **Poetry-Managed Environments**
- Dynamic environment creation per attack scenario
- Isolated execution with resource limits
- Scenario-specific dependencies
- Configurable isolation levels (low, medium, high, critical)

### 5. **Cake Build Scripts**
- Dynamically generated based on attack analysis
- Execute countermeasures in C#/.NET
- Templates for different attack types
- Leverages .NET ecosystem (Bogus for fake data, etc.)

## Setup

### Prerequisites

1. **Python 3.10+**
2. **Poetry** (Python dependency manager)
   ```powershell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   ```
3. **.NET SDK 6.0+** (for Cake scripts)
   ```powershell
   winget install Microsoft.DotNet.SDK.8
   ```
4. **Cake Tool** (dotnet-cake)
   ```powershell
   dotnet tool install -g Cake.Tool
   ```

### Installation

1. Navigate to the project directory:
   ```powershell
   cd C:\Users\redgh\zero-trust-ai-defense
   ```

2. Install Python dependencies:
   ```powershell
   poetry install
   ```

3. Verify installation:
   ```powershell
   poetry run python main.py
   ```

## Configuration

### Rules Configuration (`config/rules.yaml`)

Defines detection patterns and risk scores:

```yaml
detection_rules:
  timing_patterns:
    - name: "consistent_timing"
      threshold: 0.95
      risk_score: 60
      
  ml_attack_patterns:
    - name: "model_extraction"
      risk_score: 95
```

### Policies Configuration (`config/policies.yaml`)

Defines scenarios and countermeasure strategies:

```yaml
scenarios:
  sql_injection:
    description: "SQL injection attack detected"
    environment_requirements:
      - sqlalchemy
      - faker
    cake_template: "sql_honeypot.cake"
    counter_strategy: "database_poisoning"
    isolation_level: "high"
```

## Usage

### Basic Usage

```python
from main import DefenseOrchestrator
import time

# Initialize
orchestrator = DefenseOrchestrator("config", ".")

# Process request
request_data = {
    "timestamp": time.time(),
    "ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "endpoint": "/api/users",
    "params": {"id": "123"},
    "headers": {"Authorization": "Bearer ..."},
    "content": "SELECT * FROM users",
    "session_id": "abc123"
}

response = orchestrator.process_request(request_data)

# Handle response
if response["action"] == "allow":
    # Request passed safety checks
    print("Safe request")
    
elif response["action"] == "countermeasures":
    # Countermeasures deployed
    print(f"Threat: {response['threat_category']}")
    print(f"Risk: {response['risk_level']}")
    print(f"Actions: {response['recommended_actions']}")
```

### Running the Test

```powershell
poetry run python main.py
```

This will:
1. Initialize the defense system
2. Process a simulated SQL injection attack
3. Show the response and deployed countermeasures
4. Display system status

### Integration with Web Server

```python
from fastapi import FastAPI, Request
from main import DefenseOrchestrator

app = FastAPI()
orchestrator = DefenseOrchestrator("config", ".")

@app.middleware("http")
async def defense_middleware(request: Request, call_next):
    # Extract request data
    request_data = {
        "timestamp": time.time(),
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
        "endpoint": request.url.path,
        "params": dict(request.query_params),
        "headers": dict(request.headers),
        "content": await request.body(),
        "session_id": request.cookies.get("session_id", "")
    }
    
    # Process through defense system
    response = orchestrator.process_request(request_data)
    
    if response["action"] == "countermeasures":
        # Serve fake data instead of real response
        return JSONResponse({
            "status": "success",
            "data": "fake_data_with_tracking_token"
        })
    
    # Allow normal processing
    return await call_next(request)
```

## How It Works

### Defense Pipeline

1. **Safety Filter** (First line of defense)
   - Quick checks: IP reputation, rate limits
   - Behavioral analysis: timing patterns, human errors
   - Deep inspection: ML patterns, fingerprinting
   - Multi-stage verification to avoid false positives

2. **Pattern Detection**
   - Analyzes request timing, behavior, content
   - Detects ML-specific attacks
   - Maintains request history for pattern matching

3. **Risk Assessment**
   - Calculates risk score (0-100)
   - Categorizes threat type
   - Determines response intensity
   - Maps to scenario configuration

4. **Countermeasure Deployment**
   - Creates isolated Poetry environment
   - Generates scenario-specific Cake script
   - Executes countermeasures safely
   - Logs all actions for auditing

### Scenario Example: SQL Injection

1. **Detection**: SQL keywords detected in request
2. **Assessment**: Risk score 90, threat category "sql_injection"
3. **Environment**: Poetry creates isolated env with SQLAlchemy, Faker
4. **Script Generation**: `sql_honeypot.cake` template rendered
5. **Execution**:
   - Generates 50 fake database records
   - Each record contains tracking token
   - Creates honeypot SQL schema
   - Logs deployment
6. **Response**: Attacker receives fake data

If the attacker exfiltrates this data, the tracking tokens reveal:
- What data was taken
- When it was accessed
- Potentially where it was used

## Advanced Features

### Custom Scenarios

Add to `config/policies.yaml`:

```yaml
scenarios:
  custom_attack:
    description: "Custom attack pattern"
    environment_requirements:
      - your-library
    cake_template: "custom_counter.cake"
    counter_strategy: "custom_strategy"
    isolation_level: "high"
```

Create `cake/templates/custom_counter.cake`:

```csharp
var intensity = Argument("intensity", 10);
var trackingToken = "{{ tracking_token }}";

Task("Custom-Counter-Measure")
    .Does(() => {
        // Your countermeasure logic
    });

RunTarget("Custom-Counter-Measure");
```

### Monitoring and Logging

```python
# Get system status
status = orchestrator.get_status()
print(f"Active environments: {status['active_environments']}")
print(f"Total executions: {status['total_executions']}")

# Get execution log
log = orchestrator.cake_executor.get_execution_log()
for entry in log:
    print(f"{entry['timestamp']}: {entry['script']} - {entry['success']}")
```

## Security Considerations

### Ethical Use
- This system is designed for **defensive purposes only**
- Never use active countermeasures offensively
- Ensure compliance with local laws and regulations
- Document all actions for legal compliance

### Safe Defaults
- Strict safety filtering to avoid false positives
- Multi-stage verification before action
- Resource limits on countermeasure execution
- All actions logged for auditing

### Isolation
- Poetry environments provide filesystem isolation
- Resource limits prevent resource exhaustion
- Network isolation prevents unintended connections
- Timeout limits prevent runaway processes

## Troubleshooting

### Poetry not found
```powershell
# Install Poetry
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### Cake tool not found
```powershell
# Install Cake
dotnet tool install -g Cake.Tool

# Verify
dotnet cake --version
```

### Environment creation fails
- Check Python version (3.10+)
- Ensure Poetry is in PATH
- Check disk space
- Review logs in `logs/environment_creation.log`

## Project Structure

```
zero-trust-ai-defense/
├── config/
│   ├── rules.yaml              # Detection rules
│   └── policies.yaml           # Scenario policies
├── core/
│   ├── detector.py             # Pattern detection
│   ├── risk_scorer.py          # Risk assessment
│   ├── query_analyzer.py       # Safety filtering
│   └── orchestrator.py         # Main coordinator
├── environments/
│   └── poetry_manager.py       # Environment management
├── cake/
│   ├── generator.py            # Script generation
│   ├── executor.py             # Script execution
│   └── templates/              # Cake templates
│       ├── default.cake
│       └── sql_honeypot.cake
├── logs/                       # Execution logs
├── main.py                     # Entry point
├── pyproject.toml             # Python dependencies
└── README.md                  # This file
```

## License

This is a security tool. Use responsibly and ethically. Ensure compliance with applicable laws.

## Contributing

This is a demonstration/educational project. For production use, additional hardening and testing is required.
