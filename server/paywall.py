"""
Paywall management for web-only access

Provides a session store and dependencies to require payment before
accessing user services. Uses Redis if configured, otherwise in-memory.

Production notes:
- Replace the dev payment endpoints with a real payment provider (e.g. Stripe)
- Store sessions in Redis or a database
- Use signed/rotating cookies and HTTPS-only, Secure, HttpOnly flags
"""
from __future__ import annotations

import os
import secrets
import time
from typing import Dict, Optional, Any

from fastapi import HTTPException, Request, Response
import os

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


class BaseSessionStore:
    def create(self) -> str: ...
    def get(self, sid: str) -> Optional[Dict[str, Any]]: ...
    def set(self, sid: str, data: Dict[str, Any]) -> None: ...
    def exists(self, sid: str) -> bool: ...


class MemorySessionStore(BaseSessionStore):
    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create(self) -> str:
        sid = secrets.token_urlsafe(32)
        self.sessions[sid] = {"paid": False, "created_at": time.time()}
        return sid

    def get(self, sid: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(sid)

    def set(self, sid: str, data: Dict[str, Any]) -> None:
        self.sessions[sid] = data

    def exists(self, sid: str) -> bool:
        return sid in self.sessions


# Login token stores
class BaseLoginTokenStore:
    def create(self, email: str, ttl: int = 600) -> str: ...
    def consume(self, token: str) -> Optional[str]: ...


class MemoryLoginTokenStore(BaseLoginTokenStore):
    def __init__(self) -> None:
        self.tokens: Dict[str, Dict[str, Any]] = {}

    def create(self, email: str, ttl: int = 600) -> str:
        token = secrets.token_urlsafe(24)
        self.tokens[token] = {"email": email, "expires": time.time() + ttl}
        return token

    def consume(self, token: str) -> Optional[str]:
        rec = self.tokens.get(token)
        if not rec:
            return None
        if rec["expires"] < time.time():
            del self.tokens[token]
            return None
        del self.tokens[token]
        return str(rec["email"])


class RedisLoginTokenStore(BaseLoginTokenStore):
    def __init__(self, url: str) -> None:
        assert redis is not None, "redis package not available"
        self.client = redis.from_url(url, decode_responses=True)
        self.prefix = "ztai:login:"

    def _key(self, token: str) -> str:
        return self.prefix + token

    def create(self, email: str, ttl: int = 600) -> str:
        token = secrets.token_urlsafe(24)
        self.client.set(self._key(token), email, ex=ttl)
        return token

    def consume(self, token: str) -> Optional[str]:
        pipe = self.client.pipeline()
        key = self._key(token)
        pipe.get(key)
        pipe.delete(key)
        val, _ = pipe.execute()
        return val if val else None


class RedisSessionStore(BaseSessionStore):
    def __init__(self, url: str) -> None:
        assert redis is not None, "redis package not available"
        self.client = redis.from_url(url, decode_responses=True)
        self.prefix = "ztai:sess:"
        self.ttl = int(os.environ.get("SESSION_TTL", "604800"))  # 7 days

    def _key(self, sid: str) -> str:
        return self.prefix + sid

    def create(self) -> str:
        sid = secrets.token_urlsafe(32)
        self.client.hset(self._key(sid), mapping={"paid": "0", "created_at": str(time.time())})
        self.client.expire(self._key(sid), self.ttl)
        return sid

    def get(self, sid: str) -> Optional[Dict[str, Any]]:
        data = self.client.hgetall(self._key(sid))
        if not data:
            return None
        return {
            "paid": data.get("paid") == "1",
            "created_at": float(data.get("created_at", "0")),
            "customer_id": data.get("customer_id"),
            "verified": data.get("verified") == "1",
        }

    def set(self, sid: str, data: Dict[str, Any]) -> None:
        enc = {
            "paid": "1" if data.get("paid") else "0",
            "created_at": str(data.get("created_at", time.time())),
        }
        if "customer_id" in data:
            enc["customer_id"] = str(data["customer_id"])
        if "verified" in data:
            enc["verified"] = "1" if data.get("verified") else "0"
        self.client.hset(self._key(sid), mapping=enc)
        self.client.expire(self._key(sid), self.ttl)

    def exists(self, sid: str) -> bool:
        return self.client.exists(self._key(sid)) == 1


class PaywallManager:
    """Session and paywall manager with optional Redis backing."""

    def __init__(self) -> None:
        redis_url = os.environ.get("REDIS_URL")
        if redis_url and redis is not None:
            try:
                self.store: BaseSessionStore = RedisSessionStore(redis_url)
            except Exception:
                self.store = MemorySessionStore()
        else:
            self.store = MemorySessionStore()
        # login tokens (Redis-backed if available)
        if redis_url and redis is not None:
            try:
                self.token_store: BaseLoginTokenStore = RedisLoginTokenStore(redis_url)
            except Exception:
                self.token_store = MemoryLoginTokenStore()
        else:
            self.token_store = MemoryLoginTokenStore()

    def create_session(self) -> str:
        return self.store.create()

    def get_session(self, sid: str) -> Optional[Dict[str, Any]]:
        return self.store.get(sid)

    def is_paid(self, sid: str) -> bool:
        data = self.store.get(sid)
        return bool(data and data.get("paid"))

    def mark_paid(self, sid: str) -> None:
        data = self.store.get(sid) or {"created_at": time.time()}
        data["paid"] = True
        self.store.set(sid, data)

    def attach_customer(self, sid: str, customer_id: str, verified: bool = False) -> None:
        data = self.store.get(sid) or {"created_at": time.time(), "paid": False}
        data["customer_id"] = customer_id
        data["verified"] = verified
        self.store.set(sid, data)

    def mark_verified(self, sid: str) -> None:
        data = self.store.get(sid) or {"created_at": time.time(), "paid": False}
        data["verified"] = True
        self.store.set(sid, data)

    def mark_logged_in(self, sid: str, value: bool = True) -> None:
        data = self.store.get(sid) or {"created_at": time.time(), "paid": False}
        data["logged_in"] = value
        self.store.set(sid, data)

    # login token helpers (2FA second step)
    def create_login_token(self, email: str, ttl: int = 600) -> str:
        return self.token_store.create(email, ttl)

    def consume_login_token(self, token: str) -> Optional[str]:
        return self.token_store.consume(token)


# Singleton manager for the app
paywall_manager = PaywallManager()

# 2FA enforcement toggle (default: enabled)
FORCE_2FA = os.environ.get("FORCE_2FA", "1") == "1"


def ensure_session_cookie(request: Request, response: Response) -> str:
    """
    Ensure the client has a session cookie; create one if missing.
    Returns the session_id.
    """
    sid = request.cookies.get("session_id")
    if not sid or not paywall_manager.get_session(sid):
        sid = paywall_manager.create_session()
        # Set cookie for 7 days; tighten in production
        response.set_cookie(
            key="session_id",
            value=sid,
            max_age=7 * 24 * 3600,
            httponly=True,
            secure=False,  # set True behind HTTPS in production
            samesite="Lax",
        )
    return sid


def require_paid_session(request: Request) -> str:
    """Dependency: require an existing paid session cookie."""
    sid = request.cookies.get("session_id")
    if not sid:
        raise HTTPException(status_code=401, detail="Session not found")
    if not paywall_manager.is_paid(sid):
        # 402 Payment Required
        raise HTTPException(status_code=402, detail="Payment required")
    return sid


def require_portal_access(request: Request) -> str:
    """Dependency: require paid session; if FORCE_2FA, also require successful 2FA login."""
    sid = request.cookies.get("session_id")
    if not sid:
        raise HTTPException(status_code=401, detail="Session not found")
    sess = paywall_manager.get_session(sid) or {}
    if not sess.get("paid"):
        raise HTTPException(status_code=402, detail="Payment required")
    if FORCE_2FA and not sess.get("logged_in"):
        raise HTTPException(status_code=401, detail="Login (2FA) required")
    return sid
