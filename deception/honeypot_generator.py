"""Honeypot generator for creating enticing fake endpoints and data."""

from typing import Dict, List, Any
from faker import Faker
import secrets
import hashlib


class HoneypotGenerator:
    """Generates honeypot endpoints and fake data to trap attackers."""
    
    def __init__(self, tracking_token_manager=None):
        self.faker = Faker()
        self.token_manager = tracking_token_manager
        
    def generate_fake_env_file(self, tracking_token: str = None) -> str:
        """Generate a convincing fake .env file."""
        if not tracking_token:
            tracking_token = self._generate_token()
        
        return f"""# Environment Configuration
# DO NOT COMMIT THIS FILE

# Database
DB_HOST=prod-db-01.internal.company.com
DB_PORT=5432
DB_NAME=production
DB_USER=admin_{tracking_token[:8]}
DB_PASSWORD={self.faker.password(length=32)}_{tracking_token}

# API Keys
API_KEY={self.faker.sha256()}_{tracking_token}
SECRET_KEY={secrets.token_hex(32)}_{tracking_token}
STRIPE_SECRET_KEY=sk_live_{self.faker.sha256()[:32]}_{tracking_token}

# AWS
AWS_ACCESS_KEY_ID=AKIA{self.faker.sha256()[:16].upper()}_{tracking_token[:4]}
AWS_SECRET_ACCESS_KEY={self.faker.sha256()}_{tracking_token}
AWS_REGION=us-east-1

# JWT
JWT_SECRET={secrets.token_hex(32)}_{tracking_token}
JWT_EXPIRY=86400

# Redis
REDIS_HOST=cache-prod.internal.company.com
REDIS_PORT=6379
REDIS_PASSWORD={self.faker.password()}_{tracking_token}
"""
    
    def generate_fake_api_keys(self, count: int = 5, tracking_token: str = None) -> List[Dict[str, str]]:
        """Generate fake API keys."""
        if not tracking_token:
            tracking_token = self._generate_token()
        
        keys = []
        for i in range(count):
            keys.append({
                "key_id": f"key_{self.faker.uuid4()}",
                "api_key": f"{self.faker.sha256()[:32]}_{tracking_token}",
                "description": self.faker.bs(),
                "created_at": self.faker.iso8601(),
                "permissions": ["read", "write"],
                "tracking_token": tracking_token
            })
        
        return keys
    
    def generate_fake_database_dump(self, table_name: str, row_count: int = 100, tracking_token: str = None) -> str:
        """Generate a fake database SQL dump."""
        if not tracking_token:
            tracking_token = self._generate_token()
        
        sql = f"-- Database Dump for {table_name}\n"
        sql += f"-- Generated: {self.faker.iso8601()}\n"
        sql += f"-- WARNING: Contains tracking token {tracking_token}\n\n"
        
        sql += f"CREATE TABLE {table_name} (\n"
        sql += "  id SERIAL PRIMARY KEY,\n"
        sql += "  username VARCHAR(255),\n"
        sql += "  email VARCHAR(255),\n"
        sql += "  password_hash VARCHAR(255),\n"
        sql += "  api_key VARCHAR(255),\n"
        sql += "  created_at TIMESTAMP\n"
        sql += ");\n\n"
        
        for i in range(row_count):
            sql += f"INSERT INTO {table_name} VALUES ("
            sql += f"{i+1}, "
            sql += f"'{self.faker.user_name()}', "
            sql += f"'{self.faker.email()}', "
            sql += f"'{self.faker.sha256()}', "
            sql += f"'{self.faker.sha256()[:32]}_{tracking_token}', "
            sql += f"'{self.faker.iso8601()}'"
            sql += ");\n"
        
        return sql
    
    def generate_fake_config_file(self, format: str = "json", tracking_token: str = None) -> str:
        """Generate fake configuration file."""
        if not tracking_token:
            tracking_token = self._generate_token()
        
        if format == "json":
            import json
            config = {
                "server": {
                    "host": "0.0.0.0",
                    "port": 8080,
                    "debug": False
                },
                "database": {
                    "host": f"db-{tracking_token[:8]}.internal",
                    "port": 5432,
                    "name": "production",
                    "user": f"admin_{tracking_token[:6]}",
                    "password": f"{self.faker.password()}_{tracking_token}"
                },
                "secrets": {
                    "jwt_secret": f"{secrets.token_hex(32)}_{tracking_token}",
                    "api_key": f"{self.faker.sha256()}_{tracking_token}"
                },
                "tracking_token": tracking_token
            }
            return json.dumps(config, indent=2)
        
        elif format == "yaml":
            return f"""server:
  host: 0.0.0.0
  port: 8080
  debug: false

database:
  host: db-{tracking_token[:8]}.internal
  port: 5432
  name: production
  user: admin_{tracking_token[:6]}
  password: {self.faker.password()}_{tracking_token}

secrets:
  jwt_secret: {secrets.token_hex(32)}_{tracking_token}
  api_key: {self.faker.sha256()}_{tracking_token}

tracking_token: {tracking_token}
"""
    
    def generate_honeypot_credentials(self, count: int = 10, tracking_token: str = None) -> List[Dict[str, str]]:
        """Generate fake user credentials."""
        if not tracking_token:
            tracking_token = self._generate_token()
        
        credentials = []
        for i in range(count):
            credentials.append({
                "user_id": self.faker.uuid4(),
                "username": self.faker.user_name(),
                "email": self.faker.email(),
                "password": self.faker.password(),
                "api_token": f"{self.faker.sha256()[:32]}_{tracking_token}",
                "role": self.faker.random_element(["admin", "user", "developer"]),
                "tracking_token": tracking_token
            })
        
        return credentials
    
    def _generate_token(self) -> str:
        """Generate a tracking token."""
        return hashlib.sha256(secrets.token_bytes(32)).hexdigest()[:16]
