"""
Matrix Product State Engine
Quantum circuit execution using tensor network methods
"""
import numpy as np
from typing import Dict, List, Optional
import psutil

try:
    import quimb.tensor as qtn
    QUIMB_AVAILABLE = True
except ImportError:
    QUIMB_AVAILABLE = False


class MPSEngine:
    """
    Matrix Product State engine.
    Uses statevector for <= 20 qubits (exact), MPS for larger (approximate).
    Falls back to statevector automatically if quimb fails.
    """

    def __init__(self, num_qubits: int, max_bond: int = 256, cutoff: float = 1e-10):
        self.num_qubits = num_qubits
        self.max_bond = max_bond
        self.cutoff = cutoff
        self.gate_count = 0
        self.depth = 0
        self.current_bond_dim = 1
        self.memory_usage_mb = 0

        self._use_statevector = (not QUIMB_AVAILABLE) or (num_qubits <= 20)
        self._state = np.zeros(2 ** num_qubits, dtype=complex)
        self._state[0] = 1.0

        if not self._use_statevector:
            try:
                self.mps = qtn.MPS_computational_state('0' * num_qubits)
            except Exception:
                self._use_statevector = True

    # ── helpers ──────────────────────────────────────────────────────────────

    def _sv(self) -> np.ndarray:
        """Return current state as vector"""
        if self._use_statevector:
            return self._state
        try:
            return self.mps.to_dense()
        except Exception:
            self._use_statevector = True
            return self._state

    def _apply_sv_single(self, gate: np.ndarray, qubit: int):
        n = self.num_qubits
        # Reshape state to (2,)*n, contract on qubit axis
        psi = self._state.reshape([2] * n)
        psi = np.tensordot(gate, psi, axes=[[1], [qubit]])
        # tensordot puts new axis first → move back
        axes = list(range(1, qubit + 1)) + [0] + list(range(qubit + 1, n))
        self._state = psi.transpose(axes).reshape(2 ** n)

    def _apply_sv_two(self, gate: np.ndarray, q1: int, q2: int):
        n = self.num_qubits
        psi = self._state.reshape([2] * n)
        gate_r = gate.reshape(2, 2, 2, 2)
        # Contract on [q1, q2]
        psi = np.tensordot(gate_r, psi, axes=[[2, 3], [q1, q2]])
        # psi has shape (2,2, other dims...), new q1,q2 at positions 0,1
        # Build correct transpose
        other = [i for i in range(n) if i != q1 and i != q2]
        # current order: 0=new_q1, 1=new_q2, then other axes in original order
        inv = [None] * n
        inv[q1] = 0
        inv[q2] = 1
        for new_pos, old_pos in enumerate(other, start=2):
            inv[old_pos] = new_pos
        self._state = psi.transpose(inv).reshape(2 ** n)

    # ── public API ────────────────────────────────────────────────────────────

    def apply_gate(self, gate: np.ndarray, qubit: int):
        if qubit < 0 or qubit >= self.num_qubits:
            raise ValueError(f"Qubit index {qubit} out of range [0,{self.num_qubits})")
        if gate.shape != (2, 2):
            raise ValueError("Single-qubit gate must be 2×2")

        if self._use_statevector:
            self._apply_sv_single(gate, qubit)
        else:
            try:
                self.mps.gate_(gate, qubit, contract='auto-mps')
                self.mps.compress(max_bond=self.max_bond, cutoff=self.cutoff)
            except Exception:
                self._state = self._sv()
                self._use_statevector = True
                self._apply_sv_single(gate, qubit)

        self.gate_count += 1
        self._update_metrics()

    def apply_two_qubit_gate(self, gate: np.ndarray, qubit1: int, qubit2: int):
        if gate.shape != (4, 4):
            raise ValueError("Two-qubit gate must be 4×4")
        for q in (qubit1, qubit2):
            if q < 0 or q >= self.num_qubits:
                raise ValueError(f"Qubit {q} out of range")

        if self._use_statevector:
            self._apply_sv_two(gate, qubit1, qubit2)
        else:
            try:
                self.mps.gate_(gate.reshape(2, 2, 2, 2), (qubit1, qubit2), contract='auto-mps')
                self.mps.compress(max_bond=self.max_bond, cutoff=self.cutoff)
            except Exception:
                self._state = self._sv()
                self._use_statevector = True
                self._apply_sv_two(gate, qubit1, qubit2)

        self.gate_count += 1
        self.depth = max(self.depth, abs(qubit1 - qubit2))
        self._update_metrics()

    def measure(self, shots: int = 1024, qubits: Optional[List[int]] = None) -> Dict[str, int]:
        if qubits is None:
            qubits = list(range(self.num_qubits))

        sv = self._sv()
        probs_full = np.abs(sv) ** 2
        probs_full /= probs_full.sum()  # normalize

        indices = np.random.choice(len(probs_full), size=shots, p=probs_full)
        counts: Dict[str, int] = {}
        for idx in indices:
            bits = format(idx, f'0{self.num_qubits}b')
            key = ''.join(bits[q] for q in qubits)
            counts[key] = counts.get(key, 0) + 1

        return dict(sorted(counts.items()))

    def get_state_vector(self) -> np.ndarray:
        if self.num_qubits > 25:
            raise ValueError("State vector too large (>25 qubits)")
        return self._sv().copy()

    def reset(self):
        self._state = np.zeros(2 ** self.num_qubits, dtype=complex)
        self._state[0] = 1.0
        if not self._use_statevector and QUIMB_AVAILABLE:
            try:
                self.mps = qtn.MPS_computational_state('0' * self.num_qubits)
            except Exception:
                pass
        self.gate_count = 0
        self.depth = 0
        self.current_bond_dim = 1

    def _update_metrics(self):
        if not self._use_statevector and QUIMB_AVAILABLE:
            try:
                bd = self.mps.bond_sizes()
                self.current_bond_dim = max(bd) if bd else 1
            except Exception:
                pass
        self.memory_usage_mb = round(psutil.Process().memory_info().rss / 1024 / 1024, 2)

    def get_info(self) -> Dict:
        return {
            'num_qubits': self.num_qubits,
            'gate_count': self.gate_count,
            'circuit_depth': self.depth,
            'max_bond_dimension': self.max_bond,
            'current_bond_dimension': self.current_bond_dim,
            'memory_usage_mb': self.memory_usage_mb,
            'backend_mode': 'statevector' if self._use_statevector else 'mps',
        }

    def __repr__(self):
        return f"MPSEngine(qubits={self.num_qubits}, gates={self.gate_count})"
