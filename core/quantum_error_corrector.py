"""
Quantum Error Correction Module
Implements quantum error correction codes and detection
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class QECCode(Enum):
    """Quantum Error Correction codes"""
    SURFACE_CODE = "surface_code"
    STABILIZER_CODE = "stabilizer_code"
    TOPOLOGICAL_CODE = "topological_code"
    REPETITION_CODE = "repetition_code"
    HAMMING_CODE = "hamming_code"
    TORIC_CODE = "toric_code"


class ErrorType(Enum):
    """Types of quantum errors"""
    BIT_FLIP = "bit_flip"
    PHASE_FLIP = "phase_flip"
    AMPLITUDE_DAMPING = "amplitude_damping"
    PHASE_DAMPING = "phase_damping"
    DEPOLARIZATION = "depolarization"
    MEASUREMENT_ERROR = "measurement_error"


@dataclass
class SyndromeData:
    """Syndrome measurement results"""
    timestamp: datetime
    syndrome_bits: List[int]
    code_type: QECCode
    error_type: Optional[ErrorType]
    confidence: float  # 0.0 to 1.0
    corrected: bool = False
    correction_location: Optional[Tuple[int, int]] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class LogicalQubit:
    """Logical qubit encoded with error correction"""
    logical_id: str
    physical_qubits: List[int]
    code_type: QECCode
    data_qubits: List[int]
    syndrome_qubits: List[int]
    fidelity: float  # 0.0 to 1.0
    syndrome_history: List[SyndromeData] = field(default_factory=list)
    error_count: int = 0


class QuantumErrorCorrector:
    """Quantum Error Correction system"""

    def __init__(self):
        """Initialize QEC system"""
        self.logical_qubits: Dict[str, LogicalQubit] = {}
        self.error_history: List[Dict] = []
        self.correction_log: List[Dict] = []
        self.code_lookup: Dict = self._build_lookup_tables()

        # Thresholds
        self.error_threshold = 0.01  # 1% error threshold
        self.syndrome_measurement_fidelity = 0.99

    def encode_logical_qubit(
        self,
        logical_id: str,
        code_type: QECCode = QECCode.SURFACE_CODE,
        distance: int = 3
    ) -> LogicalQubit:
        """Encode a logical qubit using error correction code"""

        if code_type == QECCode.SURFACE_CODE:
            # Surface code: (2*distance - 1)^2 physical qubits
            num_physical = (2 * distance - 1) ** 2
        elif code_type == QECCode.REPETITION_CODE:
            # Repetition code: 2*distance - 1 physical qubits
            num_physical = 2 * distance - 1
        elif code_type == QECCode.HAMMING_CODE:
            # Hamming code: 2^distance - 1 physical qubits
            num_physical = (2 ** distance) - 1
        else:
            num_physical = 2 * distance

        physical_qubits = list(range(num_physical))
        
        # Separate data and syndrome qubits
        if code_type == QECCode.SURFACE_CODE:
            data_qubits = physical_qubits[::2]  # Every other qubit
            syndrome_qubits = physical_qubits[1::2]
        else:
            data_qubits = physical_qubits[:num_physical // 2]
            syndrome_qubits = physical_qubits[num_physical // 2:]

        logical_qubit = LogicalQubit(
            logical_id=logical_id,
            physical_qubits=physical_qubits,
            code_type=code_type,
            data_qubits=data_qubits,
            syndrome_qubits=syndrome_qubits,
            fidelity=0.99
        )

        self.logical_qubits[logical_id] = logical_qubit
        return logical_qubit

    def measure_syndrome(
        self,
        logical_id: str,
        syndrome_measurement: List[int]
    ) -> SyndromeData:
        """Measure error syndrome"""

        if logical_id not in self.logical_qubits:
            raise ValueError(f"Logical qubit {logical_id} not found")

        logical_qubit = self.logical_qubits[logical_id]

        # Determine error type from syndrome
        error_type, confidence = self._decode_syndrome(
            logical_qubit.code_type,
            syndrome_measurement
        )

        syndrome = SyndromeData(
            timestamp=datetime.now(),
            syndrome_bits=syndrome_measurement,
            code_type=logical_qubit.code_type,
            error_type=error_type,
            confidence=confidence
        )

        logical_qubit.syndrome_history.append(syndrome)

        if error_type:
            logical_qubit.error_count += 1
            self.error_history.append({
                "logical_id": logical_id,
                "error_type": error_type.value,
                "timestamp": datetime.now().isoformat(),
                "syndrome": syndrome_measurement
            })

        return syndrome

    def apply_correction(
        self,
        logical_id: str,
        syndrome_data: SyndromeData
    ) -> Dict:
        """Apply error correction"""

        if logical_id not in self.logical_qubits:
            return {"success": False, "error": "Logical qubit not found"}

        logical_qubit = self.logical_qubits[logical_id]

        # Determine correction operation
        correction_location, correction_operation = self._determine_correction(
            logical_qubit.code_type,
            syndrome_data
        )

        syndrome_data.corrected = True
        syndrome_data.correction_location = correction_location

        self.correction_log.append({
            "logical_id": logical_id,
            "timestamp": datetime.now().isoformat(),
            "syndrome": syndrome_data.syndrome_bits,
            "error_type": syndrome_data.error_type.value if syndrome_data.error_type else None,
            "correction": correction_operation
        })

        return {
            "success": True,
            "logical_id": logical_id,
            "error_type": syndrome_data.error_type.value if syndrome_data.error_type else None,
            "location": correction_location,
            "operation": correction_operation,
            "confidence": syndrome_data.confidence
        }

    def detect_logical_error(
        self,
        logical_id: str,
        repeated_syndromes: List[List[int]]
    ) -> Dict:
        """Detect uncorrectable logical errors"""

        if logical_id not in self.logical_qubits:
            return {"logical_error": False}

        logical_qubit = self.logical_qubits[logical_id]

        # Multiple identical syndromes indicate possible logical error
        unique_syndromes = set(tuple(s) for s in repeated_syndromes)
        
        if len(unique_syndromes) == 1:
            # Same syndrome repeatedly - possible logical error
            return {
                "logical_error": True,
                "logical_id": logical_id,
                "syndrome_pattern": repeated_syndromes[0],
                "error_count": len(repeated_syndromes),
                "severity": "high",
                "recommendation": "Reinitialize or apply corrective action"
            }

        return {"logical_error": False}

    def calculate_code_distance(
        self,
        code_type: QECCode,
        num_physical_qubits: int
    ) -> int:
        """Calculate code distance from physical qubits"""

        if code_type == QECCode.SURFACE_CODE:
            # Surface code: distance = sqrt((n+1)/2)
            distance = int(((num_physical_qubits + 1) / 2) ** 0.5)
        elif code_type == QECCode.REPETITION_CODE:
            # Repetition code: distance = (n+1)/2
            distance = (num_physical_qubits + 1) // 2
        else:
            distance = max(1, int(num_physical_qubits ** 0.5))

        return distance

    def estimate_logical_error_rate(
        self,
        physical_error_rate: float,
        code_distance: int,
        threshold: float = 0.01
    ) -> float:
        """Estimate logical error rate after correction"""

        # Simplified formula: Logical error rate ≈ (physical_error_rate / threshold)^code_distance
        if physical_error_rate < threshold:
            logical_error_rate = (physical_error_rate / threshold) ** code_distance
        else:
            logical_error_rate = physical_error_rate

        return logical_error_rate

    def get_qec_status(self, logical_id: str) -> Dict:
        """Get QEC status for a logical qubit"""

        if logical_id not in self.logical_qubits:
            return {"error": "Logical qubit not found"}

        logical_qubit = self.logical_qubits[logical_id]

        recent_syndromes = logical_qubit.syndrome_history[-10:] if logical_qubit.syndrome_history else []
        recent_errors = [e for e in self.error_history if e["logical_id"] == logical_id][-10:]

        return {
            "logical_id": logical_id,
            "code_type": logical_qubit.code_type.value,
            "fidelity": logical_qubit.fidelity,
            "total_errors": logical_qubit.error_count,
            "total_physical_qubits": len(logical_qubit.physical_qubits),
            "code_distance": self.calculate_code_distance(
                logical_qubit.code_type,
                len(logical_qubit.physical_qubits)
            ),
            "recent_error_rate": len(recent_errors) / max(len(recent_syndromes), 1),
            "syndromes_measured": len(logical_qubit.syndrome_history),
            "status": "HEALTHY" if logical_qubit.error_count < 5 else "DEGRADED" if logical_qubit.error_count < 20 else "CRITICAL"
        }

    def generate_qec_report(self) -> Dict:
        """Generate comprehensive QEC report"""

        total_logical_qubits = len(self.logical_qubits)
        total_errors = len(self.error_history)
        total_corrections = len(self.correction_log)

        if total_errors > 0:
            correction_rate = total_corrections / total_errors
        else:
            correction_rate = 1.0

        return {
            "report_type": "quantum_error_correction",
            "timestamp": datetime.now().isoformat(),
            "total_logical_qubits": total_logical_qubits,
            "total_errors_detected": total_errors,
            "total_corrections_applied": total_corrections,
            "correction_success_rate": correction_rate,
            "qubits_status": [
                self.get_qec_status(qid) 
                for qid in self.logical_qubits.keys()
            ],
            "error_types_detected": self._count_error_types(),
            "average_code_distance": self._calculate_average_code_distance(),
            "health_status": "EXCELLENT" if correction_rate > 0.95 else "GOOD" if correction_rate > 0.80 else "DEGRADED",
            "recommendations": self._generate_qec_recommendations(correction_rate)
        }

    def _decode_syndrome(
        self,
        code_type: QECCode,
        syndrome: List[int]
    ) -> Tuple[Optional[ErrorType], float]:
        """Decode syndrome to determine error type"""

        if not syndrome or sum(syndrome) == 0:
            return None, 1.0  # No error

        # Simplified error type determination
        ones_count = sum(syndrome)

        if ones_count == 1:
            error_type = ErrorType.BIT_FLIP
            confidence = 0.8
        elif ones_count == 2:
            error_type = ErrorType.PHASE_FLIP
            confidence = 0.7
        elif ones_count > 2:
            error_type = ErrorType.DEPOLARIZATION
            confidence = 0.6
        else:
            error_type = ErrorType.MEASUREMENT_ERROR
            confidence = 0.5

        return error_type, confidence

    def _determine_correction(
        self,
        code_type: QECCode,
        syndrome_data: SyndromeData
    ) -> Tuple[Optional[Tuple[int, int]], str]:
        """Determine correction operation from syndrome"""

        if not syndrome_data.error_type:
            return None, "no_correction"

        # Simplified correction location
        correction_qubit = sum(syndrome_data.syndrome_bits) % len(syndrome_data.syndrome_bits)

        if syndrome_data.error_type == ErrorType.BIT_FLIP:
            operation = f"X({correction_qubit})"
        elif syndrome_data.error_type == ErrorType.PHASE_FLIP:
            operation = f"Z({correction_qubit})"
        else:
            operation = f"Reset({correction_qubit})"

        return (correction_qubit, 0), operation

    def _count_error_types(self) -> Dict[str, int]:
        """Count errors by type"""

        counts = {}
        for error in self.error_history:
            error_type = error["error_type"]
            counts[error_type] = counts.get(error_type, 0) + 1

        return counts

    def _calculate_average_code_distance(self) -> float:
        """Calculate average code distance"""

        distances = []
        for logical_qubit in self.logical_qubits.values():
            distance = self.calculate_code_distance(
                logical_qubit.code_type,
                len(logical_qubit.physical_qubits)
            )
            distances.append(distance)

        return sum(distances) / len(distances) if distances else 0.0

    def _generate_qec_recommendations(self, correction_rate: float) -> List[str]:
        """Generate QEC recommendations"""

        recommendations = []

        if correction_rate < 0.80:
            recommendations.append("Low correction success rate - check physical error sources")

        if len(self.logical_qubits) > 100:
            recommendations.append("Large number of logical qubits - consider topology optimization")

        high_error_qubits = [
            qid for qid in self.logical_qubits
            if self.get_qec_status(qid)["status"] == "CRITICAL"
        ]

        if high_error_qubits:
            recommendations.append(f"Critical qubits detected: {high_error_qubits} - urgent recalibration needed")

        return recommendations if recommendations else ["All systems nominal"]

    def _build_lookup_tables(self) -> Dict:
        """Build syndrome-to-correction lookup tables"""

        return {
            "surface_code": {},
            "repetition_code": {},
            "hamming_code": {}
        }
