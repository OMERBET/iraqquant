"""
Topology Manager for IraqQuant
Manages qubit connectivity and topology
"""
import numpy as np
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx


class TopologyManager:
    """
    Manages qubit topology and connectivity
    Supports different connectivity patterns
    """
    
    def __init__(self, 
                 num_qubits: int,
                 topology_type: str = 'realistic',
                 k_neighbors: int = 4):
        """
        Initialize topology manager
        
        Args:
            num_qubits: Number of qubits
            topology_type: 'simple', 'realistic', or 'heavy_hex'
            k_neighbors: Number of neighbors for k-NN topology
        """
        self.num_qubits = num_qubits
        self.topology_type = topology_type
        self.k_neighbors = k_neighbors
        
        # Generate connectivity graph
        self.graph = self._generate_topology()
        
        # Precompute distances
        self.distances = dict(nx.all_pairs_shortest_path_length(self.graph))
    
    def _generate_topology(self) -> nx.Graph:
        """
        Generate connectivity graph based on topology type
        
        Returns:
            NetworkX graph
        """
        G = nx.Graph()
        G.add_nodes_from(range(self.num_qubits))
        
        if self.topology_type == 'simple':
            # All-to-all connectivity
            for i in range(self.num_qubits):
                for j in range(i + 1, self.num_qubits):
                    G.add_edge(i, j)
        
        elif self.topology_type == 'realistic':
            # k-nearest neighbors (linear chain with k connections)
            for i in range(self.num_qubits):
                for k in range(1, self.k_neighbors + 1):
                    j = (i + k) % self.num_qubits
                    if i < j:  # Avoid duplicate edges
                        G.add_edge(i, j)
        
        elif self.topology_type == 'heavy_hex':
            # IBM Heavy-Hex topology
            G = self._generate_heavy_hex()
        
        else:
            raise ValueError(f"Unknown topology type: {self.topology_type}")
        
        return G
    
    def _generate_heavy_hex(self) -> nx.Graph:
        """
        Generate IBM Heavy-Hex topology
        
        Returns:
            Heavy-hex graph
        """
        G = nx.Graph()
        G.add_nodes_from(range(self.num_qubits))
        
        # Heavy-hex is based on hexagonal lattice with additional connections
        # Simplified version for arbitrary number of qubits
        
        # Create approximate heavy-hex by combining linear and grid patterns
        side_length = int(np.sqrt(self.num_qubits))
        
        for i in range(self.num_qubits):
            row = i // side_length
            col = i % side_length
            
            # Horizontal connections
            if col < side_length - 1:
                G.add_edge(i, i + 1)
            
            # Vertical connections
            if row < side_length - 1:
                G.add_edge(i, i + side_length)
            
            # Diagonal connections (heavy-hex characteristic)
            if row < side_length - 1 and col < side_length - 1:
                if (row + col) % 2 == 0:
                    G.add_edge(i, i + side_length + 1)
        
        return G
    
    def is_connected(self, qubit1: int, qubit2: int) -> bool:
        """
        Check if two qubits are directly connected
        
        Args:
            qubit1: First qubit
            qubit2: Second qubit
            
        Returns:
            True if connected
        """
        return self.graph.has_edge(qubit1, qubit2)
    
    def get_neighbors(self, qubit: int) -> List[int]:
        """
        Get neighbors of a qubit
        
        Args:
            qubit: Qubit index
            
        Returns:
            List of neighbor indices
        """
        if qubit not in self.graph:
            return []
        return list(self.graph.neighbors(qubit))
    
    def get_distance(self, qubit1: int, qubit2: int) -> int:
        """
        Get shortest path distance between qubits
        
        Args:
            qubit1: First qubit
            qubit2: Second qubit
            
        Returns:
            Distance (number of hops)
        """
        if qubit1 not in self.distances or qubit2 not in self.distances[qubit1]:
            return float('inf')
        return self.distances[qubit1][qubit2]
    
    def get_path(self, qubit1: int, qubit2: int) -> List[int]:
        """
        Get shortest path between qubits
        
        Args:
            qubit1: Start qubit
            qubit2: End qubit
            
        Returns:
            List of qubits in path
        """
        try:
            return nx.shortest_path(self.graph, qubit1, qubit2)
        except nx.NetworkXNoPath:
            return []
    
    def decompose_swap_chain(self, qubit1: int, qubit2: int) -> List[Tuple[int, int]]:
        """
        Decompose long-range interaction into SWAP chain
        
        Args:
            qubit1: First qubit
            qubit2: Second qubit
            
        Returns:
            List of (control, target) pairs for SWAP gates
        """
        path = self.get_path(qubit1, qubit2)
        
        if len(path) < 2:
            return []
        
        # Generate SWAP sequence
        swaps = []
        for i in range(len(path) - 1):
            swaps.append((path[i], path[i + 1]))
        
        return swaps
    
    def get_connectivity_matrix(self) -> np.ndarray:
        """
        Get connectivity matrix
        
        Returns:
            Binary matrix (1 if connected, 0 otherwise)
        """
        matrix = np.zeros((self.num_qubits, self.num_qubits), dtype=int)
        
        for i, j in self.graph.edges():
            matrix[i, j] = 1
            matrix[j, i] = 1
        
        return matrix
    
    def get_degree_distribution(self) -> Dict[int, int]:
        """
        Get degree distribution
        
        Returns:
            Dictionary mapping degree to count
        """
        degrees = dict(self.graph.degree())
        distribution = {}
        
        for degree in degrees.values():
            distribution[degree] = distribution.get(degree, 0) + 1
        
        return distribution
    
    def get_average_connectivity(self) -> float:
        """
        Get average number of connections per qubit
        
        Returns:
            Average degree
        """
        degrees = dict(self.graph.degree())
        return sum(degrees.values()) / len(degrees) if degrees else 0
    
    def get_diameter(self) -> int:
        """
        Get graph diameter (longest shortest path)
        
        Returns:
            Diameter
        """
        try:
            return nx.diameter(self.graph)
        except nx.NetworkXError:
            # Graph not connected
            return float('inf')
    
    def is_bipartite(self) -> bool:
        """Check if topology is bipartite"""
        return nx.is_bipartite(self.graph)
    
    def get_clustering_coefficient(self) -> float:
        """Get average clustering coefficient"""
        return nx.average_clustering(self.graph)
    
    def find_optimal_qubit_mapping(self, 
                                   required_connections: List[Tuple[int, int]]) -> Dict[int, int]:
        """
        Find optimal mapping of logical to physical qubits
        
        Args:
            required_connections: List of required connections
            
        Returns:
            Mapping from logical to physical qubits
        """
        # Simplified greedy mapping
        # In production, use more sophisticated algorithms
        
        logical_qubits = set()
        for q1, q2 in required_connections:
            logical_qubits.add(q1)
            logical_qubits.add(q2)
        
        # Greedy assignment
        mapping = {}
        available_physical = set(range(self.num_qubits))
        
        for logical in sorted(logical_qubits):
            # Find physical qubit with most connections to already-mapped qubits
            best_physical = None
            best_score = -1
            
            for physical in available_physical:
                score = 0
                for other_logical, other_physical in mapping.items():
                    if self.is_connected(physical, other_physical):
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_physical = physical
            
            if best_physical is None and available_physical:
                best_physical = min(available_physical)
            
            if best_physical is not None:
                mapping[logical] = best_physical
                available_physical.remove(best_physical)
        
        return mapping
    
    def visualize(self, show_labels: bool = True) -> str:
        """
        ASCII visualization of topology
        
        Args:
            show_labels: Whether to show qubit labels
            
        Returns:
            ASCII representation
        """
        output = f"Topology: {self.topology_type}\n"
        output += f"Qubits: {self.num_qubits}\n"
        output += f"Edges: {self.graph.number_of_edges()}\n"
        output += f"Avg Connectivity: {self.get_average_connectivity():.2f}\n"
        output += "=" * 50 + "\n"
        
        # Simple adjacency list representation
        for qubit in range(min(self.num_qubits, 10)):  # Show first 10
            neighbors = self.get_neighbors(qubit)
            output += f"Q{qubit}: {neighbors}\n"
        
        if self.num_qubits > 10:
            output += "...\n"
        
        return output
    
    def get_topology_info(self) -> Dict:
        """
        Get comprehensive topology information
        
        Returns:
            Dictionary with topology statistics
        """
        return {
            'type': self.topology_type,
            'num_qubits': self.num_qubits,
            'num_edges': self.graph.number_of_edges(),
            'avg_connectivity': self.get_average_connectivity(),
            'max_degree': max(dict(self.graph.degree()).values()) if self.graph.degree() else 0,
            'min_degree': min(dict(self.graph.degree()).values()) if self.graph.degree() else 0,
            'diameter': self.get_diameter() if self.get_diameter() != float('inf') else None,
            'is_bipartite': self.is_bipartite(),
            'clustering_coefficient': self.get_clustering_coefficient(),
            'degree_distribution': self.get_degree_distribution(),
            'is_connected': nx.is_connected(self.graph)
        }
    
    def export_graph(self, format: str = 'edgelist') -> str:
        """
        Export graph in various formats
        
        Args:
            format: 'edgelist', 'adjacency', or 'gml'
            
        Returns:
            Graph representation string
        """
        if format == 'edgelist':
            edges = [f"{u} {v}" for u, v in self.graph.edges()]
            return '\n'.join(edges)
        
        elif format == 'adjacency':
            matrix = self.get_connectivity_matrix()
            return '\n'.join([' '.join(map(str, row)) for row in matrix])
        
        elif format == 'gml':
            # Simple GML format
            output = "graph [\n"
            for node in self.graph.nodes():
                output += f"  node [ id {node} ]\n"
            for u, v in self.graph.edges():
                output += f"  edge [ source {u} target {v} ]\n"
            output += "]\n"
            return output
        
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def __repr__(self) -> str:
        """String representation"""
        return f"TopologyManager(qubits={self.num_qubits}, type={self.topology_type}, edges={self.graph.number_of_edges()})"
