"""
Virtual Protected Server - Production-ready server with integrated zero-trust defense

This server includes:
- Full REST API with virtual resources
- Honeypot endpoints and fake data
- Integrated defense middleware
- Virtual filesystem and database
- Real-time threat monitoring
- Admin dashboard
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import secrets
import time
from datetime import datetime
from starlette.staticfiles import StaticFiles
import os
import stripe
import base64
from io import BytesIO

try:
    import qrcode  # optional for QR images
except Exception:
    qrcode = None

from integrations.qsharp_middleware import create_qsharp_defense_middleware
from server.virtual_resources import VirtualFileSystem, VirtualDatabase, VirtualUserManager
from server.paywall import paywall_manager, ensure_session_cookie, require_paid_session, require_portal_access, FORCE_2FA
from server.registration import registration_manager


# Initialize FastAPI with metadata
app = FastAPI(
    title="Virtual Protected Server",
    description="Production server with zero-trust AI defense and virtual honeypot resources",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)
# Serve static web assets for the paywalled portal
app.mount("/web", StaticFiles(directory=str(Path(__file__).parent.parent / "web")), name="web")

# Configure Stripe (if keys are provided)
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
STRIPE_MODE = os.environ.get("STRIPE_MODE", "payment")  # "payment" or "subscription"
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

ENABLE_DEV_PAY = os.environ.get("ENABLE_DEV_PAY", "1") == "1"
RETURN_VERIFICATION_CODE = os.environ.get("RETURN_VERIFICATION_CODE", "1") == "1"

# Initialize virtual resources
vfs = VirtualFileSystem()
vdb = VirtualDatabase()
user_manager = VirtualUserManager()

# HTTP Basic Auth
security = HTTPBasic()

# Add defense middleware
defense = create_qsharp_defense_middleware(
    app,
    config_dir="../config",
    base_dir="..",
    enable_quantum=True
)


# ==================== Request/Response Models ====================

class LoginRequest(BaseModel):
    username: str
    password: str


class UserData(BaseModel):
    user_id: int
    username: str
    email: str
    role: str
    created_at: str


class FileUpload(BaseModel):
    filename: str
    content: str
    path: str = "/"


class DatabaseQuery(BaseModel):
    query: str
    database: str = "main"


class APIKeyRequest(BaseModel):
    name: str
    permissions: List[str]


# ==================== Authentication ====================

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials"""
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "admin123")
    
    if not (correct_username and correct_password):
        # Log failed authentication attempt
        print(f"[AUTH FAILED] {credentials.username} from {time.time()}")
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# ==================== Public Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "server": "Virtual Protected Server",
        "version": "1.0.0",
        "status": "operational",
        "defense": "active",
        "features": [
            "Virtual Filesystem",
            "Virtual Database",
            "User Management",
            "API Key Generation",
            "Zero-Trust Defense"
        ],
        "documentation": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time(),
        "defense_active": True
    }


@app.post("/api/auth/login")
async def login(login_req: LoginRequest):
    """
    User login endpoint
    Protected by defense - SQL injection attempts will be caught
    """
    user = user_manager.authenticate(login_req.username, login_req.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = user_manager.generate_token(user["user_id"])
    
    return {
        "success": True,
        "token": token,
        "user": user
    }


# ==================== Paywalled Web Portal ====================

@app.get("/app", response_class=HTMLResponse)
async def portal(request: Request):
    """Web-only portal. Ensures a session cookie exists and serves the UI shell."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset=\"utf-8\" />
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
      <title>Zero-Trust AI Defense — Portal</title>
      <link rel=\"stylesheet\" href=\"/web/styles.css\" />
    </head>
    <body>
      <script>
        // Redirect to static index after cookie is set on this response
        window.location.replace('/web/index.html');
      </script>
    </body>
    </html>
    """
    response = HTMLResponse(content=html)
    ensure_session_cookie(request, response)
    return response

@app.get("/pay/config")
async def pay_config():
    return {
        "stripe_enabled": bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID),
        "mode": STRIPE_MODE,
        "price_id": STRIPE_PRICE_ID,
        "dev_enabled": ENABLE_DEV_PAY,
        "force_2fa": bool(FORCE_2FA),
    }

@app.get("/pay/status")
async def pay_status(request: Request, response: Response):
    sid = ensure_session_cookie(request, response)
    sess = paywall_manager.get_session(sid) or {}
    return {
        "paid": bool(sess.get("paid")),
        "verified": bool(sess.get("verified")),
        "customer_id": sess.get("customer_id"),
        "logged_in": bool(sess.get("logged_in")),
    }

@app.post("/pay/dev/complete")
async def pay_complete_dev(request: Request, response: Response):
    """Development-only: mark current session as paid."""
    if not ENABLE_DEV_PAY:
        raise HTTPException(status_code=403, detail="Dev payment disabled")
    sid = ensure_session_cookie(request, response)
    paywall_manager.mark_paid(sid)
    return {"success": True, "paid": True}

@app.post("/pay/create-checkout-session")
async def create_checkout_session(request: Request, response: Response):
    """Create a Stripe Checkout Session and return the redirect URL."""
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        raise HTTPException(status_code=500, detail="Stripe not configured. Set STRIPE_SECRET_KEY and STRIPE_PRICE_ID.")
    sid = ensure_session_cookie(request, response)
    # Build base URL from request
    host = request.headers.get("host", "localhost:8000")
    scheme = "https" if request.headers.get("x-forwarded-proto", "http") == "https" else "http"
    base_url = f"{scheme}://{host}"
    success_url = f"{base_url}/pay/stripe/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base_url}/pay/stripe/cancel"
    try:
        session = stripe.checkout.Session.create(
            mode="subscription" if STRIPE_MODE == "subscription" else "payment",
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"session_id": sid},
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

@app.post("/pay/webhook")
async def stripe_webhook(request: Request):
    """Stripe webhook to mark sessions paid after checkout completion."""
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Webhook not configured")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {str(e)}")

    if event.get("type") == "checkout.session.completed":
        data = event["data"]["object"]
        sid = (data.get("metadata") or {}).get("session_id")
        if sid:
            paywall_manager.mark_paid(sid)
    return {"received": True}

@app.get("/pay/stripe/success", response_class=HTMLResponse)
async def stripe_success():
    html = (Path(__file__).parent.parent / "web" / "checkout_success.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)

@app.get("/pay/stripe/cancel", response_class=HTMLResponse)
async def stripe_cancel():
        html = (Path(__file__).parent.parent / "web" / "checkout_cancel.html").read_text(encoding="utf-8")
        return HTMLResponse(content=html)


# ==================== Authentication (2FA) & Registration ====================

class LoginPassword(BaseModel):
    email: str
    password: str

class TwoFAVerify(BaseModel):
    login_token: str
    code: str

class TwoFAEnrollStart(BaseModel):
    email: str

class TwoFAEnrollVerify(BaseModel):
    email: str
    code: str

@app.post("/auth/login_password")
async def auth_login_password(payload: LoginPassword, request: Request, response: Response):
    sid = ensure_session_cookie(request, response)
    customer_id = registration_manager.login(payload.email, payload.password)
    if not customer_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # If 2FA not enabled, prompt enrollment flow
    if not registration_manager.is_otp_enabled(payload.email):
        secret = registration_manager.get_or_create_otp_secret(payload.email)
        issuer = "Zero-Trust-AI-Defense"
        label = payload.email
        otpauth_uri = f"otpauth://totp/{issuer}:{label}?secret={secret}&issuer={issuer}&digits=6"
        qr_data_url = None
        if qrcode is not None:
            img = qrcode.make(otpauth_uri)
            buf = BytesIO()
            img.save(buf, format="PNG")
            qr_data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
        return {
            "requires_2fa_enrollment": True,
            "secret": secret,
            "otpauth_uri": otpauth_uri,
            "qr_data_url": qr_data_url,
        }
    # 2FA required step
    login_token = paywall_manager.create_login_token(payload.email)
    return {"two_factor_required": True, "login_token": login_token}

@app.post("/auth/2fa_verify")
async def auth_2fa_verify(payload: TwoFAVerify, request: Request, response: Response):
    sid = ensure_session_cookie(request, response)
    email = paywall_manager.consume_login_token(payload.login_token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired login token")
    secret = registration_manager.get_otp_secret(email)
    if not secret:
        raise HTTPException(status_code=400, detail="2FA not enrolled")
    import pyotp
    totp = pyotp.TOTP(secret)
    if not totp.verify(payload.code, valid_window=1):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    # Mark logged in and attach customer
    customer_id = registration_manager.login(email, "") or registration_manager.backend.customers.get(email, {}).get("customer_id")  # type: ignore[attr-defined]
    if customer_id:
        paywall_manager.attach_customer(sid, customer_id, verified=registration_manager.is_verified(email))
    paywall_manager.mark_logged_in(sid, True)
    return {"success": True}

@app.post("/2fa/enroll_start")
async def twofa_enroll_start(payload: TwoFAEnrollStart):
    secret = registration_manager.get_or_create_otp_secret(payload.email)
    issuer = "Zero-Trust-AI-Defense"
    label = payload.email
    otpauth_uri = f"otpauth://totp/{issuer}:{label}?secret={secret}&issuer={issuer}&digits=6"
    qr_data_url = None
    if qrcode is not None:
        img = qrcode.make(otpauth_uri)
        buf = BytesIO()
        img.save(buf, format="PNG")
        qr_data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    return {"secret": secret, "otpauth_uri": otpauth_uri, "qr_data_url": qr_data_url}

@app.post("/2fa/enroll_verify")
async def twofa_enroll_verify(payload: TwoFAEnrollVerify):
    ok = registration_manager.enable_otp_if_valid(payload.email, payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid code")
    return {"success": True}

# ==================== Registration (Customer) ====================

class RegistrationStart(BaseModel):
    email: str
    password: str

class RegistrationVerify(BaseModel):
    email: str
    code: str

class RegistrationLogin(BaseModel):
    email: str
    password: str

@app.post("/register/start")
async def register_start(payload: RegistrationStart, request: Request, response: Response):
    sid = ensure_session_cookie(request, response)
    code = registration_manager.start(payload.email, payload.password)
    result = {"success": True, "message": "Verification sent"}
    if RETURN_VERIFICATION_CODE:
        result["code"] = code
    return result

@app.post("/register/verify")
async def register_verify(payload: RegistrationVerify, request: Request, response: Response):
    sid = ensure_session_cookie(request, response)
    customer_id = registration_manager.verify(payload.email, payload.code)
    if not customer_id:
        raise HTTPException(status_code=400, detail="Invalid code")
    paywall_manager.attach_customer(sid, customer_id, verified=True)
    return {"success": True, "customer_id": customer_id}

@app.post("/register/login")
async def register_login(payload: RegistrationLogin, request: Request, response: Response):
    sid = ensure_session_cookie(request, response)
    customer_id = registration_manager.login(payload.email, payload.password)
    if not customer_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # mark verified if registration backend says so
    verified = registration_manager.is_verified(payload.email)
    paywall_manager.attach_customer(sid, customer_id, verified=verified)
    return {"success": True, "customer_id": customer_id, "verified": verified}

# ==================== Virtual Filesystem ====================

@app.get("/api/files/list")
async def list_files(path: str = "/", sid: str = Depends(require_portal_access)):
    """
    List files in virtual filesystem
    Defense monitors for directory traversal attempts
    """
    try:
        files = vfs.list_directory(path)
        return {
            "path": path,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/files/read")
async def read_file(path: str, sid: str = Depends(require_portal_access)):
    """
    Read file from virtual filesystem
    Defense detects path traversal patterns
    """
    try:
        content = vfs.read_file(path)
        return {
            "path": path,
            "content": content,
            "size": len(content)
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/files/upload")
async def upload_file(file: FileUpload, sid: str = Depends(require_portal_access)):
    """Upload file to virtual filesystem"""
    try:
        vfs.write_file(file.path + "/" + file.filename, file.content)
        return {
            "success": True,
            "path": file.path + "/" + file.filename,
            "size": len(file.content)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/files/delete")
async def delete_file(path: str, sid: str = Depends(require_portal_access)):
    """Delete file from virtual filesystem"""
    try:
        vfs.delete_file(path)
        return {"success": True, "path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Virtual Database ====================

@app.post("/api/database/query")
async def database_query(query: DatabaseQuery, sid: str = Depends(require_portal_access)):
    """
    Execute database query
    SQL injection attempts are detected and fake data is returned
    """
    try:
        result = vdb.execute_query(query.query, query.database)
        return {
            "success": True,
            "query": query.query,
            "result": result,
            "rows_affected": len(result) if isinstance(result, list) else 0
        }
    except Exception as e:
        # Return fake error to confuse attackers
        return {
            "success": False,
            "error": "Query execution failed",
            "details": str(e)
        }


@app.get("/api/database/tables")
async def list_tables(database: str = "main", sid: str = Depends(require_portal_access)):
    """List database tables"""
    tables = vdb.list_tables(database)
    return {
        "database": database,
        "tables": tables,
        "count": len(tables)
    }


@app.get("/api/database/schema")
async def get_schema(table: str, database: str = "main", sid: str = Depends(require_portal_access)):
    """Get table schema"""
    schema = vdb.get_schema(table, database)
    return {
        "table": table,
        "database": database,
        "schema": schema
    }


# ==================== User Management ====================

@app.get("/api/users/list")
async def list_users(sid: str = Depends(require_portal_access)):
    """
    List all users
    Attackers trying to enumerate users get fake user list
    """
    users = user_manager.list_users()
    return {
        "users": users,
        "count": len(users)
    }


@app.get("/api/users/{user_id}")
async def get_user(user_id: int, sid: str = Depends(require_portal_access)):
    """Get user details by ID"""
    user = user_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/api/users/create")
async def create_user(user: UserData, sid: str = Depends(require_portal_access)):
    """Create new user"""
    new_user = user_manager.create_user(
        user.username,
        user.email,
        user.role
    )
    return new_user


# ==================== API Key Management ====================

@app.post("/api/keys/generate")
async def generate_api_key(key_req: APIKeyRequest, sid: str = Depends(require_portal_access)):
    """
    Generate API key
    All generated keys are tracked with unique tokens
    """
    api_key = user_manager.generate_api_key(key_req.name, key_req.permissions)
    return {
        "success": True,
        "api_key": api_key["key"],
        "name": api_key["name"],
        "permissions": api_key["permissions"],
        "created_at": api_key["created_at"]
    }


@app.get("/api/keys/list")
async def list_api_keys(sid: str = Depends(require_portal_access)):
    """List all API keys"""
    keys = user_manager.list_api_keys()
    return {
        "keys": keys,
        "count": len(keys)
    }


# ==================== Honeypot Endpoints ====================

@app.get("/admin/backup")
async def admin_backup():
    """
    Honeypot endpoint - looks like database backup
    Anyone accessing this is suspicious
    """
    # This looks like a real backup but is actually a honeypot
    return {
        "backup_file": "database_backup_2025_01_06.sql.gz",
        "size": "245MB",
        "download_url": "/admin/backup/download?file=database_backup_2025_01_06.sql.gz",
        "created_at": datetime.utcnow().isoformat()
    }


@app.get("/admin/config")
async def admin_config():
    """
    Honeypot endpoint - fake configuration file
    Contains tracking tokens
    """
    tracking_token = secrets.token_hex(16)
    return {
        "database": {
            "host": "db.internal.company.com",
            "port": 5432,
            "username": "admin_tracked_" + tracking_token[:8],
            "password": "P@ssw0rd_TRACKED_" + tracking_token[8:16],
            "database": "production"
        },
        "api_keys": {
            "stripe": "sk_live_TRACKED_" + tracking_token,
            "aws": "AKIA_TRACKED_" + tracking_token
        },
        "tracking_token": tracking_token
    }


@app.get("/.env")
async def env_file():
    """
    Honeypot - fake .env file
    Attackers often look for these
    """
    tracking_token = secrets.token_hex(16)
    return Response(
        content=f"""# Environment Configuration
DATABASE_URL=postgresql://admin:password_tracked_{tracking_token}@localhost:5432/prod
SECRET_KEY=super_secret_key_tracked_{tracking_token}
API_KEY=sk_live_tracked_{tracking_token}
AWS_ACCESS_KEY=AKIA_tracked_{tracking_token}
AWS_SECRET_KEY=secret_tracked_{tracking_token}
STRIPE_KEY=sk_live_tracked_{tracking_token}
# This is a honeypot - all credentials are tracked
""",
        media_type="text/plain"
    )


@app.get("/api/internal/secrets")
async def internal_secrets():
    """
    Honeypot - fake secrets endpoint
    Should never be accessed by legitimate users
    """
    tracking_token = secrets.token_hex(16)
    return {
        "secrets": [
            {"name": "database_password", "value": f"tracked_{tracking_token}_1"},
            {"name": "api_master_key", "value": f"tracked_{tracking_token}_2"},
            {"name": "encryption_key", "value": f"tracked_{tracking_token}_3"}
        ],
        "warning": "This is a honeypot - access logged"
    }


# ==================== Defense Monitoring ====================

@app.get("/api/defense/status")
async def defense_status(username: str = Depends(verify_credentials)):
    """Get defense system status"""
    status = defense.middleware.orchestrator.get_status()
    qsharp_stats = defense.middleware.get_qsharp_stats()
    
    return {
        "defense_system": status,
        "qsharp_stats": qsharp_stats,
        "virtual_resources": {
            "filesystem_files": len(vfs.files),
            "database_tables": len(vdb.tables),
            "users": len(user_manager.users),
            "api_keys": len(user_manager.api_keys)
        }
    }


@app.get("/api/defense/threats")
async def list_threats(username: str = Depends(verify_credentials)):
    """Get recent threat detections"""
    history = defense.middleware.qsharp_operation_history[-100:]
    threats = [h for h in history if h["threat_detected"]]
    
    return {
        "threats": threats,
        "total": len(threats),
        "recent": threats[-20:] if len(threats) > 20 else threats
    }


@app.get("/api/defense/honeypot-access")
async def honeypot_access_log(username: str = Depends(verify_credentials)):
    """Get honeypot access attempts"""
    # In production, this would read from actual logs
    return {
        "honeypot_endpoints": [
            "/admin/backup",
            "/admin/config",
            "/.env",
            "/api/internal/secrets"
        ],
        "access_attempts": vfs.honeypot_access_log,
        "total": len(vfs.honeypot_access_log)
    }


# ==================== Admin Dashboard ====================

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(username: str = Depends(verify_credentials)):
    """Admin dashboard with real-time monitoring"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Virtual Protected Server - Admin Dashboard</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: #1a1a2e;
                color: #eee;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            h1 {
                color: #00ff88;
                border-bottom: 2px solid #00ff88;
                padding-bottom: 10px;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .card {
                background: #16213e;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }
            .card h2 {
                margin-top: 0;
                color: #00ff88;
                font-size: 1.2em;
            }
            .status {
                display: flex;
                justify-content: space-between;
                padding: 10px;
                background: #0f3460;
                border-radius: 5px;
                margin: 10px 0;
            }
            .status.active {
                border-left: 4px solid #00ff88;
            }
            .status.alert {
                border-left: 4px solid #ff0055;
            }
            .threat-item {
                background: #ff0055;
                color: white;
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
            }
            button {
                background: #00ff88;
                color: #1a1a2e;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                margin: 5px;
            }
            button:hover {
                background: #00dd77;
            }
            .code {
                background: #0f0f0f;
                padding: 10px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                overflow-x: auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ Virtual Protected Server - Admin Dashboard</h1>
            
            <div class="grid">
                <div class="card">
                    <h2>🔒 Defense Status</h2>
                    <div class="status active">
                        <span>Zero-Trust Defense</span>
                        <span>✅ ACTIVE</span>
                    </div>
                    <div class="status active">
                        <span>Pattern Detection</span>
                        <span>✅ ENABLED</span>
                    </div>
                    <div class="status active">
                        <span>Quantum Enhanced</span>
                        <span>✅ ENABLED</span>
                    </div>
                </div>
                
                <div class="card">
                    <h2>📊 Virtual Resources</h2>
                    <div class="status">
                        <span>Virtual Filesystem</span>
                        <span id="fs-count">Loading...</span>
                    </div>
                    <div class="status">
                        <span>Virtual Database</span>
                        <span id="db-count">Loading...</span>
                    </div>
                    <div class="status">
                        <span>Active Users</span>
                        <span id="user-count">Loading...</span>
                    </div>
                </div>
                
                <div class="card">
                    <h2>⚠️ Recent Threats</h2>
                    <div id="threats">
                        <p>Loading threat data...</p>
                    </div>
                </div>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h2>🍯 Honeypot Access</h2>
                    <div id="honeypot-access">
                        <p>Loading honeypot data...</p>
                    </div>
                </div>
                
                <div class="card">
                    <h2>📈 System Metrics</h2>
                    <div class="status">
                        <span>Requests Processed</span>
                        <span id="requests">Loading...</span>
                    </div>
                    <div class="status alert">
                        <span>Threats Detected</span>
                        <span id="threat-count">Loading...</span>
                    </div>
                    <div class="status">
                        <span>Uptime</span>
                        <span id="uptime">Loading...</span>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🔧 Actions</h2>
                    <button onclick="refreshData()">🔄 Refresh Data</button>
                    <button onclick="viewLogs()">📋 View Logs</button>
                    <button onclick="exportThreats()">📥 Export Threats</button>
                </div>
            </div>
            
            <div class="card">
                <h2>💻 Quick Commands</h2>
                <div class="code">
# Test the defense system<br>
curl -X POST http://localhost:8000/api/auth/login -d '{"username":"admin' OR '1'='1"}'<br>
<br>
# Access honeypot<br>
curl http://localhost:8000/.env<br>
<br>
# Check defense status<br>
curl -u admin:admin123 http://localhost:8000/api/defense/status
                </div>
            </div>
        </div>
        
        <script>
            async function loadData() {
                try {
                    const response = await fetch('/api/defense/status', {
                        headers: {
                            'Authorization': 'Basic ' + btoa('admin:admin123')
                        }
                    });
                    const data = await response.json();
                    
                    document.getElementById('fs-count').textContent = 
                        data.virtual_resources.filesystem_files + ' files';
                    document.getElementById('db-count').textContent = 
                        data.virtual_resources.database_tables + ' tables';
                    document.getElementById('user-count').textContent = 
                        data.virtual_resources.users + ' users';
                } catch (error) {
                    console.error('Error loading data:', error);
                }
                
                try {
                    const threatResponse = await fetch('/api/defense/threats', {
                        headers: {
                            'Authorization': 'Basic ' + btoa('admin:admin123')
                        }
                    });
                    const threatData = await threatResponse.json();
                    
                    document.getElementById('threat-count').textContent = 
                        threatData.total + ' threats';
                    
                    const threatsDiv = document.getElementById('threats');
                    if (threatData.recent.length === 0) {
                        threatsDiv.innerHTML = '<p>No recent threats detected ✅</p>';
                    } else {
                        threatsDiv.innerHTML = threatData.recent.slice(0, 5).map(t => 
                            `<div class="threat-item">
                                <strong>Threat detected</strong><br>
                                Risk Score: ${t.risk_score}<br>
                                Time: ${new Date(t.timestamp * 1000).toLocaleString()}
                            </div>`
                        ).join('');
                    }
                } catch (error) {
                    console.error('Error loading threats:', error);
                }
            }
            
            function refreshData() {
                loadData();
                alert('Data refreshed!');
            }
            
            function viewLogs() {
                window.location.href = '/api/defense/threats';
            }
            
            function exportThreats() {
                alert('Exporting threats to CSV...');
            }
            
            // Load data on page load
            loadData();
            
            // Auto-refresh every 10 seconds
            setInterval(loadData, 10000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ==================== Server Startup ====================

if __name__ == "__main__":
    print("=" * 70)
    print("🛡️  VIRTUAL PROTECTED SERVER")
    print("=" * 70)
    print()
    print("🔒 Zero-Trust Defense: ACTIVE")
    print("🍯 Honeypot Endpoints: DEPLOYED")
    print("💾 Virtual Resources: INITIALIZED")
    print("🔐 Authentication: REQUIRED")
    print()
    print("📡 Server starting on http://localhost:8000")
    print()
    print("🔑 Default Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print()
    print("📊 Admin Dashboard: http://localhost:8000/admin/dashboard")
    print("📚 API Documentation: http://localhost:8000/api/docs")
    print()
    print("🍯 Honeypot Endpoints (DO NOT ACCESS unless testing):")
    print("   • /.env")
    print("   • /admin/backup")
    print("   • /admin/config")
    print("   • /api/internal/secrets")
    print()
    print("🧪 Test Commands:")
    print("   • Normal: curl http://localhost:8000/health")
    print("   • Attack: curl -X POST http://localhost:8000/api/auth/login \\")
    print("             -d '{\"username\":\"admin' OR '1'='1\"}'")
    print()
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
