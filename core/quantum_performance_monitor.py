"""
Quantum Performance Monitoring Module
Monitors quantum system performance, metrics, and resource usage
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import statistics


@dataclass
class QuantumMetrics:
    """Quantum system performance metrics"""
    timestamp: datetime
    qubit_count: int
    gate_count: int
    circuit_depth: int
    execution_time_ms: float
    fidelity: float
    qubits_available: int
    qubits_in_use: int
    memory_usage_mb: float
    cpu_usage_percent: float
    error_rate: float
    success_rate: float


@dataclass
class PerformanceBenchmark:
    """Performance benchmark result"""
    benchmark_id: str
    benchmark_type: str  # "latency", "throughput", "fidelity", "scalability"
    start_time: datetime
    end_time: datetime
    duration_ms: float
    result_value: float
    expected_value: float
    status: str  # "passed", "failed", "degraded"
    details: Dict = field(default_factory=dict)


class QuantumPerformanceMonitor:
    """Monitors quantum system performance"""

    def __init__(self, history_size: int = 10000):
        """Initialize performance monitor"""
        self.metrics_history: deque = deque(maxlen=history_size)
        self.benchmarks: Dict[str, PerformanceBenchmark] = {}
        self.alerts: List[Dict] = []
        self.resource_usage: Dict = {}
        
        # Performance thresholds
        self.latency_threshold_ms = 100.0
        self.throughput_threshold = 1000  # operations/second
        self.fidelity_threshold = 0.99
        self.error_rate_threshold = 0.01
        self.cpu_threshold_percent = 80.0
        self.memory_threshold_mb = 1024.0

    def record_metrics(
        self,
        qubit_count: int,
        gate_count: int,
        circuit_depth: int,
        execution_time_ms: float,
        fidelity: float,
        qubits_in_use: int,
        memory_usage_mb: float,
        cpu_usage_percent: float,
        error_rate: float
    ) -> QuantumMetrics:
        """Record quantum performance metrics"""

        success_rate = 1.0 - error_rate

        metrics = QuantumMetrics(
            timestamp=datetime.now(),
            qubit_count=qubit_count,
            gate_count=gate_count,
            circuit_depth=circuit_depth,
            execution_time_ms=execution_time_ms,
            fidelity=fidelity,
            qubits_available=qubit_count - qubits_in_use,
            qubits_in_use=qubits_in_use,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            error_rate=error_rate,
            success_rate=success_rate
        )

        self.metrics_history.append(metrics)

        # Check thresholds and generate alerts
        self._check_thresholds(metrics)

        return metrics

    def get_current_metrics(self) -> Optional[QuantumMetrics]:
        """Get current metrics"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_average_metrics(self, time_window_minutes: int = 5) -> Dict:
        """Get average metrics over time window"""

        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]

        if not recent_metrics:
            return {"error": "No metrics in time window"}

        return {
            "time_window_minutes": time_window_minutes,
            "samples": len(recent_metrics),
            "avg_execution_time_ms": statistics.mean(m.execution_time_ms for m in recent_metrics),
            "avg_fidelity": statistics.mean(m.fidelity for m in recent_metrics),
            "avg_error_rate": statistics.mean(m.error_rate for m in recent_metrics),
            "avg_memory_mb": statistics.mean(m.memory_usage_mb for m in recent_metrics),
            "avg_cpu_percent": statistics.mean(m.cpu_usage_percent for m in recent_metrics),
            "min_fidelity": min(m.fidelity for m in recent_metrics),
            "max_error_rate": max(m.error_rate for m in recent_metrics),
            "avg_success_rate": statistics.mean(m.success_rate for m in recent_metrics)
        }

    def benchmark_latency(
        self,
        circuit_operations: List[str],
        num_iterations: int = 100
    ) -> PerformanceBenchmark:
        """Benchmark operation latency"""

        benchmark_id = f"latency_{int(datetime.now().timestamp() * 1000)}"
        start_time = datetime.now()

        # Simulate execution
        import random
        execution_times = [random.gauss(50, 10) for _ in range(num_iterations)]
        avg_latency = statistics.mean(execution_times)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000

        status = "passed" if avg_latency < self.latency_threshold_ms else "degraded"

        benchmark = PerformanceBenchmark(
            benchmark_id=benchmark_id,
            benchmark_type="latency",
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration,
            result_value=avg_latency,
            expected_value=self.latency_threshold_ms,
            status=status,
            details={
                "operations": len(circuit_operations),
                "iterations": num_iterations,
                "min_latency_ms": min(execution_times),
                "max_latency_ms": max(execution_times),
                "std_dev_ms": statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            }
        )

        self.benchmarks[benchmark_id] = benchmark
        return benchmark

    def benchmark_throughput(
        self,
        num_operations: int = 10000,
        duration_seconds: int = 60
    ) -> PerformanceBenchmark:
        """Benchmark operation throughput"""

        benchmark_id = f"throughput_{int(datetime.now().timestamp() * 1000)}"
        start_time = datetime.now()

        # Simulate operations
        operations_completed = min(num_operations, self.throughput_threshold * duration_seconds)
        throughput = operations_completed / duration_seconds

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000

        status = "passed" if throughput >= self.throughput_threshold else "degraded"

        benchmark = PerformanceBenchmark(
            benchmark_id=benchmark_id,
            benchmark_type="throughput",
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration,
            result_value=throughput,
            expected_value=self.throughput_threshold,
            status=status,
            details={
                "operations_requested": num_operations,
                "operations_completed": int(operations_completed),
                "duration_seconds": duration_seconds
            }
        )

        self.benchmarks[benchmark_id] = benchmark
        return benchmark

    def benchmark_fidelity(
        self,
        num_circuits: int = 100,
        circuit_depth: int = 10
    ) -> PerformanceBenchmark:
        """Benchmark circuit fidelity"""

        benchmark_id = f"fidelity_{int(datetime.now().timestamp() * 1000)}"
        start_time = datetime.now()

        # Simulate fidelity measurements
        import random
        fidelities = [random.gauss(0.99, 0.01) for _ in range(num_circuits)]
        avg_fidelity = statistics.mean(max(0, min(1, f)) for f in fidelities)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000

        status = "passed" if avg_fidelity >= self.fidelity_threshold else "degraded"

        benchmark = PerformanceBenchmark(
            benchmark_id=benchmark_id,
            benchmark_type="fidelity",
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration,
            result_value=avg_fidelity,
            expected_value=self.fidelity_threshold,
            status=status,
            details={
                "circuits_tested": num_circuits,
                "circuit_depth": circuit_depth,
                "min_fidelity": min(max(0, f) for f in fidelities),
                "max_fidelity": min(1, max(fidelities)),
                "std_dev": statistics.stdev(max(0, min(1, f)) for f in fidelities) if len(fidelities) > 1 else 0
            }
        )

        self.benchmarks[benchmark_id] = benchmark
        return benchmark

    def monitor_resource_usage(
        self,
        qubit_count: int,
        qubits_in_use: int,
        memory_mb: float,
        cpu_percent: float
    ) -> Dict:
        """Monitor resource usage"""

        qubit_utilization = (qubits_in_use / qubit_count * 100) if qubit_count > 0 else 0

        resource_status = {
            "timestamp": datetime.now().isoformat(),
            "qubit_utilization": qubit_utilization,
            "memory_usage_mb": memory_mb,
            "memory_utilization": min(100, memory_mb / 1024 * 100),
            "cpu_usage_percent": cpu_percent,
            "status": self._get_resource_status(qubit_utilization, memory_mb, cpu_percent)
        }

        self.resource_usage = resource_status
        return resource_status

    def detect_performance_degradation(
        self,
        metrics_window: int = 100
    ) -> List[Dict]:
        """Detect performance degradation patterns"""

        issues = []

        if len(self.metrics_history) < metrics_window:
            return issues

        recent = list(self.metrics_history)[-metrics_window:]

        # Check for increasing latency trend
        latencies = [m.execution_time_ms for m in recent]
        if len(latencies) > 10:
            recent_latency = statistics.mean(latencies[-10:])
            earlier_latency = statistics.mean(latencies[:10])
            if recent_latency > earlier_latency * 1.2:  # 20% increase
                issues.append({
                    "issue": "latency_degradation",
                    "severity": "high",
                    "trend": f"Latency increased {((recent_latency/earlier_latency - 1) * 100):.1f}%",
                    "action": "Investigate system load and quantum processor performance"
                })

        # Check for decreasing fidelity trend
        fidelities = [m.fidelity for m in recent]
        if len(fidelities) > 10:
            recent_fidelity = statistics.mean(fidelities[-10:])
            earlier_fidelity = statistics.mean(fidelities[:10])
            if recent_fidelity < earlier_fidelity * 0.95:  # 5% decrease
                issues.append({
                    "issue": "fidelity_degradation",
                    "severity": "high",
                    "trend": f"Fidelity decreased from {earlier_fidelity:.4f} to {recent_fidelity:.4f}",
                    "action": "Recalibrate quantum gates and check for environmental noise"
                })

        # Check for increasing error rate trend
        error_rates = [m.error_rate for m in recent]
        if len(error_rates) > 10:
            recent_error = statistics.mean(error_rates[-10:])
            earlier_error = statistics.mean(error_rates[:10])
            if recent_error > earlier_error * 1.5:  # 50% increase
                issues.append({
                    "issue": "error_rate_increase",
                    "severity": "critical",
                    "trend": f"Error rate increased from {earlier_error*100:.2f}% to {recent_error*100:.2f}%",
                    "action": "URGENT: Check for qubit coherence issues and environmental interference"
                })

        return issues

    def get_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""

        current = self.get_current_metrics()
        average_5min = self.get_average_metrics(5)
        degradation_issues = self.detect_performance_degradation()

        recent_benchmarks = sorted(
            [b for b in self.benchmarks.values() 
             if b.end_time > datetime.now() - timedelta(hours=1)],
            key=lambda x: x.end_time,
            reverse=True
        )[:10]

        return {
            "report_type": "quantum_performance_monitor",
            "timestamp": datetime.now().isoformat(),
            "current_metrics": {
                "execution_time_ms": current.execution_time_ms if current else None,
                "fidelity": current.fidelity if current else None,
                "error_rate": current.error_rate if current else None,
                "success_rate": current.success_rate if current else None,
                "qubit_utilization": f"{(current.qubits_in_use / current.qubit_count * 100):.1f}%" if current else None,
                "memory_usage_mb": current.memory_usage_mb if current else None,
                "cpu_usage_percent": current.cpu_usage_percent if current else None
            },
            "average_5min": average_5min,
            "resource_usage": self.resource_usage,
            "degradation_issues": degradation_issues,
            "recent_benchmarks": [
                {
                    "benchmark_id": b.benchmark_id,
                    "type": b.benchmark_type,
                    "result": f"{b.result_value:.2f}",
                    "expected": f"{b.expected_value:.2f}",
                    "status": b.status
                }
                for b in recent_benchmarks
            ],
            "system_health": self._assess_system_health(),
            "recommendations": self._generate_performance_recommendations(degradation_issues)
        }

    def _check_thresholds(self, metrics: QuantumMetrics) -> None:
        """Check metrics against thresholds"""

        if metrics.execution_time_ms > self.latency_threshold_ms:
            self.alerts.append({
                "type": "high_latency",
                "severity": "warning",
                "value": metrics.execution_time_ms,
                "threshold": self.latency_threshold_ms,
                "timestamp": datetime.now().isoformat()
            })

        if metrics.fidelity < self.fidelity_threshold:
            self.alerts.append({
                "type": "low_fidelity",
                "severity": "warning",
                "value": metrics.fidelity,
                "threshold": self.fidelity_threshold,
                "timestamp": datetime.now().isoformat()
            })

        if metrics.error_rate > self.error_rate_threshold:
            self.alerts.append({
                "type": "high_error_rate",
                "severity": "critical",
                "value": metrics.error_rate,
                "threshold": self.error_rate_threshold,
                "timestamp": datetime.now().isoformat()
            })

    def _get_resource_status(self, qubit_util: float, memory: float, cpu: float) -> str:
        """Determine overall resource status"""

        if qubit_util > 90 or memory > self.memory_threshold_mb or cpu > self.cpu_threshold_percent:
            return "CRITICAL"
        elif qubit_util > 75 or memory > self.memory_threshold_mb * 0.8 or cpu > 60:
            return "WARNING"
        else:
            return "HEALTHY"

    def _assess_system_health(self) -> str:
        """Assess overall system health"""

        if not self.metrics_history:
            return "UNKNOWN"

        recent = list(self.metrics_history)[-100:]
        avg_fidelity = statistics.mean(m.fidelity for m in recent)
        avg_error = statistics.mean(m.error_rate for m in recent)

        if avg_fidelity < 0.95 or avg_error > 0.02:
            return "CRITICAL"
        elif avg_fidelity < 0.98 or avg_error > 0.01:
            return "DEGRADED"
        else:
            return "HEALTHY"

    def _generate_performance_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generate performance recommendations"""

        recommendations = []

        for issue in issues:
            if issue["issue"] == "latency_degradation":
                recommendations.append("Reduce circuit complexity or optimize gate sequences")
            elif issue["issue"] == "fidelity_degradation":
                recommendations.append("Recalibrate quantum gates and minimize environmental noise")
            elif issue["issue"] == "error_rate_increase":
                recommendations.append("URGENT: Verify qubit coherence and check for crosstalk")

        if not recommendations:
            recommendations.append("System performance is optimal")

        return recommendations
