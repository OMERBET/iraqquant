"""
Jobs API - Submit and manage quantum computing jobs (FIXED: results saved correctly)
"""
import threading
from flask import Blueprint, request, jsonify
from ..models.job import QuantumJob, JobQueue, JobStatus
from ..api.auth import require_auth
from ..config import Config

jobs_bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')
job_queue = JobQueue(max_concurrent=Config.MAX_CONCURRENT_JOBS)


def _dispatch_job(job: QuantumJob):
    """
    Execute job in background thread (fallback when Celery not available).
    Updates job status and saves results into the queue automatically.
    """
    from ..workers.tasks import execute_circuit_sync

    job.start()
    results = execute_circuit_sync(
        circuit=job.circuit,
        num_qubits=job.num_qubits,
        shots=job.shots,
        backend=job.backend,
        noise_model=job.noise_model,
        use_qec=job.use_qec,
    )

    if 'error' in results:
        job.fail(results['error'])
    else:
        job.complete(
            results=results,
            execution_time_ms=results.get('execution_time_ms', 0),
            memory_used_mb=results.get('memory_used_mb', 0),
        )


@jobs_bp.route('/submit', methods=['POST'])
@require_auth
def submit_job(user=None):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        circuit    = data.get('circuit')
        num_qubits = data.get('num_qubits', 1)
        shots      = data.get('shots', 1024)
        backend    = data.get('backend', 'mps')
        use_qec    = data.get('use_qec', False)
        noise_model = data.get('noise_model', {})

        if not circuit:
            return jsonify({'error': 'Circuit is required'}), 400
        if not Config.validate_qubits(num_qubits):
            return jsonify({'error': f'Qubits must be {Config.MIN_QUBITS}–{Config.MAX_QUBITS}'}), 400
        if not Config.validate_shots(shots):
            return jsonify({'error': f'Shots must be {Config.MIN_SHOTS}–{Config.MAX_SHOTS}'}), 400
        if backend not in ['mps', 'photonic']:
            return jsonify({'error': 'Backend must be "mps" or "photonic"'}), 400

        job = QuantumJob(
            user_id=user.user_id,
            circuit=circuit,
            num_qubits=num_qubits,
            shots=shots,
            backend=backend,
            noise_model=noise_model,
            use_qec=use_qec,
        )
        job_queue.submit(job)

        user.job_count += 1
        user.total_qubits_used += num_qubits

        # Try Celery first; fall back to thread
        try:
            from ..workers.tasks import execute_circuit as celery_task
            import redis, os
            host = os.getenv('REDIS_HOST', 'localhost')
            port = int(os.getenv('REDIS_PORT', 6379))
            r = redis.Redis(host=host, port=port, socket_connect_timeout=1)
            r.ping()
            celery_task.apply_async(
                kwargs=dict(
                    circuit=job.circuit, num_qubits=job.num_qubits,
                    shots=job.shots, backend=job.backend,
                    noise_model=job.noise_model, use_qec=job.use_qec,
                ),
                task_id=job.job_id,
            )
            # Wire Celery result back: handled via polling on /jobs/<id>/results
            # For simplicity also run in thread so queue stays updated
            raise Exception("use thread for queue update")
        except Exception:
            t = threading.Thread(target=_dispatch_job, args=(job,), daemon=True)
            t.start()

        queued_count = sum(1 for j in job_queue.jobs.values() if j.status == JobStatus.QUEUED)

        return jsonify({
            'success': True,
            'job_id': job.job_id,
            'status': job.status.value,
            'message': 'Job submitted successfully',
            'position_in_queue': queued_count,
        }), 201

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@jobs_bp.route('/<job_id>', methods=['GET'])
@require_auth
def get_job(job_id, user=None):
    try:
        job = job_queue.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        if job.user_id != user.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        return jsonify({'success': True, 'job': job.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/<job_id>/results', methods=['GET'])
@require_auth
def get_results(job_id, user=None):
    try:
        job = job_queue.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        if job.user_id != user.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        if job.status != JobStatus.COMPLETED:
            return jsonify({'error': 'Job not completed', 'status': job.status.value}), 400
        return jsonify({
            'success': True,
            'job_id': job_id,
            'results': job.results,
            'execution_time_ms': job.execution_time_ms,
            'memory_used_mb': job.memory_used_mb,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/<job_id>/cancel', methods=['POST'])
@require_auth
def cancel_job(job_id, user=None):
    try:
        job = job_queue.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        if job.user_id != user.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        if job.status not in [JobStatus.QUEUED, JobStatus.RUNNING]:
            return jsonify({'error': 'Cannot cancel', 'status': job.status.value}), 400
        job.cancel()
        return jsonify({'success': True, 'message': 'Job cancelled'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/list', methods=['GET'])
@require_auth
def list_jobs(user=None):
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)
        jobs = job_queue.get_user_jobs(user.user_id, limit=limit)
        return jsonify({'success': True, 'jobs': [j.to_dict() for j in jobs], 'total': len(jobs)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/queue/status', methods=['GET'])
def queue_status():
    try:
        return jsonify({'success': True, 'queue': job_queue.get_queue_status()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_job_queue():
    return job_queue
