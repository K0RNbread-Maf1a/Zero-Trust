"""Dashboard export utilities for monitoring systems."""

from typing import Dict, Any
import json


class DashboardExporter:
    """Exports metrics in formats compatible with monitoring dashboards."""
    
    def __init__(self, metrics_collector):
        self.metrics = metrics_collector
        
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # Counters
        for key, value in self.metrics.counters.items():
            metric_name = f"ztai_{key.replace(' ', '_')}"
            lines.append(f"# TYPE {metric_name} counter")
            lines.append(f"{metric_name} {value}")
        
        # Gauges  
        for key, value in self.metrics.gauges.items():
            metric_name = f"ztai_{key.replace(' ', '_')}"
            lines.append(f"# TYPE {metric_name} gauge")
            lines.append(f"{metric_name} {value}")
        
        return "\n".join(lines)
    
    def export_grafana_json(self) -> Dict[str, Any]:
        """Export dashboard configuration for Grafana."""
        summary = self.metrics.get_summary()
        
        return {
            "dashboard": {
                "title": "Zero-Trust AI Defense",
                "panels": [
                    {
                        "title": "Total Requests",
                        "type": "graph",
                        "targets": [{"expr": "ztai_total_requests"}]
                    },
                    {
                        "title": "Threats Detected",
                        "type": "graph",
                        "targets": [{"expr": "ztai_threats_detected"}]
                    },
                    {
                        "title": "Threat Breakdown",
                        "type": "piechart",
                        "data": summary['threat_breakdown']
                    },
                    {
                        "title": "Success Rate",
                        "type": "singlestat",
                        "value": summary['success_rate']
                    }
                ]
            }
        }
    
    def export_datadog(self) -> Dict[str, Any]:
        """Export metrics for Datadog."""
        summary = self.metrics.get_summary()
        
        metrics = []
        for key, value in self.metrics.counters.items():
            metrics.append({
                "metric": f"ztai.{key}",
                "type": "count",
                "points": [[int(self.metrics.metrics['requests'][-1]['timestamp'] if self.metrics.metrics['requests'] else 0), value]],
                "tags": ["environment:production", "service:zero-trust-defense"]
            })
        
        return {"series": metrics}
