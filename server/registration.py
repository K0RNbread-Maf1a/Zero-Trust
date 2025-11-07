"""
Customer Registration Manager

Handles customer registration, email verification (dev/demo), and login.
Backed by Redis if available, otherwise in-memory.

Security notes (demo):
- Passwords are hashed with SHA-256 for simplicity in demo. Use bcrypt/argon2 in production.
- Verification codes are stored server-side and should be sent via email. Here we expose
  the code in dev mode via API response if RETURN_VERIFICATION_CODE=1.
"""
from __future__ import annotations

import hashlib
import os
import secrets
import time
from typing import Dict, Optional, Any

import pyotp

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


class BaseRegistry:
    def create_pending(self, email: str, password: str) -> str: ...
    def verify(self, email: str, code: str) -> Optional[str]: ...
    def authenticate(self, email: str, password: str) -> Optional[str]: ...
    def is_verified(self, email: str) -> bool: ...


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class MemoryRegistry(BaseRegistry):
    def __init__(self) -> None:
        self.pending: Dict[str, Dict[str, Any]] = {}
        self.customers: Dict[str, Dict[str, Any]] = {}

    def create_pending(self, email: str, password: str) -> str:
        email = _normalize_email(email)
        code = f"{secrets.randbelow(999999):06d}"
        self.pending[email] = {
            "email": email,
            "password_hash": _hash_password(password),
            "code": code,
            "created_at": time.time(),
        }
        return code

    def verify(self, email: str, code: str) -> Optional[str]:
        email = _normalize_email(email)
        p = self.pending.get(email)
        if not p or p.get("code") != code:
            return None
        customer_id = secrets.token_hex(8)
        self.customers[email] = {
            "customer_id": customer_id,
            "email": email,
            "password_hash": p["password_hash"],
            "verified": True,
            "created_at": time.time(),
        }
        del self.pending[email]
        return customer_id

    def authenticate(self, email: str, password: str) -> Optional[str]:
        email = _normalize_email(email)
        c = self.customers.get(email)
        if c and c.get("password_hash") == _hash_password(password):
            return c.get("customer_id")
        return None

    def is_verified(self, email: str) -> bool:
        email = _normalize_email(email)
        c = self.customers.get(email)
        return bool(c and c.get("verified"))

    # 2FA methods
    def get_or_create_otp_secret(self, email: str) -> str:
        email = _normalize_email(email)
        c = self.customers.get(email)
        if not c:
            # Create an unverified customer record for enrollment flows
            self.customers[email] = {
                "customer_id": secrets.token_hex(8),
                "email": email,
                "password_hash": _hash_password(secrets.token_urlsafe(8)),
                "verified": False,
                "created_at": time.time(),
            }
            c = self.customers.get(email)
        if not c.get("otp_secret"):
            c["otp_secret"] = pyotp.random_base32()
            c["otp_enabled"] = False
        return c["otp_secret"]

    def enable_otp_if_valid(self, email: str, code: str) -> bool:
        email = _normalize_email(email)
        c = self.customers.get(email)
        if not c or not c.get("otp_secret"):
            return False
        totp = pyotp.TOTP(c["otp_secret"])
        if totp.verify(code, valid_window=1):
            c["otp_enabled"] = True
            return True
        return False

    def is_otp_enabled(self, email: str) -> bool:
        email = _normalize_email(email)
        c = self.customers.get(email)
        return bool(c and c.get("otp_enabled"))

    def get_otp_secret(self, email: str) -> Optional[str]:
        email = _normalize_email(email)
        c = self.customers.get(email)
        return c.get("otp_secret") if c else None


class RedisRegistry(BaseRegistry):
    def __init__(self, url: str) -> None:
        assert redis is not None
        self.client = redis.from_url(url, decode_responses=True)
        self.prefix = "ztai:cust:"

    def _pkey(self, email: str) -> str:
        return self.prefix + "pending:" + _normalize_email(email)

    def _ckey(self, email: str) -> str:
        return self.prefix + "cust:" + _normalize_email(email)

    def create_pending(self, email: str, password: str) -> str:
        code = f"{secrets.randbelow(999999):06d}"
        self.client.hset(self._pkey(email), mapping={
            "email": _normalize_email(email),
            "password_hash": _hash_password(password),
            "code": code,
            "created_at": str(time.time()),
        })
        self.client.expire(self._pkey(email), 3600)  # 1 hour to verify
        return code

    def verify(self, email: str, code: str) -> Optional[str]:
        p = self.client.hgetall(self._pkey(email))
        if not p or p.get("code") != code:
            return None
        customer_id = secrets.token_hex(8)
        self.client.hset(self._ckey(email), mapping={
            "customer_id": customer_id,
            "email": _normalize_email(email),
            "password_hash": p.get("password_hash"),
            "verified": "1",
            "created_at": str(time.time()),
        })
        self.client.delete(self._pkey(email))
        return customer_id

    def authenticate(self, email: str, password: str) -> Optional[str]:
        c = self.client.hgetall(self._ckey(email))
        if c and c.get("password_hash") == _hash_password(password):
            return c.get("customer_id")
        return None

    def is_verified(self, email: str) -> bool:
        c = self.client.hgetall(self._ckey(email))
        return bool(c and c.get("verified") == "1")

    # 2FA methods
    def get_or_create_otp_secret(self, email: str) -> str:
        key = self._ckey(email)
        c = self.client.hgetall(key)
        if not c:
            # Initialize record
            self.client.hset(key, mapping={
                "customer_id": secrets.token_hex(8),
                "email": _normalize_email(email),
                "password_hash": _hash_password(secrets.token_urlsafe(8)),
                "verified": "0",
                "created_at": str(time.time()),
            })
            c = self.client.hgetall(key)
        if not c.get("otp_secret"):
            secret = pyotp.random_base32()
            self.client.hset(key, mapping={"otp_secret": secret, "otp_enabled": "0"})
            return secret
        return c.get("otp_secret")

    def enable_otp_if_valid(self, email: str, code: str) -> bool:
        key = self._ckey(email)
        secret = self.client.hget(key, "otp_secret")
        if not secret:
            return False
        totp = pyotp.TOTP(secret)
        if totp.verify(code, valid_window=1):
            self.client.hset(key, mapping={"otp_enabled": "1"})
            return True
        return False

    def is_otp_enabled(self, email: str) -> bool:
        return self.client.hget(self._ckey(email), "otp_enabled") == "1"

    def get_otp_secret(self, email: str) -> Optional[str]:
        val = self.client.hget(self._ckey(email), "otp_secret")
        return val if val else None


class RegistrationManager:
    def __init__(self) -> None:
        url = os.environ.get("REDIS_URL")
        if url and redis is not None:
            try:
                self.backend: BaseRegistry = RedisRegistry(url)
            except Exception:
                self.backend = MemoryRegistry()
        else:
            self.backend = MemoryRegistry()

    def start(self, email: str, password: str) -> str:
        return self.backend.create_pending(email, password)

    def verify(self, email: str, code: str) -> Optional[str]:
        return self.backend.verify(email, code)

    def login(self, email: str, password: str) -> Optional[str]:
        return self.backend.authenticate(email, password)

    def is_verified(self, email: str) -> bool:
        return self.backend.is_verified(email)

    # 2FA
    def get_or_create_otp_secret(self, email: str) -> str:
        return self.backend.get_or_create_otp_secret(email)  # type: ignore[attr-defined]

    def enable_otp_if_valid(self, email: str, code: str) -> bool:
        return self.backend.enable_otp_if_valid(email, code)  # type: ignore[attr-defined]

    def is_otp_enabled(self, email: str) -> bool:
        return self.backend.is_otp_enabled(email)  # type: ignore[attr-defined]

    def get_otp_secret(self, email: str) -> Optional[str]:
        return self.backend.get_otp_secret(email)  # type: ignore[attr-defined]


registration_manager = RegistrationManager()
