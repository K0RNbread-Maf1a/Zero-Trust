"""
Quantum Circuit Analysis Module
Analyzes quantum circuits for security, optimization, and correctness
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum
import re


class GateType(Enum):
    """Quantum gate types"""
    SINGLE_QUBIT = "single_qubit"
    TWO_QUBIT = "two_qubit"
    MULTI_QUBIT = "multi_qubit"
    MEASUREMENT = "measurement"
    RESET = "reset"
    BARRIER = "barrier"
    CUSTOM = "custom"


class SecurityIssue(Enum):
    """Security issues in quantum circuits"""
    UNINITIALIZED_QUBIT = "uninitialized_qubit"
    MISSING_RESET = "missing_reset"
    TIMING_LEAK = "timing_leak"
    INFORMATION_LEAK = "information_leak"
    INSUFFICIENT_ISOLATION = "insufficient_isolation"
    SIDE_CHANNEL_VULNERABLE = "side_channel_vulnerable"
    UNVERIFIED_GATE = "unverified_gate"
    QUANTUM_ERROR = "quantum_error"


class OptimizationOpportunity(Enum):
    """Circuit optimization opportunities"""
    REDUNDANT_GATES = "redundant_gates"
    COMMUTING_GATES = "commuting_gates"
    IDENTITY_REMOVAL = "identity_removal"
    GATE_MERGING = "gate_merging"
    CIRCUIT_DEPTH_REDUCTION = "circuit_depth_reduction"
    UNUSED_QUBITS = "unused_qubits"


@dataclass
class QuantumGate:
    """Representation of a quantum gate"""
    gate_type: GateType
    name: str
    qubits: List[int]
    control_qubits: List[int]
    parameters: List[float]
    duration: float  # nanoseconds
    fidelity: float  # 0.0 to 1.0
    timestamp: int  # cycle number
    is_parametric: bool = False
    can_swap: bool = True
    metadata: Dict = field(default_factory=dict)


@dataclass
class CircuitAnalysis:
    """Results of circuit analysis"""
    circuit_id: str
    num_qubits: int
    num_gates: int
    circuit_depth: int
    total_duration: float
    two_qubit_gate_count: int
    measurement_count: int
    security_issues: List[Dict]
    optimization_opportunities: List[Dict]
    correctness_issues: List[Dict]
    fidelity_estimate: float
    resource_usage: Dict
    analysis_timestamp: datetime


class QuantumCircuitAnalyzer:
    """Analyzes quantum circuits for security, optimization, and correctness"""

    def __init__(self):
        """Initialize circuit analyzer"""
        self.analyzed_circuits: Dict[str, CircuitAnalysis] = {}
        self.gate_database: Dict[str, Dict] = {}
        self.circuit_templates: Dict[str, List[QuantumGate]] = {}
        
        # Thresholds
        self.max_circuit_depth = 1000
        self.max_two_qubit_gates = 500
        self.min_fidelity_threshold = 0.95

    def parse_circuit(self, circuit_code: str, circuit_id: str) -> List[QuantumGate]:
        """Parse quantum circuit from code"""
        
        gates = []
        timestamp = 0

        # Simple regex-based parsing for common gate formats
        gate_pattern = r'(\w+)\s*\((.*?)\)\s*([a-zA-Z0-9,\s]+);'
        
        for match in re.finditer(gate_pattern, circuit_code):
            gate_name = match.group(1).lower()
            parameters_str = match.group(2)
            qubits_str = match.group(3)

            # Parse qubits
            qubits = [int(q.strip().split('[')[1].split(']')[0]) 
                     for q in qubits_str.split(',') if 'q[' in q]

            # Parse parameters
            parameters = []
            if parameters_str:
                try:
                    parameters = [float(p.strip()) for p in parameters_str.split(',')]
                except:
                    pass

            # Determine gate type
            if gate_name == 'measure':
                gate_type = GateType.MEASUREMENT
                duration = 100.0
            elif gate_name == 'reset':
                gate_type = GateType.RESET
                duration = 200.0
            elif gate_name in ['cx', 'cnot']:
                gate_type = GateType.TWO_QUBIT
                duration = 50.0
            elif gate_name in ['h', 'x', 'y', 'z', 'rx', 'ry', 'rz']:
                gate_type = GateType.SINGLE_QUBIT
                duration = 25.0
            else:
                gate_type = GateType.CUSTOM
                duration = 50.0

            gate = QuantumGate(
                gate_type=gate_type,
                name=gate_name,
                qubits=qubits,
                control_qubits=[],
                parameters=parameters,
                duration=duration,
                fidelity=0.999,
                timestamp=timestamp,
                is_parametric=len(parameters) > 0
            )

            gates.append(gate)
            timestamp += 1

        return gates

    def analyze_security(self, gates: List[QuantumGate], num_qubits: int) -> List[Dict]:
        """Analyze circuit for security issues"""
        
        issues = []
        initialized_qubits: Set[int] = set()
        used_qubits: Set[int] = set()

        # Track qubit initialization and usage
        for gate in gates:
            if gate.gate_type == GateType.RESET:
                initialized_qubits.update(gate.qubits)
            
            used_qubits.update(gate.qubits)

            # Check for uninitialized qubits
            for qubit in gate.qubits:
                if gate.gate_type != GateType.RESET and qubit not in initialized_qubits:
                    if gate.gate_type != GateType.MEASUREMENT:  # Measurement can initialize implicitly
                        issues.append({
                            "issue_type": SecurityIssue.UNINITIALIZED_QUBIT.value,
                            "severity": "high",
                            "qubit": qubit,
                            "gate_index": gates.index(gate),
                            "description": f"Qubit {qubit} used without initialization",
                            "recommendation": "Add explicit Reset or initialization gate"
                        })

            # Check for timing leaks
            if gate.gate_type in [GateType.SINGLE_QUBIT, GateType.TWO_QUBIT]:
                if gate.duration not in [25.0, 50.0]:  # Non-standard duration
                    issues.append({
                        "issue_type": SecurityIssue.TIMING_LEAK.value,
                        "severity": "medium",
                        "gate": gate.name,
                        "duration": gate.duration,
                        "description": f"Non-standard gate duration could leak timing information",
                        "recommendation": "Use standardized gate durations"
                    })

        # Check for missing resets at end
        if gates and gates[-1].gate_type != GateType.RESET:
            issues.append({
                "issue_type": SecurityIssue.MISSING_RESET.value,
                "severity": "medium",
                "description": "Circuit should end with Reset for clean state",
                "recommendation": "Add Reset gates at circuit end"
            })

        # Check for unused qubits
        unused = set(range(num_qubits)) - used_qubits
        if unused:
            issues.append({
                "issue_type": SecurityIssue.INSUFFICIENT_ISOLATION.value,
                "severity": "low",
                "unused_qubits": list(unused),
                "description": f"Unused qubits could leak information: {unused}",
                "recommendation": "Isolate or measure unused qubits"
            })

        return issues

    def analyze_optimization(self, gates: List[QuantumGate]) -> List[Dict]:
        """Analyze circuit for optimization opportunities"""
        
        opportunities = []

        # Check for commuting gates
        for i in range(len(gates) - 1):
            if self._gates_commute(gates[i], gates[i + 1]):
                opportunities.append({
                    "opportunity": OptimizationOpportunity.COMMUTING_GATES.value,
                    "gates": [gates[i].name, gates[i + 1].name],
                    "positions": [i, i + 1],
                    "description": "These gates commute and can be reordered",
                    "potential_savings": "Improved parallelization"
                })

        # Check for redundant gates (X X = I, H H = I)
        for i in range(len(gates) - 1):
            if gates[i].name == gates[i + 1].name:
                if gates[i].qubits == gates[i + 1].qubits:
                    if gates[i].name in ['x', 'y', 'z', 'h']:
                        opportunities.append({
                            "opportunity": OptimizationOpportunity.IDENTITY_REMOVAL.value,
                            "gates": [gates[i].name, gates[i + 1].name],
                            "positions": [i, i + 1],
                            "description": "Two identical gates cancel out",
                            "potential_savings": "Remove 2 gates"
                        })

        # Check for circuit depth reduction opportunities
        if len(gates) > 10:
            two_qubit_gates = [g for g in gates if g.gate_type == GateType.TWO_QUBIT]
            if len(two_qubit_gates) > 20:
                opportunities.append({
                    "opportunity": OptimizationOpportunity.CIRCUIT_DEPTH_REDUCTION.value,
                    "metric": f"{len(two_qubit_gates)} two-qubit gates detected",
                    "description": "Circuit has many two-qubit gates - consider optimization",
                    "potential_savings": f"Could reduce depth by {len(two_qubit_gates) // 2} layers"
                })

        return opportunities

    def analyze_correctness(self, gates: List[QuantumGate]) -> List[Dict]:
        """Analyze circuit for correctness issues"""
        
        issues = []

        # Check for valid gate sequences
        for i, gate in enumerate(gates):
            # Measurement shouldn't precede other gates on same qubit
            if gate.gate_type == GateType.MEASUREMENT:
                for j in range(i + 1, len(gates)):
                    if gate.qubits[0] in gates[j].qubits:
                        if gates[j].gate_type != GateType.MEASUREMENT:
                            issues.append({
                                "issue_type": "post_measurement_gate",
                                "severity": "high",
                                "gate_index": i,
                                "description": "Gates applied after measurement on same qubit",
                                "recommendation": "Reorder gates or use reset"
                            })
                            break

        # Check for qubit conflicts
        for i, gate in enumerate(gates):
            for j in range(i + 1, min(i + 3, len(gates))):
                if set(gate.qubits) & set(gates[j].qubits):
                    if not self._compatible_gates(gate, gates[j]):
                        issues.append({
                            "issue_type": "gate_conflict",
                            "severity": "medium",
                            "gates": [gate.name, gates[j].name],
                            "positions": [i, j],
                            "description": "Conflicting gate operations on same qubits"
                        })

        return issues

    def estimate_fidelity(self, gates: List[QuantumGate]) -> float:
        """Estimate circuit fidelity based on gate fidelities"""
        
        fidelity = 1.0
        for gate in gates:
            fidelity *= gate.fidelity

        return fidelity

    def analyze_resources(self, gates: List[QuantumGate], num_qubits: int) -> Dict:
        """Analyze resource usage"""
        
        single_qubit = len([g for g in gates if g.gate_type == GateType.SINGLE_QUBIT])
        two_qubit = len([g for g in gates if g.gate_type == GateType.TWO_QUBIT])
        measurements = len([g for g in gates if g.gate_type == GateType.MEASUREMENT])

        # Calculate circuit depth (critical path)
        depth = len(gates)  # Simplified

        total_duration = sum(g.duration for g in gates)

        return {
            "num_qubits": num_qubits,
            "total_gates": len(gates),
            "single_qubit_gates": single_qubit,
            "two_qubit_gates": two_qubit,
            "measurements": measurements,
            "circuit_depth": depth,
            "total_duration_ns": total_duration,
            "estimated_t_gates": int(two_qubit * 0.3),  # Rough estimate
            "memory_usage_mb": num_qubits * 0.001
        }

    def full_analysis(self, circuit_code: str, circuit_id: str, num_qubits: int) -> CircuitAnalysis:
        """Perform complete circuit analysis"""
        
        gates = self.parse_circuit(circuit_code, circuit_id)

        security_issues = self.analyze_security(gates, num_qubits)
        optimization_ops = self.analyze_optimization(gates)
        correctness_issues = self.analyze_correctness(gates)
        fidelity = self.estimate_fidelity(gates)
        resources = self.analyze_resources(gates, num_qubits)

        analysis = CircuitAnalysis(
            circuit_id=circuit_id,
            num_qubits=num_qubits,
            num_gates=len(gates),
            circuit_depth=resources["circuit_depth"],
            total_duration=resources["total_duration_ns"],
            two_qubit_gate_count=resources["two_qubit_gates"],
            measurement_count=resources["measurements"],
            security_issues=security_issues,
            optimization_opportunities=optimization_ops,
            correctness_issues=correctness_issues,
            fidelity_estimate=fidelity,
            resource_usage=resources,
            analysis_timestamp=datetime.now()
        )

        self.analyzed_circuits[circuit_id] = analysis
        return analysis

    def _gates_commute(self, gate1: QuantumGate, gate2: QuantumGate) -> bool:
        """Check if two gates commute"""
        
        # Different qubits always commute
        if not set(gate1.qubits) & set(gate2.qubits):
            return True

        # Pauli gates on same qubit
        pauli_gates = ['x', 'y', 'z']
        if gate1.name in pauli_gates and gate2.name in pauli_gates:
            return gate1.name == gate2.name

        return False

    def _compatible_gates(self, gate1: QuantumGate, gate2: QuantumGate) -> bool:
        """Check if gates are compatible"""
        
        # Measurement followed by non-measurement on same qubit is incompatible
        if gate1.gate_type == GateType.MEASUREMENT and gate2.gate_type != GateType.MEASUREMENT:
            if set(gate1.qubits) & set(gate2.qubits):
                return False

        return True

    def generate_report(self, circuit_id: str) -> Dict:
        """Generate analysis report"""
        
        if circuit_id not in self.analyzed_circuits:
            return {"error": "Circuit not found"}

        analysis = self.analyzed_circuits[circuit_id]

        return {
            "circuit_id": circuit_id,
            "timestamp": analysis.analysis_timestamp.isoformat(),
            "summary": {
                "num_qubits": analysis.num_qubits,
                "total_gates": analysis.num_gates,
                "circuit_depth": analysis.circuit_depth,
                "fidelity_estimate": f"{analysis.fidelity_estimate:.4f}",
                "status": "APPROVED" if not analysis.security_issues else "REVIEW_REQUIRED"
            },
            "security": {
                "issues_found": len(analysis.security_issues),
                "critical_issues": len([i for i in analysis.security_issues if i.get("severity") == "critical"]),
                "issues": analysis.security_issues[:5]  # Top 5
            },
            "optimization": {
                "opportunities": len(analysis.optimization_opportunities),
                "top_opportunities": analysis.optimization_opportunities[:5]
            },
            "correctness": {
                "issues_found": len(analysis.correctness_issues),
                "issues": analysis.correctness_issues[:5]
            },
            "resources": analysis.resource_usage
        }
