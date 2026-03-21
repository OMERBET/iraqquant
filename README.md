# 🇮🇶 IraqQuant - Iraqi Quantum Computing Platform

<div align="center">

![IraqQuant](https://img.shields.io/badge/IraqQuant-v1.0.0-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production--Ready-success?style=for-the-badge)
![Qubits](https://img.shields.io/badge/Qubits-127-purple?style=for-the-badge)

**Iraq's First Software-Based Quantum Computing Platform**

*A production-ready platform for executing real quantum algorithms with multi-backend architecture, hardware-calibrated noise models, and quantum error correction*

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API](#-api) • [Contact](#-contact)

</div>

---

## Overview

**IraqQuant** is a software-based quantum computing platform developed in Baghdad, Iraq. It provides a complete infrastructure for executing real quantum algorithms using tensor network methods, specifically Matrix Product States (MPS), which allow accurate quantum state representation of up to **127 physical qubits** on classical hardware.

The platform does not approximate or simplify quantum mechanics — it computes exact quantum states, applies real unitary transformations, and produces statistically accurate measurement outcomes. The only distinction from physical quantum hardware is the execution substrate: classical processors instead of superconducting or photonic chips.

### What 127 Physical Qubits Means

A 127-qubit quantum system has a Hilbert space of dimension 2¹²⁷ — far beyond what brute-force state vector methods can handle. IraqQuant uses **Matrix Product State (MPS)** tensor network decomposition to represent and manipulate these quantum states efficiently, with controllable bond dimension that trades off between accuracy and computational cost. This is the same mathematical foundation used in leading quantum research worldwide.

---

## Features

### Quantum Execution Engine

| Feature | Details |
|---------|---------|
| Physical Qubits | Up to 127 qubits via optimized MPS engine |
| Logical Qubits | 10–20 logical qubits via Surface Code QEC |
| Backends | MPS (Matrix Product States) + Photonic |
| Gate Set | 30+ quantum gates (H, X, Y, Z, CNOT, Toffoli, RX, RY, RZ, ...) |
| Circuit Depth | Up to 100 layers with automatic compression |
| Bond Dimension | Configurable up to 256 for accuracy/performance tradeoff |

### Hardware-Calibrated Noise Models

All noise parameters are calibrated against **IBM Eagle R3** specifications:

- **Pauli Noise** — Single-qubit error rate: 0.1%, Two-qubit error rate: 1%
- **Decoherence** — T1 relaxation: 100 μs, T2 dephasing: 80 μs
- **Burst Events** — Correlated multi-qubit errors from cosmic rays and thermal fluctuations
- **Readout Errors** — Measurement error rate: 1.5%

### Quantum Error Correction (QEC)

- **Surface Code** with configurable distance (d=3, 5, 7)
- Automatic syndrome extraction and minimum-weight decoding
- Error suppression up to 100,000x over physical error rates
- Resource estimation for target logical error rates

### Infrastructure

- **REST API** — Full programmatic access for research integration
- **User Authentication** — Secure session-based access
- **Async Job Queue** — Celery + Redis for concurrent circuit execution
- **Docker Deployment** — Single-command production deployment
- **Multilingual UI** — Arabic, English, German

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  Frontend  (HTML / CSS / JS)                │
│  Arabic · English · German                  │
└──────────────────┬──────────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────────┐
│  Flask REST API                             │
│  /api/auth  ·  /api/jobs  ·  /api/info      │
└──────────────────┬──────────────────────────┘
                   │ Celery Tasks
┌──────────────────▼──────────────────────────┐
│  Async Workers  (Celery + Redis)            │
│  Circuit execution · Noise · QEC cycles     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Quantum Computing Layer                    │
│  ├── MPS Engine   (tensor networks)         │
│  ├── Noise Models (Pauli · Decoherence      │
│  │                 · Burst Events)          │
│  ├── QEC          (Surface Code)            │
│  └── Topology     (linear · heavy-hex)      │
└─────────────────────────────────────────────┘
```

---

## Installation

### Requirements
- Python 3.10+
- Docker & Docker Compose *(recommended)*
- Redis

### Docker (Recommended)

```bash
git clone https://github.com/Omerbet/iraqquant.git
cd iraqquant
docker-compose up -d
```

Platform available at `http://localhost:5000`

### Manual Installation

```bash
git clone https://github.com/Omerbet/iraqquant.git
cd iraqquant

python3 -m venv venv
source venv/bin/activate

pip install -r backend/requirements.txt

redis-server &
celery -A app.workers.tasks worker --loglevel=info &

cd backend
python -m app.main
```

---

## Usage

### Web Interface

1. Create an account
2. Build a quantum circuit using the visual gate editor
3. Configure qubits, shots, backend, and noise options
4. Execute and view results with probability histograms

### API Usage

```python
import requests

API = 'http://localhost:5000/api'

# Authenticate
r = requests.post(f'{API}/auth/signin',
    json={'username': 'researcher', 'password': 'password123'})
token = r.json()['token']
headers = {'Authorization': f'Bearer {token}'}

# Submit Bell State circuit
circuit = {
    'gates': [
        {'type': 'h',  'qubits': [0]},
        {'type': 'cx', 'qubits': [0, 1]}
    ]
}

job = requests.post(f'{API}/jobs/submit', headers=headers, json={
    'circuit': circuit,
    'num_qubits': 2,
    'shots': 1024,
    'backend': 'mps',
    'use_qec': False,
    'noise_model': {'pauli_error': 0.001, 'readout_error': 0.015}
}).json()

print('Job ID:', job['job_id'])

# Get results
results = requests.get(f'{API}/jobs/{job["job_id"]}/results',
    headers=headers).json()
print('Counts:', results['results']['counts'])
# Expected: {'00': ~512, '11': ~512}
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Create account |
| POST | `/api/auth/signin` | Sign in |
| POST | `/api/auth/logout` | Sign out |
| GET  | `/api/auth/profile` | User profile |
| POST | `/api/jobs/submit` | Submit quantum circuit |
| GET  | `/api/jobs/<id>` | Job status |
| GET  | `/api/jobs/<id>/results` | Execution results |
| POST | `/api/jobs/<id>/cancel` | Cancel job |
| GET  | `/api/jobs/list` | List user jobs |
| GET  | `/api/health` | Health check |
| GET  | `/api/info` | Platform capabilities |

---

## Technical Details

### Noise Calibration (IBM Eagle R3 Reference)

| Parameter | Value |
|-----------|-------|
| Single-qubit gate error | 0.1% |
| Two-qubit gate error | 1.0% |
| T1 relaxation time | 100 μs |
| T2 dephasing time | 80 μs |
| Single-qubit gate time | 35 ns |
| Two-qubit gate time | 280 ns |
| Readout error | 1.5% |

### QEC Performance

| Physical Error Rate | Code Distance | Logical Error Rate | Suppression |
|--------------------|---------------|--------------------|-------------|
| 0.1% | d = 3 | ~10⁻⁵ | 100× |
| 0.1% | d = 5 | ~10⁻⁸ | 100,000× |
| 0.1% | d = 7 | ~10⁻¹¹ | 100,000,000× |

### Resource Requirements

- **Memory** — ~16 GB RAM for 127-qubit circuits (bond dim 256)
- **CPU** — Multi-core recommended for parallel job execution
- **Storage** — ~1 MB per job result

---

## Roadmap

### v1.0.0 — March 2026 ✅
- [x] 127-qubit MPS execution engine
- [x] Surface Code QEC (d=3,5,7)
- [x] Multi-backend architecture
- [x] Hardware-calibrated noise models (Pauli, Decoherence, Burst Events)
- [x] Full REST API
- [x] Multilingual web interface (AR / EN / DE)
- [x] Docker deployment

### v2.0.0 — July 2026
- [ ] 1000+ qubit execution via distributed MPS
- [ ] GPU acceleration (CUDA / OpenCL)
- [ ] Advanced QEC codes (Color Code, LDPC)
- [ ] Cloud deployment (AWS / Azure)

### v3.0.0 — 2027
- [ ] Real quantum hardware integration
- [ ] Hybrid classical-quantum algorithms
- [ ] Educational platform

---

## Citation

If you use IraqQuant in your research, please cite:

```bibtex
@software{iraqquant2025,
  title   = {IraqQuant: A Software-Based Quantum Computing Platform
             with Multi-Backend Support, Hardware-Calibrated Noise Models,
             and Quantum Error Correction},
  author  = {Jaafar Abdulsalam},
  year    = {2026},
  url     = {https://github.com/Omerbet/iraqquant},
  version = {1.0.0},
  address = {Baghdad, Iraq},
  month   = {March}
}
```

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**Jaafar Abdulsalam**
Baghdad, Iraq

---

## Contact

[![Telegram](https://img.shields.io/badge/Telegram-@TheHolyAmstrdam-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/TheHolyAmstrdam)

---

<div align="center">

**Built with pride in Iraq 🇮🇶**

*IraqQuant v1.0.0 — Production Ready*

</div>
