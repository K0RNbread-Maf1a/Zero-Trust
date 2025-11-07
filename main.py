"""
Zero-Trust AI Defense System
Main entry point
"""
import sys
import json
import time
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from core.orchestrator import DefenseOrchestrator


def main():
    """Main entry point"""
    print("=" * 60)
    print("Zero-Trust AI Defense System")
    print("Fight Fire with Fire - AI/ML Attack Defense")
    print("=" * 60)
    print()
    
    # Initialize system
    base_dir = Path(__file__).parent
    config_dir = base_dir / "config"
    
    print("[*] Initializing defense system...")
    orchestrator = DefenseOrchestrator(str(config_dir), str(base_dir))
    print("[✓] System initialized successfully")
    print()
    
    # Example: Process a simulated attack
    print("[*] Testing with simulated SQL injection attack...")
    
    test_request = {
        "timestamp": time.time(),
        "ip": "203.0.113.42",
        "user_agent": "Mozilla/5.0 (bot)",
        "endpoint": "/api/users",
        "params": {"id": "1' OR '1'='1"},
        "headers": {"X-Forwarded-For": "203.0.113.42"},
        "content": "SELECT * FROM users WHERE id='1' OR '1'='1'",
        "session_id": "test_session_123"
    }
    
    response = orchestrator.process_request(test_request)
    
    print(f"[*] Response:")
    print(json.dumps(response, indent=2))
    print()
    
    # Show system status
    print("[*] System Status:")
    status = orchestrator.get_status()
    print(json.dumps(status, indent=2))
    print()
    
    print("[*] System is running. Use orchestrator.process_request() to process requests.")
    print("[*] Example integration:")
    print("""
    from main import DefenseOrchestrator
    
    orchestrator = DefenseOrchestrator("config", ".")
    
    # Process each incoming request
    request_data = {
        "timestamp": time.time(),
        "ip": "...",
        "user_agent": "...",
        "endpoint": "...",
        "params": {...},
        "headers": {...},
        "content": "...",
        "session_id": "..."
    }
    
    response = orchestrator.process_request(request_data)
    
    if response["action"] == "countermeasures":
        # Countermeasures deployed
        print(f"Threat detected: {response['threat_category']}")
        print(f"Risk level: {response['risk_level']}")
    """)
    
    return orchestrator


if __name__ == "__main__":
    orchestrator = main()
