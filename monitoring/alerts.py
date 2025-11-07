"""Alert management for defense system."""

from typing import Dict, List, Any, Callable
from collections import deque
import time


class AlertManager:
    """Manages alerts and notifications for security events."""
    
    def __init__(self):
        self.alerts = deque(maxlen=1000)
        self.alert_handlers: Dict[str, List[Callable]] = {}
        self.alert_thresholds = {
            'high_risk_score': 85,
            'burst_threshold': 10,  # requests per minute
            'failed_countermeasures': 3
        }
        
    def register_handler(self, alert_type: str, handler: Callable):
        """Register a handler for a specific alert type."""
        if alert_type not in self.alert_handlers:
            self.alert_handlers[alert_type] = []
        self.alert_handlers[alert_type].append(handler)
        
    def trigger_alert(self, alert_type: str, severity: str, message: str, context: Dict[str, Any] = None):
        """Trigger an alert."""
        alert = {
            'timestamp': time.time(),
            'type': alert_type,
            'severity': severity,  # info, warning, critical
            'message': message,
            'context': context or {}
        }
        
        self.alerts.append(alert)
        
        # Execute handlers
        if alert_type in self.alert_handlers:
            for handler in self.alert_handlers[alert_type]:
                try:
                    handler(alert)
                except Exception as e:
                    print(f"Alert handler error: {e}")
        
        # Log to file
        self._log_alert(alert)
        
    def check_threat_alert(self, risk_score: float, threat_category: str, ip: str):
        """Check if a threat should trigger an alert."""
        if risk_score >= self.alert_thresholds['high_risk_score']:
            self.trigger_alert(
                'high_risk_threat',
                'critical',
                f"High risk threat detected: {threat_category} from {ip}",
                {'risk_score': risk_score, 'category': threat_category, 'ip': ip}
            )
    
    def get_recent_alerts(self, minutes: int = 60, severity: str = None) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        cutoff = time.time() - (minutes * 60)
        alerts = [a for a in self.alerts if a['timestamp'] > cutoff]
        
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        return alerts
    
    def _log_alert(self, alert: Dict[str, Any]):
        """Log alert to file."""
        # This would write to logs/alerts.log in production
        pass
