"""
Quantum Gates for IraqQuant Platform
Complete set of single and two-qubit gates
"""
import numpy as np
from typing import Optional


class QuantumGates:
    """
    Collection of quantum gates
    All gates are 2x2 (single-qubit) or 4x4 (two-qubit) unitary matrices
    """
    
    def __init__(self):
        """Initialize quantum gates"""
        self.sqrt2 = np.sqrt(2)
        
    # ==================== Single-Qubit Gates ====================
    
    def I(self) -> np.ndarray:
        """Identity gate"""
        return np.array([
            [1, 0],
            [0, 1]
        ], dtype=complex)
    
    def X(self) -> np.ndarray:
        """Pauli-X gate (NOT gate)"""
        return np.array([
            [0, 1],
            [1, 0]
        ], dtype=complex)
    
    def Y(self) -> np.ndarray:
        """Pauli-Y gate"""
        return np.array([
            [0, -1j],
            [1j, 0]
        ], dtype=complex)
    
    def Z(self) -> np.ndarray:
        """Pauli-Z gate"""
        return np.array([
            [1, 0],
            [0, -1]
        ], dtype=complex)
    
    def H(self) -> np.ndarray:
        """Hadamard gate"""
        return np.array([
            [1, 1],
            [1, -1]
        ], dtype=complex) / self.sqrt2
    
    def S(self) -> np.ndarray:
        """S gate (Phase gate)"""
        return np.array([
            [1, 0],
            [0, 1j]
        ], dtype=complex)
    
    def Sdg(self) -> np.ndarray:
        """S dagger (Adjoint of S)"""
        return np.array([
            [1, 0],
            [0, -1j]
        ], dtype=complex)
    
    def T(self) -> np.ndarray:
        """T gate (π/8 gate)"""
        return np.array([
            [1, 0],
            [0, np.exp(1j * np.pi / 4)]
        ], dtype=complex)
    
    def Tdg(self) -> np.ndarray:
        """T dagger (Adjoint of T)"""
        return np.array([
            [1, 0],
            [0, np.exp(-1j * np.pi / 4)]
        ], dtype=complex)
    
    # ==================== Rotation Gates ====================
    
    def RX(self, theta: float) -> np.ndarray:
        """
        Rotation around X-axis
        
        Args:
            theta: Rotation angle in radians
        """
        cos = np.cos(theta / 2)
        sin = np.sin(theta / 2)
        return np.array([
            [cos, -1j * sin],
            [-1j * sin, cos]
        ], dtype=complex)
    
    def RY(self, theta: float) -> np.ndarray:
        """
        Rotation around Y-axis
        
        Args:
            theta: Rotation angle in radians
        """
        cos = np.cos(theta / 2)
        sin = np.sin(theta / 2)
        return np.array([
            [cos, -sin],
            [sin, cos]
        ], dtype=complex)
    
    def RZ(self, theta: float) -> np.ndarray:
        """
        Rotation around Z-axis
        
        Args:
            theta: Rotation angle in radians
        """
        return np.array([
            [np.exp(-1j * theta / 2), 0],
            [0, np.exp(1j * theta / 2)]
        ], dtype=complex)
    
    def U1(self, lambda_param: float) -> np.ndarray:
        """
        Single-parameter single-qubit gate
        
        Args:
            lambda_param: Phase parameter
        """
        return np.array([
            [1, 0],
            [0, np.exp(1j * lambda_param)]
        ], dtype=complex)
    
    def U2(self, phi: float, lambda_param: float) -> np.ndarray:
        """
        Two-parameter single-qubit gate
        
        Args:
            phi: First parameter
            lambda_param: Second parameter
        """
        return np.array([
            [1, -np.exp(1j * lambda_param)],
            [np.exp(1j * phi), np.exp(1j * (phi + lambda_param))]
        ], dtype=complex) / self.sqrt2
    
    def U3(self, theta: float, phi: float, lambda_param: float) -> np.ndarray:
        """
        Generic single-qubit rotation gate
        
        Args:
            theta: Rotation angle
            phi: First phase
            lambda_param: Second phase
        """
        cos = np.cos(theta / 2)
        sin = np.sin(theta / 2)
        return np.array([
            [cos, -np.exp(1j * lambda_param) * sin],
            [np.exp(1j * phi) * sin, np.exp(1j * (phi + lambda_param)) * cos]
        ], dtype=complex)
    
    # ==================== Two-Qubit Gates ====================
    
    def CNOT(self) -> np.ndarray:
        """
        Controlled-NOT gate (CX)
        Control on qubit 0, target on qubit 1
        """
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0]
        ], dtype=complex)
    
    def CX(self) -> np.ndarray:
        """Alias for CNOT"""
        return self.CNOT()
    
    def CZ(self) -> np.ndarray:
        """Controlled-Z gate"""
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, -1]
        ], dtype=complex)
    
    def CY(self) -> np.ndarray:
        """Controlled-Y gate"""
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, -1j],
            [0, 0, 1j, 0]
        ], dtype=complex)
    
    def SWAP(self) -> np.ndarray:
        """SWAP gate"""
        return np.array([
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1]
        ], dtype=complex)
    
    def iSWAP(self) -> np.ndarray:
        """iSWAP gate"""
        return np.array([
            [1, 0, 0, 0],
            [0, 0, 1j, 0],
            [0, 1j, 0, 0],
            [0, 0, 0, 1]
        ], dtype=complex)
    
    def SQRT_SWAP(self) -> np.ndarray:
        """Square root of SWAP gate"""
        return np.array([
            [1, 0, 0, 0],
            [0, 0.5 * (1 + 1j), 0.5 * (1 - 1j), 0],
            [0, 0.5 * (1 - 1j), 0.5 * (1 + 1j), 0],
            [0, 0, 0, 1]
        ], dtype=complex)
    
    def CH(self) -> np.ndarray:
        """Controlled-Hadamard gate"""
        h = self.H()
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, h[0, 0], h[0, 1]],
            [0, 0, h[1, 0], h[1, 1]]
        ], dtype=complex)
    
    def CRX(self, theta: float) -> np.ndarray:
        """Controlled rotation around X-axis"""
        rx = self.RX(theta)
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, rx[0, 0], rx[0, 1]],
            [0, 0, rx[1, 0], rx[1, 1]]
        ], dtype=complex)
    
    def CRY(self, theta: float) -> np.ndarray:
        """Controlled rotation around Y-axis"""
        ry = self.RY(theta)
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, ry[0, 0], ry[0, 1]],
            [0, 0, ry[1, 0], ry[1, 1]]
        ], dtype=complex)
    
    def CRZ(self, theta: float) -> np.ndarray:
        """Controlled rotation around Z-axis"""
        rz = self.RZ(theta)
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, rz[0, 0], rz[0, 1]],
            [0, 0, rz[1, 0], rz[1, 1]]
        ], dtype=complex)
    
    # ==================== Three-Qubit Gates ====================
    
    def TOFFOLI(self) -> np.ndarray:
        """
        Toffoli gate (CCX - Controlled-Controlled-NOT)
        8x8 matrix for 3 qubits
        """
        toffoli = np.eye(8, dtype=complex)
        # Flip last two elements (|110> <-> |111>)
        toffoli[6, 6] = 0
        toffoli[6, 7] = 1
        toffoli[7, 6] = 1
        toffoli[7, 7] = 0
        return toffoli
    
    def CCX(self) -> np.ndarray:
        """Alias for Toffoli gate"""
        return self.TOFFOLI()
    
    def FREDKIN(self) -> np.ndarray:
        """
        Fredkin gate (CSWAP - Controlled-SWAP)
        8x8 matrix for 3 qubits
        """
        fredkin = np.eye(8, dtype=complex)
        # Swap |101> and |110>
        fredkin[5, 5] = 0
        fredkin[5, 6] = 1
        fredkin[6, 5] = 1
        fredkin[6, 6] = 0
        return fredkin
    
    # ==================== Utility Methods ====================
    
    def is_unitary(self, gate: np.ndarray, tolerance: float = 1e-10) -> bool:
        """
        Check if a gate is unitary
        
        Args:
            gate: Gate matrix
            tolerance: Numerical tolerance
            
        Returns:
            True if unitary
        """
        product = gate @ gate.conj().T
        identity = np.eye(gate.shape[0], dtype=complex)
        return np.allclose(product, identity, atol=tolerance)
    
    def get_gate_info(self, gate: np.ndarray) -> dict:
        """
        Get information about a gate
        
        Args:
            gate: Gate matrix
            
        Returns:
            Dictionary with gate properties
        """
        eigenvalues = np.linalg.eigvals(gate)
        
        return {
            'shape': gate.shape,
            'num_qubits': int(np.log2(gate.shape[0])),
            'is_unitary': self.is_unitary(gate),
            'is_hermitian': np.allclose(gate, gate.conj().T),
            'trace': np.trace(gate),
            'determinant': np.linalg.det(gate),
            'eigenvalues': eigenvalues.tolist()
        }
    
    def apply_gate(self, gate: np.ndarray, state: np.ndarray) -> np.ndarray:
        """
        Apply gate to quantum state
        
        Args:
            gate: Gate matrix
            state: State vector
            
        Returns:
            New state vector
        """
        return gate @ state
    
    def tensor_product(self, gate1: np.ndarray, gate2: np.ndarray) -> np.ndarray:
        """
        Compute tensor product of two gates
        
        Args:
            gate1: First gate
            gate2: Second gate
            
        Returns:
            Tensor product
        """
        return np.kron(gate1, gate2)
    
    def controlled_gate(self, gate: np.ndarray) -> np.ndarray:
        """
        Create controlled version of single-qubit gate
        
        Args:
            gate: Single-qubit gate (2x2)
            
        Returns:
            Controlled gate (4x4)
        """
        if gate.shape != (2, 2):
            raise ValueError("Gate must be 2x2")
        
        controlled = np.eye(4, dtype=complex)
        controlled[2:, 2:] = gate
        return controlled
    
    def power(self, gate: np.ndarray, n: float) -> np.ndarray:
        """
        Compute gate raised to power n
        
        Args:
            gate: Gate matrix
            n: Power (can be fractional)
            
        Returns:
            Gate^n
        """
        # Diagonalize: gate = V @ D @ V^†
        eigenvalues, eigenvectors = np.linalg.eig(gate)
        
        # Raise eigenvalues to power n
        D_n = np.diag(eigenvalues ** n)
        
        # Reconstruct: gate^n = V @ D^n @ V^†
        return eigenvectors @ D_n @ eigenvectors.conj().T
    
    def get_all_single_qubit_gates(self) -> dict:
        """Get dictionary of all single-qubit gates"""
        return {
            'I': self.I(),
            'X': self.X(),
            'Y': self.Y(),
            'Z': self.Z(),
            'H': self.H(),
            'S': self.S(),
            'Sdg': self.Sdg(),
            'T': self.T(),
            'Tdg': self.Tdg()
        }
    
    def get_all_two_qubit_gates(self) -> dict:
        """Get dictionary of all two-qubit gates"""
        return {
            'CNOT': self.CNOT(),
            'CZ': self.CZ(),
            'CY': self.CY(),
            'SWAP': self.SWAP(),
            'iSWAP': self.iSWAP(),
            'SQRT_SWAP': self.SQRT_SWAP(),
            'CH': self.CH()
        }
