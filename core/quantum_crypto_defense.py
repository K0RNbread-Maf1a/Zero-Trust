"""
Quantum Cryptography Defense Module
Handles quantum key distribution, signature verification, and key management
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
from enum import Enum
import hmac
import base64

from core.orchestrator import OrchestrationContext


class QuantumKeyStatus(Enum):
    """Status of quantum keys"""
    GENERATED = "generated"
    ACTIVE = "active"
    COMPROMISED = "compromised"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class QuantumKeyMaterial:
    """Quantum key distribution material"""
    key_id: str
    protocol: str  # BB84, E91, decoy-state, etc.
    bits: List[int]
    bases: List[bool]
    sift_bits: List[int]
    final_key: str
    generation_time: datetime
    expiration_time: datetime
    status: QuantumKeyStatus = QuantumKeyStatus.GENERATED
    eavesdropping_detected: bool = False
    error_rate: float = 0.0
    source_ip: str = ""
    destination_ip: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class QuantumSignatureData:
    """Quantum digital signature data"""
    signature_id: str
    message: str
    signature: str
    quantum_signature: List[int]
    signer_id: str
    timestamp: datetime
    verified: bool = False
    verification_time: Optional[datetime] = None
    error_message: str = ""


@dataclass
class QuantumAuthChallenge:
    """Quantum authentication challenge-response"""
    challenge_id: str
    challenge_bits: List[int]
    response_bits: List[int]
    bases: List[bool]
    timestamp: datetime
    authenticated: bool = False
    confidence: float = 0.0


class QuantumCryptoDefense:
    """Quantum cryptography defense system"""

    def __init__(self, orchestrator: OrchestrationContext):
        """Initialize quantum crypto defense"""
        self.orchestrator = orchestrator
        self.active_keys: Dict[str, QuantumKeyMaterial] = {}
        self.signature_log: Dict[str, QuantumSignatureData] = {}
        self.auth_attempts: Dict[str, QuantumAuthChallenge] = {}
        self.key_rotation_interval = timedelta(hours=24)
        self.quantum_bit_error_threshold = 11.0  # BB84 threshold
        self.signature_verification_cache = {}

    def generate_quantum_key(
        self,
        key_id: str,
        protocol: str = "BB84",
        num_bits: int = 512,
        source_ip: str = "",
        destination_ip: str = ""
    ) -> QuantumKeyMaterial:
        """Generate quantum key material using BB84 protocol"""

        # Simulate quantum bit generation
        import random
        bits = [random.randint(0, 1) for _ in range(num_bits)]
        bases = [bool(random.randint(0, 1)) for _ in range(num_bits)]

        # Sift the key (keep bits where bases match - simulated)
        sift_bits = []
        sift_bases = []
        for i in range(num_bits):
            if bases[i]:  # Randomly keep ~50%
                sift_bits.append(bits[i])
                sift_bases.append(bases[i])

        # Generate final key from sifted bits
        final_key = ''.join(str(b) for b in sift_bits[:256])

        key_material = QuantumKeyMaterial(
            key_id=key_id,
            protocol=protocol,
            bits=bits,
            bases=bases,
            sift_bits=sift_bits,
            final_key=final_key,
            generation_time=datetime.now(),
            expiration_time=datetime.now() + self.key_rotation_interval,
            source_ip=source_ip,
            destination_ip=destination_ip,
            status=QuantumKeyStatus.ACTIVE
        )

        self.active_keys[key_id] = key_material
        return key_material

    def detect_eavesdropping(
        self,
        key_id: str,
        intercepted_bits: List[int],
        tolerance: float = 11.0
    ) -> Dict:
        """Detect eavesdropping (Eve) in quantum communication"""

        if key_id not in self.active_keys:
            return {
                "detected": False,
                "error_rate": 0.0,
                "error_message": "Key not found"
            }

        key_material = self.active_keys[key_id]
        total_bits = len(intercepted_bits)
        
        if total_bits == 0:
            return {"detected": False, "error_rate": 0.0}

        # Calculate quantum bit error rate (QBER)
        mismatches = sum(
            1 for i in range(total_bits)
            if key_material.bits[i] != intercepted_bits[i]
        )

        error_rate = (mismatches / total_bits) * 100

        detected = error_rate > tolerance
        key_material.eavesdropping_detected = detected
        key_material.error_rate = error_rate

        if detected:
            key_material.status = QuantumKeyStatus.COMPROMISED

        return {
            "detected": detected,
            "error_rate": error_rate,
            "threshold": tolerance,
            "mismatches": mismatches,
            "total_bits": total_bits,
            "key_id": key_id,
            "status": key_material.status.value
        }

    def sign_quantum_message(
        self,
        message: str,
        signer_id: str,
        signature_id: Optional[str] = None
    ) -> QuantumSignatureData:
        """Generate quantum digital signature"""

        if signature_id is None:
            signature_id = f"sig_{signer_id}_{int(datetime.now().timestamp() * 1000)}"

        # Create classical signature
        message_hash = hashlib.sha256(message.encode()).digest()
        classical_sig = base64.b64encode(message_hash).decode()

        # Simulate quantum signature
        import random
        quantum_sig = [random.randint(0, 1) for _ in range(256)]

        signature_data = QuantumSignatureData(
            signature_id=signature_id,
            message=message,
            signature=classical_sig,
            quantum_signature=quantum_sig,
            signer_id=signer_id,
            timestamp=datetime.now()
        )

        self.signature_log[signature_id] = signature_data
        return signature_data

    def verify_quantum_signature(
        self,
        signature_id: str,
        expected_quantum_sig: List[int],
        tolerance: float = 0.85
    ) -> Dict:
        """Verify quantum digital signature"""

        if signature_id not in self.signature_log:
            return {
                "verified": False,
                "error": "Signature not found",
                "confidence": 0.0
            }

        sig_data = self.signature_log[signature_id]

        # Compare quantum signatures
        matching_bits = sum(
            1 for i in range(min(len(sig_data.quantum_signature), len(expected_quantum_sig)))
            if sig_data.quantum_signature[i] == expected_quantum_sig[i]
        )

        total_bits = max(len(sig_data.quantum_signature), len(expected_quantum_sig))
        confidence = matching_bits / total_bits if total_bits > 0 else 0.0

        verified = confidence >= tolerance
        sig_data.verified = verified
        sig_data.verification_time = datetime.now()

        return {
            "verified": verified,
            "signature_id": signature_id,
            "confidence": confidence,
            "matching_bits": matching_bits,
            "total_bits": total_bits,
            "signer": sig_data.signer_id,
            "message_hash": hashlib.sha256(sig_data.message.encode()).hexdigest()[:16]
        }

    def quantum_authentication(
        self,
        challenge_id: str,
        challenge_bits: List[int],
        response_bits: List[int],
        bases: List[bool]
    ) -> QuantumAuthChallenge:
        """Perform quantum authentication protocol"""

        matching = sum(
            1 for i in range(min(len(challenge_bits), len(response_bits)))
            if challenge_bits[i] == response_bits[i]
        )

        total = max(len(challenge_bits), len(response_bits))
        confidence = matching / total if total > 0 else 0.0

        # Require >80% match for authentication
        authenticated = confidence > 0.80

        auth_challenge = QuantumAuthChallenge(
            challenge_id=challenge_id,
            challenge_bits=challenge_bits,
            response_bits=response_bits,
            bases=bases,
            timestamp=datetime.now(),
            authenticated=authenticated,
            confidence=confidence
        )

        self.auth_attempts[challenge_id] = auth_challenge
        return auth_challenge

    def rotate_quantum_keys(self) -> Dict:
        """Rotate expired quantum keys"""

        rotated = []
        expired = []
        now = datetime.now()

        for key_id, key_material in list(self.active_keys.items()):
            if key_material.expiration_time < now:
                key_material.status = QuantumKeyStatus.EXPIRED
                expired.append(key_id)
                
                # Generate new key
                new_key = self.generate_quantum_key(
                    f"{key_id}_rotated",
                    key_material.protocol,
                    len(key_material.bits),
                    key_material.source_ip,
                    key_material.destination_ip
                )
                rotated.append(new_key.key_id)

        return {
            "rotated": rotated,
            "expired": expired,
            "timestamp": datetime.now().isoformat(),
            "total_active_keys": len(self.active_keys)
        }

    def audit_quantum_operations(self) -> Dict:
        """Audit quantum cryptography operations"""

        return {
            "timestamp": datetime.now().isoformat(),
            "active_keys": len([k for k in self.active_keys.values() if k.status == QuantumKeyStatus.ACTIVE]),
            "compromised_keys": len([k for k in self.active_keys.values() if k.status == QuantumKeyStatus.COMPROMISED]),
            "eavesdropping_attempts": len([k for k in self.active_keys.values() if k.eavesdropping_detected]),
            "total_signatures": len(self.signature_log),
            "verified_signatures": len([s for s in self.signature_log.values() if s.verified]),
            "auth_attempts": len(self.auth_attempts),
            "successful_auth": len([a for a in self.auth_attempts.values() if a.authenticated]),
            "average_error_rate": sum(k.error_rate for k in self.active_keys.values()) / len(self.active_keys) if self.active_keys else 0.0
        }

    def generate_crypto_report(self) -> Dict:
        """Generate comprehensive cryptography report"""

        return {
            "report_type": "quantum_cryptography_audit",
            "timestamp": datetime.now().isoformat(),
            "status": "SECURE" if not any(k.eavesdropping_detected for k in self.active_keys.values()) else "COMPROMISED",
            "summary": self.audit_quantum_operations(),
            "key_rotation_status": self.rotate_quantum_keys(),
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations"""

        recommendations = []

        compromised = [k for k in self.active_keys.values() if k.status == QuantumKeyStatus.COMPROMISED]
        if compromised:
            recommendations.append(f"URGENT: {len(compromised)} compromised keys detected - initiate emergency key rotation")

        high_error = [k for k in self.active_keys.values() if k.error_rate > 15]
        if high_error:
            recommendations.append(f"WARNING: {len(high_error)} keys with high error rates - check quantum channels")

        old_keys = [k for k in self.active_keys.values() 
                   if datetime.now() - k.generation_time > timedelta(hours=20)]
        if old_keys:
            recommendations.append(f"INFO: {len(old_keys)} keys nearing rotation - schedule rotation soon")

        return recommendations
