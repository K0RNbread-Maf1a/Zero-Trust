"""Tracking token management for tracing exfiltrated data."""

import hashlib
import secrets
import time
from typing import Dict, List
import json


class TrackingTokenManager:
    """Manages tracking tokens embedded in fake data."""
    
    def __init__(self):
        self.tokens = {}  # token -> metadata
        
    def generate_token(self, context: Dict = None) -> str:
        """Generate a unique tracking token."""
        token_data = f"{secrets.token_hex(16)}{time.time()}"
        token = hashlib.sha256(token_data.encode()).hexdigest()[:16]
        
        self.tokens[token] = {
            "created_at": time.time(),
            "context": context or {},
            "accessed": []
        }
        
        return token
    
    def record_access(self, token: str, accessor_ip: str, location: str):
        """Record when/where a token is accessed."""
        if token in self.tokens:
            self.tokens[token]["accessed"].append({
                "timestamp": time.time(),
                "ip": accessor_ip,
                "location": location
            })
    
    def is_tracked(self, data: str) -> bool:
        """Check if data contains a tracking token."""
        return any(token in data for token in self.tokens.keys())
    
    def export_log(self, filepath: str):
        """Export token tracking log."""
        with open(filepath, 'w') as f:
            json.dump(self.tokens, f, indent=2)
