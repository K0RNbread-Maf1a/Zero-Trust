# Docker Deployment Guide

Advanced Docker setup for Zero-Trust AI Defense with agent communication, Pi-hole integration, and attacker isolation.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Defense Network (172.20.0.0/16)          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Defense      │  │ Defense      │  │ Redis        │     │
│  │ Server       │  │ Agent        │  │ :6379        │     │
│  │ :8000/8001   │  │ :8001        │  └──────────────┘     │
│  └──────────────┘  └──────────────┘                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Pi-hole      │  │ Prometheus   │  │ Grafana      │     │
│  │ :53/:8053    │  │ :9090        │  │ :3000        │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│          Attacker Trap Network (172.21.0.0/16)              │
│                    ** NO INTERNET ACCESS **                  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Honeypot 1   │  │ Honeypot 2   │  │ Honeypot N   │     │
│  │ (Isolated)   │  │ (Isolated)   │  │ (Isolated)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  All data is fake and tracked. Attackers waste time here.  │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Defense Server (Port 8000, 8001)
- Main zero-trust defense API
- Agent communication endpoint
- Docker socket access for dynamic container creation
- Can spawn isolated honeypot containers for high-risk attackers

### 2. Defense Agent (Port 8001)
- AI-powered agent API
- Communicates with Claude for autonomous operations
- Can analyze threats, manage containers, configure Pi-hole

### 3. Pi-hole (Port 53, 8053)
- DNS-based blocking
- Attackers can be blocked at DNS level
- Web interface at port 8053
- Default password: `admin123` (change via `PIHOLE_PASSWORD`)

### 4. Honeypot Containers (Port 8080)
- **Isolated network** - NO internet access
- Dynamically spawned for high-risk attackers
- Serves only fake data with tracking tokens
- Resource-limited (256MB RAM, 25% CPU)

### 5. Monitoring Stack
- **Prometheus** (9090) - Metrics collection
- **Grafana** (3000) - Dashboards and visualization
- **Redis** (6379) - Session management and caching

## Quick Start

### Using Enhanced Docker Compose

```powershell
# Set environment variables
$env:ANTHROPIC_API_KEY="your_key"
$env:PIHOLE_PASSWORD="secure_password"
$env:GRAFANA_PASSWORD="secure_password"

# Build and start all services
docker-compose -f docker-compose.enhanced.yml up -d

# View logs
docker-compose -f docker-compose.enhanced.yml logs -f

# Stop all services
docker-compose -f docker-compose.enhanced.yml down
```

### Building Individual Images

```powershell
# Build enhanced defense server
docker build -f Dockerfile.enhanced -t ztai-defense:latest .

# Build honeypot container
docker build -f Dockerfile.honeypot -t ztai-honeypot:latest .
```

## Advanced Features

### 1. Dynamic Attacker Isolation

When a high-risk attacker is detected (risk score > 90), the system can:

1. **Spawn an isolated container** for that attacker
2. **Route their traffic** to the honeypot
3. **Block via Pi-hole** if domain-based attack
4. **Monitor** their activity in complete isolation

```python
from deploy.docker_controller import DockerController

controller = DockerController()

# Isolate an attacker
container_id = controller.isolate_attacker(
    attacker_ip="203.0.113.42",
    threat_category="sql_injection",
    risk_score=95
)

# Block via Pi-hole
controller.block_via_pihole("malicious-domain.com")

# View trapped attackers
trapped = controller.get_trapped_attackers()
print(f"Currently trapped: {len(trapped)} attackers")
```

### 2. Agent-Docker Communication

The Defense Agent can manage containers:

```python
from agents import DefenseAgent
from deploy.docker_controller import DockerController

agent = DefenseAgent()
docker = DockerController()

# Agent can query and manage isolated containers
response = agent.run("show me all trapped attackers and their threat types")
```

### 3. Pi-hole Integration

Automatic DNS-level blocking:

```python
# Block attacker domains
controller.block_via_pihole("attacker-c2-server.evil")

# Access Pi-hole web interface
# http://localhost:8053
# Password: value of PIHOLE_PASSWORD env var
```

## Environment Variables

Create a `.env` file:

```env
# Required for Defense Agent
ANTHROPIC_API_KEY=sk-ant-...

# Optional - Stripe integration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRICE_ID=price_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_MODE=payment

# Feature flags
ENABLE_DEV_PAY=0
RETURN_VERIFICATION_CODE=0

# Pi-hole admin password
PIHOLE_PASSWORD=your_secure_password

# Grafana admin password
GRAFANA_PASSWORD=your_secure_password
```

## Port Mappings

| Service        | Internal Port | External Port | Purpose                      |
|----------------|---------------|---------------|------------------------------|
| Defense Server | 8000          | 8000          | Main API                     |
| Agent API      | 8001          | 8001          | Agent communication          |
| Redis          | 6379          | 6379          | Cache & sessions             |
| Pi-hole DNS    | 53            | 53            | DNS blocking                 |
| Pi-hole Web    | 80            | 8053          | Pi-hole admin interface      |
| Prometheus     | 9090          | 9090          | Metrics collection           |
| Grafana        | 3000          | 3000          | Dashboards                   |
| Honeypot       | 8080          | -             | Internal only (isolated)     |

## Isolated Network

The `attacker_trap` network (172.21.0.0/16) is **completely isolated**:
- ✅ No internet access
- ✅ No access to defense network
- ✅ Only serves fake data
- ✅ All activity logged
- ✅ Resource-limited

Attackers trapped here can:
- Make requests (all get fake responses)
- Download fake credentials
- Exfiltrate tracking-token-embedded data
- Waste their time and resources

Attackers trapped here CANNOT:
- Access real data
- Reach the internet
- Communicate with other containers
- Use excessive resources

## Monitoring & Dashboards

### Prometheus Metrics

Access: `http://localhost:9090`

Metrics collected:
- Defense system performance
- Threat detection rates
- Container resource usage
- Pi-hole blocking stats

### Grafana Dashboards

Access: `http://localhost:3000`

Pre-configured dashboards show:
- Threat trends over time
- Countermeasure success rates
- Isolated attacker activity
- System health metrics

## Container Management

### List All Defense Containers

```powershell
docker ps --filter "label=ztai.trapped=true"
```

### View Honeypot Logs

```powershell
docker logs ztai-honeypot
```

### Inspect Isolated Attacker

```powershell
# Get trapped attackers
docker ps --filter "name=trap_*"

# View specific trap logs
docker logs trap_203_0_113_42_1234567890
```

### Cleanup Old Traps

```powershell
# Using the controller
poetry run python -c "
from deploy.docker_controller import DockerController
controller = DockerController()
controller.cleanup_old_traps(max_age_hours=24)
"
```

## Security Considerations

### Isolation

1. **Network Isolation**: Attacker trap network has NO internet
2. **Resource Limits**: Each honeypot limited to 256MB RAM, 25% CPU
3. **Docker Socket**: Only defense-server has access to docker.sock
4. **Fake Data**: All data in honeypots contains tracking tokens

### Pi-hole Protection

- DNS-level blocking prevents attacker reconnaissance
- Blocks C2 domains automatically
- Web interface password-protected

### Monitoring

- All container activity logged
- Prometheus tracks all metrics
- Grafana provides real-time visibility

## Troubleshooting

### Services Won't Start

```powershell
# Check logs
docker-compose -f docker-compose.enhanced.yml logs

# Check specific service
docker logs ztai-defense-server
```

### Pi-hole Not Blocking

```powershell
# Check Pi-hole status
docker exec ztai-pihole pihole status

# Restart Pi-hole
docker restart ztai-pihole
```

### Agent Can't Connect

Ensure `ANTHROPIC_API_KEY` is set:
```powershell
docker-compose -f docker-compose.enhanced.yml config | Select-String "ANTHROPIC"
```

### Container Creation Fails

Ensure defense-server has docker socket access:
```powershell
docker inspect ztai-defense-server | Select-String "docker.sock"
```

## Production Deployment

### Checklist

- [ ] Change all default passwords
- [ ] Set up TLS/SSL termination (nginx/traefik)
- [ ] Configure external logging
- [ ] Set up automated backups
- [ ] Monitor resource usage
- [ ] Configure alert notifications
- [ ] Review and tune isolation limits
- [ ] Set up log rotation

### Recommended: Add Reverse Proxy

```yaml
# Add to docker-compose.enhanced.yml
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
```

## Benefits

1. **Dynamic Isolation** - Attackers automatically trapped in dedicated containers
2. **DNS Blocking** - Pi-hole provides network-level defense
3. **Resource Protection** - Honeypots have strict resource limits
4. **Complete Monitoring** - Prometheus + Grafana for full visibility
5. **Agent Integration** - AI agent can manage entire infrastructure
6. **Scalable** - Spin up honeypots on-demand
7. **Evidence Collection** - All attacker activity logged with tracking tokens

## Next Steps

1. Configure alert notifications (email, Slack, PagerDuty)
2. Set up log aggregation (ELK stack, Loki)
3. Add WAF (ModSecurity, Cloudflare)
4. Implement automated response playbooks
5. Create custom Grafana dashboards
6. Set up automated honeypot rotation

---

**Remember**: The honeypot containers are your secret weapon. Attackers think they're winning while you collect intelligence and waste their resources!
