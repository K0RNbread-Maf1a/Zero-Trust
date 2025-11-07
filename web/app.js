// Minimal client logic for the paywalled portal
async function fetchPayConfig() {
  const res = await fetch('/pay/config', { credentials: 'include' });
  if (!res.ok) return { stripe_enabled: false, dev_enabled: true };
  return res.json();
}

async function checkPaid() {
  const res = await fetch('/pay/status', { credentials: 'include' });
  if (!res.ok) return { paid: false };
  return res.json();
}

async function devPay() {
  const res = await fetch('/pay/dev/complete', { method: 'POST', credentials: 'include' });
  if (!res.ok) throw new Error('Payment failed');
  return res.json();
}

function setPaidUI(paid) {
  const badge = document.getElementById('pay-status');
  const paywall = document.getElementById('paywall');
  const app = document.getElementById('app');
  if (paid) {
    badge.textContent = 'Paid session';
    badge.style.background = '#064e3b';
    badge.style.color = '#a7f3d0';
    paywall.classList.add('hidden');
    app.classList.remove('hidden');
  } else {
    badge.textContent = 'Payment required';
    badge.style.background = '#1f2937';
    badge.style.color = '#9ca3af';
    paywall.classList.remove('hidden');
    app.classList.add('hidden');
  }
}

function tabs() {
  const tabEls = document.querySelectorAll('.tab');
  tabEls.forEach(t => t.addEventListener('click', () => {
    tabEls.forEach(x => x.classList.remove('active'));
    t.classList.add('active');
    const id = t.getAttribute('data-tab');
    document.querySelectorAll('[id^="tab-"]').forEach(p => p.classList.add('hidden'));
    document.getElementById('tab-' + id).classList.remove('hidden');
  }));
}

function setStatusWidget(status) {
  const el = document.getElementById('status-widget');
  if (!el) return;
  const bits = [];
  if (status.paid) bits.push('Paid'); else bits.push('Unpaid');
  if (status.verified) bits.push('Verified'); else bits.push('Unverified');
  if (status.customer_id) bits.push('Customer: ' + status.customer_id.slice(0,6) + '…');
  el.textContent = bits.join(' | ');
}

async function registerStart() {
  const email = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;
  const out = document.getElementById('reg-start-msg');
  const res = await fetch('/register/start', { method: 'POST', credentials: 'include', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ email, password }) });
  const data = await res.json().catch(() => ({}));
  out.textContent = res.ok ? ('Verification sent' + (data.code ? ' (code: ' + data.code + ')' : '')) : (data.detail || 'Error');
}

async function registerVerify() {
  const email = document.getElementById('ver-email').value;
  const code = document.getElementById('ver-code').value;
  const out = document.getElementById('reg-verify-msg');
  const res = await fetch('/register/verify', { method: 'POST', credentials: 'include', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ email, code }) });
  const data = await res.json().catch(() => ({}));
  out.textContent = res.ok ? 'Verified!' : (data.detail || 'Error');
  if (res.ok) {
    const status = await checkPaid();
    setPaidUI(status.paid);
    setStatusWidget(status);
  }
}

async function registerLogin() {
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const out = document.getElementById('reg-login-msg');
  const res = await fetch('/register/login', { method: 'POST', credentials: 'include', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ email, password }) });
  const data = await res.json().catch(() => ({}));
  out.textContent = res.ok ? 'Logged in (legacy)' : (data.detail || 'Error');
  if (res.ok) {
    const status = await checkPaid();
    setPaidUI(status.paid && status.logged_in);
    setStatusWidget(status);
  }
}

let _loginToken = null;

async function loginPassword() {
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const msg = document.getElementById('reg-login-msg');
  const twofaStep = document.getElementById('twofa-step');
  const enroll = document.getElementById('twofa-enroll');
  twofaStep.classList.add('hidden');
  enroll.classList.add('hidden');
  msg.textContent = '';

  const res = await fetch('/auth/login_password', { method: 'POST', credentials: 'include', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ email, password }) });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    msg.textContent = data.detail || 'Error';
    return;
  }

  if (data.requires_2fa_enrollment) {
    // Show enrollment UI
    enroll.classList.remove('hidden');
    document.getElementById('twofa-secret').value = data.secret || '';
    const qr = document.getElementById('twofa-qr');
    if (qr && data.qr_data_url) qr.src = data.qr_data_url;
    msg.textContent = '2FA enrollment required.';
    return;
  }

  if (data.two_factor_required && data.login_token) {
    _loginToken = data.login_token;
    twofaStep.classList.remove('hidden');
    msg.textContent = 'Enter your authenticator code to continue.';
    return;
  }

  msg.textContent = 'Unexpected response';
}

async function twofaVerify() {
  const code = document.getElementById('twofa-code').value;
  const out = document.getElementById('twofa-msg');
  const res = await fetch('/auth/2fa_verify', { method: 'POST', credentials: 'include', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ login_token: _loginToken, code }) });
  const data = await res.json().catch(() => ({}));
  out.textContent = res.ok ? '2FA success' : (data.detail || 'Error');
  if (res.ok) {
    const status = await checkPaid();
    setPaidUI(status.paid && status.logged_in);
    setStatusWidget(status);
  }
}

async function twofaEnrollVerify() {
  const email = document.getElementById('login-email').value;
  const code = document.getElementById('twofa-enroll-code').value;
  const out = document.getElementById('twofa-enroll-msg');
  const res = await fetch('/2fa/enroll_verify', { method: 'POST', credentials: 'include', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ email, code }) });
  const data = await res.json().catch(() => ({}));
  out.textContent = res.ok ? '2FA enabled. Click Continue again.' : (data.detail || 'Error');
}

async function listFiles() {
  const path = document.getElementById('fs-path').value || '/';
  const res = await fetch(`/api/files/list?path=${encodeURIComponent(path)}`, { credentials: 'include' });
  const out = document.getElementById('fs-list');
  out.textContent = res.ok ? JSON.stringify(await res.json(), null, 2) : await res.text();
}

async function readFile() {
  const path = document.getElementById('fs-read-path').value;
  const res = await fetch(`/api/files/read?path=${encodeURIComponent(path)}`, { credentials: 'include' });
  const out = document.getElementById('fs-content');
  out.textContent = res.ok ? JSON.stringify(await res.json(), null, 2) : await res.text();
}

async function runQuery() {
  const q = document.getElementById('db-query').value;
  const res = await fetch('/api/database/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ query: q })
  });
  const out = document.getElementById('db-result');
  out.textContent = res.ok ? JSON.stringify(await res.json(), null, 2) : await res.text();
}

async function genKey() {
  const name = document.getElementById('key-name').value || 'portal';
  const perms = (document.getElementById('key-perms').value || '').split(',').map(s => s.trim()).filter(Boolean);
  const res = await fetch('/api/keys/generate', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
    body: JSON.stringify({ name, permissions: perms })
  });
  const out = document.getElementById('key-result');
  out.textContent = res.ok ? JSON.stringify(await res.json(), null, 2) : await res.text();
}

async function createStripeCheckout() {
  const res = await fetch('/pay/create-checkout-session', { method: 'POST', credentials: 'include' });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Failed to create checkout session');
  }
  const data = await res.json();
  window.location.href = data.url;
}

window.addEventListener('DOMContentLoaded', async () => {
  // Configure buttons visibility based on /pay/config
  try {
    const cfg = await fetchPayConfig();
    const stripeSec = document.getElementById('stripe-section');
    const devSec = document.getElementById('devpay-section');
    if (stripeSec) stripeSec.style.display = cfg.stripe_enabled ? 'block' : 'none';
    if (devSec) devSec.style.display = cfg.dev_enabled ? 'block' : 'none';
    const legacyBtn = document.getElementById('btn-reg-login');
    if (legacyBtn) legacyBtn.style.display = cfg.force_2fa ? 'none' : 'inline-block';
  } catch {}

  const devBtn = document.getElementById('btn-subscribe');
  if (devBtn) {
    devBtn.addEventListener('click', async () => {
      try {
        await devPay();
        const status = await checkPaid();
        setPaidUI(status.paid);
      } catch (e) {
        alert('Payment failed: ' + e.message);
      }
    });
  }

  const stripeBtn = document.getElementById('btn-subscribe-stripe');
  if (stripeBtn) {
    stripeBtn.addEventListener('click', async () => {
      try {
        await createStripeCheckout();
      } catch (e) {
        alert('Checkout error: ' + e.message);
      }
    });
  }

  // Login with 2FA flow
  const lp = document.getElementById('btn-login-password'); if (lp) lp.addEventListener('click', loginPassword);
  const lv = document.getElementById('btn-twofa-verify'); if (lv) lv.addEventListener('click', twofaVerify);
  const le = document.getElementById('btn-twofa-enroll-verify'); if (le) le.addEventListener('click', twofaEnrollVerify);

  tabs();
  // Registration handlers
  const rs = document.getElementById('btn-reg-start'); if (rs) rs.addEventListener('click', registerStart);
  const rv = document.getElementById('btn-reg-verify'); if (rv) rv.addEventListener('click', registerVerify);
  const rl = document.getElementById('btn-reg-login'); if (rl) rl.addEventListener('click', registerLogin);

  document.getElementById('btn-list').addEventListener('click', listFiles);
  document.getElementById('btn-read').addEventListener('click', readFile);
  document.getElementById('btn-query').addEventListener('click', runQuery);
  document.getElementById('btn-gen').addEventListener('click', genKey);

  const status = await checkPaid();
  setPaidUI(status.paid && status.logged_in);
  setStatusWidget(status);
});
