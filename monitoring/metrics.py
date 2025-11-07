"""Metrics collection for defense system monitoring."""

import time
from typing import Dict, List, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json


class MetricsCollector:
    """Collects and aggregates defense system metrics."""
    
    def __init__(self, retention_hours: int = 24):
        """
        Initialize metrics collector.
        
        Args:
            retention_hours: How long to retain metrics in memory
        """
        self.retention_hours = retention_hours
        self.metrics = defaultdict(lambda: deque(maxlen=10000))
        
        # Metric types
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        
    def record_request(self, request_data: Dict[str, Any], response: Dict[str, Any]):
        """Record a processed request."""
        timestamp = time.time()
        
        self.metrics['requests'].append({
            'timestamp': timestamp,
            'ip': request_data.get('ip'),
            'endpoint': request_data.get('endpoint'),
            'action': response.get('action'),
            'risk_score': response.get('risk_score', 0),
            'risk_level': response.get('risk_level'),
            'threat_category': response.get('threat_category')
        })
        
        # Update counters
        self.counters['total_requests'] += 1
        if response.get('action') == 'countermeasures':
            self.counters['threats_detected'] += 1
            self.counters[f"threat_{response.get('threat_category', 'unknown')}"] += 1
        
    def record_countermeasure(self, scenario: str, intensity: str, success: bool, execution_time: float):
        """Record a countermeasure deployment."""
        timestamp = time.time()
        
        self.metrics['countermeasures'].append({
            'timestamp': timestamp,
            'scenario': scenario,
            'intensity': intensity,
            'success': success,
            'execution_time': execution_time
        })
        
        self.counters['total_countermeasures'] += 1
        if success:
            self.counters['successful_countermeasures'] += 1
        
        self.histograms['execution_times'].append(execution_time)
        
    def record_environment_creation(self, scenario: str, creation_time: float):
        """Record Poetry environment creation."""
        timestamp = time.time()
        
        self.metrics['environments'].append({
            'timestamp': timestamp,
            'scenario': scenario,
            'creation_time': creation_time
        })
        
        self.counters['environments_created'] += 1
        self.histograms['env_creation_times'].append(creation_time)
        
    def get_summary(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        now = time.time()
        hour_ago = now - 3600
        
        # Recent requests (last hour)
        recent_requests = [m for m in self.metrics['requests'] if m['timestamp'] > hour_ago]
        recent_threats = [r for r in recent_requests if r['risk_score'] > 80]
        
        return {
            'total_requests': self.counters['total_requests'],
            'total_threats': self.counters['threats_detected'],
            'total_countermeasures': self.counters['total_countermeasures'],
            'success_rate': (
                self.counters['successful_countermeasures'] / max(self.counters['total_countermeasures'], 1)
            ) * 100,
            'recent_hour': {
                'requests': len(recent_requests),
                'threats': len(recent_threats),
                'avg_risk_score': sum(r['risk_score'] for r in recent_threats) / max(len(recent_threats), 1)
            },
            'threat_breakdown': {
                k.replace('threat_', ''): v 
                for k, v in self.counters.items() 
                if k.startswith('threat_')
            },
            'avg_execution_time': (
                sum(self.histograms['execution_times']) / max(len(self.histograms['execution_times']), 1)
                if self.histograms['execution_times'] else 0
            )
        }
    
    def get_time_series(self, metric_name: str, window_minutes: int = 60) -> List[Dict[str, Any]]:
        """Get time series data for a metric."""
        now = time.time()
        cutoff = now - (window_minutes * 60)
        
        if metric_name not in self.metrics:
            return []
        
        return [m for m in self.metrics[metric_name] if m['timestamp'] > cutoff]
    
    def get_threat_trends(self, hours: int = 24) -> Dict[str, List[int]]:
        """Get threat trends over time."""
        now = time.time()
        cutoff = now - (hours * 3600)
        
        # Bucket by hour
        buckets = defaultdict(lambda: defaultdict(int))
        
        for request in self.metrics['requests']:
            if request['timestamp'] < cutoff:
                continue
            
            hour_bucket = int((request['timestamp'] - cutoff) / 3600)
            threat_cat = request.get('threat_category', 'none')
            
            if request['risk_score'] > 80:
                buckets[hour_bucket][threat_cat] += 1
        
        return dict(buckets)
    
    def export_json(self, filepath: str):
        """Export metrics to JSON file."""
        data = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'counters': dict(self.counters),
            'histograms': {k: list(v) for k, v in self.histograms.items()}
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff = time.time() - (self.retention_hours * 3600)
        
        for metric_type in self.metrics:
            while self.metrics[metric_type] and self.metrics[metric_type][0]['timestamp'] < cutoff:
                self.metrics[metric_type].popleft()
