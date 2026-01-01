# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Zero-Trust AI Defense System - A sophisticated security agent model that detects and counters AI/ML attacks using a "fight fire with fire" approach. The system detects attack patterns, serves poisoned data to mislead attackers, and deploys counter-agents to confuse and trap malicious bots and AI models.

## Common Commands

### Installation & Setup

```powershell
# Install dependencies
poetry install

# Run basic defense system test
poetry run python main.py

# Run production server with defense middleware
cd server
poetry run python protected_server.py

# Run the Defense Agent (AI assistant)
poetry run defense-agent
```

### Testing

There are currently **no test files** in the repository. When adding tests:
- Use pytest (already in dev dependencies)
- Run with: `poetry run pytest`

### Linting & Code Quality

Dev dependencies include:
- `black` for formatting: `poetry run black .`
- `ruff` for linting: `poetry run ruff check .`

### Development Server

```powershell
# Start the protected server with defense middleware
cd server
poetry run python protected_server.py
# Server runs on http://localhost:8000
# Admin dashboard: http://localhost:8000/admin/dashboard (admin:admin123)
# API docs: http://localhost:8000/api/docs
```

### Environment Management

```powershell
# Poetry environments are created dynamically per attack scenario
# View created environments: 
Get-ChildItem environments/

# Clean up environments manually if needed:
Remove-Item -Recurse environments/scenario_*
```

### Cake Scripts

```powershell
# Cake scripts are generated dynamically, but you can test templates:
dotnet cake cake/templates/sql_honeypot.cake --intensity=10

# Verify Cake tool is available:
dotnet cake --version
```

## High-Level Architecture

### Multi-Stage Defense Pipeline

The system uses a **four-stage defense pipeline** that processes every incoming request:

1. **Safety Filter** (`core/query_analyzer.py`)
   - Multi-stage verification to prevent false positives
   - Checks: IP reputation, rate limits, timing patterns, content analysis, ML patterns
   - Maintains user reputation scores
   - Only triggers defense on confirmed suspicious activity

2. **Pattern Detection** (`core/detector.py`)
   - Analyzes timing patterns (burst activity, consistent intervals)
   - Detects behavioral anomalies (systematic enumeration, token abuse)
   - Identifies content-based attacks (SQL injection, XSS, path traversal)
   - Recognizes ML-specific attacks (model extraction, membership inference)
   - Maintains request history per fingerprint (IP + user agent + session)

3. **Risk Assessment** (`core/risk_scorer.py`)
   - Calculates risk score (0-100) from detected patterns
   - Maps to risk levels: LOW (30-59), MEDIUM (60-79), HIGH (80-94), CRITICAL (95+)
   - Determines threat category and recommended actions
   - Decides whether to deploy countermeasures

4. **Countermeasure Deployment** (`core/orchestrator.py`)
   - Orchestrates the defense response
   - Creates isolated Poetry environments per scenario
   - Generates scenario-specific Cake scripts
   - Executes countermeasures safely with resource limits

### Dynamic Environment System

**Poetry Environment Manager** (`environments/poetry_manager.py`):
- Creates **isolated Python environments** for each attack scenario
- Each environment has scenario-specific dependencies (e.g., SQLAlchemy for SQL injection)
- Generates unique `pyproject.toml` per environment
- Applies isolation levels: low, medium, high, critical (with CPU/memory/timeout limits)
- All environment creation is logged to `logs/environment_creation.log`

**Why Poetry?** Provides filesystem isolation and dependency isolation to safely execute countermeasures without affecting the main system.

### Cake Script Generation System

**Cake Generator** (`cake/generator.py`):
- Uses **Jinja2 templates** to generate C#/.NET Cake build scripts dynamically
- Templates located in `cake/templates/`:
  - `sql_honeypot.cake` - Generates fake database records with tracking tokens
  - `flood_agent.cake` - Spawns counter-agents to flood attacker
  - `default.cake` - Generic countermeasure template
- Each script receives context: attack details, intensity level, tracking tokens
- **Tracking tokens** are embedded in all fake data to trace exfiltration

**Cake Executor** (`cake/executor.py`):
- Executes generated Cake scripts in isolated Poetry environments
- Uses `dotnet cake` command with timeout limits
- Captures stdout/stderr for logging
- Maintains execution history for auditing

**Why Cake?** Leverages .NET ecosystem (Bogus for fake data generation) and provides structured build automation for countermeasures.

### Scenario-Based Response

The system maps threat categories to predefined scenarios (`config/policies.yaml`):

- **sql_injection** → Deploy fake database with tracking tokens
- **api_scraping** → Flood attacker with contradictory data
- **credential_stuffing** → Create honeypot accounts
- **model_extraction** → Serve adversarial examples and poisoned predictions
- **data_exfiltration** → Inject adversarial data with backdoor patterns
- **directory_traversal** → Generate fake filesystem

Each scenario defines:
- `environment_requirements` - Python packages needed
- `cake_template` - Which Cake script template to use
- `counter_strategy` - Tactics to employ (from `counter_strategies` config)
- `isolation_level` - Security isolation level

### Virtual Resources (Server)

The `server/protected_server.py` implements a **full production server** with virtual resources:

**Virtual Filesystem** (`server/virtual_resources.py`):
- In-memory filesystem with realistic directory structure
- All file operations are tracked
- Supports list, read, upload, delete operations
- Detects path traversal attempts

**Virtual Database**:
- Pre-populated with 25 fake users, 50 products, 100 orders
- Simplified SQL parser to return appropriate fake data
- All queries are logged and analyzed

**Virtual User Manager**:
- 10 pre-created fake users + admin account
- Authentication with token generation
- Monitors for brute force and SQL injection in login attempts

**Honeypot Endpoints**:
- `/.env` - Fake environment variables
- `/admin/backup` - Fake database backup
- `/admin/config` - Fake configuration
- `/api/internal/secrets` - Fake API keys
- All honeypot access is logged with tracking tokens

### Integration Middleware

**QSharp Defense Middleware** (`integrations/qsharp_middleware.py`):
- FastAPI middleware that intercepts all requests
- Extracts request metadata (IP, user agent, endpoint, params, headers, content)
- Passes to DefenseOrchestrator for processing
- Serves fake data if countermeasures are deployed
- Returns 429 or blocks if risk is critical

**How to integrate with existing FastAPI apps:**
```python
from integrations.qsharp_middleware import create_qsharp_defense_middleware

create_qsharp_defense_middleware(your_app)
```

### Request Flow

```
Request → Defense Middleware → QueryAnalyzer (Safety Check)
                                    ↓ (suspicious)
                              PatternDetector (Analyze patterns)
                                    ↓
                              RiskScorer (Calculate risk)
                                    ↓ (high/critical)
                              DefenseOrchestrator
                                    ↓
                              PoetryManager (Create isolated env)
                                    ↓
                              CakeGenerator (Generate countermeasure script)
                                    ↓
                              CakeExecutor (Execute in isolated env)
                                    ↓
                              Response with fake/poisoned data
```

## Configuration Files

### `config/rules.yaml`

Defines detection rules and thresholds:
- `detection_rules`: Timing, behavioral, content, and ML attack patterns
- `safety_filters`: Whitelist patterns and multi-stage verification
- `response_policies`: Risk thresholds and response strategies

**Key thresholds:**
- `consistent_timing.threshold: 0.95` - Lower = more sensitive to bot timing
- `burst_activity.threshold: 5.0` - Requests per second that trigger alert
- `sql_injection.risk_score: 90` - High risk for SQL injection
- Risk levels: LOW (30), MEDIUM (60), HIGH (80), CRITICAL (95)

### `config/policies.yaml`

Defines attack scenarios and countermeasure strategies:
- `scenarios`: Maps threat categories to environment requirements and Cake templates
- `counter_strategies`: Tactics and intensity levels per strategy
- `isolation_levels`: CPU/memory/timeout limits per isolation level
- `poetry_templates`: Base dependencies for Poetry environments

## Defense Agent (AI Assistant)

The Defense Agent is an integrated AI assistant powered by Claude that can autonomously execute tasks, interact with the defense system, and provide AI-powered shell assistance.

### Quick Start

```powershell
# Set API key
$env:ANTHROPIC_API_KEY="your_key_here"

# Run the agent
poetry run defense-agent
```

### Capabilities

**Development Tasks:**
- Read, create, and edit files
- Search codebase with grep and file patterns
- Execute shell commands
- AI-powered command suggestions via aish (Microsoft AI Shell)

**Defense Operations:**
- Check defense system status: `/status` or "check defense status"
- Analyze threats: "analyze this request: {request_data}"
- List attack scenarios: "show available scenarios"
- View defense logs: "show recent environment logs"

**Task Management:**
- Automatically creates TODO lists for complex tasks (3+ steps)
- Tracks progress through multi-step operations
- Marks completed tasks

### Usage Examples

```
# Development
You: find all detection patterns in config/rules.yaml
Agent: [searches and displays patterns]

# Defense Operations
You: analyze a SQL injection from IP 203.0.113.42
Agent: [processes through defense pipeline, shows risk assessment]

# Shell Assistance
You: use aish to find files modified today
Agent: [provides PowerShell command suggestion]
```

### Special Commands

- `/status` - Show defense system status
- `/help` - List available tools
- `/reset` - Clear conversation history
- `/quit` - Exit agent

### aish Integration

The agent includes an `aish` tool that:
1. Attempts to use system aish if installed (Microsoft AI Shell via `winget install Microsoft.AIShell`)
2. Falls back to built-in command suggestions if unavailable
3. Provides context-aware PowerShell/cmd suggestions

The fallback mode includes patterns for:
- File operations, git commands, poetry, cake scripts
- Process management, port checking
- Defense system specific commands

### Programmatic Usage

```python
from agents import DefenseAgent
from core.orchestrator import DefenseOrchestrator

# Initialize with defense integration
orchestrator = DefenseOrchestrator("config", ".")
agent = DefenseAgent(defense_orchestrator=orchestrator)

# Execute tasks
response = agent.run("analyze recent threats")

# Access defense directly
status = agent.get_defense_status()
result = agent.process_defense_request(request_data)
```

See `agents/README.md` for complete documentation.

## Development Guidelines

### Adding New Attack Scenarios

1. **Add scenario to `config/policies.yaml`:**
   ```yaml
   scenarios:
     my_new_attack:
       description: "Description of attack"
       environment_requirements:
         - required-package
       cake_template: "my_template.cake"
       counter_strategy: "my_strategy"
       isolation_level: "high"
   ```

2. **Add counter strategy:**
   ```yaml
   counter_strategies:
     my_strategy:
       tactics:
         - "tactic_1"
         - "tactic_2"
       intensity_levels:
         low: 5
         medium: 20
         high: 50
   ```

3. **Create Cake template in `cake/templates/my_template.cake`:**
   ```csharp
   var intensity = Argument("intensity", {{ intensity }});
   var trackingToken = "{{ tracking_token }}";
   
   Task("My-Counter-Measure")
       .Does(() => {
           Information($"Deploying countermeasure: {intensity}");
           // Your C# countermeasure logic here
       });
   
   RunTarget("My-Counter-Measure");
   ```

4. **Map threat category in `core/risk_scorer.py`:**
   Add logic to `get_scenario_for_threat()` method to map threat category to scenario name.

### Adding Detection Rules

Edit `config/rules.yaml` to add new pattern detection:

```yaml
detection_rules:
  content_patterns:
    - name: "my_new_pattern"
      regex_patterns:
        - "(?i)suspicious_pattern"
      risk_score: 85
```

Then implement detection logic in `core/detector.py` in the appropriate `_check_*` method.

### Working with Virtual Resources

When modifying `server/protected_server.py`:
- **Virtual resources are in-memory** - no real data exists
- **All fake data should include tracking tokens** - use `secrets.token_hex(16)` or similar
- **Log all honeypot access** to `vfs.honeypot_access_log`
- **Maintain consistency** - fake data should be realistic but always poisoned

### Tracking Tokens

Every piece of fake data must contain a **unique tracking token**:
- Tokens are SHA-256 hashes (16-char substring)
- Generated per request/scenario in `CakeGenerator._generate_tracking_token()`
- Embedded in fake credentials, API keys, database records, file contents
- Purpose: Trace if/when/where exfiltrated data is used

### Isolation and Safety

**Always consider isolation:**
- Poetry environments provide filesystem isolation
- Resource limits prevent resource exhaustion (see `isolation_levels` in policies.yaml)
- Network isolation can be configured per level
- Cake execution has timeout limits

**Safety first:**
- Multi-stage safety filter prevents false positives
- Reputation scores track legitimate vs. suspicious users
- All actions are logged for audit (`logs/` directory)
- Never deploy countermeasures on uncertain threats

## File Structure Context

```
core/
├── orchestrator.py       # Main coordinator, processes requests through pipeline
├── detector.py           # Pattern detection (timing, behavioral, content, ML)
├── risk_scorer.py        # Risk assessment and threat categorization
└── query_analyzer.py     # Multi-stage safety filter

environments/
└── poetry_manager.py     # Creates isolated Poetry environments per scenario

cake/
├── generator.py          # Generates Cake scripts from templates
├── executor.py           # Executes Cake scripts in isolated environments
└── templates/            # Jinja2 templates for Cake scripts

server/
├── protected_server.py   # Production FastAPI server with defense
├── virtual_resources.py  # Virtual filesystem, database, user manager
├── paywall.py           # Payment/subscription management
└── registration.py      # User registration system

agents/                  # Defense Agent (AI assistant)
├── defense_agent.py     # Main agent with agentic loop
├── agent_config.py      # Configuration and system prompt
├── agent_tools.py       # Tool definitions (includes aishell integration)
├── agent_cli.py         # Rich CLI interface
└── README.md            # Agent documentation

integrations/
└── qsharp_middleware.py  # FastAPI middleware for defense integration

config/
├── rules.yaml           # Detection rules and safety filters
└── policies.yaml        # Scenarios, strategies, isolation levels

logs/                    # All logs (environment creation, counter actions)
```

## Important Notes

- **This is a defensive security tool** - Use responsibly and ethically
- **No test suite exists yet** - Add tests when implementing new features
- **False positives are critical** - The safety filter must be robust
- **All data is virtual** - No real data exposure risk in the server
- **Windows-specific paths** - Project uses Windows PowerShell conventions
- **Poetry and .NET required** - Both must be installed and in PATH
- **Cake templates use C#** - Leverage .NET ecosystem (Bogus, Newtonsoft.Json, etc.)
- **Never commit secrets** - Use environment variables for sensitive config

## Environment Variables (Server)

When running the production server:
- `STRIPE_SECRET_KEY` - Stripe API key (optional)
- `STRIPE_PRICE_ID` - Stripe price ID (optional)
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret (optional)
- `STRIPE_MODE` - "payment" or "subscription" (default: "payment")
- `ENABLE_DEV_PAY` - "1" to enable dev payment bypass (default: "1")
- `RETURN_VERIFICATION_CODE` - "1" to return 2FA codes in API (default: "1")

## Key Concepts

### Request Fingerprinting
Combines IP + user agent + session ID to create unique identifier for tracking request patterns over time.

### Risk Scoring
Additive system where each detected pattern contributes to total risk score. Multiple patterns compound the risk.

### Intensity Levels
Countermeasures scale with threat severity:
- **low** - Minimal response (e.g., 5-10 fake records)
- **medium** - Moderate response (e.g., 20-50 fake records)
- **high** - Aggressive response (e.g., 50-200 fake records)

### Counter-Agent Philosophy
Instead of just blocking attacks, the system **actively misleads** attackers with poisoned data, making their efforts counterproductive.
