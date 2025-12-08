"""
Quantum Anomaly Detection Module
Detects anomalous quantum operations and patterns
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import numpy as np
from enum import Enum

from core.orchestrator import OrchestrationContext


class AnomalyType(Enum):
    """Types of quantum anomalies"""
    STATE_COLLAPSE = "state_collapse"
    DECOHERENCE = "decoherence"
    GATE_ERROR = "gate_error"
    MEASUREMENT_BIAS = "measurement_bias"
    ENTANGLEMENT_LOSS = "entanglement_loss"
    FREQUENCY_SHIFT = "frequency_shift"
    PHASE_DRIFT = "phase_drift"
    RABI_ERROR = "rabi_error"
    T1_RELAXATION = "t1_relaxation"
    T2_DEPHASING = "t2_dephasing"


@dataclass
class QuantumAnomalyAlert:
    """Alert for detected quantum anomaly"""
    alert_id: str
    anomaly_type: AnomalyType
    severity: str  # critical, high, medium, low
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    qubit_indices: List[int]
    metric_value: float
    threshold: float
    description: str
    affected_operation: str
    recommended_action: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class QuantumSignalMetrics:
    """Quantum signal quality metrics"""
    fidelity: float  # 0.0 to 1.0
    coherence_time: float  # nanoseconds
    gate_error_rate: float  # percentage
    measurement_error_rate: float  # percentage
    readout_fidelity: float  # 0.0 to 1.0
    entanglement_fidelity: float  # 0.0 to 1.0
    timing_accuracy: float  # nanoseconds
    phase_stability: float  # 0.0 to 1.0


class QuantumAnomalyDetector:
    """Detects anomalies in quantum operations"""

    def __init__(self, orchestrator: OrchestrationContext):
        """Initialize anomaly detector"""
        self.orchestrator = orchestrator
        self.alerts: Dict[str, QuantumAnomalyAlert] = {}
        self.signal_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.baseline_metrics: Dict[str, QuantumSignalMetrics] = {}
        self.anomaly_patterns: List[Dict] = []
        
        # Thresholds
        self.fidelity_threshold = 0.99
        self.coherence_threshold = 1000  # nanoseconds
        self.gate_error_threshold = 0.1  # 0.1%
        self.measurement_error_threshold = 0.2  # 0.2%

    def establish_baseline(self, operation_name: str, metrics: QuantumSignalMetrics) -> Dict:
        """Establish baseline metrics for an operation"""
        
        self.baseline_metrics[operation_name] = metrics
        
        return {
            "operation": operation_name,
            "baseline_established": True,
            "metrics": {
                "fidelity": metrics.fidelity,
                "coherence_time": metrics.coherence_time,
                "gate_error_rate": metrics.gate_error_rate,
                "measurement_error_rate": metrics.measurement_error_rate,
                "readout_fidelity": metrics.readout_fidelity
            }
        }

    def detect_fidelity_degradation(
        self,
        operation_name: str,
        current_fidelity: float,
        qubit_indices: List[int]
    ) -> Optional[QuantumAnomalyAlert]:
        """Detect quantum operation fidelity degradation"""
        
        if operation_name not in self.baseline_metrics:
            return None

        baseline = self.baseline_metrics[operation_name]
        degradation = baseline.fidelity - current_fidelity

        if current_fidelity < self.fidelity_threshold:
            severity = "critical" if current_fidelity < 0.95 else "high"
            confidence = min(1.0, degradation * 10)

            alert = QuantumAnomalyAlert(
                alert_id=f"fidelity_{operation_name}_{int(datetime.now().timestamp() * 1000)}",
                anomaly_type=AnomalyType.GATE_ERROR,
                severity=severity,
                confidence=confidence,
                timestamp=datetime.now(),
                qubit_indices=qubit_indices,
                metric_value=current_fidelity,
                threshold=self.fidelity_threshold,
                description=f"Fidelity degradation detected: {current_fidelity:.4f} (baseline: {baseline.fidelity:.4f})",
                affected_operation=operation_name,
                recommended_action="Recalibrate gates and check for environmental noise"
            )

            self.alerts[alert.alert_id] = alert
            return alert

        return None

    def detect_decoherence(
        self,
        qubit_index: int,
        measurement_times: List[float],
        measured_values: List[int]
    ) -> Optional[QuantumAnomalyAlert]:
        """Detect qubit decoherence"""
        
        if len(measured_values) < 10:
            return None

        # Analyze decay pattern
        ones_count = [sum(measured_values[i:i+10]) for i in range(0, len(measured_values)-9, 10)]
        
        if len(ones_count) > 1:
            decay_rate = (ones_count[0] - ones_count[-1]) / max(ones_count[0], 1)
            
            if decay_rate > 0.3:  # >30% decay indicates decoherence
                alert = QuantumAnomalyAlert(
                    alert_id=f"decoherence_q{qubit_index}_{int(datetime.now().timestamp() * 1000)}",
                    anomaly_type=AnomalyType.DECOHERENCE,
                    severity="high",
                    confidence=min(1.0, decay_rate),
                    timestamp=datetime.now(),
                    qubit_indices=[qubit_index],
                    metric_value=decay_rate,
                    threshold=0.3,
                    description=f"Decoherence detected on qubit {qubit_index}: {decay_rate*100:.1f}% decay",
                    affected_operation="measurement",
                    recommended_action="Increase coherence time or reduce operation duration"
                )

                self.alerts[alert.alert_id] = alert
                return alert

        return None

    def detect_measurement_bias(
        self,
        qubit_index: int,
        measurements: List[int],
        window_size: int = 100
    ) -> Optional[QuantumAnomalyAlert]:
        """Detect measurement bias (0 or 1 bias)"""
        
        if len(measurements) < window_size:
            return None

        recent = measurements[-window_size:]
        ones_ratio = sum(recent) / len(recent)

        # Expected ~50% ones, alert if >70% or <30%
        if ones_ratio > 0.7 or ones_ratio < 0.3:
            bias_type = "ONE-bias" if ones_ratio > 0.7 else "ZERO-bias"
            alert = QuantumAnomalyAlert(
                alert_id=f"measure_bias_q{qubit_index}_{int(datetime.now().timestamp() * 1000)}",
                anomaly_type=AnomalyType.MEASUREMENT_BIAS,
                severity="medium",
                confidence=abs(ones_ratio - 0.5) * 2,
                timestamp=datetime.now(),
                qubit_indices=[qubit_index],
                metric_value=ones_ratio,
                threshold=0.5,
                description=f"Measurement bias on qubit {qubit_index}: {bias_type} ({ones_ratio*100:.1f}%)",
                affected_operation="readout",
                recommended_action="Check measurement apparatus calibration and environmental noise"
            )

            self.alerts[alert.alert_id] = alert
            return alert

        return None

    def detect_entanglement_loss(
        self,
        bell_measurements: List[Tuple[int, int]],
        correlation_threshold: float = 0.8
    ) -> Optional[QuantumAnomalyAlert]:
        """Detect loss of entanglement in Bell pairs"""
        
        if len(bell_measurements) < 10:
            return None

        # Calculate correlation between qubits
        q1_values = [m[0] for m in bell_measurements]
        q2_values = [m[1] for m in bell_measurements]

        # For maximally entangled state, values should be correlated
        correlation = 1.0
        if len(q1_values) > 1:
            try:
                correlation = np.corrcoef(q1_values, q2_values)[0, 1]
            except:
                correlation = 0.0

        if correlation < correlation_threshold:
            alert = QuantumAnomalyAlert(
                alert_id=f"entangle_loss_{int(datetime.now().timestamp() * 1000)}",
                anomaly_type=AnomalyType.ENTANGLEMENT_LOSS,
                severity="critical",
                confidence=1.0 - correlation,
                timestamp=datetime.now(),
                qubit_indices=[0, 1],  # Bell pair
                metric_value=correlation,
                threshold=correlation_threshold,
                description=f"Entanglement loss detected: correlation = {correlation:.4f}",
                affected_operation="bell_measurement",
                recommended_action="Reinitialize Bell state and check isolation"
            )

            self.alerts[alert.alert_id] = alert
            return alert

        return None

    def detect_phase_drift(
        self,
        phase_measurements: List[float],
        drift_threshold: float = 0.1
    ) -> Optional[QuantumAnomalyAlert]:
        """Detect phase drift in quantum operations"""
        
        if len(phase_measurements) < 5:
            return None

        # Calculate phase drift rate
        phase_differences = [abs(phase_measurements[i] - phase_measurements[i-1]) 
                           for i in range(1, len(phase_measurements))]
        avg_drift = statistics.mean(phase_differences)

        if avg_drift > drift_threshold:
            alert = QuantumAnomalyAlert(
                alert_id=f"phase_drift_{int(datetime.now().timestamp() * 1000)}",
                anomaly_type=AnomalyType.PHASE_DRIFT,
                severity="medium",
                confidence=min(1.0, avg_drift / 0.5),
                timestamp=datetime.now(),
                qubit_indices=list(range(len(phase_measurements))),
                metric_value=avg_drift,
                threshold=drift_threshold,
                description=f"Phase drift detected: {avg_drift:.4f} rad/operation",
                affected_operation="phase_evolution",
                recommended_action="Recalibrate RF source and check thermal stability"
            )

            self.alerts[alert.alert_id] = alert
            return alert

        return None

    def detect_gate_error_accumulation(
        self,
        operation_sequence: List[str],
        error_rates: List[float]
    ) -> List[QuantumAnomalyAlert]:
        """Detect gate error accumulation"""
        
        alerts = []
        cumulative_error = 1.0

        for i, (op, error_rate) in enumerate(zip(operation_sequence, error_rates)):
            cumulative_error *= (1 - error_rate)
            fidelity = cumulative_error

            if fidelity < self.fidelity_threshold:
                alert = QuantumAnomalyAlert(
                    alert_id=f"gate_accum_{i}_{int(datetime.now().timestamp() * 1000)}",
                    anomaly_type=AnomalyType.GATE_ERROR,
                    severity="high",
                    confidence=1.0 - fidelity,
                    timestamp=datetime.now(),
                    qubit_indices=[],
                    metric_value=error_rate,
                    threshold=self.gate_error_threshold,
                    description=f"Gate error accumulation: operation {i} ({op}) fidelity = {fidelity:.4f}",
                    affected_operation=op,
                    recommended_action="Optimize circuit depth or improve gate calibration"
                )

                self.alerts[alert.alert_id] = alert
                alerts.append(alert)

        return alerts

    def analyze_anomaly_patterns(self) -> List[Dict]:
        """Analyze patterns in detected anomalies"""
        
        patterns = []

        # Group alerts by type
        by_type = defaultdict(list)
        for alert in self.alerts.values():
            by_type[alert.anomaly_type].append(alert)

        # Find patterns
        for anomaly_type, type_alerts in by_type.items():
            if len(type_alerts) > 3:
                # Recurring anomaly pattern
                patterns.append({
                    "pattern": f"Recurring {anomaly_type.value}",
                    "occurrences": len(type_alerts),
                    "severity": type_alerts[0].severity,
                    "first_detected": min(a.timestamp for a in type_alerts).isoformat(),
                    "last_detected": max(a.timestamp for a in type_alerts).isoformat(),
                    "recommendation": f"Investigate root cause of {anomaly_type.value}"
                })

        self.anomaly_patterns = patterns
        return patterns

    def get_anomaly_report(self) -> Dict:
        """Generate comprehensive anomaly report"""
        
        critical_alerts = [a for a in self.alerts.values() if a.severity == "critical"]
        high_alerts = [a for a in self.alerts.values() if a.severity == "high"]
        medium_alerts = [a for a in self.alerts.values() if a.severity == "medium"]

        return {
            "report_type": "quantum_anomaly_detection",
            "timestamp": datetime.now().isoformat(),
            "total_alerts": len(self.alerts),
            "critical_count": len(critical_alerts),
            "high_count": len(high_alerts),
            "medium_count": len(medium_alerts),
            "status": "CRITICAL" if critical_alerts else "HEALTHY" if not high_alerts else "WARNING",
            "recent_alerts": [
                {
                    "id": a.alert_id,
                    "type": a.anomaly_type.value,
                    "severity": a.severity,
                    "description": a.description,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in sorted(self.alerts.values(), key=lambda x: x.timestamp, reverse=True)[:10]
            ],
            "patterns": self.analyze_anomaly_patterns(),
            "recommendations": self._generate_recommendations(critical_alerts, high_alerts)
        }

    def _generate_recommendations(self, critical_alerts: List, high_alerts: List) -> List[str]:
        """Generate recommendations based on detected anomalies"""
        
        recommendations = []

        if critical_alerts:
            recommendations.append(f"URGENT: {len(critical_alerts)} critical anomalies detected - immediate intervention required")

        if high_alerts:
            recommendations.append(f"WARNING: {len(high_alerts)} high-severity anomalies - schedule maintenance soon")

        # Type-specific recommendations
        decoherence_alerts = [a for a in critical_alerts + high_alerts if a.anomaly_type == AnomalyType.DECOHERENCE]
        if decoherence_alerts:
            recommendations.append("Improve cryogenic system performance and isolation")

        entanglement_alerts = [a for a in critical_alerts + high_alerts if a.anomaly_type == AnomalyType.ENTANGLEMENT_LOSS]
        if entanglement_alerts:
            recommendations.append("Check Bell pair initialization and environmental noise")

        return recommendations
