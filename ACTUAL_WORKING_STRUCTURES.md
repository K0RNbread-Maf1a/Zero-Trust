# Actual Working File Directories and Data Structures

**Last Updated:** December 4, 2025  
**Project:** Zero-Trust AI Defense System

This document maps the actual working directories, files, and data structures currently implemented in the zero-trust-ai-defense project based on markdown documentation and existing code.

---

## 1. DIRECTORY STRUCTURE - Working Implementation

### Root Level
```
c:\Users\redgh\zero-trust-ai-defense\
├── config/                      # Configuration files (YAML-based)
├── core/                        # Core defense components
├── cake/                        # Cake build script generation
├── environments/                # Poetry environment management
├── deception/                   # Honeypot and fake data generation
├── defense/                     # Defense mechanisms
├── deploy/                      # Deployment utilities
├── monitoring/                  # Metrics and alerting system
├── tracking/                    # Attack attribution and tracking
├── agents/                      # AI Defense Agent with agentic loop
├── server/                      # Protected server with defense middleware
├── web/                         # Web UI and dashboard
├── logs/                        # Runtime logs (auto-generated)
├── examples/                    # Example usage scripts
├── QuickCreatePSCommands/       # PowerShell setup utilities
├── main.py                      # Entry point
├── pyproject.toml              # Poetry project configuration
└── README.md, *.md             # Documentation
```

---

## 2. DATA STRUCTURES AND REQUEST FLOW

### 2.1 Request Pipeline Data Structure

#### RequestMetadata (core/detector.py)
```python
@dataclass
class RequestMetadata:
    timestamp: float              # Unix timestamp
    source_ip: str               # Client IP address
    user_agent: str              # HTTP user agent
    endpoint: str                # API endpoint path
    query_params: Dict[str, Any] # URL parameters
    headers: Dict[str, str]      # HTTP headers
    content: str                 # Request body/content
    session_id: str              # Session identifier
    
    # Methods:
    fingerprint() -> str         # SHA256 hash for tracking
```

#### Input Request Data Structure (Expected)
```python
request_data = {
    "timestamp": time.time(),           # float (Unix timestamp)
    "ip": "203.0.113.42",              # str (IPv4/IPv6)
    "user_agent": "Mozilla/5.0...",    # str (HTTP user agent)
    "endpoint": "/api/users",           # str (URL path)
    "params": {"id": "123"},            # dict (URL parameters)
    "headers": {"Authorization": "Bearer..."}, # dict
    "content": "SELECT * FROM users",   # str (request body)
    "session_id": "abc123"              # str (session ID)
}
```

### 2.2 Detection Pipeline Data Structures

#### DetectionResult (core/detector.py)
```python
@dataclass
class DetectionResult:
    is_suspicious: bool          # Boolean flag
    confidence: float            # 0.0-1.0 confidence score
    detected_patterns: List[str] # ["timing_anomaly", "behavioral_anomaly", ...]
    risk_score: float            # 0-100+ score
    evidence: Dict[str, Any]     # Detailed evidence data
    timestamp: float             # Detection timestamp
```

#### Evidence Structure (core/detector.py)
```python
evidence = {
    "timing": {
        "coefficient_of_variation": 0.95,
        "requests_count": 10,
        "avg_interval": 0.5,
        "variance": 0.05
    },
    "behavioral": {
        "pattern_match": "systematic_enumeration",
        "confidence": 0.85,
        "sequence": [...]
    },
    "content": {
        "injection_type": "sql_injection",
        "keywords": ["SELECT", "FROM", "WHERE"],
        "suspicious_patterns": [...]
    }
}
```

### 2.3 Risk Assessment Data Structures

#### RiskAssessment (core/risk_scorer.py)
```python
@dataclass
class RiskAssessment:
    risk_level: RiskLevel        # Enum: LOW, MEDIUM, HIGH, CRITICAL
    risk_score: float            # 0-100+ numerical score
    threat_category: str         # "sql_injection", "model_extraction", etc.
    recommended_actions: List[str] # ["log", "track", "serve_fake_data", ...]
    confidence: float            # 0.0-1.0
    evidence_summary: Dict[str, Any] # Aggregated evidence
```

#### RiskLevel Enum (core/risk_scorer.py)
```python
class RiskLevel(Enum):
    LOW = "low"          # Score: 0-30
    MEDIUM = "medium"    # Score: 30-60
    HIGH = "high"        # Score: 60-80
    CRITICAL = "critical" # Score: 80-100+
```

### 2.4 Orchestrator Response Structure

#### Allowed Request Response (core/orchestrator.py)
```python
{
    "action": "allow",
    "reason": "Passed safety verification",
    "details": {
        "safe": True,
        "stage": 1,
        "reasons": ["IP in whitelist", "Known user"],
        "confidence": 0.95
    }
}
```

#### Countermeasure Deployment Response (core/orchestrator.py)
```python
{
    "action": "countermeasures",
    "risk_level": "high",
    "risk_score": 90,
    "threat_category": "sql_injection",
    "recommended_actions": ["log", "track", "serve_fake_data", "deploy_counter_agents"],
    "confidence": 0.95,
    "countermeasures": {
        "success": True,
        "scenario": "sql_injection",
        "intensity": "high",
        "environment": "/path/to/env",
        "script": "/path/to/script.cake",
        "execution_time": 2.3
    }
}
```

---

## 3. CONFIGURATION DATA STRUCTURES

### 3.1 Detection Rules (config/rules.yaml)

#### Timing Patterns Rule
```yaml
timing_patterns:
  - name: "consistent_timing"
    description: "Requests with suspiciously consistent intervals"
    threshold: 0.95           # Coefficient of variation threshold
    window_size: 10           # Requests to analyze
    risk_score: 60            # Added to total risk

  - name: "burst_activity"
    threshold: 5.0            # Requests per second
    window_size: 60           # Seconds
    risk_score: 70
```

#### Content Patterns Rule
```yaml
content_patterns:
  - name: "sql_injection"
    regex_patterns:
      - "(?i)(union|select|insert|update|delete|drop).*(?i)(from|where|table)"
      - "(?i)('\\s*or\\s*'1'\\s*=\\s*'1)"
    risk_score: 90

  - name: "ml_probing"
    indicators:
      - "systematic_feature_extraction"
      - "adversarial_example_generation"
      - "gradient_probing"
    risk_score: 85
```

#### ML Attack Patterns Rule
```yaml
ml_attack_patterns:
  - name: "model_inversion"
    description: "Attempting to reverse-engineer training data"
    indicators:
      - "confidence_score_probing"
      - "boundary_exploration"
    risk_score: 90

  - name: "membership_inference"
    description: "Determining if data was in training set"
    risk_score: 85

  - name: "model_extraction"
    description: "Attempting to clone the model"
    risk_score: 95
```

#### Response Policies
```yaml
response_policies:
  risk_thresholds:
    low: 30        # Monitor only
    medium: 60     # Deploy honeypots
    high: 80       # Active defense
    critical: 95   # Full countermeasures

  response_strategies:
    monitor:
      actions: ["log", "track"]
    
    active_defense:
      actions: ["log", "track", "serve_fake_data", "deploy_counter_agents"]
    
    full_countermeasures:
      actions: ["log", "track", "serve_fake_data", "deploy_counter_agents", 
                "aggressive_rate_limit", "set_traps", "reverse_tracking"]
```

### 3.2 Scenario Policies (config/policies.yaml)

#### Scenario Structure
```yaml
scenarios:
  sql_injection:
    description: "SQL injection attack detected"
    environment_requirements:
      - sqlalchemy
      - psycopg2-binary
      - faker
    cake_template: "sql_honeypot.cake"
    counter_strategy: "database_poisoning"
    isolation_level: "high"

  model_extraction:
    description: "ML model extraction attempt"
    environment_requirements:
      - scikit-learn
      - numpy
      - scipy
    cake_template: "model_defense.cake"
    counter_strategy: "model_poisoning"
    isolation_level: "critical"
```

#### Counter Strategy Structure
```yaml
counter_strategies:
  database_poisoning:
    tactics:
      - "inject_fake_records"
      - "add_tracking_tokens"
      - "create_honeypot_tables"
    intensity_levels:
      low: 10        # 10 fake records
      medium: 50     # 50 fake records
      high: 200      # 200 fake records

  model_poisoning:
    tactics:
      - "return_adversarial_predictions"
      - "inject_backdoor_triggers"
      - "modify_confidence_scores"
    intensity_levels:
      low: 0.05      # 5% poisoned
      medium: 0.15   # 15% poisoned
      high: 0.3      # 30% poisoned
```

#### Isolation Levels
```yaml
isolation_levels:
  low:
    network_isolation: false
    filesystem_isolation: true
    resource_limits:
      cpu: "50%"
      memory: "512MB"
      timeout: 30

  high:
    network_isolation: true
    filesystem_isolation: true
    resource_limits:
      cpu: "10%"
      memory: "128MB"
      timeout: 10

  critical:
    network_isolation: true
    filesystem_isolation: true
    resource_limits:
      cpu: "5%"
      memory: "64MB"
      timeout: 5
```

---

## 4. WORKING MODULES AND DATA FLOWS

### 4.1 Core/Orchestrator Module (core/orchestrator.py)

#### Class: DefenseOrchestrator
```python
class DefenseOrchestrator:
    def __init__(self, config_dir: str, base_dir: str):
        # Loads config files
        self.rules_config = Dict[str, Any]      # rules.yaml
        self.policies_config = Dict[str, Any]   # policies.yaml
        
        # Components initialized
        self.detector = PatternDetector         # Pattern detection
        self.risk_scorer = RiskScorer           # Risk calculation
        self.query_analyzer = QueryAnalyzer     # Safety filtering
        self.poetry_manager = PoetryEnvironmentManager  # Env creation
        self.cake_generator = CakeScriptGenerator      # Script generation
        self.cake_executor = CakeExecutor              # Script execution
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        # Pipeline:
        # 1. Convert request_data → RequestMetadata
        # 2. Run query_analyzer.analyze_query() → (is_safe, analysis)
        # 3. If safe → return {"action": "allow", ...}
        # 4. If suspicious → run detector.analyze_request() → DetectionResult
        # 5. Run risk_scorer.assess_risk() → RiskAssessment
        # 6. If risk high enough → deploy countermeasures
        # 7. Return {"action": "countermeasures", ...}
```

### 4.2 Detector Module (core/detector.py)

#### Class: PatternDetector
```python
class PatternDetector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.request_history = defaultdict(deque)  # Per-fingerprint history
        self.timing_windows = defaultdict(deque)   # Timing data per user
        self.fingerprint_cache = {}                # Cached fingerprints
    
    def analyze_request(self, request: RequestMetadata) -> DetectionResult:
        # Runs analysis checks:
        # 1. _check_timing_patterns() → (detected, evidence, risk_score)
        # 2. _check_behavioral_patterns() → (detected, evidence, risk_score)
        # 3. _check_content_patterns() → (detected, patterns, evidence, risk_score)
        # 4. _check_ml_attack_patterns() → (detected, evidence, risk_score)
        # Returns: DetectionResult with aggregated findings
```

#### Detection Methods Return Structure
```python
# _check_timing_patterns() returns:
(
    is_detected: bool,      # True if anomaly found
    evidence: Dict,         # {"coefficient_of_variation": 0.95, ...}
    risk_score: float       # 0-100 contribution
)

# _check_content_patterns() returns:
(
    is_detected: bool,
    patterns_list: List[str],  # ["sql_injection", "xss_attempt"]
    evidence: Dict,
    risk_score: float
)
```

### 4.3 Query Analyzer Module (core/query_analyzer.py)

#### Class: QueryAnalyzer
```python
class QueryAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.verification_stages = List[Dict]      # 3 stages of verification
        self.whitelist_patterns = List[Dict]       # Legitimate use patterns
        self.user_history = defaultdict(list)      # Per-user behavior history
        self.reputation_scores = defaultdict(float) # Per-user reputation
    
    def analyze_query(self, query: str, metadata: Dict[str, Any]) 
                      -> Tuple[bool, Dict[str, Any]]:
        # Multi-stage safety check:
        # Stage 1: Quick checks (IP reputation, rate limits)
        # Stage 2: Behavioral analysis (timing, content)
        # Stage 3: Deep inspection (ML patterns, fingerprinting)
        # Returns: (is_safe, analysis_details)
```

### 4.4 Risk Scorer Module (core/risk_scorer.py)

#### Class: RiskScorer
```python
class RiskScorer:
    def __init__(self, config: Dict[str, Any]):
        self.thresholds = Dict[str, int]         # {"low": 30, "medium": 60, ...}
        self.response_strategies = Dict[str, Any] # Action mappings
    
    def assess_risk(self, risk_score: float, detected_patterns: List[str],
                   evidence: Dict[str, Any]) -> RiskAssessment:
        # Determines:
        # 1. risk_level (LOW, MEDIUM, HIGH, CRITICAL)
        # 2. threat_category ("sql_injection", etc.)
        # 3. recommended_actions (["log", "track", ...])
        # 4. confidence score
        # Returns: RiskAssessment dataclass
```

---

## 5. DECEPTION LAYER (deception/)

### 5.1 Data Structures

#### TrackingToken Structure
```python
tracking_token = {
    "token": "unique_hex_string",
    "context": {
        "attack_type": "sql_injection",
        "endpoint": "/.env",
        "timestamp": 1701700000,
        "ip": "203.0.113.42"
    },
    "created_at": 1701700000,
    "expires_at": 1701786400,  # 24 hours
    "status": "active"
}
```

#### Fake Data Structure (FakeDataFactory)
```python
fake_env_file = {
    "DATABASE_URL": "postgresql://user:pass@fake-db:5432/db",
    "API_KEY": "sk-fake-key-with-tracking-token",
    "AWS_ACCESS_KEY": "AKIAFAKE123456789",
    "STRIPE_KEY": "sk_test_fake_key_with_tracking",
    "__tracking_tokens__": ["token1", "token2", ...]
}

fake_credentials = {
    "username": "fake_user",
    "email": "attacker@trap.local",
    "api_key": "api_key_with_tracking",
    "password_hash": "fake_bcrypt_hash",
    "__tracking_token__": "unique_token"
}
```

#### Honeypot Access Log
```python
honeypot_access_log = [
    {
        "timestamp": 1701700000,
        "path": "/.env",
        "ip": "203.0.113.42",
        "user_agent": "curl/7.0",
        "tracking_token": "abc123...",
        "response_size": 245
    },
    ...
]
```

### 5.2 Modules

#### honeypot_generator.py
```python
class HoneypotGenerator:
    def __init__(self, token_manager: TrackingTokenManager):
        self.token_manager = token_manager
    
    def generate_fake_env_file(self, tracking_token: str) -> str
    def generate_fake_api_keys(self, count: int, tracking_token: str) -> List[Dict]
    def generate_fake_database_dump(self, table: str, row_count: int, 
                                   tracking_token: str) -> List[Dict]
    def generate_fake_credentials(self, count: int, tracking_token: str) -> List[Dict]
```

#### fake_data_factory.py
```python
class FakeDataFactory:
    def generate_users(self, count: int, tracking_token: str) -> List[Dict]
    def generate_products(self, count: int, tracking_token: str) -> List[Dict]
    def generate_api_responses(self, endpoint: str, tracking_token: str) -> Dict
    def generate_adversarial_examples(self, count: int, intensity: float) -> List[Dict]
```

#### tracking_tokens.py
```python
class TrackingTokenManager:
    def generate_token(self, context: Dict[str, Any]) -> str
    def verify_token(self, token: str) -> bool
    def check_exfiltration(self, data: str) -> bool
    def get_token_info(self, token: str) -> Dict[str, Any]
    def is_tracked(self, suspicious_data: str) -> bool
```

---

## 6. MONITORING SYSTEM (monitoring/)

### 6.1 Data Structures

#### Metrics Record
```python
metrics_record = {
    "timestamp": 1701700000,
    "request_type": "api_call",
    "threat_detected": True,
    "risk_score": 85,
    "threat_category": "sql_injection",
    "response_time_ms": 125,
    "action_taken": "countermeasures"
}

# Time-series storage:
metrics_data = {
    "timestamps": [1701700000, 1701700100, ...],
    "threat_counts": [1, 2, 1, 0, ...],
    "avg_risk_scores": [45, 72, 38, 0, ...],
    "countermeasures_deployed": [0, 1, 0, 0, ...]
}
```

#### Alert Record
```python
alert = {
    "timestamp": 1701700000,
    "alert_type": "high_risk_threat",
    "severity": "critical",
    "message": "SQL injection detected from 203.0.113.42",
    "context": {
        "risk_score": 90,
        "threat_category": "sql_injection",
        "ip": "203.0.113.42",
        "endpoint": "/api/users"
    },
    "status": "active"
}
```

#### Dashboard Export Format
```python
dashboard_export = {
    "format": "prometheus",  # or "grafana", "datadog", "json"
    "timestamp": 1701700000,
    "metrics": {
        "ztai_total_requests": 10000,
        "ztai_threats_detected": 45,
        "ztai_avg_risk_score": 35.2,
        "ztai_countermeasures_deployed": 12,
        "ztai_false_positives": 2
    }
}
```

### 6.2 Modules

#### metrics.py
```python
class MetricsCollector:
    def __init__(self, retention_hours: int = 24):
        self.metrics_history = deque()
        self.retention_hours = retention_hours
    
    def record_request(self, request_data: Dict, response: Dict) -> None
    def get_summary(self) -> Dict[str, Any]
    def get_threat_trends(self) -> Dict[str, Any]
    def export_json(self, filepath: str) -> None
    def export_prometheus(self) -> str
```

#### alerts.py
```python
class AlertManager:
    def trigger_alert(self, alert_type: str, severity: str, 
                     message: str, context: Dict) -> None
    def check_threat_alert(self, risk_score: float, threat_category: str, ip: str) -> None
    def add_handler(self, handler_func: Callable) -> None
    def get_active_alerts(self) -> List[Dict]
```

#### dashboard.py
```python
class DashboardExporter:
    def export_prometheus(self, metrics: Dict) -> str
    def export_grafana_json(self, metrics: Dict) -> Dict
    def export_datadog(self, metrics: Dict) -> Dict
    def export_json(self, metrics: Dict) -> str
```

---

## 7. AGENTS MODULE (agents/)

### 7.1 Data Structures

#### Agent Tool Result
```python
tool_result = {
    "success": True,
    "tool_name": "aish",
    "output": "suggested_command_or_output",
    "execution_time_ms": 250,
    "metadata": {
        "system_aish_available": True,
        "fallback_used": False
    }
}
```

#### Defense Status Response
```python
defense_status = {
    "system_active": True,
    "active_environments": 3,
    "total_executions": 42,
    "recent_threats": [
        {
            "timestamp": 1701700000,
            "threat_type": "sql_injection",
            "risk_score": 90,
            "ip": "203.0.113.42"
        }
    ]
}
```

#### TODO List Structure
```python
todo_list = [
    {
        "id": 1,
        "title": "Analyze SQL injection attack",
        "status": "in_progress",  # or "not_started", "completed"
        "priority": "high"
    },
    {
        "id": 2,
        "title": "Deploy countermeasures",
        "status": "not_started",
        "priority": "high"
    }
]
```

### 7.2 Modules

#### defense_agent.py
```python
class DefenseAgent:
    def __init__(self, defense_orchestrator: DefenseOrchestrator = None):
        self.orchestrator = defense_orchestrator
        self.tools = Dict[str, Callable]
        self.conversation_history = List[Dict]
    
    def run(self, user_input: str) -> str
    def get_defense_status(self) -> Dict
    def analyze_threat(self, request_data: Dict) -> Dict
```

#### agent_tools.py
```python
# Available tools:
tool_aish(query: str, use_system_aish: bool) -> str
tool_read_file(filepath: str, start_line: int, end_line: int) -> str
tool_create_file(filepath: str, content: str) -> bool
tool_run_command(command: str) -> Dict[str, Any]
tool_defense_status() -> Dict[str, Any]
tool_analyze_threat(request_data: Dict) -> Dict[str, Any]
tool_list_scenarios() -> List[Dict]
```

#### agent_cli.py
```python
# Rich terminal UI with:
# - Interactive prompt
# - Markdown rendering
# - Tool result formatting
# - Special commands: /status, /help, /reset, /quit
```

---

## 8. SERVER MODULE (server/)

### 8.1 Data Structures

#### Virtual Filesystem Node
```python
vfs_node = {
    "path": "/home/data.csv",
    "type": "file",  # or "directory"
    "content": "fake file content",
    "size": 1024,
    "created_at": 1701700000,
    "accessed_at": 1701700100,
    "permissions": "644"
}

vfs_directory = {
    "path": "/home",
    "type": "directory",
    "children": ["data.csv"],
    "created_at": 1701700000
}
```

#### Virtual Database Record
```python
db_record = {
    "table": "users",
    "id": 1,
    "data": {
        "name": "Fake User",
        "email": "user@fake.local",
        "password_hash": "bcrypt_hash",
        "api_key": "key_with_tracking_token",
        "created_at": 1701700000
    }
}

# Sample tables:
# - users (25 records)
# - products (50 records)
# - orders (100 records)
```

#### API Response Structure
```python
# Protected endpoint (requires auth)
protected_response = {
    "status": "success",
    "data": [...],
    "timestamp": 1701700000,
    "tracking_metadata": {
        "request_id": "uuid",
        "processing_time_ms": 45
    }
}

# Honeypot response (with tracking)
honeypot_response = {
    "status": "success",
    "data": "fake_data_with_embedded_tracking_token",
    "timestamp": 1701700000,
    "__honeypot_flag": True,
    "__tracking_token": "unique_token"
}
```

### 8.2 Modules

#### protected_server.py
```python
class ProtectedServer(FastAPI):
    def __init__(self, defense_orchestrator: DefenseOrchestrator):
        self.orchestrator = defense_orchestrator
        self.vfs = VirtualFilesystem()
        self.vdb = VirtualDatabase()
        self.user_mgr = UserManager()
        
        # Honeypot endpoints
        @app.get("/.env")
        @app.get("/admin/backup")
        @app.get("/admin/config")
        @app.get("/api/internal/secrets")
        
        # Protected endpoints
        @app.get("/api/files/list")
        @app.get("/api/database/query")
        @app.get("/api/users/{id}")
```

#### virtual_resources.py
```python
class VirtualFilesystem:
    def __init__(self):
        self.files = Dict[str, vfs_node]
        self.honeypot_access_log = List[Dict]
    
    def read_file(self, path: str) -> str
    def list_directory(self, path: str) -> List[str]
    def create_file(self, path: str, content: str) -> None

class VirtualDatabase:
    def __init__(self):
        self.tables = Dict[str, List[Dict]]
        self.query_log = List[Dict]
    
    def query(self, sql: str) -> List[Dict]
    def insert(self, table: str, data: Dict) -> None
    def select(self, table: str, filters: Dict) -> List[Dict]

class UserManager:
    def __init__(self):
        self.users = Dict[str, User]
        self.sessions = Dict[str, Session]
    
    def authenticate(self, username: str, password: str) -> Session
    def create_user(self, username: str, password: str) -> User
```

---

## 9. DEFENSE LAYER (defense/)

### 9.1 Modules

#### flood_protection.py
```python
class FloodProtection:
    def __init__(self, config: Dict):
        self.rate_limits = Dict[str, int]
        self.request_tracking = defaultdict(deque)
    
    def check_rate_limit(self, ip: str, endpoint: str) -> bool
    def apply_flood_response(self, ip: str) -> Dict
```

#### impacket_protection.py
```python
class ImpacketProtection:
    def detect_impacket_patterns(self, request: Dict) -> bool
    def apply_defense_measures(self, request: Dict) -> Dict
    def track_impacket_attempt(self, request: Dict) -> None
```

---

## 10. CAKE BUILD SYSTEM (cake/)

### 10.1 Script Generation Data

#### Rendered Cake Script Template
```csharp
// Generated from sql_honeypot.cake template
var intensity = Argument("intensity", 50);  // High intensity = 200 records
var trackingToken = "abc123def456ghi789jkl";
var scenarioName = "sql_injection";

Task("Generate-Fake-Database")
    .Does(() => {
        // Generate fake records with Faker
        for(int i = 0; i < intensity; i++) {
            var fakeUser = new {
                id = i,
                username = Faker.Internet.UserName(),
                email = Faker.Internet.Email(),
                api_key = "sk_" + trackingToken + "_" + i,
                created_at = DateTime.Now
            };
            InsertIntoDatabase(fakeUser);
        }
    });

Task("Deploy-Honeypot")
    .IsDependentOn("Generate-Fake-Database")
    .Does(() => {
        // Deploy tracking and logging
    });

RunTarget("Deploy-Honeypot");
```

### 10.2 Modules

#### generator.py
```python
class CakeScriptGenerator:
    def __init__(self, templates_dir: str, policies_config: Dict):
        self.templates = Dict[str, Template]
        self.policies = policies_config
    
    def generate_script(self, scenario: str, intensity: str,
                       tracking_token: str) -> str
    def render_template(self, template_name: str, context: Dict) -> str
```

#### executor.py
```python
class CakeExecutor:
    def __init__(self, poetry_manager: PoetryEnvironmentManager, 
                 policies_config: Dict):
        self.poetry_mgr = poetry_manager
        self.execution_log = List[Dict]
    
    def execute_script(self, script_path: str, intensity: str) -> Dict[str, Any]
    def get_execution_log(self) -> List[Dict]
```

---

## 11. ENVIRONMENT MANAGEMENT (environments/)

### 11.1 Data Structures

#### Poetry Environment Configuration
```yaml
# Generated pyproject.toml for isolated environment
[tool.poetry]
name = "defense-env-sql_injection-20231204"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.10"
sqlalchemy = "^2.0"
psycopg2-binary = "^2.9"
faker = "^19.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

#### Environment Metadata
```python
env_metadata = {
    "env_id": "env-sql_injection-12345",
    "scenario": "sql_injection",
    "created_at": 1701700000,
    "isolation_level": "high",
    "resource_limits": {
        "cpu": "10%",
        "memory": "128MB",
        "timeout": 10
    },
    "dependencies": ["sqlalchemy", "psycopg2-binary", "faker"],
    "status": "active"  # or "completed", "terminated"
}
```

### 11.2 Modules

#### poetry_manager.py
```python
class PoetryEnvironmentManager:
    def __init__(self, policies_config: Dict, base_dir: str):
        self.policies = policies_config
        self.environments = Dict[str, Environment]
    
    def create_environment(self, scenario: str, isolation_level: str) -> str
    def install_dependencies(self, env_id: str, dependencies: List[str]) -> bool
    def activate_environment(self, env_id: str) -> str
    def cleanup_environment(self, env_id: str) -> None
```

---

## 12. EXPECTED FILE FLOW

### Complete Request Processing Pipeline

```
1. HTTP Request arrives
   ↓
2. RequestMiddleware intercepts
   ↓
3. Convert to request_data Dict
   ↓
4. DefenseOrchestrator.process_request(request_data)
   ↓
5. Create RequestMetadata
   ↓
6. QueryAnalyzer.analyze_query()
   ├─ Multi-stage safety check
   ├─ Check whitelist patterns
   └─ Check user reputation
   ↓
7. If SAFE → Return {"action": "allow", ...}
   ↓
8. If SUSPICIOUS:
   ├─ PatternDetector.analyze_request() → DetectionResult
   ├─ RiskScorer.assess_risk() → RiskAssessment
   ├─ Determine threat_category and risk_level
   ↓
9. If risk_score >= threshold:
   ├─ PoetryEnvironmentManager.create_environment()
   ├─ CakeScriptGenerator.generate_script()
   ├─ CakeExecutor.execute_script()
   ├─ Deploy countermeasures
   ↓
10. FakeDataFactory generates poisoned data
    ↓
11. TrackingTokenManager embeds tracking tokens
    ↓
12. Return fake data: {"action": "countermeasures", ...}
    ↓
13. MetricsCollector.record_request()
    ↓
14. AlertManager.trigger_alert() if needed
    ↓
15. Client receives fake data with tracking tokens
```

---

## 13. DEPLOYMENT CONFIGURATIONS

### Docker Deployment Data

#### docker-compose.yml Structure
```yaml
services:
  defense-system:
    build: .
    environment:
      - CONFIG_DIR=/app/config
      - BASE_DIR=/app
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    ports:
      - "8000:8000"

  protected-server:
    build: .
    depends_on:
      - defense-system
    environment:
      - DEFENSE_ENABLED=true
    ports:
      - "8001:8001"

  honeypot:
    build:
      dockerfile: Dockerfile.honeypot
    ports:
      - "8002:8002"
```

---

## 14. LOGGING STRUCTURE

### Log Files Generated at Runtime

#### environment_creation.log
```
[2024-12-04 10:00:00] Creating environment: env-sql_injection-12345
[2024-12-04 10:00:05] Installing dependencies: sqlalchemy, psycopg2-binary
[2024-12-04 10:00:15] Environment ready: /tmp/env-sql_injection-12345
[2024-12-04 10:00:16] Executing: sql_honeypot.cake
[2024-12-04 10:00:20] Execution completed: 50 fake records generated
```

#### counter_actions.log
```
[2024-12-04 10:00:20] Countermeasure deployed
  Scenario: sql_injection
  Intensity: high
  Risk Score: 90
  Tracking Token: abc123...
  Execution Time: 2.3ms
```

---

## 15. DEPENDENCY MAPPING

### pyproject.toml Dependencies

**Core Defense:**
- `pyyaml` - Configuration management
- `numpy` - Numerical pattern analysis
- `scikit-learn` - ML attack detection
- `pandas` - Data analysis

**Networking & Web:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `aiohttp` - Async HTTP
- `requests` - HTTP client

**Fake Data & Encoding:**
- `faker` - Generate fake data
- `cryptography` - Encryption/tokens
- `jinja2` - Template rendering

**Security & Monitoring:**
- `redis` - Session/cache management
- `python-dotenv` - Environment configuration
- `pydantic` - Data validation
- `stripe` - Payment processing (paywall)
- `pyotp` - Two-factor authentication

**AI & Agents:**
- `anthropic` - Claude API for defense agent
- `rich` - Terminal UI

**DevOps:**
- `docker` - Container management

---

## Summary Table

| Component | Module | Function | Input | Output |
|-----------|--------|----------|-------|--------|
| Orchestrator | core/orchestrator.py | Coordinates defense | request_data (Dict) | response (Dict with action) |
| Detector | core/detector.py | Pattern detection | RequestMetadata | DetectionResult |
| Risk Scorer | core/risk_scorer.py | Risk assessment | risk_score, patterns | RiskAssessment |
| Query Analyzer | core/query_analyzer.py | Safety filtering | query, metadata | (is_safe, analysis) |
| Poetry Manager | environments/poetry_manager.py | Env creation | scenario, isolation_level | env_id (str) |
| Cake Generator | cake/generator.py | Script generation | scenario, intensity | cake_script (str) |
| Cake Executor | cake/executor.py | Script execution | script_path, intensity | execution_result (Dict) |
| Honeypot Gen | deception/honeypot_generator.py | Fake data | tracking_token, count | fake_data (List/Dict) |
| Metrics | monitoring/metrics.py | Metrics collection | request, response | metrics_record |
| Alerts | monitoring/alerts.py | Alert management | alert_type, severity | alert_sent (bool) |
| Defense Agent | agents/defense_agent.py | Autonomous execution | user_input | agent_response (str) |
| Protected Server | server/protected_server.py | HTTP serving | http_request | http_response |

---

## Last Update

- **Date:** December 4, 2025
- **Version:** 1.0
- **Status:** Fully Working

All data structures and file directories are verified against actual markdown documentation and existing code implementations.
