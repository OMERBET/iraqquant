"""
Surface Code Implementation for Quantum Error Correction
Converts physical qubits to logical qubits with error correction
"""
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import itertools


@dataclass
class SurfaceCodePatch:
    """
    Single surface code patch
    d×d array of data qubits with (d-1)×(d-1) ancilla qubits
    """
    distance: int  # Code distance (d)
    data_qubits: List[int]  # Physical qubit indices for data
    x_ancillas: List[int]  # X-type stabilizer ancillas
    z_ancillas: List[int]  # Z-type stabilizer ancillas
    logical_qubit_id: int  # Logical qubit index
    
    def __post_init__(self):
        expected_data = self.distance ** 2
        expected_ancillas = (self.distance - 1) ** 2
        
        assert len(self.data_qubits) == expected_data, \
            f"Expected {expected_data} data qubits, got {len(self.data_qubits)}"
        assert len(self.x_ancillas) == expected_ancillas, \
            f"Expected {expected_ancillas} X ancillas, got {len(self.x_ancillas)}"
        assert len(self.z_ancillas) == expected_ancillas, \
            f"Expected {expected_ancillas} Z ancillas, got {len(self.z_ancillas)}"


class SurfaceCode:
    """
    Surface code quantum error correction
    
    Maps physical qubits to logical qubits with distance-d code
    Each logical qubit requires d² data qubits + 2(d-1)² ancilla qubits
    """
    
    def __init__(self, 
                 num_physical_qubits: int = 127,
                 code_distance: int = 3):
        """
        Initialize surface code
        
        Args:
            num_physical_qubits: Total physical qubits available
            code_distance: Code distance (d) - higher = better correction
        """
        self.num_physical_qubits = num_physical_qubits
        self.code_distance = code_distance
        
        # Calculate resources needed per logical qubit
        self.data_qubits_per_logical = code_distance ** 2
        self.ancilla_qubits_per_logical = 2 * (code_distance - 1) ** 2
        self.total_qubits_per_logical = (self.data_qubits_per_logical + 
                                         self.ancilla_qubits_per_logical)
        
        # Calculate number of logical qubits we can support
        self.num_logical_qubits = num_physical_qubits // self.total_qubits_per_logical
        
        # Create patches
        self.patches: List[SurfaceCodePatch] = []
        self._allocate_patches()
        
        # Error correction parameters
        self.syndrome_history: List[Dict] = []
        self.correction_count = 0
        
    def _allocate_patches(self):
        """Allocate physical qubits to surface code patches"""
        current_qubit = 0
        
        for logical_id in range(self.num_logical_qubits):
            # Allocate data qubits
            data_qubits = list(range(current_qubit, 
                                    current_qubit + self.data_qubits_per_logical))
            current_qubit += self.data_qubits_per_logical
            
            # Allocate X-type ancillas
            num_x_ancillas = (self.code_distance - 1) ** 2
            x_ancillas = list(range(current_qubit, current_qubit + num_x_ancillas))
            current_qubit += num_x_ancillas
            
            # Allocate Z-type ancillas
            z_ancillas = list(range(current_qubit, current_qubit + num_x_ancillas))
            current_qubit += num_x_ancillas
            
            patch = SurfaceCodePatch(
                distance=self.code_distance,
                data_qubits=data_qubits,
                x_ancillas=x_ancillas,
                z_ancillas=z_ancillas,
                logical_qubit_id=logical_id
            )
            
            self.patches.append(patch)
    
    def get_stabilizer_measurements(self, 
                                   patch: SurfaceCodePatch) -> Dict[str, List[Tuple]]:
        """
        Get stabilizer generator configurations for a patch
        
        Args:
            patch: Surface code patch
            
        Returns:
            Dictionary with X and Z stabilizer configurations
        """
        d = patch.distance
        
        # X-type stabilizers (measure XXXX on 4 adjacent data qubits)
        x_stabilizers = []
        for i in range(d - 1):
            for j in range(d - 1):
                ancilla_idx = i * (d - 1) + j
                ancilla = patch.x_ancillas[ancilla_idx]
                
                # Connected data qubits (in 2D grid)
                data_indices = [
                    i * d + j,           # top-left
                    i * d + (j + 1),     # top-right
                    (i + 1) * d + j,     # bottom-left
                    (i + 1) * d + (j + 1) # bottom-right
                ]
                data_qubits = [patch.data_qubits[idx] for idx in data_indices]
                
                x_stabilizers.append((ancilla, data_qubits, 'X'))
        
        # Z-type stabilizers (measure ZZZZ on 4 adjacent data qubits)
        z_stabilizers = []
        for i in range(d - 1):
            for j in range(d - 1):
                ancilla_idx = i * (d - 1) + j
                ancilla = patch.z_ancillas[ancilla_idx]
                
                data_indices = [
                    i * d + j,
                    i * d + (j + 1),
                    (i + 1) * d + j,
                    (i + 1) * d + (j + 1)
                ]
                data_qubits = [patch.data_qubits[idx] for idx in data_indices]
                
                z_stabilizers.append((ancilla, data_qubits, 'Z'))
        
        return {
            'x_stabilizers': x_stabilizers,
            'z_stabilizers': z_stabilizers
        }
    
    def measure_syndromes(self, 
                         physical_state: np.ndarray,
                         patch_id: int = 0) -> Dict:
        """
        Measure error syndromes for a patch
        
        Args:
            physical_state: Physical qubit state
            patch_id: Which patch to measure
            
        Returns:
            Syndrome measurement results
        """
        if patch_id >= len(self.patches):
            raise ValueError(f"Invalid patch_id {patch_id}")
        
        patch = self.patches[patch_id]
        stabilizers = self.get_stabilizer_measurements(patch)
        
        # Perform syndrome measurements
        x_syndromes = []
        for ancilla, data_qubits, pauli_type in stabilizers['x_stabilizers']:
            # Simplified: random syndrome with some error probability
            syndrome = np.random.choice([0, 1], p=[0.95, 0.05])
            x_syndromes.append(syndrome)
        
        z_syndromes = []
        for ancilla, data_qubits, pauli_type in stabilizers['z_stabilizers']:
            syndrome = np.random.choice([0, 1], p=[0.95, 0.05])
            z_syndromes.append(syndrome)
        
        syndrome_data = {
            'patch_id': patch_id,
            'x_syndromes': x_syndromes,
            'z_syndromes': z_syndromes,
            'total_x_violations': sum(x_syndromes),
            'total_z_violations': sum(z_syndromes)
        }
        
        self.syndrome_history.append(syndrome_data)
        
        return syndrome_data
    
    def decode_syndromes(self, syndrome_data: Dict) -> List[Tuple[int, str]]:
        """
        Decode syndromes to find error locations
        Using minimum-weight perfect matching (simplified)
        
        Args:
            syndrome_data: Syndrome measurement results
            
        Returns:
            List of (qubit_index, error_type) corrections
        """
        corrections = []
        
        # X-type errors (detected by Z stabilizers)
        z_violations = [i for i, s in enumerate(syndrome_data['z_syndromes']) if s == 1]
        if z_violations:
            # Simplified: correct first violation
            patch = self.patches[syndrome_data['patch_id']]
            error_qubit = patch.data_qubits[z_violations[0]]
            corrections.append((error_qubit, 'X'))
        
        # Z-type errors (detected by X stabilizers)
        x_violations = [i for i, s in enumerate(syndrome_data['x_syndromes']) if s == 1]
        if x_violations:
            patch = self.patches[syndrome_data['patch_id']]
            error_qubit = patch.data_qubits[x_violations[0]]
            corrections.append((error_qubit, 'Z'))
        
        return corrections
    
    def apply_corrections(self, 
                         corrections: List[Tuple[int, str]]) -> int:
        """
        Apply error corrections
        
        Args:
            corrections: List of (qubit, error_type) to correct
            
        Returns:
            Number of corrections applied
        """
        # In real implementation, would apply Pauli corrections
        # Here we just count them
        self.correction_count += len(corrections)
        return len(corrections)
    
    def run_qec_cycle(self, 
                     physical_state: np.ndarray,
                     patch_id: int = 0) -> Dict:
        """
        Run one QEC cycle: measure syndromes, decode, correct
        
        Args:
            physical_state: Physical qubit state
            patch_id: Patch to correct
            
        Returns:
            QEC cycle results
        """
        # Measure syndromes
        syndromes = self.measure_syndromes(physical_state, patch_id)
        
        # Decode to find errors
        corrections = self.decode_syndromes(syndromes)
        
        # Apply corrections
        num_corrections = self.apply_corrections(corrections)
        
        return {
            'syndromes': syndromes,
            'corrections': corrections,
            'num_corrections': num_corrections,
            'total_corrections': self.correction_count
        }
    
    def get_logical_error_rate(self, 
                              physical_error_rate: float) -> float:
        """
        Estimate logical error rate from physical error rate
        
        For distance-d surface code:
        P_L ≈ c * (p / p_th)^((d+1)/2) where p_th ≈ 0.01
        
        Args:
            physical_error_rate: Physical qubit error rate
            
        Returns:
            Logical error rate
        """
        p = physical_error_rate
        d = self.code_distance
        p_threshold = 0.01  # Surface code threshold
        
        if p >= p_threshold:
            # Above threshold - no benefit
            return p
        
        # Below threshold - exponential suppression
        c = 0.1  # Prefactor (depends on decoder)
        logical_error_rate = c * (p / p_threshold) ** ((d + 1) / 2)
        
        return logical_error_rate
    
    def estimate_required_distance(self, 
                                  target_error_rate: float,
                                  physical_error_rate: float) -> int:
        """
        Estimate required code distance for target logical error rate
        
        Args:
            target_error_rate: Target logical error rate
            physical_error_rate: Physical error rate
            
        Returns:
            Required code distance
        """
        if physical_error_rate >= 0.01:
            return -1  # Cannot achieve with surface code
        
        # Solve: target = c * (p / p_th)^((d+1)/2)
        c = 0.1
        p_th = 0.01
        
        ratio = target_error_rate / c
        exponent = np.log(ratio) / np.log(physical_error_rate / p_th)
        
        required_d = int(np.ceil(2 * exponent - 1))
        
        return max(3, required_d)  # Minimum distance is 3
    
    def get_resource_requirements(self) -> Dict:
        """Get resource requirements summary"""
        return {
            'physical_qubits_total': self.num_physical_qubits,
            'physical_qubits_used': len(self.patches) * self.total_qubits_per_logical,
            'physical_qubits_unused': (self.num_physical_qubits - 
                                      len(self.patches) * self.total_qubits_per_logical),
            'code_distance': self.code_distance,
            'logical_qubits': self.num_logical_qubits,
            'qubits_per_logical': self.total_qubits_per_logical,
            'data_qubits_per_logical': self.data_qubits_per_logical,
            'ancilla_qubits_per_logical': self.ancilla_qubits_per_logical,
            'overhead_ratio': self.total_qubits_per_logical / 1,
            'total_corrections_applied': self.correction_count
        }
    
    def get_code_performance(self, physical_error_rate: float) -> Dict:
        """
        Get expected code performance metrics
        
        Args:
            physical_error_rate: Physical error rate
            
        Returns:
            Performance metrics
        """
        logical_error_rate = self.get_logical_error_rate(physical_error_rate)
        
        return {
            'physical_error_rate': physical_error_rate,
            'logical_error_rate': logical_error_rate,
            'error_suppression_factor': physical_error_rate / logical_error_rate if logical_error_rate > 0 else float('inf'),
            'code_distance': self.code_distance,
            'threshold': 0.01,
            'below_threshold': physical_error_rate < 0.01,
            'effective': logical_error_rate < physical_error_rate
        }
    
    def visualize_patch(self, patch_id: int = 0) -> str:
        """
        ASCII visualization of a surface code patch
        
        Args:
            patch_id: Patch to visualize
            
        Returns:
            ASCII art representation
        """
        if patch_id >= len(self.patches):
            return "Invalid patch ID"
        
        patch = self.patches[patch_id]
        d = patch.distance
        
        output = f"Surface Code Patch {patch_id} (Distance {d}):\n"
        output += f"Logical Qubit: {patch.logical_qubit_id}\n\n"
        
        # Create grid
        grid = []
        for i in range(2 * d - 1):
            grid.append([' '] * (2 * d - 1))
        
        # Place data qubits
        for i in range(d):
            for j in range(d):
                grid[2*i][2*j] = 'D'
        
        # Place X ancillas
        for i in range(d - 1):
            for j in range(d - 1):
                grid[2*i + 1][2*j + 1] = 'X'
        
        # Place Z ancillas (offset)
        for i in range(d - 1):
            for j in range(d - 1):
                if grid[2*i][2*j + 1] == ' ':
                    grid[2*i][2*j + 1] = 'Z'
                if grid[2*i + 1][2*j] == ' ':
                    grid[2*i + 1][2*j] = 'Z'
        
        # Print grid
        for row in grid:
            output += ' '.join(row) + '\n'
        
        output += "\nLegend: D=Data qubit, X=X-stabilizer ancilla, Z=Z-stabilizer ancilla\n"
        
        return output
