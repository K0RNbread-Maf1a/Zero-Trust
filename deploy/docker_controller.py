"""
Docker Controller - Manages dynamic container isolation for attackers.

Capabilities:
1. Spawn isolated containers for high-risk attackers
2. Route attacker traffic to honeypot containers
3. Block attacker IPs via Pi-hole
4. Monitor container resource usage
"""

import docker
from typing import Dict, List, Optional
import time
import requests


class DockerController:
    """Controls Docker containers for attacker isolation."""
    
    def __init__(self, pihole_url: str = "http://pihole:80"):
        try:
            self.client = docker.from_env()
            self.pihole_url = pihole_url
            self.isolated_containers: Dict[str, str] = {}  # IP -> container_id
        except Exception as e:
            print(f"Warning: Docker not available: {e}")
            self.client = None
    
    def isolate_attacker(self, attacker_ip: str, threat_category: str, risk_score: int) -> Optional[str]:
        """
        Isolate an attacker in a dedicated honeypot container.
        
        Args:
            attacker_ip: IP address of attacker
            threat_category: Type of attack
            risk_score: Risk score (0-100)
            
        Returns:
            Container ID if successful, None otherwise
        """
        if not self.client:
            return None
        
        try:
            # Check if already isolated
            if attacker_ip in self.isolated_containers:
                return self.isolated_containers[attacker_ip]
            
            # Create isolated container
            container = self.client.containers.run(
                "ztai-honeypot:latest",
                detach=True,
                name=f"trap_{attacker_ip.replace('.', '_')}_{int(time.time())}",
                network="attacker_trap",
                environment={
                    "ATTACKER_IP": attacker_ip,
                    "THREAT_CATEGORY": threat_category,
                    "RISK_SCORE": str(risk_score)
                },
                labels={
                    "ztai.trapped": "true",
                    "ztai.attacker_ip": attacker_ip,
                    "ztai.threat": threat_category,
                    "ztai.timestamp": str(time.time())
                },
                mem_limit="256m",
                cpu_period=100000,
                cpu_quota=25000,  # 25% CPU
                restart_policy={"Name": "unless-stopped"}
            )
            
            self.isolated_containers[attacker_ip] = container.id
            print(f"[DOCKER] Isolated {attacker_ip} in container {container.short_id}")
            
            return container.id
            
        except Exception as e:
            print(f"[DOCKER] Failed to isolate {attacker_ip}: {e}")
            return None
    
    def block_via_pihole(self, domain_or_ip: str) -> bool:
        """
        Block a domain or IP via Pi-hole.
        
        Args:
            domain_or_ip: Domain name or IP to block
            
        Returns:
            True if successful
        """
        try:
            # Add to Pi-hole blacklist
            response = requests.post(
                f"{self.pihole_url}/admin/api.php",
                data={
                    "list": "black",
                    "add": domain_or_ip,
                    "token": self._get_pihole_token()
                },
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"[PIHOLE] Blocked {domain_or_ip}")
                return True
                
        except Exception as e:
            print(f"[PIHOLE] Failed to block {domain_or_ip}: {e}")
        
        return False
    
    def get_trapped_attackers(self) -> List[Dict]:
        """Get list of currently trapped attackers."""
        if not self.client:
            return []
        
        try:
            containers = self.client.containers.list(
                filters={"label": "ztai.trapped=true"}
            )
            
            trapped = []
            for container in containers:
                trapped.append({
                    "container_id": container.short_id,
                    "attacker_ip": container.labels.get("ztai.attacker_ip"),
                    "threat": container.labels.get("ztai.threat"),
                    "timestamp": float(container.labels.get("ztai.timestamp", 0)),
                    "status": container.status
                })
            
            return trapped
            
        except Exception as e:
            print(f"[DOCKER] Error getting trapped attackers: {e}")
            return []
    
    def release_attacker(self, attacker_ip: str) -> bool:
        """
        Release an attacker from isolation (stop and remove container).
        
        Args:
            attacker_ip: IP address to release
            
        Returns:
            True if successful
        """
        if not self.client or attacker_ip not in self.isolated_containers:
            return False
        
        try:
            container_id = self.isolated_containers[attacker_ip]
            container = self.client.containers.get(container_id)
            
            container.stop(timeout=5)
            container.remove()
            
            del self.isolated_containers[attacker_ip]
            print(f"[DOCKER] Released {attacker_ip} from isolation")
            
            return True
            
        except Exception as e:
            print(f"[DOCKER] Error releasing {attacker_ip}: {e}")
            return False
    
    def cleanup_old_traps(self, max_age_hours: int = 24):
        """Clean up trap containers older than specified hours."""
        if not self.client:
            return
        
        try:
            containers = self.client.containers.list(
                filters={"label": "ztai.trapped=true"}
            )
            
            current_time = time.time()
            cleaned = 0
            
            for container in containers:
                timestamp = float(container.labels.get("ztai.timestamp", 0))
                age_hours = (current_time - timestamp) / 3600
                
                if age_hours > max_age_hours:
                    container.stop(timeout=5)
                    container.remove()
                    cleaned += 1
            
            if cleaned > 0:
                print(f"[DOCKER] Cleaned up {cleaned} old trap containers")
                
        except Exception as e:
            print(f"[DOCKER] Error during cleanup: {e}")
    
    def get_container_stats(self, container_id: str) -> Optional[Dict]:
        """Get resource usage stats for a container."""
        if not self.client:
            return None
        
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0
            
            # Calculate memory usage
            mem_usage = stats["memory_stats"]["usage"]
            mem_limit = stats["memory_stats"]["limit"]
            mem_percent = (mem_usage / mem_limit) * 100.0 if mem_limit > 0 else 0
            
            return {
                "cpu_percent": cpu_percent,
                "memory_usage_mb": mem_usage / (1024 * 1024),
                "memory_limit_mb": mem_limit / (1024 * 1024),
                "memory_percent": mem_percent
            }
            
        except Exception as e:
            print(f"[DOCKER] Error getting stats: {e}")
            return None
    
    def _get_pihole_token(self) -> str:
        """Get Pi-hole API token (placeholder - should be configured)."""
        # In production, this would read from environment or config
        return ""
