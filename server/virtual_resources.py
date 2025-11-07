"""
Virtual Resources - Simulated filesystem, database, and user management

These provide realistic honeypot resources that look and behave like real systems
but are completely virtual and tracked.
"""
import secrets
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from faker import Faker


fake = Faker()


class VirtualFileSystem:
    """
    Virtual filesystem that mimics a real file system
    All files are in-memory and tracked
    """
    
    def __init__(self):
        self.files = {}
        self.honeypot_access_log = []
        self._initialize_default_files()
    
    def _initialize_default_files(self):
        """Create some default files"""
        self.files = {
            "/": {"type": "directory", "contents": {}},
            "/home": {"type": "directory", "contents": {}},
            "/var": {"type": "directory", "contents": {}},
            "/etc": {"type": "directory", "contents": {}},
            
            # Some realistic files
            "/etc/config.json": {
                "type": "file",
                "content": '{"app": "protected_server", "version": "1.0.0"}',
                "size": 50,
                "created": time.time()
            },
            "/var/log/app.log": {
                "type": "file",
                "content": "[INFO] Server started\n[INFO] Defense active\n",
                "size": 100,
                "created": time.time()
            },
            "/home/data.csv": {
                "type": "file",
                "content": "id,name,email\n1,Alice,alice@example.com\n2,Bob,bob@example.com\n",
                "size": 200,
                "created": time.time()
            }
        }
    
    def list_directory(self, path: str) -> List[Dict[str, Any]]:
        """List files in a directory"""
        if path not in self.files:
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if self.files[path]["type"] != "directory":
            raise NotADirectoryError(f"Not a directory: {path}")
        
        # List all files starting with this path
        files = []
        for file_path, info in self.files.items():
            if file_path.startswith(path) and file_path != path:
                relative = file_path[len(path):].lstrip("/")
                if "/" not in relative or relative.split("/")[0]:
                    files.append({
                        "name": file_path.split("/")[-1],
                        "path": file_path,
                        "type": info["type"],
                        "size": info.get("size", 0),
                        "created": info.get("created", time.time())
                    })
        
        return files
    
    def read_file(self, path: str) -> str:
        """Read file contents"""
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        
        if self.files[path]["type"] != "file":
            raise IsADirectoryError(f"Is a directory: {path}")
        
        # Log access
        self._log_access(path)
        
        return self.files[path]["content"]
    
    def write_file(self, path: str, content: str):
        """Write file contents"""
        self.files[path] = {
            "type": "file",
            "content": content,
            "size": len(content),
            "created": time.time()
        }
    
    def delete_file(self, path: str):
        """Delete a file"""
        if path in self.files:
            del self.files[path]
    
    def _log_access(self, path: str):
        """Log file access"""
        self.honeypot_access_log.append({
            "path": path,
            "timestamp": time.time(),
            "action": "read"
        })


class VirtualDatabase:
    """
    Virtual database that mimics a real SQL database
    All data is fake but looks realistic
    """
    
    def __init__(self):
        self.tables = {}
        self._initialize_default_tables()
    
    def _initialize_default_tables(self):
        """Create some default tables with fake data"""
        
        # Users table
        self.tables["users"] = {
            "schema": {
                "user_id": "INTEGER PRIMARY KEY",
                "username": "VARCHAR(255)",
                "email": "VARCHAR(255)",
                "password_hash": "VARCHAR(255)",
                "role": "VARCHAR(50)",
                "created_at": "TIMESTAMP"
            },
            "data": [
                {
                    "user_id": i,
                    "username": fake.user_name(),
                    "email": fake.email(),
                    "password_hash": fake.sha256(),
                    "role": "user" if i > 2 else "admin",
                    "created_at": fake.date_time_this_year().isoformat()
                }
                for i in range(1, 26)
            ]
        }
        
        # Products table
        self.tables["products"] = {
            "schema": {
                "product_id": "INTEGER PRIMARY KEY",
                "name": "VARCHAR(255)",
                "price": "DECIMAL(10,2)",
                "stock": "INTEGER",
                "category": "VARCHAR(100)"
            },
            "data": [
                {
                    "product_id": i,
                    "name": fake.commerce.product_name(),
                    "price": float(fake.commerce.price()),
                    "stock": fake.random_int(0, 100),
                    "category": fake.word()
                }
                for i in range(1, 51)
            ]
        }
        
        # Orders table
        self.tables["orders"] = {
            "schema": {
                "order_id": "INTEGER PRIMARY KEY",
                "user_id": "INTEGER",
                "product_id": "INTEGER",
                "quantity": "INTEGER",
                "total": "DECIMAL(10,2)",
                "order_date": "TIMESTAMP"
            },
            "data": [
                {
                    "order_id": i,
                    "user_id": fake.random_int(1, 25),
                    "product_id": fake.random_int(1, 50),
                    "quantity": fake.random_int(1, 10),
                    "total": float(fake.commerce.price()),
                    "order_date": fake.date_time_this_year().isoformat()
                }
                for i in range(1, 101)
            ]
        }
    
    def execute_query(self, query: str, database: str = "main") -> List[Dict[str, Any]]:
        """
        Execute a database query
        This is simplified - a real implementation would parse SQL
        """
        query_lower = query.lower().strip()
        
        # Handle SELECT queries
        if query_lower.startswith("select"):
            # Parse table name (simplified)
            if "from" in query_lower:
                parts = query_lower.split("from")
                if len(parts) > 1:
                    table_part = parts[1].strip().split()[0]
                    
                    if table_part in self.tables:
                        # Return some data (simplified - not parsing WHERE clauses)
                        return self.tables[table_part]["data"][:10]
            
            # Default: return first table data
            if self.tables:
                first_table = list(self.tables.keys())[0]
                return self.tables[first_table]["data"][:10]
        
        # Handle other queries
        elif query_lower.startswith("insert"):
            return [{"affected_rows": 1}]
        elif query_lower.startswith("update"):
            return [{"affected_rows": fake.random_int(1, 10)}]
        elif query_lower.startswith("delete"):
            return [{"affected_rows": fake.random_int(1, 5)}]
        
        return []
    
    def list_tables(self, database: str = "main") -> List[str]:
        """List all tables"""
        return list(self.tables.keys())
    
    def get_schema(self, table: str, database: str = "main") -> Dict[str, str]:
        """Get table schema"""
        if table in self.tables:
            return self.tables[table]["schema"]
        return {}


class VirtualUserManager:
    """
    Virtual user management system
    Handles authentication, user data, and API keys
    """
    
    def __init__(self):
        self.users = {}
        self.tokens = {}
        self.api_keys = {}
        self._initialize_default_users()
    
    def _initialize_default_users(self):
        """Create some default users"""
        self.users = {
            1: {
                "user_id": 1,
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin123",  # In production, this would be hashed
                "role": "admin",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        # Add some fake users
        for i in range(2, 11):
            self.users[i] = {
                "user_id": i,
                "username": fake.user_name(),
                "email": fake.email(),
                "password": fake.password(),
                "role": "user",
                "created_at": fake.date_time_this_year().isoformat()
            }
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user"""
        for user in self.users.values():
            if user["username"] == username and user["password"] == password:
                # Don't return password
                user_data = user.copy()
                del user_data["password"]
                return user_data
        return None
    
    def generate_token(self, user_id: int) -> str:
        """Generate authentication token"""
        token = secrets.token_urlsafe(32)
        self.tokens[token] = {
            "user_id": user_id,
            "created_at": time.time(),
            "expires_at": time.time() + 86400  # 24 hours
        }
        return token
    
    def verify_token(self, token: str) -> Optional[int]:
        """Verify authentication token"""
        if token in self.tokens:
            token_data = self.tokens[token]
            if token_data["expires_at"] > time.time():
                return token_data["user_id"]
        return None
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users"""
        users = []
        for user in self.users.values():
            user_data = user.copy()
            del user_data["password"]  # Never expose passwords
            users.append(user_data)
        return users
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if user_id in self.users:
            user_data = self.users[user_id].copy()
            del user_data["password"]
            return user_data
        return None
    
    def create_user(self, username: str, email: str, role: str = "user") -> Dict[str, Any]:
        """Create a new user"""
        user_id = max(self.users.keys()) + 1
        
        user = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password": secrets.token_urlsafe(16),  # Random password
            "role": role,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.users[user_id] = user
        
        user_data = user.copy()
        del user_data["password"]
        return user_data
    
    def generate_api_key(self, name: str, permissions: List[str]) -> Dict[str, Any]:
        """Generate an API key"""
        key = "sk_" + secrets.token_urlsafe(32)
        tracking_token = secrets.token_hex(8)
        
        api_key_data = {
            "key": key + "_tracked_" + tracking_token,
            "name": name,
            "permissions": permissions,
            "created_at": datetime.utcnow().isoformat(),
            "tracking_token": tracking_token
        }
        
        self.api_keys[key] = api_key_data
        
        return api_key_data
    
    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List all API keys"""
        return [
            {
                "name": data["name"],
                "key": data["key"][:20] + "...",  # Truncate for security
                "permissions": data["permissions"],
                "created_at": data["created_at"]
            }
            for data in self.api_keys.values()
        ]
