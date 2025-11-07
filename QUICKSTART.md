# Quick Start Guide

## Installation (5 minutes)

### 1. Install Prerequisites

```powershell
# Install Poetry (Python dependency manager)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Install .NET SDK (if not already installed)
winget install Microsoft.DotNet.SDK.8

# Install Cake Tool
dotnet tool install -g Cake.Tool
```

### 2. Install Dependencies

```powershell
cd C:\Users\redgh\zero-trust-ai-defense
poetry install
```

### 3. Test Installation

```powershell
poetry run python main.py
```

You should see output showing the system initializing and processing a test SQL injection attack.

## Basic Usage

### As a Standalone System

```python
from main import DefenseOrchestrator
import time

# Initialize
orchestrator = DefenseOrchestrator("config", ".")

# Process a request
request = {
    "timestamp": time.time(),
    "ip": "203.0.113.42",
    "user_agent": "suspicious-bot/1.0",
    "endpoint": "/api/users",
    "params": {"id": "1' OR '1'='1"},
    "headers": {},
    "content": "SELECT * FROM users",
    "session_id": "session123"
}

response = orchestrator.process_request(request)
print(response)
```

### As Web Middleware (FastAPI Example)

```python
from fastapi import FastAPI, Request
from main import DefenseOrchestrator
import time

app = FastAPI()
orchestrator = DefenseOrchestrator("config", ".")

@app.middleware("http")
async def defense_middleware(request: Request, call_next):
    request_data = {
        "timestamp": time.time(),
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
        "endpoint": request.url.path,
        "params": dict(request.query_params),
        "headers": dict(request.headers),
        "content": str(await request.body()),
        "session_id": request.cookies.get("session_id", "")
    }
    
    response = orchestrator.process_request(request_data)
    
    if response["action"] == "countermeasures":
        # Serve fake data
        return {"data": "poisoned_data_with_tracking_token"}
    
    return await call_next(request)
```

## Understanding the Response

### Safe Request
```json
{
  "action": "allow",
  "reason": "Passed safety verification",
  "details": {...}
}
```

### Suspicious Request (Countermeasures Deployed)
```json
{
  "action": "countermeasures",
  "risk_level": "high",
  "risk_score": 90,
  "threat_category": "sql_injection",
  "recommended_actions": ["log", "track", "serve_fake_data", ...],
  "confidence": 0.95,
  "countermeasures": {
    "success": true,
    "scenario": "sql_injection",
    "intensity": "high",
    "environment": "/path/to/env",
    "script": "/path/to/script.cake",
    "execution_time": 2.3
  }
}
```

## Configuration

### Adjusting Detection Sensitivity

Edit `config/rules.yaml`:

```yaml
detection_rules:
  timing_patterns:
    - name: "consistent_timing"
      threshold: 0.95  # Lower = more sensitive
      risk_score: 60   # Higher = more aggressive response
```

### Adding Custom Scenarios

Edit `config/policies.yaml`:

```yaml
scenarios:
  my_custom_attack:
    description: "My custom attack pattern"
    environment_requirements:
      - requests
      - faker
    cake_template: "my_template.cake"
    counter_strategy: "custom_strategy"
    isolation_level: "high"
```

Create `cake/templates/my_template.cake`:

```csharp
var intensity = Argument("intensity", {{ intensity }});
var trackingToken = "{{ tracking_token }}";

Task("My-Custom-Counter")
    .Does(() => {
        // Your countermeasure logic here
        Information($"Deploying custom countermeasure: {intensity}");
    });

RunTarget("My-Custom-Counter");
```

## Monitoring

### Check System Status

```python
status = orchestrator.get_status()
print(f"Active environments: {status['active_environments']}")
print(f"Total executions: {status['total_executions']}")
```

### View Execution Logs

Logs are stored in:
- `logs/environment_creation.log` - Environment creation history
- `logs/counter_actions.log` - Countermeasure deployments

### Cleanup

```python
# Cleanup old environments
orchestrator.cleanup()
```

## Common Attack Scenarios

### 1. SQL Injection
**Detected by:** SQL keywords in content
**Response:** Deploys fake database with tracking tokens
**Cake Template:** `sql_honeypot.cake`

### 2. API Scraping
**Detected by:** Burst activity, consistent timing
**Response:** Floods attacker with fake data, contradictions
**Cake Template:** `flood_agent.cake`

### 3. Model Extraction
**Detected by:** Systematic parameter exploration
**Response:** Serves adversarial examples, poisoned data
**Cake Template:** `model_defense.cake`

## Troubleshooting

### "Poetry not found"
```powershell
# Add Poetry to PATH, then restart terminal
$env:Path += ";$env:APPDATA\Python\Scripts"
```

### "dotnet cake not found"
```powershell
# Ensure .NET tools are in PATH
dotnet tool list -g
# If Cake.Tool not listed, install it
dotnet tool install -g Cake.Tool
```

### "Module not found" errors
```powershell
# Reinstall dependencies
cd C:\Users\redgh\zero-trust-ai-defense
poetry install
```

### Environment creation fails
- Check you have write permissions to the directory
- Ensure sufficient disk space
- Check `logs/environment_creation.log` for details

## Next Steps

1. **Test with your own data**: Modify `main.py` to test with your specific attack patterns
2. **Integrate with your app**: Add the middleware to your web framework
3. **Customize scenarios**: Add attack patterns specific to your application
4. **Monitor effectiveness**: Track which countermeasures are most effective
5. **Tune sensitivity**: Adjust thresholds to reduce false positives

## Safety Reminders

- ✅ Use for **defensive purposes only**
- ✅ Test thoroughly before production use
- ✅ Monitor for false positives
- ✅ Review logs regularly
- ✅ Ensure legal compliance
- ❌ Never deploy offensive countermeasures
- ❌ Never use without safety filtering enabled

## Getting Help

Check the full README.md for:
- Complete architecture documentation
- Detailed API reference
- Advanced configuration options
- Security considerations
- Contributing guidelines
