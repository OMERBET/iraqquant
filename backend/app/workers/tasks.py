"""
Celery tasks - quantum circuit execution (FIXED: results saved to JobQueue)
"""
import time
import psutil
from celery import Celery
from typing import Dict, Any
import numpy as np

from ..config import Config
from ..core.mps_engine import MPSEngine
from ..core.gates import QuantumGates
from ..noise.pauli_noise import PauliNoise, DecoherenceNoise
from ..noise.burst_events import BurstEventGenerator
from ..qec.surface_code import SurfaceCode

celery_app = Celery(
    'iraqquant',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND
)
celery_app.conf.update(
    task_serializer=Config.CELERY_TASK_SERIALIZER,
    result_serializer=Config.CELERY_RESULT_SERIALIZER,
    accept_content=Config.CELERY_ACCEPT_CONTENT,
    timezone=Config.CELERY_TIMEZONE,
    task_track_started=True,
    task_time_limit=Config.JOB_TIMEOUT_SECONDS,
)


def _run_circuit(circuit, num_qubits, shots, backend, noise_model, use_qec, update_fn=None) -> Dict:
    """
    Core execution logic (shared by Celery task and direct execution).
    Returns results dict.
    """
    start_time = time.time()
    mem_start = psutil.Process().memory_info().rss / 1024 / 1024

    def _update(msg, pct=0):
        if update_fn:
            update_fn(msg, pct)

    _update('Initializing')

    # ── Noise models ─────────────────────────────────────────────────────────
    pauli_noise = None
    burst_gen = None

    if noise_model:
        if noise_model.get('pauli_error'):
            pauli_noise = PauliNoise(
                single_qubit_error=noise_model.get('pauli_error', Config.DEFAULT_ERROR_RATE),
                readout_error=noise_model.get('readout_error', Config.READOUT_ERROR)
            )
        if noise_model.get('burst_events'):
            burst_gen = BurstEventGenerator(burst_rate_per_hour=Config.BURST_RATE_PER_HOUR)

    # ── QEC ──────────────────────────────────────────────────────────────────
    surface_code = None
    qec_info = None
    if use_qec:
        _update('Initializing QEC')
        surface_code = SurfaceCode(num_qubits, code_distance=3)
        effective_qubits = surface_code.num_logical_qubits
        qec_info = surface_code.get_resource_requirements()
    else:
        effective_qubits = num_qubits

    # ── Engine ───────────────────────────────────────────────────────────────
    _update('Initializing engine')
    engine = MPSEngine(num_qubits)   # photonic falls back to MPS for now

    # ── Execute gates ─────────────────────────────────────────────────────────
    gates_obj = QuantumGates()
    gate_list = circuit.get('gates', [])
    total_gates = len(gate_list)

    for idx, gate in enumerate(gate_list):
        _update('Executing circuit', int((idx / max(total_gates, 1)) * 100))

        gtype  = gate['type'].lower()
        qubits = gate['qubits']
        params = gate.get('params', [])

        SINGLE = {
            'h': gates_obj.H, 'x': gates_obj.X, 'y': gates_obj.Y,
            'z': gates_obj.Z, 's': gates_obj.S, 't': gates_obj.T,
            'sdg': gates_obj.Sdg, 'tdg': gates_obj.Tdg,
        }
        PARAM1 = {'rx': gates_obj.RX, 'ry': gates_obj.RY, 'rz': gates_obj.RZ}
        TWO = {
            'cx': gates_obj.CNOT, 'cnot': gates_obj.CNOT,
            'cz': gates_obj.CZ,   'cy': gates_obj.CY,
            'swap': gates_obj.SWAP,
        }

        if gtype in SINGLE:
            engine.apply_gate(SINGLE[gtype](), qubits[0])
        elif gtype in PARAM1:
            theta = params[0] if params else 0.0
            engine.apply_gate(PARAM1[gtype](theta), qubits[0])
        elif gtype in TWO:
            engine.apply_two_qubit_gate(TWO[gtype](), qubits[0], qubits[1])
        else:
            raise ValueError(f"Unknown gate type: {gtype}")

        # Pauli noise after each gate
        if pauli_noise and np.random.random() < noise_model.get('pauli_error', 0):
            err = np.random.choice(['x', 'y', 'z'])
            err_map = {'x': gates_obj.X, 'y': gates_obj.Y, 'z': gates_obj.Z}
            engine.apply_gate(err_map[err](), qubits[0])

    # ── Measure ──────────────────────────────────────────────────────────────
    _update('Measuring', 95)
    counts = engine.measure(shots=shots)

    if pauli_noise:
        counts = pauli_noise.apply_readout_noise(counts)

    total_shots = sum(counts.values())
    probabilities = {s: c / total_shots for s, c in counts.items()}

    execution_time = (time.time() - start_time) * 1000
    mem_end = psutil.Process().memory_info().rss / 1024 / 1024

    return {
        'counts': counts,
        'probabilities': probabilities,
        'num_qubits': num_qubits,
        'effective_qubits': effective_qubits,
        'shots': shots,
        'backend': backend,
        'execution_time_ms': round(execution_time, 2),
        'memory_used_mb': round(mem_end - mem_start, 2),
        'engine_info': engine.get_info(),
        'use_qec': use_qec,
        'qec_info': qec_info,
        'noise_applied': noise_model is not None and bool(noise_model),
    }


@celery_app.task(bind=True, name='tasks.execute_circuit')
def execute_circuit(self, circuit, num_qubits, shots, backend='mps',
                    noise_model=None, use_qec=False) -> Dict[str, Any]:
    """Celery task: execute circuit and return results"""
    try:
        def _upd(msg, pct=0):
            self.update_state(state='RUNNING', meta={'status': msg, 'progress': pct})

        return _run_circuit(circuit, num_qubits, shots, backend,
                            noise_model, use_qec, _upd)
    except Exception as e:
        return {'error': str(e), 'error_type': type(e).__name__, 'status': 'failed'}


def execute_circuit_sync(circuit, num_qubits, shots, backend='mps',
                         noise_model=None, use_qec=False) -> Dict[str, Any]:
    """
    Synchronous execution (used when Celery/Redis not available).
    Called directly from the jobs API.
    """
    try:
        return _run_circuit(circuit, num_qubits, shots, backend, noise_model, use_qec)
    except Exception as e:
        return {'error': str(e), 'error_type': type(e).__name__, 'status': 'failed'}


@celery_app.task(name='tasks.cleanup_old_jobs')
def cleanup_old_jobs():
    from ..api.jobs import get_job_queue
    removed = get_job_queue().cleanup_old_jobs(hours=Config.JOB_RETENTION_HOURS)
    return {'removed_jobs': removed, 'timestamp': time.time()}


celery_app.conf.beat_schedule = {
    'cleanup-old-jobs': {'task': 'tasks.cleanup_old_jobs', 'schedule': 3600.0},
}
