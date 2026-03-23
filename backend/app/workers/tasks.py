"""
Celery tasks - quantum circuit execution
FIX 3: Noise models properly connected to engine
NEW  : Cosmic ray physics (ionization diffusion + QP poisoning + noise logger)
"""
import time
import uuid
import psutil
from celery import Celery
from typing import Dict, Any
import numpy as np

from ..config import Config
from ..core.mps_engine import MPSEngine
from ..core.gates import QuantumGates
from ..noise.pauli_noise import PauliNoise, DecoherenceNoise
from ..noise.burst_events import BurstEventGenerator
from ..noise.cosmic_ray import CosmicRaySimulator
from ..noise.noise_logger import NoiseLogger
from ..qec.surface_code import SurfaceCode

celery_app = Celery(
    'iraqquant',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    task_serializer=Config.CELERY_TASK_SERIALIZER,
    result_serializer=Config.CELERY_RESULT_SERIALIZER,
    accept_content=Config.CELERY_ACCEPT_CONTENT,
    timezone=Config.CELERY_TIMEZONE,
    task_track_started=True,
    task_time_limit=Config.JOB_TIMEOUT_SECONDS,
)

_GATES = QuantumGates()
_SINGLE = {
    'h': _GATES.H, 'x': _GATES.X, 'y': _GATES.Y,
    'z': _GATES.Z, 's': _GATES.S, 't': _GATES.T,
    'sdg': _GATES.Sdg, 'tdg': _GATES.Tdg,
}
_PARAM1 = {'rx': _GATES.RX, 'ry': _GATES.RY, 'rz': _GATES.RZ}
_TWO = {
    'cx': _GATES.CNOT, 'cnot': _GATES.CNOT,
    'cz': _GATES.CZ, 'cy': _GATES.CY,
    'swap': _GATES.SWAP,
}


def _run_circuit(circuit, num_qubits, shots, backend,
                 noise_model, use_qec, update_fn=None) -> Dict:
    start_time = time.time()
    mem_start = psutil.Process().memory_info().rss / 1024 / 1024
    job_id = str(uuid.uuid4())[:8]
    logger = NoiseLogger(job_id)

    def _update(msg, pct=0):
        if update_fn:
            update_fn(msg, pct)

    _update('Initializing', 0)

    # ── Noise models ──────────────────────────────────────────────────────────
    pauli_noise = None
    burst_gen = None
    cosmic_sim = None

    if noise_model:
        pauli_err = noise_model.get('pauli_error', 0)
        if pauli_err > 0:
            pauli_noise = PauliNoise(
                single_qubit_error=pauli_err,
                two_qubit_error=noise_model.get('two_qubit_error', pauli_err * 10),
                readout_error=noise_model.get('readout_error', Config.READOUT_ERROR),
            )
        if noise_model.get('burst_events', False):
            burst_gen = BurstEventGenerator(
                burst_rate_per_hour=Config.BURST_RATE_PER_HOUR,
                min_burst_qubits=Config.MIN_BURST_QUBITS,
                max_burst_qubits=Config.MAX_BURST_QUBITS,
                total_qubits=num_qubits,
            )
        # NEW: cosmic ray simulation
        if noise_model.get('cosmic_rays', False):
            _update('Initializing cosmic ray simulator', 5)
            cosmic_sim = CosmicRaySimulator(
                num_qubits=num_qubits,
                base_t1_us=Config.T1_TIME_US,
                base_t2_us=Config.T2_TIME_US,
            )

    # ── QEC ───────────────────────────────────────────────────────────────────
    surface_code = None
    qec_info = None
    effective_qubits = num_qubits
    if use_qec:
        _update('Initializing QEC', 8)
        surface_code = SurfaceCode(num_qubits, code_distance=3)
        effective_qubits = surface_code.num_logical_qubits
        qec_info = surface_code.get_resource_requirements()

    # ── Engine ────────────────────────────────────────────────────────────────
    _update('Initializing engine', 10)
    engine = MPSEngine(num_qubits)

    gate_list = circuit.get('gates', [])
    total_gates = len(gate_list)
    circuit_duration_us = total_gates * Config.TWO_QUBIT_GATE_TIME_NS / 1000.0

    # ── Pre-compute: burst events ──────────────────────────────────────────────
    burst_error_map = np.zeros(num_qubits)
    burst_summary = None
    if burst_gen:
        events_b = burst_gen.generate_events(circuit_duration_us)
        burst_summary = burst_gen.calculate_burst_statistics(events_b)
        burst_error_map = burst_gen.get_error_map(events_b)

    # ── Pre-compute: cosmic ray errors ────────────────────────────────────────
    cosmic_result = None
    cosmic_gate_errors = np.zeros(total_gates)
    if cosmic_sim:
        _update('Simulating cosmic ray events', 12)
        cosmic_result = cosmic_sim.compute_gate_errors(
            gate_list, circuit_duration_us
        )
        cosmic_gate_errors = np.array(cosmic_result['gate_errors'])
        # Log to noise memory layer
        logger.log_cosmic_events(
            cosmic_result['events'], cosmic_result
        )

    # ── Execute gates ──────────────────────────────────────────────────────────
    for idx, gate in enumerate(gate_list):
        _update('Executing circuit', 15 + int((idx / max(total_gates, 1)) * 75))

        gtype  = gate['type'].lower()
        qubits = gate['qubits']
        params = gate.get('params', [])

        if gtype in _SINGLE:
            engine.apply_gate(_SINGLE[gtype](), qubits[0])
        elif gtype in _PARAM1:
            theta = params[0] if params else 0.0
            engine.apply_gate(_PARAM1[gtype](theta), qubits[0])
        elif gtype in _TWO:
            engine.apply_two_qubit_gate(_TWO[gtype](), qubits[0], qubits[1])
        else:
            raise ValueError(f"Unknown gate type: '{gtype}'")

        # ── Pauli noise (per gate, per qubit) ─────────────────────────────────
        if pauli_noise:
            gate_type_str = 'two' if gtype in _TWO else 'single'
            errors = pauli_noise.apply_gate_noise(len(qubits), gate_type_str)
            for qubit_offset, pauli_op in errors:
                target_q = qubits[min(qubit_offset, len(qubits) - 1)]
                err_mat = {'X': _GATES.X(), 'Y': _GATES.Y(),
                           'Z': _GATES.Z()}.get(pauli_op, _GATES.I())
                engine.apply_gate(err_mat, target_q)
                logger.log_gate_error(idx, target_q, 'pauli',
                                      pauli_noise.single_qubit_error)

        # ── Burst events ──────────────────────────────────────────────────────
        if burst_gen:
            for q in qubits:
                if q < num_qubits and burst_error_map[q] > 0.3:
                    sev = float(burst_error_map[q])
                    if np.random.random() < min(sev, 1.0):
                        op = np.random.choice(['X', 'Y', 'Z'])
                        err_mat = {'X': _GATES.X(), 'Y': _GATES.Y(),
                                   'Z': _GATES.Z()}[op]
                        engine.apply_gate(err_mat, q)
                        logger.log_gate_error(idx, q, 'burst', sev)

        # ── Cosmic ray errors (NEW: physics-based) ────────────────────────────
        if cosmic_sim and cosmic_gate_errors[idx] > 0:
            for q in qubits:
                if q < num_qubits:
                    p_err = cosmic_gate_errors[idx]
                    if np.random.random() < p_err:
                        # QP poisoning → mostly phase errors (Z) and some X
                        op = np.random.choice(['X', 'Z', 'Z', 'Z'])  # Z-biased
                        err_mat = {'X': _GATES.X(), 'Z': _GATES.Z()}[op]
                        engine.apply_gate(err_mat, q)
                        logger.log_gate_error(idx, q, 'cosmic_qp', p_err)

    # ── QEC cycle ─────────────────────────────────────────────────────────────
    qec_result = None
    if surface_code:
        _update('Running QEC cycle', 92)
        dummy = np.zeros(2)
        qec_result = surface_code.run_qec_cycle(dummy, patch_id=0)

    # ── Measure ───────────────────────────────────────────────────────────────
    _update('Measuring', 96)
    counts = engine.measure(shots=shots)

    if pauli_noise:
        counts = pauli_noise.apply_readout_noise(counts)

    total_shots = sum(counts.values())
    probabilities = {s: c / total_shots for s, c in counts.items()}

    # ── Finalize logging ──────────────────────────────────────────────────────
    xqp_map = cosmic_result['xqp_map'] if cosmic_result else None
    logger.log_job_summary(num_qubits, total_gates, shots, xqp_map)

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
        'qec_corrections': qec_result,
        'noise_applied': noise_model is not None and bool(noise_model),
        'burst_summary': burst_summary,
        # NEW fields
        'cosmic_ray_result': {
            'events': cosmic_result['statistics'] if cosmic_result else None,
            'poisoned_qubits': cosmic_result['poisoned_qubits'] if cosmic_result else [],
            'affected_regions': cosmic_result['affected_regions'][:10] if cosmic_result else [],
        },
    }


@celery_app.task(bind=True, name='tasks.execute_circuit')
def execute_circuit(self, circuit, num_qubits, shots, backend='mps',
                    noise_model=None, use_qec=False) -> Dict[str, Any]:
    try:
        def _upd(msg, pct=0):
            self.update_state(state='RUNNING', meta={'status': msg, 'progress': pct})
        return _run_circuit(circuit, num_qubits, shots, backend,
                            noise_model, use_qec, _upd)
    except Exception as e:
        return {'error': str(e), 'error_type': type(e).__name__, 'status': 'failed'}


def execute_circuit_sync(circuit, num_qubits, shots, backend='mps',
                         noise_model=None, use_qec=False) -> Dict[str, Any]:
    try:
        return _run_circuit(circuit, num_qubits, shots, backend,
                            noise_model, use_qec)
    except Exception as e:
        return {'error': str(e), 'error_type': type(e).__name__, 'status': 'failed'}


@celery_app.task(name='tasks.cleanup_old_jobs')
def cleanup_old_jobs():
    from ..api.jobs import get_job_queue
    NoiseLogger.clear_old_records(days=7)
    removed = get_job_queue().cleanup_old_jobs(hours=Config.JOB_RETENTION_HOURS)
    return {'removed_jobs': removed, 'timestamp': time.time()}


celery_app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'tasks.cleanup_old_jobs',
        'schedule': 3600.0,
    },
}
