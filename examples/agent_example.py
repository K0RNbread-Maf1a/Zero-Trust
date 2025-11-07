"""
Example script demonstrating Defense Agent usage.

This shows how to use the Defense Agent programmatically to:
1. Analyze threats
2. Check defense system status
3. Execute development tasks
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import DefenseAgent
from core.orchestrator import DefenseOrchestrator
import time


def main():
    print("=" * 60)
    print("Defense Agent Example")
    print("=" * 60)
    print()
    
    # Initialize defense system
    print("[1] Initializing defense system...")
    base_dir = Path(__file__).parent.parent
    config_dir = base_dir / "config"
    
    try:
        orchestrator = DefenseOrchestrator(str(config_dir), str(base_dir))
        print("✓ Defense system initialized")
    except Exception as e:
        print(f"✗ Could not initialize defense system: {e}")
        print("  Continuing without defense integration...")
        orchestrator = None
    
    # Initialize agent
    print("\n[2] Initializing Defense Agent...")
    agent = DefenseAgent(defense_orchestrator=orchestrator)
    print("✓ Agent initialized")
    
    # Example 1: Check defense status
    print("\n[3] Checking defense system status...")
    status = agent.get_defense_status()
    print(f"Status: {status}")
    
    # Example 2: Analyze a simulated threat
    if orchestrator:
        print("\n[4] Analyzing a simulated SQL injection threat...")
        threat_data = {
            "timestamp": time.time(),
            "ip": "203.0.113.42",
            "user_agent": "Mozilla/5.0 (bot)",
            "endpoint": "/api/users",
            "params": {"id": "1' OR '1'='1"},
            "headers": {"X-Forwarded-For": "203.0.113.42"},
            "content": "SELECT * FROM users WHERE id='1' OR '1'='1'",
            "session_id": "example_session"
        }
        
        result = agent.process_defense_request(threat_data)
        print(f"Threat Analysis Result:")
        print(f"  Action: {result.get('action')}")
        print(f"  Risk Level: {result.get('risk_level')}")
        print(f"  Risk Score: {result.get('risk_score')}")
        print(f"  Threat Category: {result.get('threat_category')}")
    
    # Example 3: Use agent conversationally
    print("\n[5] Using agent conversationally...")
    print("\nAsking agent to list Python files in core directory...")
    
    try:
        response = agent.run("list all Python files in the core directory")
        print("\nAgent Response:")
        print(response)
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Make sure ANTHROPIC_API_KEY is set in your environment")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
