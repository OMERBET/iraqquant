"""
Job Model for IraqQuant Platform
Quantum circuit execution jobs
"""
import secrets
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class JobStatus(Enum):
    """Job execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QuantumJob:
    """Quantum circuit execution job"""
    
    def __init__(self,
                 user_id: str,
                 circuit: Dict,
                 num_qubits: int,
                 shots: int = 1024,
                 backend: str = 'mps',
                 noise_model: Optional[Dict] = None,
                 use_qec: bool = False,
                 job_id: Optional[str] = None):
        """
        Initialize quantum job
        
        Args:
            user_id: User who submitted the job
            circuit: Quantum circuit definition
            num_qubits: Number of qubits
            shots: Number of measurements
            backend: Backend type ('mps' or 'photonic')
            noise_model: Noise configuration
            use_qec: Whether to use QEC
            job_id: Unique job ID
        """
        self.job_id = job_id or f"job_{secrets.token_hex(8)}"
        self.user_id = user_id
        self.circuit = circuit
        self.num_qubits = num_qubits
        self.shots = shots
        self.backend = backend
        self.noise_model = noise_model or {}
        self.use_qec = use_qec
        
        # Status tracking
        self.status = JobStatus.QUEUED
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Results
        self.results: Optional[Dict] = None
        self.error_message: Optional[str] = None
        
        # Metadata
        self.execution_time_ms: Optional[float] = None
        self.memory_used_mb: Optional[float] = None
        
    def start(self):
        """Mark job as started"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, results: Dict, execution_time_ms: float, memory_used_mb: float):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.results = results
        self.execution_time_ms = execution_time_ms
        self.memory_used_mb = memory_used_mb
    
    def fail(self, error_message: str):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def cancel(self):
        """Cancel job"""
        if self.status in [JobStatus.QUEUED, JobStatus.RUNNING]:
            self.status = JobStatus.CANCELLED
            self.completed_at = datetime.utcnow()
    
    def get_duration_ms(self) -> Optional[float]:
        """Get job duration in milliseconds"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'job_id': self.job_id,
            'user_id': self.user_id,
            'status': self.status.value,
            'num_qubits': self.num_qubits,
            'shots': self.shots,
            'backend': self.backend,
            'use_qec': self.use_qec,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time_ms': self.execution_time_ms,
            'memory_used_mb': self.memory_used_mb,
            'error_message': self.error_message,
            'has_results': self.results is not None
        }
    
    def to_dict_full(self) -> Dict:
        """Convert to dictionary with full details"""
        data = self.to_dict()
        data['circuit'] = self.circuit
        data['noise_model'] = self.noise_model
        data['results'] = self.results
        return data


class JobQueue:
    """Simple in-memory job queue"""
    
    def __init__(self, max_concurrent: int = 10):
        self.jobs: Dict[str, QuantumJob] = {}
        self.max_concurrent = max_concurrent
        self.queue: List[str] = []  # job_ids in queue order
    
    def submit(self, job: QuantumJob) -> str:
        """
        Submit job to queue
        
        Args:
            job: QuantumJob to submit
            
        Returns:
            Job ID
        """
        self.jobs[job.job_id] = job
        self.queue.append(job.job_id)
        return job.job_id
    
    def get_job(self, job_id: str) -> Optional[QuantumJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_next_job(self) -> Optional[QuantumJob]:
        """Get next job to execute"""
        # Count running jobs
        running = sum(1 for job in self.jobs.values() 
                     if job.status == JobStatus.RUNNING)
        
        if running >= self.max_concurrent:
            return None
        
        # Find next queued job
        for job_id in self.queue:
            job = self.jobs.get(job_id)
            if job and job.status == JobStatus.QUEUED:
                return job
        
        return None
    
    def get_user_jobs(self, user_id: str, limit: int = 50) -> List[QuantumJob]:
        """Get jobs for a user"""
        user_jobs = [job for job in self.jobs.values() if job.user_id == user_id]
        # Sort by creation time (newest first)
        user_jobs.sort(key=lambda j: j.created_at, reverse=True)
        return user_jobs[:limit]
    
    def get_queue_status(self) -> Dict:
        """Get queue statistics"""
        queued = sum(1 for job in self.jobs.values() 
                    if job.status == JobStatus.QUEUED)
        running = sum(1 for job in self.jobs.values() 
                     if job.status == JobStatus.RUNNING)
        completed = sum(1 for job in self.jobs.values() 
                       if job.status == JobStatus.COMPLETED)
        failed = sum(1 for job in self.jobs.values() 
                    if job.status == JobStatus.FAILED)
        
        return {
            'total_jobs': len(self.jobs),
            'queued': queued,
            'running': running,
            'completed': completed,
            'failed': failed,
            'max_concurrent': self.max_concurrent,
            'queue_length': len(self.queue)
        }
    
    def cleanup_old_jobs(self, hours: int = 24):
        """Remove jobs older than specified hours"""
        cutoff = datetime.utcnow()
        cutoff = cutoff.replace(hour=cutoff.hour - hours)
        
        old_job_ids = [
            job_id for job_id, job in self.jobs.items()
            if job.completed_at and job.completed_at < cutoff
        ]
        
        for job_id in old_job_ids:
            del self.jobs[job_id]
            if job_id in self.queue:
                self.queue.remove(job_id)
        
        return len(old_job_ids)
