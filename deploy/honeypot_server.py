"""
Honeypot Server - Runs in isolated container for trapped attackers.
NO internet access. All data is fake and tracked.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import sys
from pathlib import Path
import time
import json

sys.path.insert(0, str(Path(__file__).parent))

from deception.honeypot_generator import HoneypotGenerator
from deception.tracking_tokens import TrackingTokenManager

app = FastAPI(title="Honeypot Trap", docs_url=None, redoc_url=None)

token_mgr = TrackingTokenManager()
honeypot = HoneypotGenerator(token_mgr)

# Log all access attempts
access_log = []

@app.middleware("http")
async def log_access(request: Request, call_next):
    """Log all access attempts to this honeypot."""
    access_log.append({
        "timestamp": time.time(),
        "method": request.method,
        "path": request.url.path,
        "ip": request.client.host,
        "headers": dict(request.headers)
    })
    
    # Save to file
    with open("/honeypot/data/tracking/access.log", "a") as f:
        f.write(json.dumps(access_log[-1]) + "\n")
    
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    """Fake root endpoint."""
    return {"message": "Production API Server", "version": "2.1.0"}

@app.get("/.env")
async def fake_env():
    """Serve fake environment file."""
    tracking_token = token_mgr.generate_token(context={"endpoint": "/.env"})
    return PlainTextResponse(honeypot.generate_fake_env_file(tracking_token))

@app.get("/admin/config")
async def fake_config():
    """Serve fake config."""
    tracking_token = token_mgr.generate_token(context={"endpoint": "/admin/config"})
    return JSONResponse(json.loads(honeypot.generate_fake_config_file("json", tracking_token)))

@app.get("/admin/backup")
async def fake_backup():
    """Serve fake database dump."""
    tracking_token = token_mgr.generate_token(context={"endpoint": "/admin/backup"})
    return PlainTextResponse(honeypot.generate_fake_database_dump("users", 1000, tracking_token))

@app.get("/api/keys")
async def fake_api_keys():
    """Serve fake API keys."""
    tracking_token = token_mgr.generate_token(context={"endpoint": "/api/keys"})
    return JSONResponse(honeypot.generate_fake_api_keys(20, tracking_token))

@app.get("/api/users")
async def fake_users():
    """Serve fake user credentials."""
    tracking_token = token_mgr.generate_token(context={"endpoint": "/api/users"})
    return JSONResponse(honeypot.generate_honeypot_credentials(50, tracking_token))

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "trapped", "access_count": len(access_log)}

if __name__ == "__main__":
    import uvicorn
    print("[HONEYPOT] Starting isolated honeypot server...")
    print("[HONEYPOT] NO internet access - all data is fake and tracked")
    uvicorn.run(app, host="0.0.0.0", port=8080)
