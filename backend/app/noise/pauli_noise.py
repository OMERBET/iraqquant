"""
Pauli Noise Models for IraqQuant
Hardware-calibrated quantum noise models based on IBM Eagle R3
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
# quimb removed - not needed for noise models


class PauliNoise:
    """
    Implements realistic Pauli noise channels (X, Y, Z errors)
    Calibrated based on IBM Eagle R3 specifications
    """
    
    def __init__(self, 
                 single_qubit_error: float = 0.001,
                 two_qubit_error: float = 0.01,
                 readout_error: float = 0.015):
        """
        Initialize Pauli noise model
        
        Args:
            single_qubit_error: Single-qubit gate error rate
            two_qubit_error: Two-qubit gate error rate  
            readout_error: Measurement readout error rate
        """
        self.single_qubit_error = single_qubit_error
        self.two_qubit_error = two_qubit_error
        self.readout_error = readout_error
        
        # Pauli matrices
        self.I = np.array([[1, 0], [0, 1]], dtype=complex)
        self.X = np.array([[0, 1], [1, 0]], dtype=complex)
        self.Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        self.Z = np.array([[1, 0], [0, -1]], dtype=complex)
        
        self.paulis = {'I': self.I, 'X': self.X, 'Y': self.Y, 'Z': self.Z}
        
    def apply_gate_noise(self, 
                         num_qubits: int, 
                         gate_type: str = 'single') -> List[Tuple[int, str]]:
        """
        Generate Pauli errors for gate operations
        
        Args:
            num_qubits: Number of qubits affected
            gate_type: 'single' or 'two' qubit gate
            
        Returns:
            List of (qubit_index, pauli_op) errors to apply
        """
        error_rate = self.single_qubit_error if gate_type == 'single' else self.two_qubit_error
        errors = []
        
        for qubit in range(num_qubits):
            if np.random.random() < error_rate:
                # Depolarizing channel: equal probability for X, Y, Z
                pauli_op = np.random.choice(['X', 'Y', 'Z'])
                errors.append((qubit, pauli_op))
                
        return errors
    
    def apply_readout_noise(self, measurements: Dict[str, int]) -> Dict[str, int]:
        """
        Apply readout errors to measurement results
        
        Args:
            measurements: Dictionary of measurement outcomes
            
        Returns:
            Noisy measurement results
        """
        noisy_measurements = {}
        
        for bitstring, count in measurements.items():
            # Flip each bit with readout_error probability
            for _ in range(count):
                noisy_bits = list(bitstring)
                for i in range(len(noisy_bits)):
                    if np.random.random() < self.readout_error:
                        noisy_bits[i] = '1' if noisy_bits[i] == '0' else '0'
                
                noisy_string = ''.join(noisy_bits)
                noisy_measurements[noisy_string] = noisy_measurements.get(noisy_string, 0) + 1
        
        return noisy_measurements
    
    def get_kraus_operators(self, error_rate: float) -> List[np.ndarray]:
        """
        Get Kraus operators for depolarizing channel
        
        Args:
            error_rate: Probability of error
            
        Returns:
            List of Kraus operators
        """
        p = error_rate
        
        # Depolarizing channel Kraus operators
        K0 = np.sqrt(1 - p) * self.I
        K1 = np.sqrt(p/3) * self.X
        K2 = np.sqrt(p/3) * self.Y
        K3 = np.sqrt(p/3) * self.Z
        
        return [K0, K1, K2, K3]
    
    def apply_depolarizing_noise(self, 
                                  density_matrix: np.ndarray, 
                                  error_rate: float) -> np.ndarray:
        """
        Apply depolarizing noise to density matrix
        
        Args:
            density_matrix: Input quantum state
            error_rate: Depolarizing error rate
            
        Returns:
            Noisy density matrix
        """
        kraus_ops = self.get_kraus_operators(error_rate)
        noisy_rho = np.zeros_like(density_matrix)
        
        for K in kraus_ops:
            noisy_rho += K @ density_matrix @ K.conj().T
            
        return noisy_rho
    
    def calculate_fidelity(self, 
                          ideal_state: np.ndarray, 
                          noisy_state: np.ndarray) -> float:
        """
        Calculate fidelity between ideal and noisy states
        
        Args:
            ideal_state: Ideal quantum state
            noisy_state: Noisy quantum state
            
        Returns:
            Fidelity value [0, 1]
        """
        # For pure states
        if ideal_state.ndim == 1 and noisy_state.ndim == 1:
            return np.abs(np.vdot(ideal_state, noisy_state))**2
        
        # For density matrices
        sqrt_rho = np.linalg.matrix_power(ideal_state, 0.5)
        fidelity_matrix = sqrt_rho @ noisy_state @ sqrt_rho
        eigenvalues = np.linalg.eigvalsh(fidelity_matrix)
        
        return (np.sum(np.sqrt(np.maximum(eigenvalues, 0))))**2
    
    def get_noise_statistics(self, num_gates: int, gate_type: str = 'single') -> Dict:
        """
        Get expected noise statistics for a circuit
        
        Args:
            num_gates: Number of gates in circuit
            gate_type: Type of gates
            
        Returns:
            Dictionary with noise statistics
        """
        error_rate = self.single_qubit_error if gate_type == 'single' else self.two_qubit_error
        
        expected_errors = num_gates * error_rate
        error_variance = num_gates * error_rate * (1 - error_rate)
        
        return {
            'expected_errors': expected_errors,
            'error_variance': error_variance,
            'error_std': np.sqrt(error_variance),
            'total_gates': num_gates,
            'error_rate': error_rate
        }


class DecoherenceNoise:
    """
    T1 (amplitude damping) and T2 (dephasing) noise models
    """
    
    def __init__(self, 
                 t1_time_us: float = 100.0,
                 t2_time_us: float = 80.0,
                 gate_time_ns: float = 35.0):
        """
        Initialize decoherence model
        
        Args:
            t1_time_us: T1 relaxation time (microseconds)
            t2_time_us: T2 dephasing time (microseconds)
            gate_time_ns: Gate operation time (nanoseconds)
        """
        self.t1_time_us = t1_time_us
        self.t2_time_us = t2_time_us
        self.gate_time_ns = gate_time_ns
        
        # Convert to same units (microseconds)
        self.gate_time_us = gate_time_ns / 1000.0
        
    def get_t1_error_rate(self) -> float:
        """Calculate T1 error probability for one gate"""
        return 1 - np.exp(-self.gate_time_us / self.t1_time_us)
    
    def get_t2_error_rate(self) -> float:
        """Calculate T2 error probability for one gate"""
        return 1 - np.exp(-self.gate_time_us / self.t2_time_us)
    
    def amplitude_damping_kraus(self, error_rate: float) -> List[np.ndarray]:
        """
        Kraus operators for amplitude damping (T1 decay)
        
        Args:
            error_rate: T1 error probability
            
        Returns:
            List of Kraus operators
        """
        gamma = error_rate
        
        K0 = np.array([
            [1, 0],
            [0, np.sqrt(1 - gamma)]
        ], dtype=complex)
        
        K1 = np.array([
            [0, np.sqrt(gamma)],
            [0, 0]
        ], dtype=complex)
        
        return [K0, K1]
    
    def phase_damping_kraus(self, error_rate: float) -> List[np.ndarray]:
        """
        Kraus operators for phase damping (T2 dephasing)
        
        Args:
            error_rate: T2 error probability
            
        Returns:
            List of Kraus operators
        """
        gamma = error_rate
        
        K0 = np.array([
            [1, 0],
            [0, np.sqrt(1 - gamma)]
        ], dtype=complex)
        
        K1 = np.array([
            [0, 0],
            [0, np.sqrt(gamma)]
        ], dtype=complex)
        
        return [K0, K1]
    
    def apply_decoherence(self, 
                         density_matrix: np.ndarray,
                         num_gates: int = 1) -> np.ndarray:
        """
        Apply both T1 and T2 decoherence
        
        Args:
            density_matrix: Input state
            num_gates: Number of gates to execute
            
        Returns:
            Decohered density matrix
        """
        rho = density_matrix.copy()
        
        # Apply decoherence for each gate
        for _ in range(num_gates):
            # T1 decay
            t1_rate = self.get_t1_error_rate()
            for K in self.amplitude_damping_kraus(t1_rate):
                rho = K @ rho @ K.conj().T
            
            # T2 dephasing
            t2_rate = self.get_t2_error_rate()
            for K in self.phase_damping_kraus(t2_rate):
                rho = K @ rho @ K.conj().T
        
        return rho
    
    def get_coherence_time_info(self) -> Dict:
        """Get coherence time information"""
        return {
            't1_us': self.t1_time_us,
            't2_us': self.t2_time_us,
            'gate_time_ns': self.gate_time_ns,
            't1_error_per_gate': self.get_t1_error_rate(),
            't2_error_per_gate': self.get_t2_error_rate(),
            'max_gates_t1': int(self.t1_time_us / self.gate_time_us),
            'max_gates_t2': int(self.t2_time_us / self.gate_time_us)
        }
