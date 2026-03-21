"""
Burst Event Noise Model
Processes correlated errors affecting multiple qubits simultaneously
Based on real quantum hardware observations
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta


class BurstEvent:
    """Single burst error event"""
    
    def __init__(self, 
                 time: float,
                 affected_qubits: List[int],
                 error_type: str,
                 severity: float):
        """
        Initialize burst event
        
        Args:
            time: Time of occurrence (in microseconds)
            affected_qubits: List of affected qubit indices
            error_type: Type of error ('cosmic_ray', 'thermal_fluctuation', etc.)
            severity: Error severity [0, 1]
        """
        self.time = time
        self.affected_qubits = affected_qubits
        self.error_type = error_type
        self.severity = severity
        
    def __repr__(self):
        return f"BurstEvent(t={self.time:.2f}us, qubits={self.affected_qubits}, type={self.error_type})"


class BurstEventGenerator:
    """
    Generates realistic burst error events
    Models correlated errors from cosmic rays, thermal fluctuations, etc.
    """
    
    def __init__(self,
                 burst_rate_per_hour: float = 0.5,
                 min_burst_qubits: int = 5,
                 max_burst_qubits: int = 15,
                 total_qubits: int = 127):
        """
        Initialize burst event generator
        
        Args:
            burst_rate_per_hour: Average bursts per hour
            min_burst_qubits: Minimum qubits affected per burst
            max_burst_qubits: Maximum qubits affected per burst
            total_qubits: Total number of qubits in system
        """
        self.burst_rate_per_hour = burst_rate_per_hour
        self.min_burst_qubits = min_burst_qubits
        self.max_burst_qubits = max_burst_qubits
        self.total_qubits = total_qubits
        
        # Convert to rate per microsecond
        self.burst_rate_per_us = burst_rate_per_hour / (3600 * 1e6)
        
        # Event types and their probabilities
        self.event_types = {
            'cosmic_ray': 0.40,      # High energy particle
            'thermal_fluctuation': 0.30,  # Temperature spike
            'crosstalk': 0.20,       # Control line interference
            'power_fluctuation': 0.10  # Power supply noise
        }
        
    def generate_events(self, 
                       duration_us: float,
                       seed: Optional[int] = None) -> List[BurstEvent]:
        """
        Generate burst events for a given time duration
        
        Args:
            duration_us: Processing duration in microseconds
            seed: Random seed for reproducibility
            
        Returns:
            List of burst events
        """
        if seed is not None:
            np.random.seed(seed)
        
        # Poisson process: number of events
        expected_events = self.burst_rate_per_us * duration_us
        num_events = np.random.poisson(expected_events)
        
        events = []
        for _ in range(num_events):
            # Random time within duration
            time = np.random.uniform(0, duration_us)
            
            # Number of affected qubits
            num_affected = np.random.randint(self.min_burst_qubits, 
                                            self.max_burst_qubits + 1)
            
            # Select affected qubits (spatially correlated)
            affected_qubits = self._select_correlated_qubits(num_affected)
            
            # Event type
            event_type = np.random.choice(
                list(self.event_types.keys()),
                p=list(self.event_types.values())
            )
            
            # Severity (higher for cosmic rays)
            if event_type == 'cosmic_ray':
                severity = np.random.uniform(0.5, 1.0)
            else:
                severity = np.random.uniform(0.2, 0.6)
            
            event = BurstEvent(time, affected_qubits, event_type, severity)
            events.append(event)
        
        # Sort by time
        events.sort(key=lambda e: e.time)
        
        return events
    
    def _select_correlated_qubits(self, num_qubits: int) -> List[int]:
        """
        Select spatially correlated qubits
        Models physical proximity effects
        
        Args:
            num_qubits: Number of qubits to select
            
        Returns:
            List of qubit indices
        """
        # Start from random qubit
        center = np.random.randint(0, self.total_qubits)
        
        # Add nearby qubits (simple linear topology assumption)
        affected = [center]
        
        for _ in range(num_qubits - 1):
            # Find qubits near existing affected qubits
            candidates = []
            for q in affected:
                # Neighbors within distance 3
                for neighbor in range(max(0, q-3), min(self.total_qubits, q+4)):
                    if neighbor not in affected:
                        candidates.append(neighbor)
            
            if candidates:
                # Weight by proximity to cluster center
                weights = [1.0 / (abs(c - center) + 1) for c in candidates]
                weights = np.array(weights) / sum(weights)
                
                new_qubit = np.random.choice(candidates, p=weights)
                affected.append(new_qubit)
            else:
                # Fallback: random qubit
                remaining = [q for q in range(self.total_qubits) if q not in affected]
                if remaining:
                    affected.append(np.random.choice(remaining))
        
        return sorted(affected)
    
    def apply_burst_to_circuit(self, 
                               circuit_duration_us: float,
                               gate_times: List[Tuple[float, List[int]]],
                               seed: Optional[int] = None) -> Dict:
        """
        Apply burst events to circuit execution
        
        Args:
            circuit_duration_us: Total circuit execution time
            gate_times: List of (time, qubits) for each gate
            seed: Random seed
            
        Returns:
            Dictionary with burst information and affected gates
        """
        events = self.generate_events(circuit_duration_us, seed)
        
        affected_gates = []
        for gate_idx, (gate_time, gate_qubits) in enumerate(gate_times):
            for event in events:
                # Check if event occurs during gate
                if abs(event.time - gate_time) < 1.0:  # 1us window
                    # Check if any gate qubit is affected
                    if any(q in event.affected_qubits for q in gate_qubits):
                        affected_gates.append({
                            'gate_index': gate_idx,
                            'gate_time': gate_time,
                            'gate_qubits': gate_qubits,
                            'event': event,
                            'overlap': len(set(gate_qubits) & set(event.affected_qubits))
                        })
        
        return {
            'total_events': len(events),
            'events': events,
            'affected_gates': affected_gates,
            'circuit_duration_us': circuit_duration_us,
            'burst_rate': self.burst_rate_per_hour
        }
    
    def get_error_map(self, events: List[BurstEvent]) -> np.ndarray:
        """
        Create error map showing which qubits were affected
        
        Args:
            events: List of burst events
            
        Returns:
            Array of error counts per qubit
        """
        error_map = np.zeros(self.total_qubits)
        
        for event in events:
            for qubit in event.affected_qubits:
                error_map[qubit] += event.severity
        
        return error_map
    
    def calculate_burst_statistics(self, events: List[BurstEvent]) -> Dict:
        """
        Calculate statistics about burst events
        
        Args:
            events: List of burst events
            
        Returns:
            Dictionary with statistics
        """
        if not events:
            return {
                'total_events': 0,
                'avg_affected_qubits': 0,
                'max_affected_qubits': 0,
                'avg_severity': 0,
                'event_types': {}
            }
        
        affected_counts = [len(e.affected_qubits) for e in events]
        severities = [e.severity for e in events]
        
        event_type_counts = {}
        for e in events:
            event_type_counts[e.error_type] = event_type_counts.get(e.error_type, 0) + 1
        
        return {
            'total_events': len(events),
            'avg_affected_qubits': np.mean(affected_counts),
            'max_affected_qubits': np.max(affected_counts),
            'min_affected_qubits': np.min(affected_counts),
            'avg_severity': np.mean(severities),
            'max_severity': np.max(severities),
            'event_types': event_type_counts,
            'most_common_type': max(event_type_counts, key=event_type_counts.get)
        }
    
    def visualize_timeline(self, events: List[BurstEvent], duration_us: float) -> str:
        """
        Create ASCII timeline visualization of burst events
        
        Args:
            events: List of burst events
            duration_us: Total duration
            
        Returns:
            ASCII art timeline
        """
        width = 80
        timeline = [' '] * width
        
        for event in events:
            pos = int((event.time / duration_us) * (width - 1))
            
            # Symbol based on severity
            if event.severity > 0.7:
                symbol = '█'
            elif event.severity > 0.4:
                symbol = '▓'
            else:
                symbol = '░'
            
            timeline[pos] = symbol
        
        output = "Burst Event Timeline:\n"
        output += "0" + "-" * (width - 2) + f"{duration_us:.0f}us\n"
        output += ''.join(timeline) + "\n"
        output += f"Total events: {len(events)}\n"
        output += "Legend: █ severe  ▓ moderate  ░ mild\n"
        
        return output


class BurstMitigation:
    """
    Techniques to mitigate burst event effects
    """
    
    @staticmethod
    def detect_burst_signature(measurement_results: Dict[str, int],
                               threshold: float = 0.3) -> bool:
        """
        Detect if measurement results show burst event signature
        
        Args:
            measurement_results: Dictionary of measurement counts
            threshold: Detection threshold
            
        Returns:
            True if burst detected
        """
        total_shots = sum(measurement_results.values())
        
        # Check for unusual clustering in results
        sorted_counts = sorted(measurement_results.values(), reverse=True)
        
        if len(sorted_counts) > 1:
            # If top result is disproportionately large
            top_ratio = sorted_counts[0] / total_shots
            if top_ratio > threshold and len(sorted_counts) > 2:
                second_ratio = sorted_counts[1] / total_shots
                if top_ratio / (second_ratio + 0.01) > 5:
                    return True
        
        return False
    
    @staticmethod
    def temporal_filtering(jobs: List[Dict], 
                          time_window_us: float = 100.0) -> List[Dict]:
        """
        Filter out jobs affected by temporal burst clustering
        
        Args:
            jobs: List of job results with timestamps
            time_window_us: Time window for burst detection
            
        Returns:
            Filtered job list
        """
        if len(jobs) < 2:
            return jobs
        
        # Sort by timestamp
        sorted_jobs = sorted(jobs, key=lambda j: j.get('timestamp', 0))
        
        filtered = []
        skip_until = 0
        
        for i, job in enumerate(sorted_jobs):
            if i < skip_until:
                continue
            
            # Check for burst signature
            if BurstMitigation.detect_burst_signature(job.get('results', {})):
                # Skip jobs in time window
                skip_until = i + 1
                while (skip_until < len(sorted_jobs) and 
                       sorted_jobs[skip_until]['timestamp'] - job['timestamp'] < time_window_us):
                    skip_until += 1
            else:
                filtered.append(job)
        
        return filtered
