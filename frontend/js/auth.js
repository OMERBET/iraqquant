/**
 * auth.js - Authentication module
 */

const API = '/api';
let _token = localStorage.getItem('iq_token') || null;
let _user  = JSON.parse(localStorage.getItem('iq_user') || 'null');

/* ── helpers ─────────────────────────────────────────────────────────────── */
function saveSession(token, user) {
  _token = token; _user = user;
  localStorage.setItem('iq_token', token);
  localStorage.setItem('iq_user', JSON.stringify(user));
}
function clearSession() {
  _token = null; _user = null;
  localStorage.removeItem('iq_token');
  localStorage.removeItem('iq_user');
}
function getToken()    { return _token; }
function getCurrentUser() { return _user; }
function isLoggedIn()  { return !!_token; }

/* ── API calls ───────────────────────────────────────────────────────────── */
async function apiSignUp(username, email, password) {
  const res = await fetch(`${API}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password }),
  });
  return res.json();
}

async function apiSignIn(username, password) {
  const res = await fetch(`${API}/auth/signin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  return res.json();
}

async function apiLogout() {
  if (!_token) return;
  await fetch(`${API}/auth/logout`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${_token}` },
  }).catch(() => {});
  clearSession();
}

/* ── UI wiring ───────────────────────────────────────────────────────────── */
function showModal(id)  { document.getElementById(id).style.display = 'flex'; }
function hideModal(id)  { document.getElementById(id).style.display = 'none'; }
function showError(id, msg) {
  let el = document.getElementById(id);
  if (!el) {
    el = document.createElement('p');
    el.id = id; el.className = 'form-error';
    el.style.cssText = 'color:#ef4444;margin-top:.5rem;font-size:.9rem';
  }
  el.textContent = msg;
  return el;
}

function updateNavUI() {
  const loggedIn = isLoggedIn();
  document.getElementById('btnSignIn').style.display  = loggedIn ? 'none' : '';
  document.getElementById('btnSignUp').style.display  = loggedIn ? 'none' : '';
  document.getElementById('userMenu').style.display   = loggedIn ? 'flex' : 'none';
  if (loggedIn && _user) {
    document.getElementById('username').textContent = _user.username;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  updateNavUI();

  /* open modals */
  document.getElementById('btnSignIn').addEventListener('click', () => showModal('signInModal'));
  document.getElementById('btnSignUp').addEventListener('click', () => showModal('signUpModal'));
  document.getElementById('btnGetStarted')?.addEventListener('click', () => {
    if (isLoggedIn()) {
      document.getElementById('playground').style.display = 'block';
      document.getElementById('playground').scrollIntoView({ behavior: 'smooth' });
    } else { showModal('signInModal'); }
  });

  /* close modals */
  document.querySelectorAll('.close').forEach(btn => {
    btn.addEventListener('click', () => {
      hideModal('signInModal'); hideModal('signUpModal');
    });
  });
  document.getElementById('switchToSignUp')?.addEventListener('click', e => {
    e.preventDefault(); hideModal('signInModal'); showModal('signUpModal');
  });
  document.getElementById('switchToSignIn')?.addEventListener('click', e => {
    e.preventDefault(); hideModal('signUpModal'); showModal('signInModal');
  });

  /* sign-in form */
  document.getElementById('signInForm').addEventListener('submit', async e => {
    e.preventDefault();
    const username = document.getElementById('signInUsername').value.trim();
    const password = document.getElementById('signInPassword').value;
    const btn = e.target.querySelector('button[type=submit]');
    btn.disabled = true; btn.textContent = '...';

    const data = await apiSignIn(username, password);
    btn.disabled = false; btn.textContent = 'دخول';

    if (data.success) {
      saveSession(data.token, data.user);
      hideModal('signInModal');
      updateNavUI();
      document.getElementById('playground').style.display = 'block';
    } else {
      const err = showError('signInError', data.error || 'فشل تسجيل الدخول');
      e.target.appendChild(err);
    }
  });

  /* sign-up form */
  document.getElementById('signUpForm').addEventListener('submit', async e => {
    e.preventDefault();
    const username = document.getElementById('signUpUsername').value.trim();
    const email    = document.getElementById('signUpEmail').value.trim();
    const password = document.getElementById('signUpPassword').value;
    const btn = e.target.querySelector('button[type=submit]');
    btn.disabled = true; btn.textContent = '...';

    const data = await apiSignUp(username, email, password);
    btn.disabled = false; btn.textContent = 'إنشاء حساب';

    if (data.success) {
      /* auto sign-in after registration */
      const loginData = await apiSignIn(username, password);
      if (loginData.success) {
        saveSession(loginData.token, loginData.user);
        hideModal('signUpModal');
        updateNavUI();
        document.getElementById('playground').style.display = 'block';
      }
    } else {
      const err = showError('signUpError', data.error || 'فشل إنشاء الحساب');
      e.target.appendChild(err);
    }
  });

  /* logout */
  document.getElementById('btnLogout').addEventListener('click', async () => {
    await apiLogout();
    updateNavUI();
    document.getElementById('playground').style.display = 'none';
  });
});
