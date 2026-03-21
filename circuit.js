/**
 * circuit.js - Circuit builder and job execution
 */

const API = window.API || '/api';
let _circuit = { gates: [] };
let _pollingInterval = null;

/* ── Circuit state ───────────────────────────────────────────────────────── */
function addGate(type) {
  const numQubits = parseInt(document.getElementById('numQubits').value) || 2;
  let gate;

  if (['cx', 'cz', 'swap'].includes(type)) {
    if (numQubits < 2) {
      alert('البوابات ذات الكيوبتين تحتاج على الأقل 2 كيوبت');
      return;
    }
    gate = { type, qubits: [0, 1] };
  } else {
    gate = { type, qubits: [0] };
  }

  _circuit.gates.push(gate);
  renderCircuit();
}

function removeGate(index) {
  _circuit.gates.splice(index, 1);
  renderCircuit();
}

function clearCircuit() {
  _circuit = { gates: [] };
  renderCircuit();
}

function renderCircuit() {
  const display = document.getElementById('circuitDisplay');
  if (_circuit.gates.length === 0) {
    display.innerHTML = '<p class="placeholder">قم بإضافة بوابات لبناء الدائرة</p>';
    return;
  }
  display.innerHTML = _circuit.gates.map((g, i) => `
    <span class="circuit-gate" title="اضغط للحذف" onclick="removeGate(${i})" style="cursor:pointer">
      ${g.type.toUpperCase()}
      <small style="opacity:.7">[${g.qubits.join(',')}]</small>
      <span style="opacity:.5;margin-right:.3rem">×</span>
    </span>
  `).join('');
}

/* ── Execution ───────────────────────────────────────────────────────────── */
async function runCircuit() {
  if (!isLoggedIn()) { showModal('signInModal'); return; }
  if (_circuit.gates.length === 0) {
    setStatus('أضف بوابات أولاً', 'warning'); return;
  }

  const numQubits  = parseInt(document.getElementById('numQubits').value)  || 2;
  const numShots   = parseInt(document.getElementById('numShots').value)   || 1024;
  const backend    = document.getElementById('backend').value;
  const useQec     = document.getElementById('useQEC').checked;
  const useNoise   = document.getElementById('useNoise').checked;

  const payload = {
    circuit: _circuit,
    num_qubits: numQubits,
    shots: numShots,
    backend,
    use_qec: useQec,
    noise_model: useNoise ? { pauli_error: 0.001, readout_error: 0.015 } : {},
  };

  setStatus('جاري إرسال الدائرة...', 'info');
  document.getElementById('btnRunCircuit').disabled = true;

  try {
    const res = await fetch(`${API}/jobs/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.success) {
      setStatus('جاري التنفيذ...', 'info');
      pollResults(data.job_id);
    } else {
      setStatus(data.error || 'خطأ في الإرسال', 'error');
      document.getElementById('btnRunCircuit').disabled = false;
    }
  } catch (err) {
    setStatus('خطأ في الاتصال بالسيرفر', 'error');
    document.getElementById('btnRunCircuit').disabled = false;
  }
}

function pollResults(jobId) {
  let attempts = 0;
  const MAX = 60;

  if (_pollingInterval) clearInterval(_pollingInterval);

  _pollingInterval = setInterval(async () => {
    attempts++;
    if (attempts > MAX) {
      clearInterval(_pollingInterval);
      setStatus('انتهت مهلة الانتظار', 'error');
      document.getElementById('btnRunCircuit').disabled = false;
      return;
    }

    try {
      const res = await fetch(`${API}/jobs/${jobId}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      const data = await res.json();
      const status = data.job?.status;

      if (status === 'completed') {
        clearInterval(_pollingInterval);
        fetchAndShowResults(jobId);
      } else if (status === 'failed') {
        clearInterval(_pollingInterval);
        setStatus('فشل التنفيذ: ' + (data.job?.error_message || ''), 'error');
        document.getElementById('btnRunCircuit').disabled = false;
      } else {
        setStatus(`جاري التنفيذ... (${attempts}s)`, 'info');
      }
    } catch (_) { /* retry */ }
  }, 1000);
}

async function fetchAndShowResults(jobId) {
  try {
    const res = await fetch(`${API}/jobs/${jobId}/results`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    const data = await res.json();

    if (data.success) {
      renderResults(data.results);
      setStatus('اكتمل التنفيذ ✓', 'success');
    } else {
      setStatus('فشل جلب النتائج', 'error');
    }
  } catch (err) {
    setStatus('خطأ في جلب النتائج', 'error');
  } finally {
    document.getElementById('btnRunCircuit').disabled = false;
  }
}

/* ── Results rendering ───────────────────────────────────────────────────── */
let _chart = null;

function renderResults(results) {
  const container = document.getElementById('results');
  container.style.display = 'block';

  const counts = results.counts || {};
  const labels = Object.keys(counts);
  const values = Object.values(counts);
  const totalShots = values.reduce((a, b) => a + b, 0);

  // Stats
  const statsEl = document.getElementById('resultStats');
  statsEl.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-top:1rem">
      <div class="stat-box"><strong>وقت التنفيذ</strong><br>${results.execution_time_ms?.toFixed(1) || 0} ms</div>
      <div class="stat-box"><strong>عدد القياسات</strong><br>${results.shots?.toLocaleString()}</div>
      <div class="stat-box"><strong>الكيوبتات</strong><br>${results.num_qubits}</div>
      <div class="stat-box"><strong>الذاكرة</strong><br>${results.memory_used_mb?.toFixed(1) || 0} MB</div>
    </div>
  `;

  // Chart
  const ctx = document.getElementById('resultsChart').getContext('2d');
  if (_chart) _chart.destroy();

  _chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'عدد القياسات',
        data: values,
        backgroundColor: labels.map((_, i) =>
          `hsl(${220 + i * (140 / Math.max(labels.length, 1))},70%,55%)`),
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const pct = ((ctx.raw / totalShots) * 100).toFixed(1);
              return `${ctx.raw} قياس (${pct}%)`;
            },
          },
        },
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: 'العدد' } },
        x: { title: { display: true, text: 'الحالة' } },
      },
    },
  });
}

/* ── Status helper ───────────────────────────────────────────────────────── */
function setStatus(msg, type = 'info') {
  const el = document.getElementById('jobStatus');
  const colors = { info: '#dbeafe', success: '#d1fae5', error: '#fee2e2', warning: '#fef9c3' };
  const borders = { info: '#3b82f6', success: '#10b981', error: '#ef4444', warning: '#f59e0b' };
  el.style.background    = colors[type]  || colors.info;
  el.style.borderColor   = borders[type] || borders.info;
  el.innerHTML = `<p>${msg}</p>`;
}

/* ── DOM wiring ─────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.gate-btn').forEach(btn => {
    btn.addEventListener('click', () => addGate(btn.dataset.gate));
  });
  document.getElementById('btnRunCircuit').addEventListener('click', runCircuit);
  document.getElementById('btnClearCircuit').addEventListener('click', clearCircuit);
});
