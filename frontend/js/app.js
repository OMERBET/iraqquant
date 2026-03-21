/**
 * app.js - Main application logic
 */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Smooth scroll nav links ──────────────────────────────────────────── */
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
      const href = link.getAttribute('href');
      if (href && href.startsWith('#')) {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) target.scrollIntoView({ behavior: 'smooth' });
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        link.classList.add('active');
      }
    });
  });

  /* ── Learn More ───────────────────────────────────────────────────────── */
  document.getElementById('btnLearnMore')?.addEventListener('click', () => {
    document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' });
  });

  /* ── Intersection Observer: active nav on scroll ─────────────────────── */
  const sections = document.querySelectorAll('section[id]');
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        document.querySelectorAll('.nav-link').forEach(l => {
          l.classList.toggle('active', l.getAttribute('href') === `#${id}`);
        });
      }
    });
  }, { threshold: 0.4 });
  sections.forEach(s => observer.observe(s));

  /* ── Close modals on backdrop click ─────────────────────────────────── */
  ['signInModal', 'signUpModal'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('click', e => {
      if (e.target === el) { el.style.display = 'none'; }
    });
  });

  /* ── Load platform stats from API ────────────────────────────────────── */
  fetch('/api/info')
    .then(r => r.json())
    .then(data => {
      if (data.capabilities) {
        const c = data.capabilities;
        const statNums = document.querySelectorAll('.stat-number');
        if (statNums[0]) statNums[0].textContent = c.max_qubits;
        if (statNums[1]) statNums[1].textContent = c.backends?.length || 2;
      }
    })
    .catch(() => { /* API not yet available — show static values */ });

  /* ── Inject Chart.js from CDN if not present ─────────────────────────── */
  if (!window.Chart) {
    const s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js';
    document.head.appendChild(s);
  }

  /* ── stat-box style (used by circuit.js results) ─────────────────────── */
  const style = document.createElement('style');
  style.textContent = `
    .stat-box {
      background: var(--light);
      border-radius: 8px;
      padding: .75rem 1rem;
      font-size: .9rem;
      border: 1px solid #e2e8f0;
    }
    .stat-box strong { display:block; color: var(--primary-color); margin-bottom:.25rem; }
    .form-error { color:#ef4444; font-size:.9rem; margin-top:.5rem; }
    #signInModal, #signUpModal { display:none; justify-content:center; align-items:center; }
  `;
  document.head.appendChild(style);

});
