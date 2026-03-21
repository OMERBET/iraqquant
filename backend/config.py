"""
Configuration for IraqQuant Platform
"""
import os

class Config:
    """System configuration"""
    
    # Platform Info
    PLATFORM_NAME = "IraqQuant Computing Platform"
    VERSION = "1.0.0"
    DESCRIPTION = "Software-based Quantum Computing Platform"
    
    # Computational Limits
    MAX_QUBITS = 127
    MIN_QUBITS = 1
    MAX_DEPTH = 100
    MAX_SHOTS = 10000
    MIN_SHOTS = 1
    
    # Memory Management
    MAX_BOND_DIM = 256
    MIN_BOND_DIM = 16
    MEMORY_LIMIT_GB = 16
    COMPRESSION_THRESHOLD = 0.90
    TRUNCATION_CUTOFF = 1e-10
    
    # Noise Models (IBM Eagle R3)
    DEFAULT_ERROR_RATE = 0.001
    T1_TIME_US = 100.0
    T2_TIME_US = 80.0
    SINGLE_QUBIT_GATE_TIME_NS = 35
    TWO_QUBIT_GATE_TIME_NS = 280
    READOUT_ERROR = 0.015
    
    # Burst Events
    BURST_RATE_PER_HOUR = 0.5
    MIN_BURST_QUBITS = 5
    MAX_BURST_QUBITS = 15
    
    # Topology
    TOPOLOGY_LEVELS = {
        'simple': 'All-to-all connectivity',
        'realistic': 'k-nearest neighbors (default)',
        'heavy_hex': 'IBM-style heavy-hex topology'
    }
    DEFAULT_TOPOLOGY = 'realistic'
    K_NEIGHBORS = 4
    
    # Job Management
    JOB_TIMEOUT_SECONDS = 600
    JOB_RETENTION_HOURS = 24
    MAX_CONCURRENT_JOBS = 10
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # Celery
    CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}'
    CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate_qubits(cls, num_qubits: int) -> bool:
        return cls.MIN_QUBITS <= num_qubits <= cls.MAX_QUBITS
    
    @classmethod
    def validate_shots(cls, shots: int) -> bool:
        return cls.MIN_SHOTS <= shots <= cls.MAX_SHOTS
    
    @classmethod
    def validate_depth(cls, depth: int) -> bool:
        return 0 <= depth <= cls.MAX_DEPTH
