# Zero Trust AI Defense - Node.js Fallback Library

A comprehensive Node.js fallback implementation of the Zero Trust AI Defense system, providing threat detection, risk scoring, honeypot generation, and attacker isolation capabilities.

## Features

- **Pattern Detection**: Detects malicious patterns including SQL injection, XSS, path traversal, command injection
- **Risk Scoring**: Evaluates threat levels and recommends countermeasures
- **Honeypot Generation**: Creates fake credentials, API keys, database dumps, and environment files
- **Attacker Isolation**: Dynamically isolates high-risk attackers in Docker containers
- **Metrics Collection**: Tracks requests, threats, and countermeasures
- **Express Server**: Production-ready HTTP server with defense middleware

## Installation

```bash
cd nodejs-fallback
npm install
```

## Quick Start

### As a Library

```javascript
import { initializeFallbackDefense } from '@ztai/defense-fallback';

const defense = initializeFallbackDefense();

// Analyze a request
const requestData = {
  ip: '192.168.1.100',
  method: 'GET',
  endpoint: '/api/users',
  headers: { 'user-agent': 'curl/7.68.0' },
  body: {},
  timestamp: Date.now() / 1000
};

const patterns = defense.detector.detectPatterns(requestData);
const riskAssessment = defense.scorer.scoreRequest(patterns);

console.log('Risk Level:', riskAssessment.riskLevel);
console.log('Risk Score:', riskAssessment.riskScore);
console.log('Threat Category:', riskAssessment.threatCategory);
```

### As a Server

```bash
# Start defense server
npm run server

# Start honeypot server (for isolated containers)
npm run honeypot
```

### CLI Mode

```bash
# Interactive defense analysis
npm start
```

## API Reference

### PatternDetector

Detects malicious patterns in incoming requests.

```javascript
import { PatternDetector } from '@ztai/defense-fallback/lib/detector.js';

const detector = new PatternDetector();
const patterns = detector.detectPatterns(requestData);
```

**Methods:**
- `detectPatterns(requestData)` - Analyzes request and returns detected patterns
- `checkTimingPatterns(requestData)` - Detects timing-based attacks
- `checkContentPatterns(requestData)` - Detects content-based attacks (SQLi, XSS, etc.)
- `checkBehavioralPatterns(requestData)` - Detects behavioral anomalies

### RiskScorer

Evaluates risk levels and recommends countermeasures.

```javascript
import { RiskScorer } from '@ztai/defense-fallback/lib/risk-scorer.js';

const scorer = new RiskScorer();
const assessment = scorer.scoreRequest(patterns);
```

**Risk Levels:**
- `LOW`: Score < 30
- `MEDIUM`: Score 30-59
- `HIGH`: Score 60-79
- `CRITICAL`: Score ≥ 80

**Returns:**
```javascript
{
  riskScore: 85,
  riskLevel: 'CRITICAL',
  threatCategory: 'injection_attack',
  recommendedAction: 'isolate_attacker',
  patterns: [...]
}
```

### HoneypotGenerator

Generates fake data to deceive attackers.

```javascript
import { HoneypotGenerator } from '@ztai/defense-fallback/lib/honeypot-generator.js';

const honeypot = new HoneypotGenerator();
const fakeEnv = honeypot.generateFakeEnvFile();
const fakeKeys = honeypot.generateFakeAPIKeys(5);
```

**Methods:**
- `generateFakeEnvFile()` - Creates fake .env file content
- `generateFakeAPIKeys(count)` - Generates fake API keys
- `generateFakeCredentials(count)` - Creates fake user credentials
- `generateFakeDatabaseDump()` - Generates fake SQL dump
- `generateTrackingToken()` - Creates tracking token for exfiltration monitoring

### MetricsCollector

Tracks defense system metrics.

```javascript
import { MetricsCollector } from '@ztai/defense-fallback/lib/metrics.js';

const metrics = new MetricsCollector();
metrics.recordRequest(requestData, riskAssessment);
const summary = metrics.getSummary();
```

**Methods:**
- `recordRequest(requestData, riskAssessment)` - Records request metrics
- `getSummary()` - Returns metrics summary
- `getThreatBreakdown()` - Returns threat category breakdown

### DockerController

Manages attacker isolation containers.

```javascript
import { DockerController } from '@ztai/defense-fallback/lib/docker-controller.js';

const docker = new DockerController();
await docker.isolateAttacker('attacker-123', '192.168.1.100');
```

**Methods:**
- `isolateAttacker(attackerId, attackerIp)` - Creates isolated container
- `getTrappedAttackers()` - Lists all trapped attackers
- `releaseAttacker(attackerId)` - Releases attacker from isolation
- `cleanupOldTraps(maxAgeHours)` - Removes old isolation containers

### DefenseServer

Express server with integrated defense middleware.

```javascript
import { DefenseServer } from '@ztai/defense-fallback/lib/server.js';

const server = new DefenseServer({ port: 3000 });
server.start();
```

**Endpoints:**
- `GET /health` - Health check
- `GET /metrics` - Metrics summary
- `GET /defense/status` - Defense system status
- `GET /api/data` - Example protected endpoint
- `GET /.env` - Example honeypot endpoint

### HoneypotServer

Standalone server for isolated attacker containers.

```javascript
import { HoneypotServer } from '@ztai/defense-fallback/lib/honeypot-server.js';

const honeypot = new HoneypotServer({ port: 8080 });
honeypot.start();
```

**Endpoints:**
- `GET /.env` - Fake environment file
- `GET /api/keys` - Fake API keys
- `GET /admin/users` - Fake user credentials
- `GET /backup/database.sql` - Fake database dump
- `GET /admin` - Fake admin panel
- `POST /admin/login` - Fake login (always succeeds)
- `GET /honeypot/log` - Access log

## Usage Examples

### Basic Threat Detection

```javascript
import { PatternDetector, RiskScorer } from '@ztai/defense-fallback';

const detector = new PatternDetector();
const scorer = new RiskScorer();

const maliciousRequest = {
  ip: '10.0.0.1',
  endpoint: "/api/users?id=1' OR '1'='1",
  body: {},
  timestamp: Date.now() / 1000
};

const patterns = detector.detectPatterns(maliciousRequest);
const assessment = scorer.scoreRequest(patterns);

if (assessment.riskLevel === 'CRITICAL') {
  console.log('🚨 Critical threat detected!');
  console.log('Category:', assessment.threatCategory);
  console.log('Action:', assessment.recommendedAction);
}
```

### Defense Middleware Integration

```javascript
import express from 'express';
import { PatternDetector, RiskScorer, HoneypotGenerator } from '@ztai/defense-fallback';

const app = express();
const detector = new PatternDetector();
const scorer = new RiskScorer();
const honeypot = new HoneypotGenerator();

app.use(express.json());

app.use((req, res, next) => {
  const requestData = {
    ip: req.ip,
    method: req.method,
    endpoint: req.path,
    headers: req.headers,
    body: req.body,
    timestamp: Date.now() / 1000
  };

  const patterns = detector.detectPatterns(requestData);
  const assessment = scorer.scoreRequest(patterns);

  if (assessment.riskLevel === 'CRITICAL') {
    return res.status(403).json({ error: 'Access denied' });
  }

  if (assessment.riskLevel === 'HIGH') {
    // Serve honeypot data
    req.isHighRisk = true;
  }

  next();
});

app.get('/api/data', (req, res) => {
  if (req.isHighRisk) {
    return res.json({
      data: honeypot.generateFakeCredentials(10),
      _tracking: honeypot.generateTrackingToken()
    });
  }
  
  res.json({ data: 'Real protected data' });
});

app.listen(3000);
```

### Docker Isolation

```javascript
import { DockerController } from '@ztai/defense-fallback';

const docker = new DockerController();

// Isolate critical threat
async function handleCriticalThreat(attackerId, attackerIp) {
  const result = await docker.isolateAttacker(attackerId, attackerIp);
  
  if (result.success) {
    console.log(`✅ Attacker ${attackerId} isolated in container ${result.containerId}`);
  } else {
    console.error(`❌ Failed to isolate: ${result.error}`);
  }
}

// List trapped attackers
const trapped = await docker.getTrappedAttackers();
console.log(`Currently trapped: ${trapped.length} attackers`);

// Cleanup old traps (older than 24 hours)
await docker.cleanupOldTraps(24);
```

### Metrics Monitoring

```javascript
import { MetricsCollector } from '@ztai/defense-fallback';

const metrics = new MetricsCollector();

// Record requests continuously
setInterval(() => {
  const summary = metrics.getSummary();
  
  console.log('Total Requests:', summary.totalRequests);
  console.log('Total Threats:', summary.totalThreats);
  console.log('Recent Hour:', summary.recentHour);
  console.log('Threat Breakdown:', summary.threatBreakdown);
}, 60000); // Every minute
```

## Docker Integration

The library works with Docker to provide attacker isolation. Ensure Docker is running:

```bash
# Build honeypot image
docker build -f ../Dockerfile.honeypot -t ztai-honeypot .

# Create isolated network
docker network create --driver bridge --subnet 172.21.0.0/16 --internal attacker_trap
```

## Environment Variables

Create a `.env` file:

```env
PORT=3000
HONEYPOT_PORT=8080
DOCKER_HOST=unix:///var/run/docker.sock
ENABLE_CONTAINER_ISOLATION=true
```

## Scripts

```bash
npm start          # Run CLI mode
npm run server     # Start defense server
npm run detector   # Test pattern detector
npm run honeypot   # Start honeypot server
```

## Integration with Python System

This Node.js fallback library mirrors the Python implementation architecture:

```
Python System          →    Node.js Fallback
─────────────────────────────────────────────
PatternDetector       →    PatternDetector
RiskScorer            →    RiskScorer
HoneypotGenerator     →    HoneypotGenerator
MetricsCollector      →    MetricsCollector
DockerController      →    DockerController
FastAPI Server        →    Express/DefenseServer
```

Use the Node.js version when:
- Python is unavailable or restricted
- You need a lightweight deployment
- Integration with Node.js infrastructure is required
- You want faster cold-start times

## Threat Categories Detected

- `injection_attack` - SQL injection, command injection
- `xss_attack` - Cross-site scripting
- `path_traversal` - Directory traversal attempts
- `token_abuse` - API token misuse
- `reconnaissance` - Scanning and enumeration
- `credential_stuffing` - Brute force attacks
- `data_exfiltration` - Suspicious data access patterns

## Recommended Actions

Based on risk level, the system recommends:

- **LOW**: `monitor` - Log and continue
- **MEDIUM**: `rate_limit` - Apply rate limiting
- **HIGH**: `serve_honeypot` - Serve fake data
- **CRITICAL**: `isolate_attacker` - Isolate in container

## License

Part of the Zero Trust AI Defense system.

## Contributing

See main repository README for contribution guidelines.
