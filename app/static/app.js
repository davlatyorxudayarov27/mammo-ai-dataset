'use strict';

const $ = (id) => document.getElementById(id);
const SVG_NS = 'http://www.w3.org/2000/svg';

const state = {
  current: null,
  meta: null,
  frame: 0,
  frames: 1,
  wc: null, ww: null,
  defaultWc: null, defaultWw: null,
  invert: false,
  scale: 1, tx: 0, ty: 0,
  fitScale: 1,
  localEnabled: false,
  tool: 'select',
  annotations: [],
  selectedId: null,
  labels: [],
  birads: [],
  saving: false,
  dirty: false,
  aiAvailable: false,
  aiModels: [],
  suggestions: [],
  allSuggestions: [],
  aiThreshold: 0.25,
};

function setStatus(msg) { $('status').textContent = msg; }

const TOKEN_KEY = 'mamograf_jwt';
function getToken() { return localStorage.getItem(TOKEN_KEY); }
function setToken(t) { if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY); }

async function api(url, opts) {
  opts = opts || {};
  const headers = new Headers(opts.headers || {});
  const tok = getToken();
  if (tok && !headers.has('Authorization')) headers.set('Authorization', `Bearer ${tok}`);
  const res = await fetch(url, { ...opts, headers });
  if (res.status === 401) {
    setToken(null);
    state._user = null;
    updateUserBar();
    if (state.authRequired) showLoginModal('Sessiya tugadi. Qayta kiring.');
    throw new Error('401 Unauthorized');
  }
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    throw new Error(`${res.status} ${res.statusText}: ${txt}`);
  }
  return res;
}
async function apiJson(url, opts) { return (await api(url, opts)).json(); }

function el(name, attrs, children) {
  const e = document.createElementNS(SVG_NS, name);
  if (attrs) for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (children) for (const c of children) e.appendChild(c);
  return e;
}

function clamp01(v) { return Math.max(0, Math.min(1, v)); }
function uid() { return 'b' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
function colorFor(label) {
  const m = state.labels.find(l => l.name === label);
  return m ? m.color : '#ff5050';
}

// (A2) AI annotation zonasi -> rang. Backend `zone` maydonida jo'natadi.
const AI_ZONE_COLORS = {
  auto_accept: '#22c55e',   // yashil
  review:      '#eab308',   // sariq
  suspect:     '#ef4444',   // qizil (pulsatsiya — CSS .ai-zone-suspect orqali)
};
function colorForAnn(a) {
  if (a && a.zone && AI_ZONE_COLORS[a.zone]) return AI_ZONE_COLORS[a.zone];
  return colorFor(a && a.label);
}
function aiZoneClass(a) {
  return (a && a.zone) ? ` ai-zone-${a.zone}` : '';
}

function refSource() {
  if (!state.current) return null;
  return state.current.kind === 'upload' ? 'upload' : 'local';
}
function refValue() {
  if (!state.current) return null;
  return state.current.kind === 'upload' ? state.current.id : state.current.path;
}

function imageUrl() {
  if (!state.current) return '';
  const params = new URLSearchParams();
  params.set('frame', state.frame);
  if (state.wc != null) params.set('wc', state.wc);
  if (state.ww != null) params.set('ww', state.ww);
  if (state.invert) params.set('invert', 'true');
  if (state.current.kind === 'upload') {
    return `/api/files/${encodeURIComponent(state.current.id)}/image?${params}`;
  }
  params.set('path', state.current.path);
  return `/api/local/image?${params}`;
}

async function loadConfig() {
  const cfg = await apiJson('/api/config');
  state.localEnabled = !!cfg.local_browsing;
  state.authRequired = !!cfg.auth_required;
  if (state.localEnabled) $('localTabBtn').hidden = false;
}

function showLoginModal(errMsg) {
  $('loginErr').textContent = errMsg || '';
  $('loginModal').hidden = false;
  setTimeout(() => $('loginUsername').focus(), 50);
}
function hideLoginModal() {
  $('loginModal').hidden = true;
  $('loginErr').textContent = '';
}

function updateUserBar() {
  const info = $('userInfo');
  const logout = $('logoutBtn');
  const login = $('loginBtn');
  const admin = $('adminBtn');
  const stats = $('statsBtn');
  const bell = $('bellWrap');
  if (state._user) {
    const name = state._user.display_name || state._user.username;
    info.innerHTML = `${name} <span class="role">${state._user.role}</span>`;
    info.hidden = false;
    logout.hidden = false;
    login.hidden = true;
    admin.hidden = state._user.role !== 'admin';
    stats.hidden = !(state._user.role === 'admin' || state._user.role === 'reviewer');
    $('pacsBtn').hidden = !(state._user.role === 'admin' || state._user.role === 'reviewer');
    $('overviewBtn').hidden = false;
    $('auditBtn').hidden = !(state._user.role === 'admin' || state._user.role === 'reviewer');
    $('reviewBtn').hidden = !(state._user.role === 'admin' || state._user.role === 'reviewer');
    $('exportAnnBtn').hidden = false;
    $('reportBtn').hidden = false;
    $('trainPrepBtn').hidden = !(state._user.role === 'admin' || state._user.role === 'reviewer');
    $('modelMgrBtn').hidden = !(state._user.role === 'admin' || state._user.role === 'reviewer');
    const ms = $('modelStudioLink'); if (ms) ms.hidden = !(state._user.role === 'admin' || state._user.role === 'reviewer');
    $('totpBtn').hidden = false;
    $('totpBtn').textContent = state._user.totp_enrolled ? '🔒' : '🔓';
    $('totpBtn').title = state._user.totp_enrolled
      ? "2FA yoqilgan — boshqarish"
      : "2FA o'chirilgan — yoqish tavsiya etiladi";
    bell.hidden = false;
  } else {
    info.hidden = true;
    logout.hidden = true;
    admin.hidden = true;
    stats.hidden = true;
    $('pacsBtn').hidden = true;
    $('overviewBtn').hidden = true;
    $('auditBtn').hidden = true;
    $('reviewBtn').hidden = true;
    $('exportAnnBtn').hidden = true;
    $('reportBtn').hidden = true;
    $('trainPrepBtn').hidden = true;
    $('modelMgrBtn').hidden = true;
    const ms2 = $('modelStudioLink'); if (ms2) ms2.hidden = true;
    $('activeLearnBadge').hidden = true;
    $('totpBtn').hidden = true;
    bell.hidden = true;
    login.hidden = !state.authRequired;
  }
}

function isAnnotator() { return state._user && state._user.role === 'annotator'; }
function isReviewer() { return state._user && (state._user.role === 'reviewer' || state._user.role === 'admin'); }
function isAdmin() { return state._user && state._user.role === 'admin'; }
function ownAnn(a) { return state._user && a.created_by === state._user.username; }
function canEditAnn(a) {
  if (!state._user) return false;
  if (a.status === 'approved' && isAnnotator()) return false;
  if (isAnnotator() && a.created_by && !ownAnn(a)) return false;
  return true;
}

async function attemptResumeSession() {
  if (!getToken()) return false;
  try {
    const me = await apiJson('/api/auth/me');
    state._user = me;
    updateUserBar();
    return true;
  } catch (e) {
    setToken(null);
    state._user = null;
    return false;
  }
}

async function doLogin(username, password, totpCode) {
  const body = { username, password };
  if (totpCode) body.totp_code = totpCode;
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let parsed = null;
    try { parsed = await res.json(); } catch (e) {}
    const detail = parsed && parsed.detail;
    if (res.status === 401 && detail && typeof detail === 'object' && detail.error === 'totp_required') {
      const err = new Error('TOTP kodi kerak');
      err.totp_required = true;
      throw err;
    }
    if (res.status === 401) throw new Error("Noto'g'ri foydalanuvchi/parol/kod");
    throw new Error(typeof detail === 'string' ? detail : `xato: ${res.status}`);
  }
  const data = await res.json();
  setToken(data.token);
  state._user = data.user;
  updateUserBar();
  return data;
}

function doLogout() {
  setToken(null);
  state._user = null;
  updateUserBar();
  if (state.authRequired) showLoginModal();
}

(function bindAuthUi() {
  const form = $('loginForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const u = $('loginUsername').value.trim();
    const p = $('loginPassword').value;
    const t = $('loginTotp').value.trim();
    if (!u || !p) return;
    const submit = $('loginSubmit');
    submit.disabled = true;
    try {
      await doLogin(u, p, t || null);
      hideLoginModal();
      $('loginPassword').value = '';
      $('loginTotp').value = '';
      $('loginTotpRow').hidden = true;
      await loadAuthedAssets();
      setStatus(`xush kelibsiz, ${state._user.display_name || state._user.username}`);
    } catch (err) {
      if (err.totp_required) {
        $('loginTotpRow').hidden = false;
        $('loginErr').textContent = 'Authenticator kodingizni kiriting';
        setTimeout(() => $('loginTotp').focus(), 50);
      } else {
        $('loginErr').textContent = err.message;
      }
    } finally {
      submit.disabled = false;
    }
  });
  $('logoutBtn').addEventListener('click', doLogout);
  $('loginBtn').addEventListener('click', () => showLoginModal());
  $('adminBtn').addEventListener('click', openAdminModal);
  $('adminCloseBtn').addEventListener('click', () => { $('adminModal').hidden = true; });
  $('reviewBtn').addEventListener('click', openReviewModal);
  $('reviewCloseBtn').addEventListener('click', () => { $('reviewModal').hidden = true; });
})();

// ===== Dashboard =====

async function loadDashboard() {
  if (!state._user) return;
  const status = $('dashStatus').value;
  const own = $('dashOwn').checked;
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (own) params.set('own', 'true');
  params.set('limit', '500');
  let data;
  try {
    data = await apiJson(`/api/annotations/list?${params}`);
  } catch (e) {
    setStatus("dashboard xatosi: " + e.message);
    return;
  }
  $('dashMeta').textContent = `${data.count} / ${data.total} ta annotatsiya`;
  const ul = $('dashList');
  ul.innerHTML = '';
  for (const it of data.items) {
    const li = document.createElement('li');
    li.className = 'dash-row';
    const top = document.createElement('div');
    top.className = 'row';
    const left = document.createElement('div');

    const name = document.createElement('div');
    name.className = 'name';
    const lbl = it.label || '—';
    const typeIcon = it.type === 'polygon' ? '⬢' : '▭';
    const nameTxt = document.createElement('span');
    nameTxt.textContent = `${typeIcon} ${lbl}`;
    nameTxt.style.fontWeight = '600';
    name.appendChild(nameTxt);
    if (it.bi_rads) {
      const br = document.createElement('span');
      br.className = 'badge';
      br.textContent = it.bi_rads;
      name.appendChild(br);
    }
    const sp = document.createElement('span');
    sp.className = `status-pill status-${it.status}`;
    sp.textContent = it.status;
    name.appendChild(sp);
    left.appendChild(name);

    const sub = document.createElement('div');
    sub.className = 'meta';
    if (it.patient) {
      sub.textContent = `${it.patient.last_name || ''} ${it.patient.first_name || ''} (ID ${it.patient.patient_id})`;
    } else {
      sub.textContent = it.ref;
    }
    left.appendChild(sub);

    const sub2 = document.createElement('div');
    sub2.className = 'meta';
    sub2.style.opacity = '0.7';
    const updated = (it.updated_at || '').slice(0, 16).replace('T', ' ');
    const reviewer = it.reviewed_by ? ` · ${it.status === 'approved' ? '✓' : '✗'}${it.reviewed_by}` : '';
    sub2.textContent = `${it.created_by || '—'} · ${updated}${reviewer}`;
    left.appendChild(sub2);

    if (it.review_note && it.status === 'rejected') {
      const note = document.createElement('div');
      note.className = 'review-note';
      note.textContent = `« ${it.review_note} »`;
      note.style.marginTop = '3px';
      left.appendChild(note);
    }

    top.appendChild(left);
    li.appendChild(top);
    li.addEventListener('click', () => openAnnotationFromDashboard(it));
    ul.appendChild(li);
  }
}

async function openAnnotationFromDashboard(it) {
  if (it.source === 'upload') {
    await openItem({ kind: 'upload', id: it.ref });
  } else {
    await openItem({ kind: 'local', path: it.ref });
  }
  setTimeout(() => {
    state.selectedId = it.annotation_id;
    renderSvg();
    renderAnnoList();
    document.querySelectorAll('.meta-pane .tab').forEach(b => b.classList.remove('active'));
    document.querySelector('.meta-pane .tab[data-rtab="anno"]')?.classList.add('active');
    document.querySelectorAll('.meta-pane .rpane').forEach(p => p.hidden = p.dataset.rpane !== 'anno');
  }, 600);
}

(function bindDashboardUi() {
  $('dashStatus').addEventListener('change', loadDashboard);
  $('dashOwn').addEventListener('change', loadDashboard);
  $('dashRefresh').addEventListener('click', loadDashboard);
})();

// ===== Notifications =====

let _notifPollTimer = null;

async function refreshNotifications() {
  if (!state._user) return;
  try {
    const data = await apiJson('/api/notifications?limit=20');
    state._notifs = data.notifications || [];
    state._notifUnread = data.unread_count || 0;
    const badge = $('bellBadge');
    if (state._notifUnread > 0) {
      badge.textContent = state._notifUnread > 99 ? '99+' : state._notifUnread;
      badge.hidden = false;
    } else {
      badge.hidden = true;
    }
  } catch (e) {
    // non-fatal
  }
}

function renderBellDropdown() {
  const dd = $('bellDropdown');
  dd.innerHTML = '';
  const head = document.createElement('div');
  head.className = 'head';
  head.innerHTML = `<span>Bildirishnomalar</span>`;
  if (state._notifUnread > 0) {
    const all = document.createElement('button');
    all.textContent = "Hammasini o'qildi qilish";
    all.addEventListener('click', async (e) => {
      e.stopPropagation();
      try {
        await api('/api/notifications/mark-read', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ all: true }),
        });
        await refreshNotifications();
        renderBellDropdown();
      } catch (err) {}
    });
    head.appendChild(all);
  }
  dd.appendChild(head);

  if (!state._notifs || state._notifs.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = "Bildirishnomalar yo'q";
    dd.appendChild(empty);
    return;
  }

  for (const n of state._notifs) {
    const row = document.createElement('div');
    row.className = 'notif-row' + (n.read_at ? '' : ' unread');
    const head2 = document.createElement('div');
    head2.className = 'title';
    const k = document.createElement('span');
    k.className = `notif-kind ${n.kind}`;
    k.textContent = n.kind;
    head2.appendChild(k);
    const t = document.createElement('span');
    t.textContent = n.title || '';
    head2.appendChild(t);
    row.appendChild(head2);

    if (n.body) {
      const b = document.createElement('div');
      b.className = 'body';
      b.textContent = n.body;
      row.appendChild(b);
    }
    const m = document.createElement('div');
    m.className = 'meta';
    m.textContent = (n.ts || '').slice(0, 16).replace('T', ' ') + (n.actor ? ` · ${n.actor}` : '');
    row.appendChild(m);

    row.addEventListener('click', async () => {
      if (!n.read_at) {
        try {
          await api('/api/notifications/mark-read', {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({ ids: [n.id] }),
          });
        } catch (e) {}
      }
      $('bellDropdown').hidden = true;
      if (n.link_source && n.link_ref) {
        await openAnnotationFromDashboard({
          source: n.link_source,
          ref: n.link_ref,
          annotation_id: n.link_annotation_id,
        });
      }
      await refreshNotifications();
    });
    dd.appendChild(row);
  }
}

(function bindNotifUi() {
  $('bellBtn').addEventListener('click', async (e) => {
    e.stopPropagation();
    const dd = $('bellDropdown');
    if (dd.hidden) {
      await refreshNotifications();
      renderBellDropdown();
      dd.hidden = false;
    } else {
      dd.hidden = true;
    }
  });
  document.addEventListener('click', (e) => {
    const dd = $('bellDropdown');
    if (!dd.hidden && !dd.contains(e.target) && e.target !== $('bellBtn')) {
      dd.hidden = true;
    }
  });
})();

function startNotifPolling() {
  if (_notifPollTimer) clearInterval(_notifPollTimer);
  _notifPollTimer = setInterval(refreshNotifications, 30000);
}

async function openAdminModal() {
  $('adminModal').hidden = false;
  await renderAdminUsers();
}

async function renderAdminUsers() {
  const body = $('adminBody');
  body.innerHTML = '<div class="report-empty">Yuklanmoqda…</div>';
  let data;
  try {
    data = await apiJson('/api/auth/users');
  } catch (e) {
    body.innerHTML = `<div class="admin-err">${e.message}</div>`;
    return;
  }
  body.innerHTML = '';

  let settings = { totp_required_roles: [] };
  try { settings = await apiJson('/api/settings'); } catch (e) {}

  const settingsBar = document.createElement('div');
  settingsBar.style.cssText = 'background:var(--panel-2);border:1px solid var(--border);border-radius:4px;padding:10px;margin-bottom:10px';
  settingsBar.innerHTML = `
    <div style="font-size:11px;color:var(--muted);text-transform:uppercase;margin-bottom:6px">TOTP majburiy rollar</div>
    <div style="display:flex;gap:14px;align-items:center">
      ${['admin', 'reviewer', 'annotator'].map(r => `
        <label style="display:flex;align-items:center;gap:4px;font-size:12px">
          <input type="checkbox" data-totp-role="${r}" ${settings.totp_required_roles.includes(r) ? 'checked' : ''}/>
          ${r}
        </label>
      `).join('')}
    </div>
  `;
  body.appendChild(settingsBar);
  settingsBar.querySelectorAll('input[data-totp-role]').forEach(cb => {
    cb.addEventListener('change', async () => {
      const roles = [];
      settingsBar.querySelectorAll('input[data-totp-role]').forEach(c => {
        if (c.checked) roles.push(c.dataset.totpRole);
      });
      try {
        await api('/api/settings', {
          method: 'PATCH',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ totp_required_roles: roles }),
        });
      } catch (e) { alert(e.message); cb.checked = !cb.checked; }
    });
  });

  const auditBar = document.createElement('div');
  auditBar.style.cssText = 'display:flex; justify-content:flex-end; gap:6px; margin-bottom:10px;';
  const auditBtn = document.createElement('button');
  auditBtn.textContent = '⤓ Audit log CSV';
  auditBtn.title = 'Barcha annotation_history yozuvlarini CSV sifatida tushirish';
  auditBtn.addEventListener('click', async () => {
    const tok = getToken();
    const res = await fetch('/api/annotations/history.csv', {
      headers: { 'Authorization': `Bearer ${tok}` },
    });
    if (!res.ok) { alert('audit eksport xatosi: ' + res.status); return; }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_log_${new Date().toISOString().slice(0,10)}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });
  auditBar.appendChild(auditBtn);
  body.appendChild(auditBar);
  const table = document.createElement('table');
  table.className = 'user-table';
  table.innerHTML = `<thead><tr>
    <th>username</th><th>role</th><th>display name</th><th>email</th>
    <th>last login</th><th>active</th><th>amallar</th>
  </tr></thead>`;
  const tbody = document.createElement('tbody');
  for (const u of data.users) {
    const tr = document.createElement('tr');
    if (!u.is_active) tr.className = 'inactive';
    tr.innerHTML = `
      <td><b>${u.username}</b></td>
      <td><span class="role-pill role-${u.role}">${u.role}</span></td>
      <td>${u.display_name || ''}</td>
      <td>${u.email || ''}</td>
      <td style="font-size:10px; color: var(--muted)">${(u.last_login_at || '—').slice(0, 19).replace('T',' ')}</td>
      <td>${u.is_active ? '✓' : '✗'}</td>
    `;
    const actions = document.createElement('td');
    actions.className = 'row-actions';

    const roleSel = document.createElement('select');
    roleSel.title = 'role';
    for (const r of ['admin', 'reviewer', 'annotator']) {
      const o = document.createElement('option');
      o.value = r; o.textContent = r;
      if (u.role === r) o.selected = true;
      roleSel.appendChild(o);
    }
    roleSel.addEventListener('change', async () => {
      try {
        await api(`/api/auth/users/${encodeURIComponent(u.username)}`, {
          method: 'PATCH',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ role: roleSel.value }),
        });
        await renderAdminUsers();
      } catch (e) {
        alert("Role o'zgartirib bo'lmadi: " + e.message);
        roleSel.value = u.role;
      }
    });
    actions.appendChild(roleSel);

    const toggleBtn = document.createElement('button');
    toggleBtn.textContent = u.is_active ? 'Disable' : 'Enable';
    toggleBtn.addEventListener('click', async () => {
      try {
        await api(`/api/auth/users/${encodeURIComponent(u.username)}`, {
          method: 'PATCH',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ is_active: !u.is_active }),
        });
        await renderAdminUsers();
      } catch (e) { alert(e.message); }
    });
    actions.appendChild(toggleBtn);

    const pwdBtn = document.createElement('button');
    pwdBtn.textContent = '🔑 Reset';
    pwdBtn.addEventListener('click', async () => {
      const np = prompt(`Yangi parol (${u.username} uchun, min 4):`, '');
      if (np === null) return;
      if (np.length < 4) { alert('parol kalta'); return; }
      try {
        await api(`/api/auth/users/${encodeURIComponent(u.username)}/reset-password`, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ new_password: np }),
        });
        alert(`${u.username} parolini yangilandi`);
      } catch (e) { alert(e.message); }
    });
    actions.appendChild(pwdBtn);

    if (u.username !== state._user.username) {
      const delBtn = document.createElement('button');
      delBtn.textContent = '🗑';
      delBtn.style.color = 'var(--danger)';
      delBtn.title = "O'chirish";
      delBtn.addEventListener('click', async () => {
        if (!confirm(`'${u.username}' o'chirilsinmi?`)) return;
        try {
          await api(`/api/auth/users/${encodeURIComponent(u.username)}`, { method: 'DELETE' });
          await renderAdminUsers();
        } catch (e) { alert(e.message); }
      });
      actions.appendChild(delBtn);
    }

    tr.appendChild(actions);
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  body.appendChild(table);

  const form = document.createElement('div');
  form.className = 'admin-create-form';
  form.innerHTML = `
    <label>Username <input type="text" id="newUsername" /></label>
    <label>Role
      <select id="newRole">
        <option value="annotator">annotator</option>
        <option value="reviewer">reviewer</option>
        <option value="admin">admin</option>
      </select>
    </label>
    <label>Display name <input type="text" id="newDisplayName" /></label>
    <label>Email <input type="text" id="newEmail" /></label>
    <label>Password <input type="password" id="newPassword" /></label>
    <div class="admin-err" id="newErr"></div>
    <div class="actions"><button id="newSubmit">+ Yaratish</button></div>
  `;
  body.appendChild(form);
  $('newSubmit').addEventListener('click', async () => {
    const username = $('newUsername').value.trim();
    const password = $('newPassword').value;
    const role = $('newRole').value;
    const display_name = $('newDisplayName').value.trim() || null;
    const email = $('newEmail').value.trim() || null;
    if (!username || !password) {
      $('newErr').textContent = "username va parol kerak"; return;
    }
    if (password.length < 4) {
      $('newErr').textContent = "parol kalta (min 4)"; return;
    }
    try {
      await api('/api/auth/users', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ username, password, role, display_name, email }),
      });
      await renderAdminUsers();
    } catch (e) {
      $('newErr').textContent = e.message;
    }
  });
}

async function loadAiStatus() {
  let s;
  try {
    s = await apiJson('/api/inference/status');
  } catch (e) {
    state.aiAvailable = false; return;
  }
  state.aiAvailable = !!s.available && (s.models || []).length > 0;
  state.aiModels = s.models || [];
  state.aiDevice = s.device_name || s.device;
  state.aiInstalled = !!s.available;
  const sel = $('aiModelSelect');
  sel.innerHTML = '';
  for (const m of state.aiModels) {
    const o = document.createElement('option');
    o.value = m.name;
    o.textContent = m.stem;
    sel.appendChild(o);
  }
  // Ensemble (Weighted Boxes Fusion of all models) — only meaningful with ≥2 models.
  if (state.aiModels.length >= 2) {
    const o = document.createElement('option');
    o.value = '__ensemble__';
    o.textContent = '🧬 Ensemble (barcha modellar · WBF)';
    sel.appendChild(o);
  }
  if (state.aiAvailable) {
    sel.hidden = false;
    $('aiRunBtn').hidden = false;
    $('aiThresholdWrap').hidden = false;
    $('aiTtaWrap').hidden = false;
    $('aiRunBtn').title = `AI tahlil (${state.aiDevice})`;
    // (A3) Heatmap tugmasi — kamida 2 ta model bo'lsa ko'rinadi
    const hb = $('aiHeatmapBtn');
    if (hb) hb.hidden = !(state.aiModels && state.aiModels.length >= 2);
  } else if (state.aiInstalled) {
    setStatus(`AI tayyor, lekin model topilmadi (app/models/*.pt qo'shing)`);
  }
}

function closeAllMultiSelects() {
  // .ms parent'idagi va body'ga portallangan ms-panel'lar
  document.querySelectorAll('.ms .ms-panel, .ms-panel.ms-portal').forEach(p => { p.hidden = true; });
}
document.addEventListener('click', closeAllMultiSelects);

// Reusable checkbox dropdown for picking one OR several labels.
// opts: { selected: string[], onChange(arr), compact?: bool, placeholder?: string }
function buildLabelMultiSelect(opts) {
  const host = document.createElement('span');
  host.className = 'ms' + (opts.compact ? ' ms-compact' : '');
  let selected = [...(opts.selected || [])];

  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'ms-toggle';

  const panel = document.createElement('div');
  panel.className = 'ms-panel';
  panel.hidden = true;

  function renderToggle() {
    if (selected.length === 0) {
      toggle.textContent = opts.placeholder || 'Label tanlang';
      toggle.classList.remove('has-sel');
    } else {
      toggle.textContent = selected.join(', ');
      toggle.classList.add('has-sel');
    }
    toggle.title = toggle.textContent;
  }

  function buildOptions() {
    panel.innerHTML = '';
    for (const l of state.labels) {
      const opt = document.createElement('label');
      opt.className = 'ms-opt';
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = selected.includes(l.name);
      const dot = document.createElement('span');
      dot.className = 'ms-dot';
      dot.style.background = l.color;
      const name = document.createElement('span');
      name.className = 'ms-name';
      name.textContent = l.name;
      opt.appendChild(cb); opt.appendChild(dot); opt.appendChild(name);
      cb.addEventListener('change', () => {
        if (cb.checked) {
          if (!selected.includes(l.name)) selected.push(l.name);
        } else {
          selected = selected.filter(x => x !== l.name);
        }
        renderToggle();
        if (opts.onChange) opts.onChange([...selected]);
      });
      opt.addEventListener('click', e => e.stopPropagation());
      panel.appendChild(opt);
    }
  }

  // (Bug fix) — panelni portal sifatida body'ga ko'chiramiz, overflow:hidden
  // ancestor (meta-pane) tomonidan kesilmasin
  function positionPanel() {
    const r = toggle.getBoundingClientRect();
    panel.style.left = `${Math.round(r.left)}px`;
    panel.style.top = `${Math.round(r.bottom + 4)}px`;
    panel.style.minWidth = `${Math.max(180, Math.round(r.width))}px`;
    const panelRect = panel.getBoundingClientRect();
    if (panelRect.bottom > window.innerHeight - 10) {
      panel.style.top = `${Math.round(r.top - panelRect.height - 4)}px`;
    }
  }
  toggle.addEventListener('click', e => {
    e.stopPropagation();
    const willOpen = panel.hidden;
    closeAllMultiSelects();
    if (willOpen) {
      buildOptions();
      panel.classList.add('ms-portal');
      if (panel.parentElement !== document.body) document.body.appendChild(panel);
      panel.hidden = false;
      positionPanel();
    }
  });
  window.addEventListener('scroll', () => { if (!panel.hidden) positionPanel(); }, true);
  window.addEventListener('resize', () => { if (!panel.hidden) positionPanel(); });

  host._msSet = (arr) => { selected = [...(arr || [])]; renderToggle(); };
  host._msGet = () => [...selected];

  renderToggle();
  host.appendChild(toggle);
  host.appendChild(panel);
  return host;
}

async function loadLabels() {
  const data = await apiJson('/api/labels');
  state.labels = data.labels || [];
  state.birads = data.birads || [];

  // Toolbar keeps the classic single <select> (one label for the next new
  // annotation). Multiple labels are added per-annotation in the right panel.
  const sel = $('labelSelect');
  sel.innerHTML = '';
  for (const l of state.labels) {
    const o = document.createElement('option');
    o.value = l.name; o.textContent = l.name;
    o.style.color = l.color;
    sel.appendChild(o);
  }

  const bsel = $('biradsSelect');
  for (const b of state.birads) {
    const o = document.createElement('option');
    o.value = b; o.textContent = `BI-RADS ${b}`;
    bsel.appendChild(o);
  }
}

async function refreshUploads() {
  const data = await apiJson('/api/files');
  renderFileList($('uploadList'), data.files.map(f => ({
    kind: 'upload', id: f.id, label: fileLabel(f), sub: fileSub(f),
    removable: true, annoCount: f.annotation_count || 0,
  })));
}
function fileLabel(f) {
  const parts = [];
  if (f.patient) parts.push(f.patient);
  if (f.modality) parts.push(f.modality);
  return parts.join(' · ') || f.id;
}
function fileSub(f) {
  const parts = [];
  if (f.laterality) parts.push(f.laterality);
  if (f.view) parts.push(f.view);
  if (f.study_date) parts.push(f.study_date);
  if (f.rows && f.cols) parts.push(`${f.cols}×${f.rows}`);
  return parts.join(' · ');
}

function renderFileList(ul, items) {
  ul.innerHTML = '';
  const batchable = items.some(i => i.kind === 'upload' || i.kind === 'local');
  if (batchable && state._user && state.aiAvailable) {
    const bar = document.createElement('div');
    bar.style.cssText = 'padding:6px 10px; border-bottom:1px solid var(--border); display:flex; gap:6px; align-items:center;';
    bar.innerHTML = `
      <span style="font-size:10px; color:var(--muted)">tanlangan: <span id="batchCount_${ul.id}">0</span></span>
      <button class="batch-ai-btn" data-list="${ul.id}" style="font-size:11px; padding:3px 8px;" disabled>🤖 AI batch</button>
    `;
    ul.appendChild(bar);
  }
  for (const it of items) {
    const li = document.createElement('li');
    li.className = it.kind === 'dir' ? 'dir' : 'file';
    li.dataset.kind = it.kind;
    if (it.id) li.dataset.id = it.id;
    if (it.path != null) li.dataset.path = it.path;

    const top = document.createElement('div');
    top.className = 'row';

    if ((it.kind === 'upload' || it.kind === 'local') && state._user) {
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.className = 'batch-cb';
      cb.style.cssText = 'margin-right:6px;';
      cb.addEventListener('click', e => e.stopPropagation());
      cb.addEventListener('change', () => updateBatchCount(ul));
      top.appendChild(cb);
    }

    const left = document.createElement('div');
    const name = document.createElement('div');
    name.className = 'name';
    name.textContent = it.label;
    if (it.annoCount && it.annoCount > 0) {
      const pill = document.createElement('span');
      pill.className = 'anno-pill';
      pill.textContent = it.annoCount;
      pill.title = `${it.annoCount} annotatsiya`;
      name.appendChild(pill);
    }
    left.appendChild(name);
    if (it.sub) {
      const sub = document.createElement('div');
      sub.className = 'meta';
      sub.textContent = it.sub;
      left.appendChild(sub);
    }
    top.appendChild(left);

    if (it.removable) {
      const x = document.createElement('button');
      x.className = 'delete';
      x.textContent = '✕';
      x.title = "O'chirish";
      x.addEventListener('click', async (e) => {
        e.stopPropagation();
        await api(`/api/files/${encodeURIComponent(it.id)}`, { method: 'DELETE' });
        if (state.current && state.current.id === it.id) clearViewer();
        refreshUploads();
      });
      top.appendChild(x);
    }

    li.appendChild(top);
    li.addEventListener('click', () => onItemClick(it, li));
    ul.appendChild(li);
  }
}

function updateBatchCount(ul) {
  const checked = ul.querySelectorAll('.batch-cb:checked');
  const count = checked.length;
  const span = ul.querySelector(`#batchCount_${ul.id}`);
  if (span) span.textContent = count;
  const btn = ul.querySelector('.batch-ai-btn');
  if (btn) btn.disabled = count === 0;
}

document.addEventListener('click', async (e) => {
  if (!e.target.classList.contains('batch-ai-btn')) return;
  const ulId = e.target.dataset.list;
  const ul = document.getElementById(ulId);
  if (!ul) return;
  const items = [];
  ul.querySelectorAll('.batch-cb:checked').forEach(cb => {
    const li = cb.closest('li');
    if (!li) return;
    if (li.dataset.kind === 'upload') items.push({ source: 'upload', ref: li.dataset.id });
    else if (li.dataset.kind === 'local') items.push({ source: 'local', ref: li.dataset.path });
  });
  if (!items.length) return;
  const model = $('aiModelSelect').value;
  if (!model) { alert("AI model tanlang (toolbar'dan)"); return; }
  if (!confirm(`${items.length} ta DICOM'ga ${model} bilan AI batch ishga tushirilsinmi?\n\nNatijalar avtomatik annotation sifatida saqlanadi.`)) return;
  e.target.disabled = true;
  e.target.textContent = '⏳ ishlamoqda…';
  try {
    const r = await apiJson('/api/inference/batch', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ items, model, conf: state.aiThreshold || 0.25, auto_save: true,
                              tta: !!($('aiTtaToggle') && $('aiTtaToggle').checked) }),
    });
    const ok = r.results.filter(x => x.ok).length;
    const det = r.results.reduce((s, x) => s + (x.detections || 0), 0);
    alert(`Batch tugadi:\n✓ ${ok}/${items.length} muvaffaqiyat\n${det} ta detection saqlandi`);
    refreshActiveList();
  } catch (err) {
    alert("xato: " + err.message);
  } finally {
    e.target.disabled = false;
    e.target.textContent = '🤖 AI batch';
  }
});

async function onItemClick(it, li) {
  if (it.kind === 'dir') { loadLocalDir(it.path); return; }
  document.querySelectorAll('.file-list li.active').forEach(x => x.classList.remove('active'));
  li.classList.add('active');
  await openItem(it);
}

async function openItem(it) {
  // Safety net: persist unsaved work before leaving the current image so
  // manual-save mode never silently loses annotations on navigation.
  if (state.dirty && state.current) {
    try { await saveAnnotations(); } catch (e) { /* keep navigating */ }
  }
  setStatus("o'qilmoqda…");
  state.current = { kind: it.kind, id: it.id, path: it.path };
  state.frame = 0;
  state.wc = null; state.ww = null;
  state.invert = false;
  state.scale = 1; state.tx = 0; state.ty = 0;
  state.annotations = [];
  state.selectedId = null;
  state.suggestions = [];
  state.allSuggestions = [];
  $('aiClearBtn').hidden = true;
  $('aiAcceptAllBtn').hidden = true;

  let metaUrl;
  if (it.kind === 'upload') metaUrl = `/api/files/${encodeURIComponent(it.id)}/metadata`;
  else metaUrl = `/api/local/metadata?path=${encodeURIComponent(it.path)}`;

  const meta = await apiJson(metaUrl);
  state.meta = meta;
  renderMeta(meta);

  state.defaultWc = parseFirstNumber(meta.WindowCenter);
  state.defaultWw = parseFirstNumber(meta.WindowWidth);
  state.frames = parseInt(meta.NumberOfFrames || '1', 10) || 1;
  // (B2) PixelSpacing — "0.07\\0.07" yoki "[0.07, 0.07]" formatda. Yo'q bo'lsa null.
  state.spacing_mm = (function parseSpacing(s) {
    if (s == null || s === '') return null;
    const str = String(s).replace(/[\[\]]/g, '');
    const parts = str.split(/[,\\ ]+/).map(parseFloat).filter(x => !isNaN(x) && x > 0);
    return parts.length >= 2 ? [parts[0], parts[1]] : (parts.length === 1 ? [parts[0], parts[0]] : null);
  })(meta.PixelSpacing || meta.ImagerPixelSpacing);
  applyDefaults();
  configureFrameSlider();
  configureWlSliders(meta);

  await loadAnnotations();
  state.dirty = false;
  setSaveStatus('', '');
  updateSaveBtn();
  loadReport().catch(() => {});
  await loadImage(true);
  $('deidBtn').hidden = false;
  $('srBtn').hidden = false;
  $('segBtn').hidden = false;
  $('maskPngBtn').hidden = false;
  $('maskNiftiBtn').hidden = false;
  $('radiomicsBtn').hidden = false;
  $('cStoreBtn').hidden = false;
  $('tplSelect').hidden = false;
  $('tplSaveBtn').hidden = false;
  refreshTemplates().catch(() => {});
  wsConnect();
  setStatus('tayyor');
}

const RECORD_SECTIONS = [
  ['report', 'Mammografiya hisoboti'],
  ['complaints', 'Shikoyatlari'],
  ['history', 'Anamnesis morbi'],
  ['clinical_findings', "Klinik ko'rinish"],
  ['recommendations', 'Tavsiyalar'],
  ['diagnosis', 'Tashxis'],
  ['treatment', 'Davolash / oilaviy anamnez'],
  ['lab_notes', 'Laboratoriya / UTT / gistologiya'],
  ['disease_info', 'Status praesens'],
  ['occupational', 'Status localis'],
  ['admission_reason', 'Kelish sababi'],
  ['diagnostic_procedures', 'Diagnostik amaliyot'],
  ['discharge_meds', 'Chiqish dorilari'],
];

function _dismissedKey() {
  if (!state.current) return null;
  return `mamograf_dismissed_${refSource()}__${refValue()}`;
}
function getDismissed() {
  const k = _dismissedKey();
  if (!k) return new Set();
  try {
    const raw = localStorage.getItem(k);
    return new Set(raw ? JSON.parse(raw) : []);
  } catch (e) { return new Set(); }
}
function addDismissed(patientId) {
  const k = _dismissedKey();
  if (!k) return;
  const s = getDismissed();
  s.add(patientId);
  try { localStorage.setItem(k, JSON.stringify([...s])); } catch (e) {}
}
function clearDismissed() {
  const k = _dismissedKey();
  if (k) try { localStorage.removeItem(k); } catch (e) {}
}

async function loadReport() {
  if (!state.meta) return;
  state._linked = null;

  const refS = refSource();
  const refV = refValue();
  if (refS && refV) {
    try {
      const linkData = await apiJson(`/api/db/link?source=${refS}&ref=${encodeURIComponent(refV)}`);
      if (linkData.linked && linkData.patient) {
        state._linked = linkData;
        state._matchInput = {
          patient_id: state.meta.PatientID || '',
          name: state.meta.PatientName || '',
          birth_date: state.meta.PatientBirthDate || '',
          parsed: {},
        };
        await loadAndRenderPatient(linkData.patient.patient_id, /*append*/false);
        return;
      }
    } catch (e) {
      // ignore — fall through to fuzzy match
    }
  }

  const params = new URLSearchParams();
  if (state.meta.PatientID) params.set('patient_id', state.meta.PatientID);
  if (state.meta.PatientName) params.set('name', state.meta.PatientName);
  if (state.meta.PatientBirthDate) params.set('birth_date', state.meta.PatientBirthDate);
  let data;
  try {
    data = await apiJson(`/api/db/match?${params}`);
  } catch (e) {
    renderReportError(e.message);
    return;
  }
  state._matchInput = data.input;
  const dismissed = getDismissed();
  data.candidates = (data.candidates || []).filter(c => !dismissed.has(c.patient.patient_id));
  if (data.candidates.length === 1 && data.candidates[0].score >= 80) {
    renderReportInputBar(data.input);
    await loadAndRenderPatient(data.candidates[0].patient.patient_id, /*append*/true);
  } else if (data.candidates.length > 0) {
    renderReportCandidates(data);
  } else {
    renderReportEmpty(data.input);
  }
}

async function saveLink(patientId, confidence) {
  await api('/api/db/link', {
    method: 'PUT',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      source: refSource(),
      ref: refValue(),
      patient_id: patientId,
      confidence: Math.round(Number(confidence) || 0),
    }),
  });
}

async function unlinkPatient() {
  if (!state.current) return;
  if (!confirm("Bemor bilan aloqani uzasizmi?")) return;
  try {
    await api(
      `/api/db/link?source=${refSource()}&ref=${encodeURIComponent(refValue())}`,
      { method: 'DELETE' },
    );
    state._linked = null;
    await loadReport();
  } catch (e) {
    setStatus('uzish xatosi: ' + e.message);
  }
}

function renderReportError(msg) {
  const pane = $('reportPane');
  pane.innerHTML = `<div class="report-empty">Xato: ${msg}</div>`;
}

function renderReportInputBar(input) {
  const pane = $('reportPane');
  pane.innerHTML = '';
  const head = document.createElement('div');
  head.className = 'report-input';
  const parsed = input.parsed || {};
  head.innerHTML = `DICOM: <b>${input.name || '—'}</b> · ID <b>${input.patient_id || '—'}</b> · DOB <b>${parsed.dob || input.birth_date || '—'}</b>`;
  pane.appendChild(head);
}

function renderReportCandidates(data) {
  renderReportInputBar(data.input);
  const pane = $('reportPane');
  const title = document.createElement('div');
  title.className = 'report-section-title';
  const dismissedCount = getDismissed().size;
  title.innerHTML = `${data.candidates.length} ta nomzod` +
    (dismissedCount > 0
      ? ` <a href="#" id="restoreDismissed" style="font-size:10px; color:var(--accent); margin-left:6px; text-decoration:none">+${dismissedCount} yashirilgan ↺</a>`
      : '');
  pane.appendChild(title);
  const restore = pane.querySelector('#restoreDismissed');
  if (restore) restore.addEventListener('click', (e) => { e.preventDefault(); clearDismissed(); loadReport(); });
  for (const c of data.candidates) {
    pane.appendChild(buildCandidateBtn(c));
  }
  appendManualSearch(pane);
}

function buildCandidateBtn(c) {
  const p = c.patient;
  const btn = document.createElement('div');
  btn.className = 'report-candidate';
  const scoreCls = c.score >= 80 ? 'high' : (c.score >= 60 ? 'med' : '');
  const top = document.createElement('div');
  top.className = 'top';
  const nm = document.createElement('div');
  nm.className = 'name';
  nm.textContent = `${p.last_name || ''} ${p.first_name || ''}`.trim() || '—';
  const sc = document.createElement('div');
  sc.className = `score ${scoreCls}`;
  sc.textContent = `${c.score}%`;
  const dismissBtn = document.createElement('button');
  dismissBtn.className = 'cand-dismiss';
  dismissBtn.textContent = '✕';
  dismissBtn.title = "Bu nomzodni ro'yxatdan olib tashlash";
  dismissBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    addDismissed(p.patient_id);
    btn.remove();
    const list = document.querySelectorAll('#reportPane .report-candidate');
    if (list.length === 0) {
      const pane = $('reportPane');
      const empty = document.createElement('div');
      empty.className = 'report-empty';
      empty.innerHTML = `Barcha nomzodlar yashirildi. <a href="#" id="restoreDismissed">Ko'rsatish</a>`;
      pane.appendChild(empty);
      const link = pane.querySelector('#restoreDismissed');
      if (link) link.addEventListener('click', (ev) => { ev.preventDefault(); clearDismissed(); loadReport(); });
    }
  });
  top.append(nm, sc, dismissBtn);
  btn.appendChild(top);
  const meta1 = document.createElement('div');
  meta1.className = 'meta-line';
  meta1.textContent = `ID ${p.patient_id} · ${p.sex || '—'} · DOB ${p.birth_date || '—'}`;
  btn.appendChild(meta1);
  const meta2 = document.createElement('div');
  meta2.className = 'meta-line';
  meta2.textContent = `${c.record_count} yozuv${c.last_visit ? ' · oxirgi ' + c.last_visit : ''} · ${(c.reasons || []).join(', ')}`;
  btn.appendChild(meta2);

  const actions = document.createElement('div');
  actions.className = 'cand-actions';
  const previewBtn = document.createElement('button');
  previewBtn.className = 'cand-btn';
  previewBtn.textContent = '👁 Yozuvlarni ko\'rish';
  previewBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    loadAndRenderPatient(p.patient_id, /*append*/false);
  });
  const linkBtn = document.createElement('button');
  linkBtn.className = 'cand-btn link';
  linkBtn.textContent = '🔗 Bog\'lash';
  linkBtn.title = 'Shu DICOM bilan shu bemorni doimiy bog\'lash';
  linkBtn.addEventListener('click', async (e) => {
    e.stopPropagation();
    try {
      await saveLink(p.patient_id, c.score);
      await loadReport();
    } catch (err) {
      setStatus('bog\'lash xatosi: ' + err.message);
    }
  });
  actions.append(previewBtn, linkBtn);
  btn.appendChild(actions);
  return btn;
}

function renderReportEmpty(input) {
  const pane = $('reportPane');
  pane.innerHTML = '';
  renderReportInputBar(input);
  const empty = document.createElement('div');
  empty.className = 'report-empty';
  empty.innerHTML = `Mos hisobot topilmadi.<br>Quyida ID yoki ism bo'yicha qo'lda qidirishingiz mumkin.`;
  pane.appendChild(empty);
  appendManualSearch(pane);
}

function appendManualSearch(pane) {
  const wrap = document.createElement('div');
  wrap.className = 'report-search';
  const inp = document.createElement('input');
  inp.type = 'text';
  inp.placeholder = "ID yoki ism (masalan, 14173 yoki SHUKUROVA)";
  const btn = document.createElement('button');
  btn.textContent = 'Qidirish';
  const run = async () => {
    const q = inp.value.trim();
    if (!q) return;
    try {
      const data = await apiJson(`/api/db/search?q=${encodeURIComponent(q)}&limit=15`);
      renderManualResults(data, q);
    } catch (e) { renderReportError(e.message); }
  };
  btn.addEventListener('click', run);
  inp.addEventListener('keydown', (e) => { if (e.key === 'Enter') run(); });
  wrap.append(inp, btn);
  pane.appendChild(wrap);
}

function renderManualResults(data, q) {
  const pane = $('reportPane');
  let title = pane.querySelector('.report-section-title.manual');
  if (!title) {
    title = document.createElement('div');
    title.className = 'report-section-title manual';
    pane.appendChild(title);
  }
  title.textContent = `Qidiruv natijalari "${q}" — ${data.results.length}`;
  let listWrap = pane.querySelector('.manual-results');
  if (listWrap) listWrap.remove();
  listWrap = document.createElement('div');
  listWrap.className = 'manual-results';
  for (const r of data.results) {
    const c = {
      patient: r,
      score: 0,
      reasons: ['qo\'lda qidiruv'],
      record_count: r.record_count || 0,
      last_visit: r.last_visit,
    };
    listWrap.appendChild(buildCandidateBtn(c));
  }
  pane.appendChild(listWrap);
}

async function loadAndRenderPatient(patientId, append) {
  let data;
  try {
    data = await apiJson(`/api/db/patient/${encodeURIComponent(patientId)}`);
  } catch (e) {
    renderReportError(e.message);
    return;
  }
  const pane = $('reportPane');
  if (!append) {
    pane.innerHTML = '';
    if (state._matchInput) renderReportInputBar(state._matchInput);
  }

  const isLinked = state._linked && state._linked.patient && state._linked.patient.patient_id === patientId;

  if (isLinked) {
    const banner = document.createElement('div');
    banner.className = 'link-banner linked';
    const txt = document.createElement('div');
    const lk = state._linked.link || {};
    const conf = lk.confidence != null ? ` · ${lk.confidence}%` : '';
    const at = lk.confirmed_at ? ` · ${lk.confirmed_at.slice(0, 10)}` : '';
    txt.innerHTML = `🔗 <b>Bog'langan</b>${conf}${at}`;
    const unlink = document.createElement('button');
    unlink.className = 'link-action';
    unlink.textContent = '🔓 Aloqani uzish';
    unlink.addEventListener('click', unlinkPatient);
    banner.append(txt, unlink);
    pane.appendChild(banner);
  }

  const head = document.createElement('div');
  head.className = 'report-patient';
  const p = data.patient;
  const nm = document.createElement('div');
  nm.className = 'name';
  nm.textContent = `${p.last_name || ''} ${p.first_name || ''}`.trim() || '—';
  const id = document.createElement('div');
  id.className = 'id';
  id.textContent = `ID ${p.patient_id} · ${p.sex || '—'} · DOB ${p.birth_date || '—'} · ${data.records.length} yozuv`;
  head.append(nm, id);

  if (!isLinked) {
    const linkHere = document.createElement('button');
    linkHere.className = 'link-action primary';
    linkHere.textContent = "🔗 Shu bemorga doimiy bog'lash";
    linkHere.addEventListener('click', async () => {
      try {
        await saveLink(p.patient_id, null);
        await loadReport();
      } catch (e) { setStatus("bog'lash xatosi: " + e.message); }
    });
    head.appendChild(linkHere);
  }

  const sw = document.createElement('button');
  sw.className = 'switch';
  sw.textContent = '← Boshqa bemorni tanlash';
  sw.addEventListener('click', () => loadReport());
  head.appendChild(sw);
  pane.appendChild(head);

  for (let i = 0; i < data.records.length; i++) {
    pane.appendChild(buildRecordCard(data.records[i], i === 0));
  }

  const badge = $('reportBadge');
  badge.textContent = data.records.length;
  badge.hidden = data.records.length === 0;
}

function buildRecordCard(r, openByDefault) {
  const det = document.createElement('details');
  det.className = 'record-card';
  if (openByDefault) det.open = true;

  const sum = document.createElement('summary');
  const dt = document.createElement('span');
  dt.className = 'date';
  dt.textContent = r.service_date || '—';
  sum.appendChild(dt);
  if (r.exam_code) {
    const code = document.createElement('span');
    code.className = 'code';
    code.textContent = r.exam_code;
    sum.appendChild(code);
  }
  if (r.exam_name) {
    const en = document.createElement('span');
    en.textContent = r.exam_name;
    sum.appendChild(en);
  }
  det.appendChild(sum);

  const body = document.createElement('div');
  body.className = 'record-body';
  let any = false;
  for (const [key, label] of RECORD_SECTIONS) {
    const v = r[key];
    if (!v) continue;
    any = true;
    const sec = document.createElement('div');
    sec.className = 'record-section';
    const lbl = document.createElement('div');
    lbl.className = 'record-section-label';
    lbl.textContent = label;
    const pre = document.createElement('pre');
    pre.textContent = v;
    sec.append(lbl, pre);
    body.appendChild(sec);
  }
  if (!any) {
    const empty = document.createElement('div');
    empty.className = 'report-empty';
    empty.style.padding = '8px 0 0';
    empty.textContent = 'Bo\'sh yozuv';
    body.appendChild(empty);
  }
  det.appendChild(body);
  return det;
}

async function loadAnnotations() {
  if (!state.current) return;
  try {
    const data = await apiJson(`/api/annotations?source=${refSource()}&ref=${encodeURIComponent(refValue())}`);
    state.annotations = (data.annotations || []).map(normalizeAnn);
  } catch (e) {
    state.annotations = [];
  }
  renderSvg();
  renderAnnoList();
}

function normalizeAnn(a) {
  const out = Object.assign({}, a);
  if (!out.id) out.id = uid();
  if (!out.bbox) out.bbox = [0, 0, 0, 0];
  if (typeof out.frame !== 'number') out.frame = 0;
  // Multi-label support: `labels` is the source of truth, `label` stays as the
  // primary (first) label for backward compatibility (color, export, stats).
  if (Array.isArray(out.labels) && out.labels.length) {
    out.label = out.labels[0];
  } else {
    out.labels = out.label ? [out.label] : [];
  }
  return out;
}

// Read the primary + full label set for an annotation, tolerating old records.
function annLabels(a) {
  if (Array.isArray(a.labels) && a.labels.length) return a.labels;
  return a.label ? [a.label] : [];
}
function annLabelText(a) {
  const ls = annLabels(a);
  return ls.length ? ls.join(' + ') : '—';
}

// Primary label chosen in the toolbar for a new annotation (always one).
// Extra labels are added afterwards via the per-annotation editor.
function pendingLabels() {
  const sel = $('labelSelect');
  const v = sel ? sel.value : '';
  return v ? [v] : [state.labels[0]?.name || 'mass'];
}

function parseFirstNumber(v) {
  if (v == null) return null;
  if (typeof v === 'number') return v;
  const s = String(v).trim();
  const m = s.match(/-?\d+(\.\d+)?/);
  return m ? parseFloat(m[0]) : null;
}

function applyDefaults() {
  state.wc = state.defaultWc;
  state.ww = state.defaultWw;
  $('wcInput').value = state.wc != null ? Math.round(state.wc) : '';
  $('wwInput').value = state.ww != null ? Math.round(state.ww) : '';
  if (state.wc != null) $('wcSlider').value = clampRange($('wcSlider'), state.wc);
  if (state.ww != null) $('wwSlider').value = clampRange($('wwSlider'), state.ww);
}

function clampRange(input, v) {
  const min = parseFloat(input.min), max = parseFloat(input.max);
  return Math.max(min, Math.min(max, v));
}

function configureFrameSlider() {
  const s = $('frameSlider');
  s.min = 0;
  s.max = Math.max(0, state.frames - 1);
  s.value = 0;
  s.disabled = state.frames <= 1;
  $('frameLabel').textContent = `1 / ${state.frames}`;
}

function configureWlSliders(meta) {
  const bits = parseInt(meta.BitsStored || '12', 10);
  const signed = String(meta.PixelRepresentation || '0') === '1';
  let lo, hi;
  if (signed) { lo = -(1 << (bits - 1)); hi = (1 << (bits - 1)) - 1; }
  else { lo = 0; hi = (1 << bits) - 1; }
  const wcS = $('wcSlider'); wcS.min = lo; wcS.max = hi;
  if (state.wc != null) wcS.value = clampRange(wcS, state.wc);
  const wwS = $('wwSlider'); wwS.min = 1; wwS.max = hi - lo;
  if (state.ww != null) wwS.value = clampRange(wwS, state.ww);
}

function renderMeta(meta) {
  const tbody = $('metaTable').querySelector('tbody');
  tbody.innerHTML = '';
  const order = [
    'PatientName','PatientID','PatientSex','PatientAge','PatientBirthDate',
    'StudyDate','StudyDescription','SeriesDescription',
    'Modality','BodyPartExamined','ImageLaterality','ViewPosition',
    'Rows','Columns','BitsStored','NumberOfFrames','PhotometricInterpretation',
    'WindowCenter','WindowWidth','RescaleSlope','RescaleIntercept',
    'PixelSpacing','ImagerPixelSpacing','BodyPartThickness','CompressionForce',
    'KVP','ExposureTime','XRayTubeCurrent',
    'Manufacturer','ManufacturerModelName','InstitutionName',
    'StudyInstanceUID','SeriesInstanceUID','TransferSyntaxUID',
  ];
  const seen = new Set();
  const addRow = (k, v) => {
    if (v === undefined || v === null || v === '') return;
    const tr = document.createElement('tr');
    const td1 = document.createElement('td'); td1.textContent = k;
    const td2 = document.createElement('td'); td2.textContent = v;
    tr.append(td1, td2); tbody.appendChild(tr);
  };
  for (const k of order) { if (k in meta) { addRow(k, meta[k]); seen.add(k); } }
  for (const [k, v] of Object.entries(meta)) { if (!seen.has(k)) addRow(k, v); }
}

function clearViewer() {
  wsClose();
  state.current = null;
  state.meta = null;
  state.annotations = [];
  state.selectedId = null;
  state.suggestions = [];
  state._matchInput = null;
  $('imgStack').hidden = true;
  $('srView').hidden = true;
  $('srView').innerHTML = '';
  $('emptyState').style.display = '';
  $('dicomImg').removeAttribute('src');
  $('metaTable').querySelector('tbody').innerHTML = '';
  $('reportPane').innerHTML = '';
  $('reportBadge').hidden = true;
  $('aiClearBtn').hidden = true;
  $('deidBtn').hidden = true;
  $('srBtn').hidden = true;
  $('segBtn').hidden = true;
  $('maskPngBtn').hidden = true;
  $('maskNiftiBtn').hidden = true;
  $('radiomicsBtn').hidden = true;
  $('cStoreBtn').hidden = true;
  $('tplSelect').hidden = true;
  $('tplSaveBtn').hidden = true;
  renderSvg();
  renderAnnoList();
}

let _imgLoadToken = 0;
async function loadImage(fitAfter) {
  if (!state.current) return;
  const token = ++_imgLoadToken;
  const url = imageUrl();

  try {
    const probe = await fetch(url, { method: 'HEAD' });
    if (probe.status === 422 || (state.meta && (state.meta.Modality === 'SR' || (state.meta.Modality || '').toUpperCase() === 'SR'))) {
      if (probe.status === 422 || state.meta?.Modality === 'SR') {
        await renderSrView();
        return;
      }
    }
  } catch (e) {
    // fall through to img-tag flow
  }

  const img = $('dicomImg');
  img.onload = async () => {
    if (token !== _imgLoadToken) return;
    if (img.naturalWidth === 0) {
      // still failed — try SR fallback
      const r = await fetch(url);
      if (r.status === 422) { await renderSrView(); return; }
      setStatus("rasmni o'qib bo'lmadi");
      return;
    }
    $('srView').hidden = true;
    $('emptyState').style.display = 'none';
    $('imgStack').hidden = false;
    syncSvgViewBox();
    if (fitAfter) fitToScreen();
    else applyTransform();
    renderSvg();
  };
  img.onerror = async () => {
    if (token !== _imgLoadToken) return;
    try {
      const r = await fetch(url);
      if (r.status === 422) {
        await renderSrView();
        return;
      }
    } catch (e) {}
    setStatus("rasmni o'qib bo'lmadi");
  };
  img.src = url;
}

async function renderSrView() {
  $('imgStack').hidden = true;
  $('emptyState').style.display = 'none';
  const view = $('srView');
  view.hidden = false;
  view.innerHTML = '<div class="empty">SR matni yuklanmoqda…</div>';

  let data = null;
  try {
    if (state.current.kind === 'upload') {
      data = await apiJson(`/api/files/${encodeURIComponent(state.current.id)}/sr-content`);
    } else {
      data = await apiJson(`/api/local/sr-content?path=${encodeURIComponent(state.current.path)}`);
    }
  } catch (e) {
    const m = state.meta || {};
    view.innerHTML = `
      <div class="sr-head">
        <h2>📄 ${m.Modality || 'Structured Report'} — bu DICOM rasm emas</h2>
        <div class="meta">
          Bemor: <b>${m.PatientName || '—'}</b> · ID ${m.PatientID || '—'}
          <span class="sr-flag">Modality: ${m.Modality || '—'}</span>
        </div>
      </div>
      <div class="empty" style="padding-top:14px">
        SR matn parserga ulanmadi (server eski kodda bo'lishi mumkin).<br>
        <b>Server qayta ishga tushirilsin</b> (run.bat ni yopib qayta oching) keyin Ctrl+F5.
      </div>
      <div class="sr-item depth-1"><div class="lbl">Xom xato</div><div class="val">${e.message}</div></div>
    `;
    return;
  }

  view.innerHTML = '';
  const head = document.createElement('div');
  head.className = 'sr-head';
  const title = document.createElement('h2');
  title.textContent = '📄 ' + (data.items?.[0]?.name || 'Structured Report');
  head.appendChild(title);
  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.innerHTML = `Bemor: <b>${data.patient_name || '—'}</b> · ID ${data.patient_id || '—'} · ${data.content_date || ''}` +
    (data.completion_flag ? `<span class="sr-flag">${data.completion_flag}</span>` : '') +
    (data.verification_flag ? `<span class="sr-flag">${data.verification_flag}</span>` : '') +
    `<span class="sr-flag">Modality: ${data.modality || '—'}</span>`;
  head.appendChild(meta);
  view.appendChild(head);

  for (const it of (data.items || []).slice(1)) {
    const div = document.createElement('div');
    div.className = `sr-item depth-${Math.min(it.depth || 1, 4)}`;
    const lbl = document.createElement('div');
    lbl.className = 'lbl';
    lbl.textContent = `${it.type || ''}${it.name ? ' · ' + it.name : ''}`;
    div.appendChild(lbl);
    const val = document.createElement('div');
    val.className = 'val';
    val.textContent = it.text || it.value || '';
    div.appendChild(val);
    view.appendChild(div);
  }

  setStatus(`📄 SR — ${data.modality || 'Structured Report'}`);
}

function syncSvgViewBox() {
  const img = $('dicomImg');
  const svg = $('annoSvg');
  if (!img.naturalWidth) return;
  svg.setAttribute('viewBox', `0 0 ${img.naturalWidth} ${img.naturalHeight}`);
  svg.setAttribute('width', img.naturalWidth);
  svg.setAttribute('height', img.naturalHeight);
}

let _wlDebounce;
function scheduleReload() {
  clearTimeout(_wlDebounce);
  _wlDebounce = setTimeout(() => loadImage(false), 150);
}

function fitToScreen() {
  const wrap = $('canvasWrap');
  const img = $('dicomImg');
  if (!img.naturalWidth) return;
  const sx = wrap.clientWidth / img.naturalWidth;
  const sy = wrap.clientHeight / img.naturalHeight;
  const s = Math.min(sx, sy) * 0.98;
  state.scale = s; state.fitScale = s;
  state.tx = 0; state.ty = 0;
  applyTransform();
}
function oneToOne() { state.scale = 1; state.tx = 0; state.ty = 0; applyTransform(); }
let _lastScale = 1;
function applyTransform() {
  $('imgStack').style.transform = `translate(${state.tx}px, ${state.ty}px) scale(${state.scale})`;
  $('zoomLbl').textContent = `${Math.round(state.scale * 100)}%`;
  if (state.current && state.selectedId && Math.abs(state.scale - _lastScale) > 1e-3) {
    _lastScale = state.scale;
    renderSvg();
  } else {
    _lastScale = state.scale;
  }
}

// pan & zoom
(() => {
  const wrap = $('canvasWrap');
  let dragging = false, lastX = 0, lastY = 0;

  let touchMode = null;
  let lastTouchX = 0, lastTouchY = 0;
  let lastPinchDist = 0;
  let lastPinchCx = 0, lastPinchCy = 0;

  function dist(t1, t2) {
    const dx = t2.clientX - t1.clientX;
    const dy = t2.clientY - t1.clientY;
    return Math.hypot(dx, dy);
  }

  wrap.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
      touchMode = 'pan';
      lastTouchX = e.touches[0].clientX;
      lastTouchY = e.touches[0].clientY;
    } else if (e.touches.length >= 2) {
      touchMode = 'pinch';
      lastPinchDist = dist(e.touches[0], e.touches[1]);
      lastPinchCx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
      lastPinchCy = (e.touches[0].clientY + e.touches[1].clientY) / 2;
    }
    e.preventDefault();
  }, { passive: false });

  wrap.addEventListener('touchmove', (e) => {
    if (touchMode === 'pan' && e.touches.length === 1) {
      const t = e.touches[0];
      state.tx += t.clientX - lastTouchX;
      state.ty += t.clientY - lastTouchY;
      lastTouchX = t.clientX;
      lastTouchY = t.clientY;
      applyTransform();
      e.preventDefault();
    } else if (touchMode === 'pinch' && e.touches.length >= 2) {
      const d = dist(e.touches[0], e.touches[1]);
      if (lastPinchDist > 0) {
        const factor = d / lastPinchDist;
        const newScale = Math.max(0.05, Math.min(40, state.scale * factor));
        const cx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
        const cy = (e.touches[0].clientY + e.touches[1].clientY) / 2;
        const rect = wrap.getBoundingClientRect();
        const px = cx - rect.left - rect.width / 2;
        const py = cy - rect.top - rect.height / 2;
        state.tx = px - (px - state.tx) * (newScale / state.scale);
        state.ty = py - (py - state.ty) * (newScale / state.scale);
        state.tx += cx - lastPinchCx;
        state.ty += cy - lastPinchCy;
        state.scale = newScale;
        applyTransform();
      }
      lastPinchDist = d;
      lastPinchCx = (e.touches[0].clientX + e.touches[1].clientX) / 2;
      lastPinchCy = (e.touches[0].clientY + e.touches[1].clientY) / 2;
      e.preventDefault();
    }
  }, { passive: false });

  wrap.addEventListener('touchend', (e) => {
    if (e.touches.length === 0) {
      touchMode = null;
    } else if (e.touches.length === 1) {
      touchMode = 'pan';
      lastTouchX = e.touches[0].clientX;
      lastTouchY = e.touches[0].clientY;
    }
  });

  wrap.addEventListener('mousedown', (e) => {
    if (state.tool === 'bbox' && e.target.id === 'annoSvg') return;
    if (e.button !== 0 && e.button !== 1) return;
    dragging = true; lastX = e.clientX; lastY = e.clientY;
    wrap.classList.add('dragging');
  });
  window.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    state.tx += e.clientX - lastX;
    state.ty += e.clientY - lastY;
    lastX = e.clientX; lastY = e.clientY;
    applyTransform();
  });
  window.addEventListener('mouseup', () => { dragging = false; wrap.classList.remove('dragging'); });
  wrap.addEventListener('wheel', (e) => {
    e.preventDefault();
    const factor = Math.exp(-e.deltaY * 0.0015);
    const newScale = Math.max(0.05, Math.min(40, state.scale * factor));
    const rect = wrap.getBoundingClientRect();
    const cx = e.clientX - rect.left - rect.width / 2;
    const cy = e.clientY - rect.top - rect.height / 2;
    state.tx = cx - (cx - state.tx) * (newScale / state.scale);
    state.ty = cy - (cy - state.ty) * (newScale / state.scale);
    state.scale = newScale;
    applyTransform();
  }, { passive: false });
})();

// upload — parallel + progress
const UPLOAD_CONCURRENCY = 3;

function uploadOne(file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload');
    const tok = getToken();
    if (tok) xhr.setRequestHeader('Authorization', `Bearer ${tok}`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(e.loaded, e.total);
    };
    xhr.onload = () => {
      if (xhr.status === 401) { setToken(null); state._user = null; updateUserBar(); reject(new Error('401')); return; }
      if (xhr.status >= 200 && xhr.status < 300) {
        try { resolve(JSON.parse(xhr.responseText)); }
        catch (e) { resolve({}); }
      } else reject(new Error(`HTTP ${xhr.status}: ${xhr.responseText}`));
    };
    xhr.onerror = () => reject(new Error('network error'));
    xhr.onabort = () => reject(new Error('aborted'));
    const fd = new FormData();
    fd.append('files', file, file.name);
    xhr.send(fd);
  });
}

(() => {
  const dz = $('dropZone');
  const inp = $('fileInput');
  const finp = $('folderInput');

  const upload = async (filesIn) => {
    if (!filesIn || filesIn.length === 0) return;
    const files = Array.from(filesIn);
    const total = files.length;
    let done = 0;
    let failed = 0;
    const totalBytes = files.reduce((s, f) => s + f.size, 0);
    let totalUploaded = 0;
    const fileProgress = new Map();
    const t0 = performance.now();

    const fmtSize = (n) => {
      if (n < 1024) return `${n} B`;
      if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
      return `${(n / 1024 / 1024).toFixed(1)} MB`;
    };

    const refreshStatus = () => {
      const sumLoaded = [...fileProgress.values()].reduce((s, v) => s + v, 0) + totalUploaded;
      const pct = totalBytes ? (sumLoaded * 100 / totalBytes) : 0;
      const elapsed = (performance.now() - t0) / 1000;
      const rate = elapsed > 0.5 ? sumLoaded / elapsed : 0;
      const rateStr = rate > 0 ? ` · ${fmtSize(rate)}/s` : '';
      const etaStr = rate > 0 ? ` · ETA ${Math.max(0, Math.round((totalBytes - sumLoaded) / rate))}s` : '';
      setStatus(`📤 ${done}/${total} · ${pct.toFixed(0)}%${rateStr}${etaStr}`);
    };

    const queue = files.slice();
    // (Background task) — AI'ni kutib turish uchun file_id'lar
    const aiQueuedIds = [];
    const worker = async () => {
      while (queue.length) {
        const f = queue.shift();
        try {
          const resp = await uploadOne(f, (loaded, _t) => {
            fileProgress.set(f, loaded);
            refreshStatus();
          });
          totalUploaded += f.size;
          fileProgress.delete(f);
          done++;
          // Background AI ni eslaymiz
          if (resp && resp.files) {
            for (const fi of resp.files) {
              if (fi.ai_inference && fi.ai_inference.queued && fi.id) aiQueuedIds.push(fi.id);
            }
          }
        } catch (e) {
          failed++;
          fileProgress.delete(f);
          console.error('upload', f.name, e.message);
        }
        refreshStatus();
      }
    };

    refreshStatus();
    const workers = [];
    for (let i = 0; i < Math.min(UPLOAD_CONCURRENCY, files.length); i++) {
      workers.push(worker());
    }
    await Promise.all(workers);

    await refreshUploads();
    const elapsed = ((performance.now() - t0) / 1000).toFixed(1);
    if (failed) setStatus(`✓ ${done}/${total} yuklandi · ${failed} xato (${elapsed}s)`);
    else setStatus(`✓ ${done} ta fayl yuklandi (${elapsed}s)`);

    // (Background task) — AI fonda tugagani uchun annotation'larni tortish
    if (aiQueuedIds.length > 0) {
      setStatus(`✓ ${done} fayl · 🤖 AI fonda tahlil qilmoqda...`);
      let polls = 0;
      const POLL_INTERVAL_MS = 3000;
      const MAX_POLLS = 25;  // ~75 sek
      const poll = async () => {
        polls++;
        try {
          await refreshUploads();
          // Joriy fayl AI kutyaptmi?
          if (state.current && state.current.kind === 'upload' && aiQueuedIds.includes(state.current.id)) {
            await loadAnnotations();
          }
        } catch {}
        // Hammasi tugadimi tekshirish
        try {
          const files = await apiJson('/api/files');
          let stillQueued = 0;
          for (const fid of aiQueuedIds) {
            const f = (files.files || []).find(x => x.id === fid);
            if (f && (f.annotation_count || 0) === 0) stillQueued++;
          }
          if (stillQueued === 0) {
            setStatus(`✓ AI tahlil tugadi (${done} fayl)`);
            return;
          }
          if (polls >= MAX_POLLS) {
            setStatus(`⚠ AI hali tugamadi (${stillQueued} ta kutyapti) — qo'lda Refresh bosing`);
            return;
          }
        } catch {}
        setTimeout(poll, POLL_INTERVAL_MS);
      };
      setTimeout(poll, POLL_INTERVAL_MS);
    }
  };

  dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('drag'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
  dz.addEventListener('drop', (e) => {
    e.preventDefault();
    dz.classList.remove('drag');
    upload(e.dataTransfer.files);
  });
  $('pickFiles').addEventListener('click', () => inp.click());
  $('pickFolder').addEventListener('click', () => finp.click());
  inp.addEventListener('change', (e) => upload(e.target.files));
  finp.addEventListener('change', (e) => upload(e.target.files));
})();

// left tabs
document.querySelectorAll('.sidebar .tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.sidebar .tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const t = btn.dataset.tab;
    document.querySelectorAll('.sidebar .pane').forEach(p => p.hidden = p.dataset.pane !== t);
    if (t === 'local' && state.localEnabled) loadLocalDir('');
    if (t === 'links') loadLinks('');
    if (t === 'dashboard') loadDashboard();
    if (t === 'worklist') loadWorklist();
  });
});

// ===== Worklist =====

async function loadWorklist() {
  if (!state._user) return;
  const status = $('wlStatus').value;
  const own = $('wlOwn').checked;
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (own) params.set('own', 'true');
  let data;
  try {
    data = await apiJson(`/api/worklist?${params}`);
  } catch (e) {
    setStatus('worklist xatosi: ' + e.message);
    return;
  }
  $('wlMeta').textContent = `${data.count} ta yozuv`;
  const ul = $('wlList');
  ul.innerHTML = '';
  for (const it of data.items) {
    const li = document.createElement('li');
    li.className = 'dash-row';
    const left = document.createElement('div');

    const name = document.createElement('div');
    name.className = 'name';
    const ttl = document.createElement('span');
    ttl.style.fontWeight = '600';
    ttl.textContent = it.patient_name || it.patient_id;
    name.appendChild(ttl);
    if (it.priority && it.priority !== 'normal') {
      const pr = document.createElement('span');
      pr.className = `wl-priority ${it.priority}`;
      pr.textContent = it.priority;
      name.appendChild(pr);
    }
    const sp = document.createElement('span');
    sp.className = `wl-status-${it.status}`;
    sp.textContent = it.status;
    sp.style.fontSize = '11px';
    sp.style.marginLeft = '4px';
    name.appendChild(sp);
    left.appendChild(name);

    const sub = document.createElement('div');
    sub.className = 'meta';
    const ass = it.assigned_to ? `→ ${it.assigned_to}` : 'tayinlanmagan';
    sub.textContent = `ID ${it.patient_id} · ${it.modality || '—'} · ${it.study_date || '—'} · ${ass}`;
    left.appendChild(sub);

    if (it.last_name && state._user.role !== 'annotator') {
      const sub2 = document.createElement('div');
      sub2.className = 'meta';
      sub2.style.opacity = '0.7';
      sub2.textContent = `xlsx: ${it.last_name} ${it.first_name || ''} (${it.record_count} yozuv)`;
      left.appendChild(sub2);
    }

    const top = document.createElement('div');
    top.className = 'row';
    top.appendChild(left);
    li.appendChild(top);

    if (state._user.role === 'admin' || state._user.role === 'reviewer') {
      li.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        promptWorklistEdit(it);
      });
      li.title = "Right-click: tayinlash/status o'zgartirish";
    }
    li.addEventListener('click', () => {
      if (it.last_name) showPatientOverview(it.patient_id);
    });
    ul.appendChild(li);
  }
}

async function promptWorklistEdit(it) {
  const mode = prompt(
    `'${it.patient_name || it.patient_id}' uchun:\n\n` +
    `1 — assign\n` +
    `2 — priority (low/normal/high/urgent)\n` +
    `3 — status (pending/in_progress/done/skipped)\n` +
    `Tanlang:`, ''
  );
  if (!mode) return;
  let body = {};
  if (mode === '1') {
    const u = prompt('Foydalanuvchi nomi (bo\'sh — bekor qilish):', it.assigned_to || '');
    if (u === null) return;
    body.assigned_to = u || '';
  } else if (mode === '2') {
    const p = prompt('Priority:', it.priority || 'normal');
    if (!p) return;
    body.priority = p;
  } else if (mode === '3') {
    const s = prompt('Status:', it.status || 'pending');
    if (!s) return;
    body.status = s;
  } else return;
  try {
    await api(`/api/worklist/${it.id}`, {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    await loadWorklist();
  } catch (e) { alert(e.message); }
}

(function bindWorklistUi() {
  $('wlStatus').addEventListener('change', loadWorklist);
  $('wlOwn').addEventListener('change', loadWorklist);
  $('wlRefresh').addEventListener('click', loadWorklist);
})();

// ===== Patient overview modal =====

async function showPatientOverview(patientId) {
  let data;
  try {
    data = await apiJson(`/api/db/patient/${encodeURIComponent(patientId)}/overview`);
  } catch (e) {
    alert('xatosi: ' + e.message);
    return;
  }
  const body = $('patientBody');
  const p = data.patient;
  body.innerHTML = '';
  const wrap = document.createElement('div');
  wrap.className = 'patient-overview';

  const head = document.createElement('div');
  head.className = 'pat-head';
  const nm = document.createElement('div');
  nm.className = 'name';
  nm.textContent = `${p.last_name || ''} ${p.first_name || ''}`.trim() || '—';
  head.appendChild(nm);
  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.textContent = `ID ${p.patient_id} · ${p.sex || '—'} · DOB ${p.birth_date || '—'} · ` +
    `${data.records.length} yozuv · ${data.dicoms.length} bog'langan DICOM · ${data.worklist.length} worklist`;
  head.appendChild(meta);
  wrap.appendChild(head);

  if (!data.timeline.length) {
    const empty = document.createElement('div');
    empty.className = 'report-empty';
    empty.textContent = "Timeline bo'sh.";
    wrap.appendChild(empty);
    body.appendChild(wrap);
    $('patientModal').hidden = false;
    return;
  }

  for (const t of data.timeline) {
    const item = document.createElement('div');
    item.className = `timeline-item kind-${t.kind}`;
    if (t.kind === 'dicom') item.classList.add('dicom-row');
    const ts = document.createElement('div');
    ts.className = 'ts';
    ts.textContent = t.ts || '—';
    const bd = document.createElement('div');
    bd.className = 'body';
    if (t.kind === 'record') {
      bd.innerHTML = `📄 <b>${t.exam_code || '—'}</b> ${t.exam_name || ''}` +
        (t.diagnosis ? ` — <i>${(t.diagnosis || '').slice(0,100)}</i>` : '');
    } else if (t.kind === 'worklist') {
      bd.innerHTML = `📥 ${t.modality || '—'} · status: <b>${t.status}</b>` +
        (t.assigned_to ? ` · ${t.assigned_to}` : '');
    } else if (t.kind === 'dicom') {
      const sCounts = Object.entries(t.annotation_statuses || {}).map(([k,v]) => `${k}:${v}`).join(' ');
      bd.innerHTML = `🖼 <b>${t.ref}</b> · ${t.annotation_count} ann ${sCounts ? `(${sCounts})` : ''}`;
      item.addEventListener('click', () => {
        $('patientModal').hidden = true;
        if (t.source === 'upload') openItem({ kind: 'upload', id: t.ref });
        else openItem({ kind: 'local', path: t.ref });
      });
    }
    item.append(ts, bd);
    wrap.appendChild(item);
  }
  body.appendChild(wrap);
  $('patientModal').hidden = false;
}

$('patientCloseBtn').addEventListener('click', () => { $('patientModal').hidden = true; });

// ===== De-identification modal =====

async function openDeidModal() {
  if (!state.current) return;
  const body = $('deidBody');
  body.innerHTML = '<div class="report-empty">PHI maydonlar tekshirilmoqda…</div>';
  $('deidModal').hidden = false;
  let data;
  try {
    data = await apiJson(
      `/api/deidentify/detect?source=${refSource()}&ref=${encodeURIComponent(refValue())}`
    );
  } catch (e) {
    body.innerHTML = `<div class="admin-err">${e.message}</div>`;
    return;
  }
  body.innerHTML = '';

  const sec = document.createElement('div');
  sec.className = 'deid-section';
  const h3 = document.createElement('h3');
  h3.textContent = `${data.count} ta PHI maydon topildi`;
  sec.appendChild(h3);

  const table = document.createElement('table');
  table.className = 'deid-table';
  for (const item of data.phi_tags_found) {
    const tr = document.createElement('tr');
    if (item.preserves_year) tr.classList.add('preserves');
    tr.innerHTML = `<td>${item.tag}${item.preserves_year ? ' (yil saqlanadi)' : ''}</td>` +
      `<td><code>${(item.value || '').replace(/[<>&]/g, '_')}</code></td>`;
    table.appendChild(tr);
  }
  sec.appendChild(table);
  body.appendChild(sec);

  const note = document.createElement('div');
  note.className = 'report-empty';
  note.style.fontSize = '11px';
  note.textContent = 'Anonimlashtirilgan DICOM yuklab olinganda: ism/ID/manzil tozalanadi, sana — yilni saqlab, sanai 01.01 ga moslashtiriladi, "PatientIdentityRemoved=YES" yoziladi.';
  body.appendChild(note);

  const actions = document.createElement('div');
  actions.className = 'deid-actions';
  const dl = document.createElement('button');
  dl.textContent = '⤓ Anonimlashtirilgan DICOM yuklab olish';
  dl.addEventListener('click', async () => {
    const tok = getToken();
    const res = await fetch(
      `/api/deidentify/download?source=${refSource()}&ref=${encodeURIComponent(refValue())}`,
      { headers: { 'Authorization': `Bearer ${tok}` } },
    );
    if (!res.ok) { alert('xato: ' + res.status); return; }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const stem = (refValue() || 'anon').split('/').pop().replace(/\.dcm$/i, '');
    a.download = `${stem}_anon.dcm`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });
  actions.appendChild(dl);
  body.appendChild(actions);
}

// ===== Research / radiologist verification (review_decisions) =====

async function openReviewModal() {
  $('reviewModal').hidden = false;
  await renderReviewQueue('pending');
}

async function renderReviewQueue(filter) {
  const body = $('reviewBody');
  body.innerHTML = '<div class="report-empty">Yuklanmoqda…</div>';
  let data;
  try {
    data = await apiJson(`/api/research/review/queue?status=${encodeURIComponent(filter)}&limit=200`);
  } catch (e) {
    body.innerHTML = `<div class="admin-err">${e.message}</div>`;
    return;
  }
  body.innerHTML = '';

  const counts = data.counts || {};
  const tabBar = document.createElement('div');
  tabBar.style.cssText = 'display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;align-items:center';
  const tabs = [
    ['pending',  `⏳ Kutmoqda (${counts.pending  || 0})`],
    ['accepted', `✓ Qabul (${counts.accepted || 0})`],
    ['edited',   `✎ Tahrirlangan (${counts.edited   || 0})`],
    ['rejected', `✗ Rad etilgan (${counts.rejected || 0})`],
    ['all',      `Barchasi`],
  ];
  for (const [key, label] of tabs) {
    const b = document.createElement('button');
    b.textContent = label;
    b.style.cssText = 'padding:6px 10px;font-size:12px;'
      + (key === filter ? 'background:var(--accent);color:#fff;font-weight:bold' : '');
    b.addEventListener('click', () => renderReviewQueue(key));
    tabBar.appendChild(b);
  }

  const exportBtn = document.createElement('button');
  exportBtn.textContent = '⤓ Gold labels JSONL';
  exportBtn.title = 'Tasdiqlangan + tahrirlangan barcha review yozuvlarini eksport qilish';
  exportBtn.style.cssText = 'margin-left:auto;padding:6px 10px;font-size:12px';
  exportBtn.addEventListener('click', async () => {
    const tok = getToken();
    const res = await fetch('/api/research/review/export?include_status=accepted,edited', {
      headers: { 'Authorization': `Bearer ${tok}` },
    });
    if (!res.ok) { alert('eksport xatosi: ' + res.status); return; }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gold_labels_${new Date().toISOString().slice(0,10)}.jsonl`;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  });
  tabBar.appendChild(exportBtn);
  body.appendChild(tabBar);

  if (!data.items || !data.items.length) {
    const empty = document.createElement('div');
    empty.className = 'report-empty';
    empty.textContent = `${filter} statusida review yo'q.`;
    body.appendChild(empty);
    return;
  }

  const table = document.createElement('table');
  table.className = 'user-table';
  table.style.fontSize = '12px';
  table.innerHTML = `<thead><tr>
    <th>SOP UID</th><th>Ko'rinish</th><th>Pseudo</th><th>Status</th>
    <th>Reviewer</th><th>Imported</th><th>Amallar</th>
  </tr></thead>`;
  const tbody = document.createElement('tbody');
  for (const it of data.items) {
    const tr = document.createElement('tr');
    const sopShort = (it.sop_uid || '').slice(-20);
    const view = `${it.laterality}-${it.view}`;
    tr.innerHTML = `
      <td title="${it.sop_uid}"><code style="font-size:10px">…${sopShort}</code></td>
      <td>${view}</td>
      <td>${it.n_pseudo} ${it.n_final ? `→ <b>${it.n_final}</b>` : ''}</td>
      <td><span class="role-pill role-${it.status === 'accepted' || it.status === 'edited' ? 'admin' : it.status === 'rejected' ? 'annotator' : 'reviewer'}">${it.status}</span></td>
      <td>${it.reviewer || '—'}</td>
      <td style="font-size:10px;color:var(--muted)">${(it.imported_at || '').slice(0,16).replace('T',' ')}</td>
    `;
    const actions = document.createElement('td');
    actions.style.cssText = 'display:flex;gap:4px;flex-wrap:wrap';

    const inspectBtn = document.createElement('button');
    inspectBtn.textContent = '🔍 Ko\'rish';
    inspectBtn.style.cssText = 'padding:3px 8px;font-size:11px';
    inspectBtn.addEventListener('click', () => openReviewItem(it.id));
    actions.appendChild(inspectBtn);

    if (it.status === 'pending') {
      const acceptBtn = document.createElement('button');
      acceptBtn.textContent = '✓';
      acceptBtn.title = 'Pseudo-bboxlarni o\'zgartirmasdan qabul qilish';
      acceptBtn.style.cssText = 'padding:3px 8px;font-size:11px;background:#2a7e2a;color:#fff';
      acceptBtn.addEventListener('click', async () => {
        if (!confirm('Pseudo-bboxlarni gold deb belgilaysizmi?')) return;
        await decideReview(it.id, 'accepted', null, '');
        await renderReviewQueue(filter);
      });
      actions.appendChild(acceptBtn);

      const rejectBtn = document.createElement('button');
      rejectBtn.textContent = '✗';
      rejectBtn.title = 'Bu element uchun bbox emas (rad etish)';
      rejectBtn.style.cssText = 'padding:3px 8px;font-size:11px;background:#a02020;color:#fff';
      rejectBtn.addEventListener('click', async () => {
        const reason = prompt('Rad etish sababi (ixtiyoriy):') || '';
        await decideReview(it.id, 'rejected', null, reason);
        await renderReviewQueue(filter);
      });
      actions.appendChild(rejectBtn);
    }

    tr.appendChild(actions);
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  body.appendChild(table);
}

async function decideReview(reviewId, status, finalBboxes, comments) {
  try {
    await api(`/api/research/review/${reviewId}/decide`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        status,
        final_bboxes: finalBboxes,
        comments: comments || '',
      }),
    });
  } catch (e) {
    alert('decide xatosi: ' + e.message);
  }
}

async function openReviewItem(reviewId) {
  let item;
  try {
    item = await apiJson(`/api/research/review/${reviewId}`);
  } catch (e) {
    alert('item yuklash xatosi: ' + e.message);
    return;
  }
  const body = $('reviewBody');
  body.innerHTML = '';

  const back = document.createElement('button');
  back.textContent = '← Roʻyxatga qaytish';
  back.style.cssText = 'padding:6px 10px;margin-bottom:12px;font-size:12px';
  back.addEventListener('click', () => renderReviewQueue('pending'));
  body.appendChild(back);

  const wrap = document.createElement('div');
  wrap.style.cssText = 'display:grid;grid-template-columns:1fr 320px;gap:16px;align-items:start';

  const left = document.createElement('div');
  left.style.cssText = 'position:relative;background:#000;border:1px solid var(--border);min-height:300px';
  if (item.has_preview) {
    const img = document.createElement('img');
    img.style.cssText = 'display:block;max-width:100%;height:auto';
    img.id = 'reviewPreviewImg';
    const tok = getToken();
    const r = await fetch(`/api/research/review/${reviewId}/preview`, {
      headers: { 'Authorization': `Bearer ${tok}` },
    });
    if (r.ok) {
      const blob = await r.blob();
      img.src = URL.createObjectURL(blob);
      img.onload = () => {
        // overlay pseudo bboxes as SVG
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', `0 0 ${img.naturalWidth} ${img.naturalHeight}`);
        svg.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none';
        for (const b of (item.pseudo_bboxes || [])) {
          const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
          rect.setAttribute('x', b.x0); rect.setAttribute('y', b.y0);
          rect.setAttribute('width',  Math.max(0, b.x1 - b.x0));
          rect.setAttribute('height', Math.max(0, b.y1 - b.y0));
          rect.setAttribute('fill', 'none');
          rect.setAttribute('stroke', '#ffb000');
          rect.setAttribute('stroke-width', '4');
          rect.setAttribute('stroke-dasharray', '8,4');
          svg.appendChild(rect);
          const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
          txt.setAttribute('x', b.x0 + 6); txt.setAttribute('y', b.y0 + 22);
          txt.setAttribute('fill', '#ffb000');
          txt.setAttribute('font-size', '20');
          txt.textContent = `cls=${b.cls} c=${(b.confidence || 0).toFixed(2)}`;
          svg.appendChild(txt);
        }
        left.appendChild(svg);
      };
      left.appendChild(img);
    } else {
      left.innerHTML = '<div style="padding:18px;color:#888">Preview unavailable</div>';
    }
  } else {
    left.innerHTML = '<div style="padding:18px;color:#888">Preview unavailable</div>';
  }

  const right = document.createElement('div');
  right.innerHTML = `
    <div style="font-size:11px;color:var(--muted);margin-bottom:4px">SOP UID</div>
    <code style="display:block;font-size:10px;word-break:break-all;background:var(--panel-2);padding:4px;border-radius:3px;margin-bottom:10px">${item.sop_uid}</code>
    <div style="font-size:11px;color:var(--muted)">Ko'rinish</div>
    <div style="margin-bottom:10px"><b>${item.laterality} - ${item.view}</b> · status: <b>${item.status}</b></div>
    <div style="font-size:11px;color:var(--muted)">Findings (matn)</div>
    <pre style="font-size:11px;background:var(--panel-2);padding:6px;border-radius:3px;max-height:140px;overflow:auto;margin-bottom:10px">${JSON.stringify(item.findings || {}, null, 2)}</pre>
    <div style="font-size:11px;color:var(--muted)">Pseudo-bboxlar (${(item.pseudo_bboxes || []).length})</div>
    <pre style="font-size:11px;background:var(--panel-2);padding:6px;border-radius:3px;max-height:160px;overflow:auto;margin-bottom:10px">${JSON.stringify(item.pseudo_bboxes || [], null, 2)}</pre>
  `;

  const decideBar = document.createElement('div');
  decideBar.style.cssText = 'display:flex;flex-direction:column;gap:6px';
  if (item.status === 'pending' || item.status === 'rejected') {
    const acc = document.createElement('button');
    acc.textContent = '✓ Qabul (pseudo-ni gold)';
    acc.style.cssText = 'padding:8px;background:#2a7e2a;color:#fff;font-weight:bold';
    acc.addEventListener('click', async () => {
      if (!confirm('Pseudo-bboxlarni gold deb belgilaysizmi?')) return;
      await decideReview(reviewId, 'accepted', item.pseudo_bboxes || [], '');
      await renderReviewQueue('pending');
    });
    decideBar.appendChild(acc);
  }
  if (item.status === 'pending' || item.status === 'accepted') {
    const rej = document.createElement('button');
    rej.textContent = '✗ Rad etish';
    rej.style.cssText = 'padding:8px;background:#a02020;color:#fff';
    rej.addEventListener('click', async () => {
      const reason = prompt('Rad etish sababi (ixtiyoriy):') || '';
      await decideReview(reviewId, 'rejected', null, reason);
      await renderReviewQueue('pending');
    });
    decideBar.appendChild(rej);
  }
  right.appendChild(decideBar);

  wrap.appendChild(left);
  wrap.appendChild(right);
  body.appendChild(wrap);
}

async function openStatsModal() {
  $('statsModal').hidden = false;
  const body = $('statsBody');
  body.innerHTML = '<div class="report-empty">Yuklanmoqda…</div>';
  let s;
  try {
    s = await apiJson('/api/stats/overview');
  } catch (e) {
    body.innerHTML = `<div class="admin-err">${e.message}</div>`;
    return;
  }
  body.innerHTML = '';

  const grid = document.createElement('div');
  grid.className = 'stats-grid';
  const cards = [
    ['Foydalanuvchilar', `${s.users_active} / ${s.users_total}`],
    ['Bemorlar', s.patients_total],
    ['Yozuvlar', s.records_total],
    ['Bog\'langan DICOM', s.dicom_links_total],
    ['Annotatsiyalar', s.annotations_total],
    ['AI dan kelgan', s.ai_originated_annotations],
    ['Worklist', s.worklist_total],
    ['Audit hodisalar', s.history_events],
  ];
  for (const [lbl, num] of cards) {
    const c = document.createElement('div');
    c.className = 'stats-card';
    c.innerHTML = `<div class="lbl">${lbl}</div><div class="num">${num}</div>`;
    grid.appendChild(c);
  }
  body.appendChild(grid);

  // (Yangi) Lokal DICOM papkasi statistikasi — alohida skanerlash, async
  const localSec = document.createElement('div');
  localSec.className = 'stats-section';
  localSec.innerHTML = `<h3>📁 Lokal DICOM papkasi <button id="localDicomRefresh" style="float:right;font-size:11px;padding:2px 8px;background:var(--panel-2);border:1px solid var(--border);color:var(--text);border-radius:3px;cursor:pointer">↻ Skan</button></h3>
    <div id="localDicomStats" style="font-size:13px;color:var(--muted)">yuklanmoqda…</div>`;
  body.appendChild(localSec);
  loadLocalDicomStats();
  const refreshBtn = $('localDicomRefresh');
  if (refreshBtn) refreshBtn.addEventListener('click', async () => {
    refreshBtn.disabled = true;
    refreshBtn.textContent = '⏳ Skanerlanmoqda...';
    // Kesh-bypass uchun yangi parametr
    await loadLocalDicomStats(true);
    refreshBtn.disabled = false;
    refreshBtn.textContent = '↻ Skan';
  });

  if (s.review_seconds) {
    const sec = document.createElement('div');
    sec.className = 'stats-section';
    sec.innerHTML = `<h3>Review davomiyligi (sekund)</h3>` +
      `<div style="display:flex;gap:14px;color:var(--muted);font-size:12px">` +
      `  <span>n=${s.review_seconds.count}</span>` +
      `  <span>median=${s.review_seconds.median}s</span>` +
      `  <span>p90=${s.review_seconds.p90}s</span>` +
      `  <span>mean=${s.review_seconds.mean}s</span>` +
      `</div>`;
    body.appendChild(sec);
  }

  body.appendChild(buildBarSection('Annotatsiyalar status bo\'yicha', s.annotations_by_status, 'status', statusBarColor));
  body.appendChild(buildBarSection('Top label\'lar', s.annotations_by_label.slice(0, 10), 'label'));
  body.appendChild(buildBarSection('Top yaratuvchilar', s.annotations_by_creator.slice(0, 10), 'user'));
  body.appendChild(buildBarSection('Worklist statuslar', s.worklist_by_status, 'status'));
  body.appendChild(buildBarSection('Audit action turlari', s.history_by_action, 'action'));
  body.appendChild(buildBarSection('Top audit yaratuvchilar', s.history_per_user.slice(0, 10), 'username'));

  if (s.history_last_30_days && s.history_last_30_days.length) {
    const sec = document.createElement('div');
    sec.className = 'stats-section';
    sec.innerHTML = `<h3>Oxirgi 30 kun audit faolligi</h3>`;
    const max = Math.max(...s.history_last_30_days.map(d => d.n));
    const spark = document.createElement('div');
    spark.className = 'stats-spark';
    for (const d of s.history_last_30_days) {
      const bar = document.createElement('div');
      bar.className = 'day';
      bar.style.height = `${Math.max(2, Math.round(d.n * 100 / max))}%`;
      bar.title = `${d.day}: ${d.n}`;
      spark.appendChild(bar);
    }
    sec.appendChild(spark);
    body.appendChild(sec);
  }
}

function statusBarColor(label) {
  return ({ approved: 'green', submitted: 'yellow', rejected: 'red', done: 'green', in_progress: 'yellow' })[label] || '';
}

function buildBarSection(title, items, key, colorFn) {
  const sec = document.createElement('div');
  sec.className = 'stats-section';
  sec.innerHTML = `<h3>${title}</h3>`;
  if (!items || !items.length) {
    sec.innerHTML += '<div class="report-empty" style="padding:6px 0">— bo\'sh</div>';
    return sec;
  }
  const max = Math.max(...items.map(i => i.n)) || 1;
  for (const it of items) {
    const lbl = it[key] || '?';
    const row = document.createElement('div');
    row.className = 'stats-bar-row';
    const bar = document.createElement('div');
    bar.className = 'bar';
    if (colorFn) {
      const c = colorFn(lbl);
      if (c) bar.classList.add(c);
    }
    bar.style.width = `${Math.round(it.n * 100 / max)}%`;
    row.innerHTML = `<div class="lbl" title="${lbl}">${lbl}</div>`;
    row.appendChild(bar);
    const num = document.createElement('div');
    num.className = 'num';
    num.textContent = it.n;
    row.appendChild(num);
    sec.appendChild(row);
  }
  return sec;
}

function toggleMobile(selector) {
  const el = document.querySelector(selector);
  if (!el) return;
  el.classList.toggle('open');
}
$('mobileSidebarBtn').addEventListener('click', () => toggleMobile('aside.sidebar'));
$('mobileMetaBtn').addEventListener('click', () => toggleMobile('aside.meta-pane'));

$('statsBtn').addEventListener('click', openStatsModal);
$('statsCloseBtn').addEventListener('click', () => { $('statsModal').hidden = true; });

async function loadLocalDicomStats(bypassCache) {
  const div = $('localDicomStats');
  if (!div) return;
  div.innerHTML = '<span style="color:var(--muted)">Skanerlanmoqda — bir necha sek (katta papka bo\'lsa 10-30 sek)...</span>';
  try {
    const url = bypassCache ? '/api/stats/local_dicom?nocache=' + Date.now() : '/api/stats/local_dicom';
    const j = await apiJson(url);
    if (!j.enabled) {
      div.innerHTML = `<div style="color:#eab308">⚠ ${j.message}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:4px">Server'da <code>LOCAL_DICOM_ROOT=&lt;yo'l&gt;</code> env-var o'rnating</div>`;
      return;
    }
    const modList = (j.by_modality || []).map(m => `<span style="background:var(--panel-2);padding:2px 6px;border-radius:3px;margin-right:4px">${m.modality}: <strong>${m.count}</strong></span>`).join('');
    const subList = (j.top_subdirs || []).slice(0, 10).map(d => `
      <tr><td style="padding:2px 8px;font-family:monospace">${d.name}</td><td style="padding:2px 8px;text-align:right"><strong>${d.dicom_count}</strong></td></tr>
    `).join('');
    div.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
        <div class="stats-card"><div class="lbl">DICOM fayllari</div><div class="num">${j.dicom_files.toLocaleString()}</div></div>
        <div class="stats-card"><div class="lbl">Noyob bemorlar (PatientID)</div><div class="num">${j.unique_patients.toLocaleString()}</div></div>
      </div>
      <div style="font-size:12px;color:var(--muted);margin-bottom:6px">Papka: <code>${j.root}</code> · Skan: ${j.scan_duration_s} sek ${j.errors ? `· ${j.errors} xato` : ''}</div>
      ${modList ? `<div style="margin-bottom:8px"><strong>Modality bo'yicha:</strong><br>${modList}</div>` : ''}
      ${subList ? `<details><summary style="cursor:pointer">Top papkalar (${j.top_subdirs.length})</summary>
        <table style="margin-top:4px;border-collapse:collapse;font-size:12px"><thead><tr style="background:var(--panel-2)"><th style="padding:2px 8px;text-align:left">Papka</th><th style="padding:2px 8px;text-align:right">DICOM</th></tr></thead><tbody>${subList}</tbody></table>
      </details>` : ''}
    `;
  } catch (e) {
    div.innerHTML = `<div style="color:#ef4444">Xato: ${e.message || e}</div>`;
  }
}

// ===== PACS modal =====

let _pacsSelectedSrv = null;
let _pacsLastQuery = null;

async function openPacsModal() {
  $('pacsModal').hidden = false;
  await renderPacsServers();
}

async function renderPacsServers() {
  const body = $('pacsBody');
  body.innerHTML = '<div class="report-empty">Yuklanmoqda…</div>';
  let data;
  try { data = await apiJson('/api/pacs/servers'); }
  catch (e) { body.innerHTML = `<div class="admin-err">${e.message}</div>`; return; }
  body.innerHTML = '';

  const left = document.createElement('div');
  left.style.cssText = 'display:flex; flex-direction:column; gap:6px; margin-bottom:12px;';
  const h = document.createElement('h3');
  h.style.cssText = 'font-size:12px; color:var(--muted); text-transform:uppercase; margin:0';
  h.textContent = 'Serverlar';
  left.appendChild(h);

  for (const s of data.servers) {
    const row = document.createElement('div');
    row.style.cssText = 'display:flex; gap:6px; padding:6px 8px; background:var(--panel-2); border:1px solid var(--border); border-radius:4px; align-items:center; cursor:pointer;';
    if (_pacsSelectedSrv && _pacsSelectedSrv.id === s.id) {
      row.style.borderColor = 'var(--accent)';
    }
    const info = document.createElement('div');
    info.style.flex = '1';
    info.innerHTML = `<b>${s.name}</b> <span style="color:var(--muted);font-size:11px">${s.host}:${s.port} (${s.aet})</span>`;
    row.appendChild(info);

    const echoBtn = document.createElement('button');
    echoBtn.textContent = '🩺 Echo';
    echoBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      try {
        const r = await apiJson(`/api/pacs/servers/${s.id}/echo`, { method: 'POST' });
        alert(r.ok ? 'Echo OK ✓' : `Echo xato: ${r.status}`);
      } catch (err) { alert(err.message); }
    });
    row.appendChild(echoBtn);

    if (state._user.role === 'admin') {
      const del = document.createElement('button');
      del.textContent = '🗑'; del.style.color = 'var(--danger)';
      del.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (!confirm(`'${s.name}' o'chirilsinmi?`)) return;
        try {
          await api(`/api/pacs/servers/${s.id}`, { method: 'DELETE' });
          if (_pacsSelectedSrv && _pacsSelectedSrv.id === s.id) _pacsSelectedSrv = null;
          await renderPacsServers();
        } catch (err) { alert(err.message); }
      });
      row.appendChild(del);
    }

    row.addEventListener('click', () => {
      _pacsSelectedSrv = s;
      renderPacsServers();
    });

    left.appendChild(row);
  }

  if (state._user.role === 'admin' || state._user.role === 'reviewer') {
    const form = document.createElement('div');
    form.style.cssText = 'display:grid; grid-template-columns: 1fr 1fr 80px 1fr 1fr; gap:6px; margin-top:8px;';
    form.innerHTML = `
      <input type="text" id="pNewName" placeholder="nomi" />
      <input type="text" id="pNewHost" placeholder="host/IP" />
      <input type="number" id="pNewPort" placeholder="4242" min="1" max="65535" />
      <input type="text" id="pNewAet" placeholder="AET" />
      <button id="pNewSubmit">+ Qo'shish</button>
    `;
    left.appendChild(form);
  }
  body.appendChild(left);

  const submit = $('pNewSubmit');
  if (submit) {
    submit.addEventListener('click', async () => {
      const name = $('pNewName').value.trim();
      const host = $('pNewHost').value.trim();
      const port = parseInt($('pNewPort').value, 10);
      const aet = $('pNewAet').value.trim();
      if (!name || !host || !aet || !port) { alert('Hamma maydonlar kerak'); return; }
      try {
        await api('/api/pacs/servers', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ name, host, port, aet }),
        });
        await renderPacsServers();
      } catch (e) { alert(e.message); }
    });
  }

  if (_pacsSelectedSrv) {
    const right = document.createElement('div');
    right.style.cssText = 'border-top: 1px solid var(--border); padding-top:12px;';
    const h2 = document.createElement('h3');
    h2.style.cssText = 'font-size:12px; color:var(--muted); text-transform:uppercase; margin:0 0 6px';
    h2.textContent = `Qidirish — ${_pacsSelectedSrv.name}`;
    right.appendChild(h2);

    const form = document.createElement('div');
    form.style.cssText = 'display:grid; grid-template-columns: 1fr 1fr 1fr 1fr 100px; gap:6px;';
    form.innerHTML = `
      <input type="text" id="pqId" placeholder="Patient ID" />
      <input type="text" id="pqName" placeholder="Patient name" />
      <input type="text" id="pqMod" placeholder="Modality (MG)" value="MG" />
      <input type="text" id="pqDate" placeholder="StudyDate YYYYMMDD" />
      <button id="pqSubmit">🔍 Qidirish</button>
    `;
    right.appendChild(form);

    const results = document.createElement('div');
    results.id = 'pacsResults';
    results.style.cssText = 'margin-top:10px; max-height:300px; overflow:auto;';
    if (_pacsLastQuery) {
      renderPacsResults(results, _pacsLastQuery);
    }
    right.appendChild(results);

    body.appendChild(right);

    $('pqSubmit').addEventListener('click', async () => {
      const params = {
        patient_id: $('pqId').value.trim(),
        patient_name: $('pqName').value.trim(),
        modality: $('pqMod').value.trim(),
        study_date: $('pqDate').value.trim(),
      };
      results.innerHTML = '<div class="report-empty">Qidirilmoqda…</div>';
      try {
        const data = await apiJson(`/api/pacs/servers/${_pacsSelectedSrv.id}/query`, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(params),
        });
        _pacsLastQuery = data.results;
        renderPacsResults(results, data.results);
      } catch (e) {
        results.innerHTML = `<div class="admin-err">${e.message}</div>`;
      }
    });
  }
}

function renderPacsResults(container, results) {
  container.innerHTML = '';
  if (!results || !results.length) {
    container.innerHTML = '<div class="report-empty">— natija yo\'q</div>';
    return;
  }
  const meta = document.createElement('div');
  meta.style.cssText = 'color:var(--muted); font-size:11px; margin-bottom:6px';
  meta.textContent = `${results.length} ta study`;
  container.appendChild(meta);

  const table = document.createElement('table');
  table.className = 'user-table';
  table.innerHTML = `<thead><tr>
    <th>Patient ID</th><th>Name</th><th>Date</th><th>Modality</th><th>Description</th><th></th>
  </tr></thead>`;
  const tbody = document.createElement('tbody');
  for (const r of results) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.patient_id || ''}</td>
      <td>${r.patient_name || ''}</td>
      <td>${r.study_date || ''}</td>
      <td>${r.modalities || ''}</td>
      <td style="font-size:10px; color:var(--muted)">${(r.description || '').slice(0,40)}</td>
    `;
    const tdAct = document.createElement('td');
    const btn = document.createElement('button');
    btn.textContent = '→ Worklist';
    btn.title = "Worklist'ga qo'shish";
    btn.addEventListener('click', async () => {
      const dt = r.study_date || '';
      const formatted = dt.length === 8 ? `${dt.slice(0,4)}-${dt.slice(4,6)}-${dt.slice(6,8)}` : dt;
      try {
        await api('/api/pacs/to-worklist', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            patient_id: r.patient_id,
            patient_name: r.patient_name,
            study_date: formatted,
            modality: (r.modalities || '').split('\\').shift() || '',
          }),
        });
        btn.textContent = '✓ qo\'shildi';
        btn.disabled = true;
      } catch (e) { alert(e.message); }
    });
    tdAct.appendChild(btn);
    tr.appendChild(tdAct);
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  container.appendChild(table);
}

$('pacsBtn').addEventListener('click', openPacsModal);
$('pacsCloseBtn').addEventListener('click', () => { $('pacsModal').hidden = true; });

// ===== TOTP modal =====

async function openTotpModal() {
  $('totpModal').hidden = false;
  await renderTotp();
}

async function renderTotp() {
  const body = $('totpBody');
  if (state._user.totp_enrolled) {
    body.innerHTML = `
      <div class="report-empty" style="padding:0 0 8px">
        2FA hozir <b style="color:var(--ok)">yoqilgan</b>. Har kirishda authenticator kodi so'raladi.
      </div>
      <h3 style="font-size:12px;color:var(--muted);text-transform:uppercase;margin:14px 0 6px">O'chirish</h3>
      <div style="display:flex;gap:6px">
        <input type="password" id="totpDisablePwd" placeholder="parolingiz" style="flex:1; background:var(--panel-2);border:1px solid var(--border);color:var(--text);padding:6px;border-radius:3px"/>
        <button id="totpDisableBtn" style="color:var(--danger)">2FA ni o'chirish</button>
      </div>
      <div class="modal-err" id="totpErr"></div>
    `;
    $('totpDisableBtn').addEventListener('click', async () => {
      const pwd = $('totpDisablePwd').value;
      if (!pwd) { $('totpErr').textContent = 'parol kerak'; return; }
      try {
        await api('/api/auth/totp/disable', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ password: pwd }),
        });
        state._user.totp_enrolled = false;
        updateUserBar();
        await renderTotp();
      } catch (e) {
        $('totpErr').textContent = e.message;
      }
    });
    return;
  }

  body.innerHTML = '<div class="report-empty">QR kod tayyorlanmoqda…</div>';
  let setup;
  try {
    setup = await apiJson('/api/auth/totp/setup', { method: 'POST' });
  } catch (e) {
    body.innerHTML = `<div class="admin-err">${e.message}</div>`;
    return;
  }

  body.innerHTML = `
    <p style="margin:0 0 10px;font-size:12px;color:var(--muted)">
      Telefoningizdagi authenticator (Google Authenticator, Authy, 1Password, ...)'da bu QR kodni skanerlang
      yoki secret'ni qo'lda kiriting:
    </p>
    <div style="display:flex;gap:14px;align-items:flex-start">
      <img src="${setup.qr_png_data_url}" alt="QR" style="width:180px;height:180px;background:#fff;padding:8px;border-radius:6px"/>
      <div style="flex:1">
        <div style="font-size:10px;color:var(--muted);text-transform:uppercase">Secret (manual)</div>
        <code style="display:block;background:var(--panel-2);padding:6px;border-radius:3px;font-size:11px;word-break:break-all;margin-top:4px">${setup.secret}</code>
        <div style="font-size:10px;color:var(--muted);margin-top:10px">App'dagi 6 raqamli kodni kiriting:</div>
        <input type="text" id="totpVerifyCode" inputmode="numeric" maxlength="6"
               style="width:120px; background:var(--panel-2); border:1px solid var(--border); color:var(--text); padding:8px; font-size:18px; letter-spacing:4px; border-radius:3px; margin-top:6px"/>
        <button id="totpVerifyBtn" style="display:block;margin-top:8px">✓ Yoqish</button>
        <div class="modal-err" id="totpErr"></div>
      </div>
    </div>
  `;
  $('totpVerifyBtn').addEventListener('click', async () => {
    const code = $('totpVerifyCode').value.trim();
    if (code.length !== 6) { $('totpErr').textContent = '6 raqamli kod kerak'; return; }
    try {
      await api('/api/auth/totp/verify', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      state._user.totp_enrolled = true;
      updateUserBar();
      await renderTotp();
      setStatus('✓ 2FA yoqildi');
    } catch (e) {
      $('totpErr').textContent = e.message;
    }
  });
}

$('totpBtn').addEventListener('click', openTotpModal);
$('totpCloseBtn').addEventListener('click', () => { $('totpModal').hidden = true; });

// ===== Annotated DICOMs overview =====

async function openOverviewModal() {
  $('overviewModal').hidden = false;
  await renderOverview();
}

async function renderOverview(filter) {
  const body = $('overviewBody');
  body.innerHTML = '<div class="report-empty">Yuklanmoqda…</div>';
  const params = new URLSearchParams();
  if (filter && filter.status) params.set('status', filter.status);
  if (filter && filter.own) params.set('own', 'true');
  let data;
  try {
    data = await apiJson(`/api/annotations/overview?${params}&limit=300`);
  } catch (e) {
    body.innerHTML = `<div class="admin-err">${e.message}</div>`;
    return;
  }
  body.innerHTML = '';

  const ctrl = document.createElement('div');
  ctrl.className = 'ov-controls';
  const sel = document.createElement('select');
  sel.innerHTML = `
    <option value="">Barcha statuslar</option>
    <option value="draft">Drafts</option>
    <option value="submitted">Submitted</option>
    <option value="approved">Approved</option>
    <option value="rejected">Rejected</option>
  `;
  if (filter && filter.status) sel.value = filter.status;
  sel.addEventListener('change', () => renderOverview({ status: sel.value, own: ownChk.checked }));

  const ownChk = document.createElement('input');
  ownChk.type = 'checkbox';
  ownChk.checked = !!(filter && filter.own);
  ownChk.addEventListener('change', () => renderOverview({ status: sel.value, own: ownChk.checked }));
  const ownLbl = document.createElement('label');
  ownLbl.style.cssText = 'display:flex; gap:4px; align-items:center; font-size:12px; color:var(--muted)';
  ownLbl.append(ownChk, document.createTextNode(' faqat meniki'));

  ctrl.appendChild(sel);
  ctrl.appendChild(ownLbl);
  body.appendChild(ctrl);

  const meta = document.createElement('div');
  meta.className = 'ov-meta-bar';
  meta.textContent = `${data.count} / ${data.total} ta annotatsiyalangan DICOM`;
  body.appendChild(meta);

  if (!data.items.length) {
    const empty = document.createElement('div');
    empty.className = 'report-empty';
    empty.textContent = "Topilmadi.";
    body.appendChild(empty);
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'ov-grid';
  for (const it of data.items) {
    const card = document.createElement('div');
    card.className = 'ov-card';

    const name = document.createElement('div');
    name.className = 'ov-name';
    if (it.patient) {
      name.textContent = `${it.patient.last_name || ''} ${it.patient.first_name || ''}`.trim();
    } else {
      name.textContent = it.ref.split('/').pop();
    }
    card.appendChild(name);

    const m1 = document.createElement('div');
    m1.className = 'ov-meta';
    if (it.patient) {
      m1.textContent = `ID ${it.patient.patient_id} · ${it.patient.sex || '—'} · DOB ${it.patient.birth_date || '—'}`;
    } else {
      m1.textContent = `${it.source}: ${it.ref}`;
    }
    card.appendChild(m1);

    const m2 = document.createElement('div');
    m2.className = 'ov-meta';
    m2.style.opacity = '0.7';
    m2.textContent = `${it.annotation_count} ann · ${(it.creators || []).join(', ') || '—'} · ${(it.latest_ts || '').slice(0,10)}`;
    card.appendChild(m2);

    const stats = document.createElement('div');
    stats.className = 'ov-stats';
    for (const [s, n] of Object.entries(it.by_status)) {
      const p = document.createElement('span');
      p.className = `ov-pill ${s}`;
      p.textContent = `${s}: ${n}`;
      stats.appendChild(p);
    }
    card.appendChild(stats);

    if (Object.keys(it.by_label).length) {
      const labels = document.createElement('div');
      labels.className = 'ov-labels';
      labels.textContent = Object.entries(it.by_label)
        .map(([k, v]) => `${k}×${v}`).join(', ');
      card.appendChild(labels);
    }

    card.addEventListener('click', () => {
      $('overviewModal').hidden = true;
      if (it.source === 'upload') openItem({ kind: 'upload', id: it.ref });
      else openItem({ kind: 'local', path: it.ref });
    });
    grid.appendChild(card);
  }
  body.appendChild(grid);
}

$('overviewBtn').addEventListener('click', openOverviewModal);
$('overviewCloseBtn').addEventListener('click', () => { $('overviewModal').hidden = true; });

// ===== Annotation templates =====

async function refreshTemplates() {
  if (!state._user) return;
  try {
    const data = await apiJson('/api/templates');
    state._templates = data.templates || [];
    const sel = $('tplSelect');
    sel.innerHTML = '<option value="">📑 Template…</option>';
    for (const t of state._templates) {
      const o = document.createElement('option');
      o.value = t.id;
      o.textContent = `${t.name} (${t.annotation_count})`;
      sel.appendChild(o);
    }
  } catch (e) {}
}

$('tplSelect').addEventListener('change', async (e) => {
  const id = e.target.value;
  if (!id) return;
  try {
    const t = await apiJson(`/api/templates/${id}`);
    if (!t.payload || !t.payload.length) { setStatus('template bo\'sh'); return; }
    const now = new Date().toISOString();
    let added = 0;
    for (const a of t.payload) {
      const fresh = JSON.parse(JSON.stringify(a));
      fresh.id = uid();
      fresh.frame = state.frame;
      fresh.created_at = now;
      fresh.updated_at = now;
      fresh.note = (fresh.note ? fresh.note + ' ' : '') + `[tpl: ${t.name}]`;
      state.annotations.push(fresh);
      added++;
    }
    state.selectedId = state.annotations[state.annotations.length - 1].id;
    renderSvg(); renderAnnoList();
    scheduleAutosave();
    setStatus(`✓ ${added} ann (template "${t.name}")`);
  } catch (err) {
    setStatus('template xato: ' + err.message);
  }
  e.target.value = '';
});

$('tplSaveBtn').addEventListener('click', async () => {
  if (!state.annotations.length) { alert("hech narsa yo'q"); return; }
  const name = prompt("Template nomi:", `tpl_${new Date().toISOString().slice(0,10)}`);
  if (!name) return;
  const desc = prompt("Tavsif (ixtiyoriy):", "") || null;
  const isShared = confirm("Hammaga ko'rinsinmi? (Cancel = faqat menga)");
  try {
    const r = await apiJson('/api/templates', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        name, description: desc, is_shared: isShared,
        payload: state.annotations,
      }),
    });
    setStatus(`✓ template "${name}" saqlandi (${r.annotation_count} ann)`);
    await refreshTemplates();
  } catch (e) { alert(e.message); }
});

// ===== C-STORE =====

async function pickPacsServer() {
  let data;
  try { data = await apiJson('/api/pacs/servers'); }
  catch (e) { alert(e.message); return null; }
  if (!data.servers || !data.servers.length) {
    alert("PACS server qo'shilmagan. 🏥 PACS modal orqali qo'shing.");
    return null;
  }
  if (data.servers.length === 1) return data.servers[0];
  const names = data.servers.map((s, i) => `${i + 1}. ${s.name} (${s.host}:${s.port})`).join('\n');
  const choice = prompt(`Qaysi PACS serverga yuborish?\n${names}\n\nRaqam:`, "1");
  const idx = parseInt(choice, 10) - 1;
  return data.servers[idx] || null;
}

$('cStoreBtn').addEventListener('click', async () => {
  if (!state.current) return;
  const srv = await pickPacsServer();
  if (!srv) return;
  if (!confirm(`'${srv.name}' (${srv.aet}@${srv.host}:${srv.port}) serverga joriy DICOM yuborilsinmi?`)) return;
  setStatus(`📤 ${srv.name} ga yuborilmoqda…`);
  try {
    const r = await apiJson(`/api/pacs/servers/${srv.id}/store`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        items: [{ source: refSource(), ref: refValue() }],
      }),
    });
    setStatus(`✓ ${r.sent}/${r.total} yuborildi (${r.failed} xato)`);
  } catch (e) {
    setStatus("PACS xato: " + e.message);
  }
});

// ===== Audit timeline =====

async function openAuditModal() {
  $('auditModal').hidden = false;
  await renderAuditTimeline();
}

async function renderAuditTimeline(filter) {
  const body = $('auditBody');
  body.innerHTML = '<div class="report-empty">Yuklanmoqda…</div>';
  const params = new URLSearchParams();
  if (filter && filter.username) params.set('username', filter.username);
  if (filter && filter.action) params.set('action', filter.action);
  params.set('limit', '300');
  let data;
  try { data = await apiJson(`/api/audit/timeline?${params}`); }
  catch (e) { body.innerHTML = `<div class="admin-err">${e.message}</div>`; return; }
  body.innerHTML = '';

  const ctrl = document.createElement('div');
  ctrl.className = 'ov-controls';
  const userInp = document.createElement('input');
  userInp.placeholder = 'username';
  userInp.value = (filter && filter.username) || '';
  userInp.style.cssText = 'background:var(--panel-2);border:1px solid var(--border);color:var(--text);padding:4px 8px;border-radius:3px';
  const actSel = document.createElement('select');
  actSel.innerHTML = `
    <option value="">Barcha amallar</option>
    <option value="create">create</option>
    <option value="update">update</option>
    <option value="delete">delete</option>
    <option value="status">status</option>
  `;
  if (filter && filter.action) actSel.value = filter.action;
  const apply = document.createElement('button');
  apply.textContent = '🔍';
  apply.addEventListener('click', () => renderAuditTimeline({
    username: userInp.value.trim(),
    action: actSel.value,
  }));
  ctrl.append(userInp, actSel, apply);
  body.appendChild(ctrl);

  const meta = document.createElement('div');
  meta.className = 'ov-meta-bar';
  meta.textContent = `${data.count} ta hodisa (eng so'nggi)`;
  body.appendChild(meta);

  if (!data.events.length) {
    const empty = document.createElement('div');
    empty.className = 'report-empty';
    empty.textContent = "Hodisalar yo'q";
    body.appendChild(empty);
    return;
  }
  let lastDay = '';
  for (const ev of data.events) {
    const day = (ev.ts || '').slice(0, 10);
    if (day !== lastDay) {
      const sep = document.createElement('div');
      sep.style.cssText = 'margin:12px 0 4px; color:var(--accent); font-weight:600; font-size:12px';
      sep.textContent = day;
      body.appendChild(sep);
      lastDay = day;
    }
    const row = document.createElement('div');
    row.className = 'hist-row';
    row.style.borderLeft = '3px solid var(--border)';
    row.style.paddingLeft = '10px';
    row.innerHTML = `<div class="row-head">
      <span class="action-pill action-${ev.action}">${ev.action}</span>
      <span class="who">${ev.username || '—'}</span>
      <span class="ts">${(ev.ts || '').slice(11, 19)}</span>
      <span class="ts" style="opacity:0.7">${ev.ref}</span>
    </div>`;
    if (ev.action === 'status' && ev.prev_snapshot && ev.new_snapshot) {
      const t = document.createElement('div');
      t.style.cssText = 'margin-top:4px; font-size:11px';
      const note = ev.new_snapshot.note ? ` ("${ev.new_snapshot.note}")` : '';
      t.innerHTML = `<b>${ev.prev_snapshot.status}</b> → <b>${ev.new_snapshot.status}</b>${note}`;
      row.appendChild(t);
    }
    body.appendChild(row);
  }
}

$('auditBtn').addEventListener('click', openAuditModal);
$('auditCloseBtn').addEventListener('click', () => { $('auditModal').hidden = true; });

$('deidBtn').addEventListener('click', openDeidModal);
$('deidCloseBtn').addEventListener('click', () => { $('deidModal').hidden = true; });

async function downloadDicomExport(kind, suffix, label) {
  if (!state.current) return;
  const tok = getToken();
  setStatus(`${label} yaratilmoqda…`);
  const res = await fetch(
    `/api/export/${kind}?source=${refSource()}&ref=${encodeURIComponent(refValue())}`,
    { headers: { 'Authorization': `Bearer ${tok}` } },
  );
  if (!res.ok) {
    if (res.status === 404) alert("Annotatsiyalar yo'q — avval annotatsiya qiling");
    else if (res.status === 503) {
      const err = await res.text();
      alert(`Server ${kind} eksportni qo'llab-quvvatlamayapti:\n${err}`);
    } else alert(`${label} xato: ` + res.status);
    setStatus('');
    return;
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const stem = (refValue() || 'anon').split('/').pop().replace(/\.dcm$/i, '');
  a.download = `${stem}_${suffix}.dcm`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  setStatus(`${label} yuklab olindi`);
}

$('srBtn').addEventListener('click', () => downloadDicomExport('dicom-sr', 'sr', 'DICOM-SR'));
$('segBtn').addEventListener('click', () => downloadDicomExport('dicom-seg', 'seg', 'DICOM-SEG'));

async function downloadMaskExport(format, ext, label) {
  if (!state.current) return;
  const tok = getToken();
  setStatus(`${label} yaratilmoqda…`);
  const res = await fetch(
    `/api/export/mask?source=${refSource()}&ref=${encodeURIComponent(refValue())}&format=${format}`,
    { headers: { 'Authorization': `Bearer ${tok}` } },
  );
  if (!res.ok) {
    if (res.status === 404) alert("Annotatsiyalar yo'q — avval annotatsiya qiling");
    else if (res.status === 422) alert('Rasm o\'lchamlari noma\'lum — maska yaratib bo\'lmadi');
    else alert(`${label} xato: ` + res.status);
    setStatus('');
    return;
  }
  const legend = res.headers.get('X-Mask-Legend');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const stem = (refValue() || 'anon').split('/').pop().replace(/\.dcm$/i, '');
  a.download = `${stem}_${ext}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
  setStatus(`${label} yuklab olindi${legend ? ' · legend: ' + legend : ''}`);
}
$('maskPngBtn').addEventListener('click', () => downloadMaskExport('png', 'mask.png', 'Mask PNG'));
$('maskNiftiBtn').addEventListener('click', () => downloadMaskExport('nifti', 'mask.nii.gz', 'Mask NIfTI'));

(function bindLinksUi() {
  const inp = $('linksSearch');
  let timer = null;
  inp.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => loadLinks(inp.value), 300);
  });
  inp.addEventListener('keydown', (e) => { if (e.key === 'Enter') loadLinks(inp.value); });
  $('linksRefresh').addEventListener('click', () => loadLinks(inp.value));
})();

// right tabs
document.querySelectorAll('.meta-pane .tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.meta-pane .tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const t = btn.dataset.rtab;
    document.querySelectorAll('.meta-pane .rpane').forEach(p => p.hidden = p.dataset.rpane !== t);
  });
});

let _currentLocalDir = '';

function refreshActiveList() {
  const uploadsActive = !document.querySelector('.sidebar [data-pane="uploads"]').hidden;
  if (uploadsActive) {
    refreshUploads().catch(() => {});
  } else if (state.localEnabled) {
    loadLocalDir(_currentLocalDir).catch(() => {});
  }
}

async function loadLinks(q) {
  setStatus("bog'langanlar olinmoqda…");
  try {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    params.set('limit', '500');
    const data = await apiJson(`/api/db/links?${params}`);
    $('linksMeta').textContent = `${data.count} ta bog'langan DICOM` + (q ? ` ("${q}")` : '');
    const ul = $('linksList');
    ul.innerHTML = '';
    for (const r of data.links) {
      const li = document.createElement('li');
      li.className = 'link-row';
      const top = document.createElement('div');
      top.className = 'row';
      const left = document.createElement('div');
      const name = document.createElement('div');
      name.className = 'name';
      name.textContent = `${r.last_name || ''} ${r.first_name || ''}`.trim() || '—';
      if (r.annotation_count > 0) {
        const pill = document.createElement('span');
        pill.className = 'anno-pill';
        pill.textContent = r.annotation_count;
        pill.title = `${r.annotation_count} annotatsiya`;
        name.appendChild(pill);
      }
      left.appendChild(name);
      const sub = document.createElement('div');
      sub.className = 'meta';
      const conf = r.confidence != null ? `${r.confidence}%` : 'qo\'lda';
      sub.textContent = `ID ${r.patient_id} · DOB ${r.birth_date || '—'} · ${r.record_count} yozuv · oxirgi ${r.last_visit || '—'} · ${conf}`;
      left.appendChild(sub);
      const sub2 = document.createElement('div');
      sub2.className = 'meta';
      sub2.textContent = `${r.source}: ${r.ref}`;
      sub2.style.opacity = '0.7';
      left.appendChild(sub2);
      top.appendChild(left);
      li.appendChild(top);
      li.addEventListener('click', () => openLinkedRef(r));
      ul.appendChild(li);
    }
    setStatus('tayyor');
  } catch (e) {
    setStatus("xato: " + e.message);
  }
}

async function openLinkedRef(r) {
  document.querySelectorAll('.file-list li.active').forEach(x => x.classList.remove('active'));
  if (r.source === 'upload') {
    await openItem({ kind: 'upload', id: r.ref });
  } else {
    await openItem({ kind: 'local', path: r.ref });
  }
}

async function loadLocalDir(subdir) {
  setStatus("ro'yxat olinmoqda…");
  _currentLocalDir = subdir || '';
  try {
    const data = await apiJson(`/api/local/list?subdir=${encodeURIComponent(subdir)}`);
    $('crumb').textContent = subdir ? '/' + subdir : '/';
    const items = [];
    if (subdir) items.push({ kind: 'dir', label: '..', path: data.parent });
    for (const d of data.dirs) items.push({ kind: 'dir', label: d.name, path: d.path });
    for (const f of data.files) items.push({
      kind: 'local', label: f.name, sub: humanSize(f.size),
      path: f.path, annoCount: f.annotation_count || 0,
    });
    renderFileList($('localList'), items);
    setStatus('tayyor');
  } catch (e) {
    setStatus('xato: ' + e.message);
  }
}
function humanSize(n) {
  if (!n) return '';
  const u = ['B','KB','MB','GB'];
  let i = 0; while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(i ? 1 : 0)} ${u[i]}`;
}

// toolbar buttons
$('fitBtn').addEventListener('click', fitToScreen);
$('oneToOneBtn').addEventListener('click', oneToOne);
$('invertBtn').addEventListener('click', () => {
  state.invert = !state.invert;
  $('invertBtn').classList.toggle('active', state.invert);
  loadImage(false);
});
$('resetWlBtn').addEventListener('click', () => {
  state.wc = state.defaultWc; state.ww = state.defaultWw;
  applyDefaults();
  loadImage(false);
});

// frame slider
$('frameSlider').addEventListener('input', (e) => {
  state.frame = parseInt(e.target.value, 10) || 0;
  $('frameLabel').textContent = `${state.frame + 1} / ${state.frames}`;
  loadImage(false);
  renderSvg();
});

// (B4) Mammografiya W/L presetlari — tezkor sozlash uchun
const MAMMO_PRESETS = {
  mass: { wc: 2000, ww: 4000, label: '🔵 Mass' },
  calc: { wc: 600,  ww: 1200, label: '⚪ Calc' },
  skin: { wc: 2500, ww: 5000, label: '🟡 Skin' },
};
const WL_CUSTOM_KEY = 'mamograf_wl_presets';

function loadCustomWlPresets() {
  try {
    const j = localStorage.getItem(WL_CUSTOM_KEY);
    return j ? JSON.parse(j) : {};
  } catch { return {}; }
}
function saveCustomWlPresets(obj) {
  try { localStorage.setItem(WL_CUSTOM_KEY, JSON.stringify(obj)); } catch {}
}

function refreshCustomPresetSelect() {
  const sel = $('wlCustomSelect');
  if (!sel) return;
  const presets = loadCustomWlPresets();
  const names = Object.keys(presets).sort();
  sel.innerHTML = '<option value="">— maxsus —</option>';
  for (const n of names) {
    const opt = document.createElement('option');
    opt.value = n;
    opt.textContent = `${n} (${presets[n].wc}/${presets[n].ww})`;
    sel.appendChild(opt);
  }
  if (names.length > 0) {
    const opt = document.createElement('option');
    opt.value = '__delete__';
    opt.textContent = '— o\'chirish —';
    sel.appendChild(opt);
  }
}

function setActivePresetBtn(name) {
  document.querySelectorAll('.wl-preset[data-preset]').forEach(b => {
    b.classList.toggle('active', b.dataset.preset === name);
  });
  state.activeWlPreset = name || null;
}

function applyWl(wc, ww, presetName) {
  state.wc = wc;
  state.ww = ww;
  $('wcInput').value = Math.round(wc);
  $('wwInput').value = Math.round(ww);
  $('wcSlider').value = clampRange($('wcSlider'), wc);
  $('wwSlider').value = clampRange($('wwSlider'), ww);
  setActivePresetBtn(presetName);
  loadImage(false);
}

async function applyAutoWl() {
  // Histogramma asosida — DICOM metadata'dan WC/WW
  if (!state.current) return;
  try {
    const md = await apiJson(`/api/files/${state.current.id || ''}/metadata`).catch(() => null);
    // Aniqlangan WC/WW DICOM tag'larida (WindowCenter / WindowWidth)
    const wc = md && (md.WindowCenter || md.window_center);
    const ww = md && (md.WindowWidth || md.window_width);
    if (wc != null && ww != null) {
      const wcVal = Array.isArray(wc) ? wc[0] : wc;
      const wwVal = Array.isArray(ww) ? ww[0] : ww;
      applyWl(parseFloat(wcVal), parseFloat(wwVal), 'auto');
      return;
    }
  } catch {}
  // Fallback: DICOM default'i
  if (state.defaultWc != null && state.defaultWw != null) {
    applyWl(state.defaultWc, state.defaultWw, 'auto');
  } else {
    setStatus('Auto W/L: DICOM\'da WindowCenter yo\'q');
  }
}

(function bindWlPresets() {
  document.querySelectorAll('.wl-preset[data-preset]').forEach(btn => {
    btn.addEventListener('click', () => {
      const name = btn.dataset.preset;
      if (name === 'auto') { applyAutoWl(); return; }
      const p = MAMMO_PRESETS[name];
      if (p) applyWl(p.wc, p.ww, name);
    });
  });
  const sel = $('wlCustomSelect');
  if (sel) {
    sel.addEventListener('change', () => {
      const v = sel.value;
      if (!v) return;
      if (v === '__delete__') {
        const presets = loadCustomWlPresets();
        const name = prompt('O\'chirish uchun preset nomi:\n' + Object.keys(presets).join(', '));
        if (name && presets[name]) {
          delete presets[name];
          saveCustomWlPresets(presets);
          refreshCustomPresetSelect();
        }
        sel.value = '';
        return;
      }
      const p = loadCustomWlPresets()[v];
      if (p) applyWl(p.wc, p.ww, null);
      sel.value = '';
    });
  }
  const saveBtn = $('wlSaveBtn');
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      if (state.wc == null || state.ww == null) {
        alert('Avval WC va WW qiymatlarini sozlang'); return;
      }
      const name = prompt('Preset nomi (mas. "yuqori kontrast"):');
      if (!name || !name.trim()) return;
      const presets = loadCustomWlPresets();
      presets[name.trim()] = { wc: Math.round(state.wc), ww: Math.round(state.ww) };
      saveCustomWlPresets(presets);
      refreshCustomPresetSelect();
      setStatus(`Preset "${name}" saqlandi (WC=${Math.round(state.wc)}, WW=${Math.round(state.ww)})`);
    });
  }
  refreshCustomPresetSelect();
})();

// W/L bindings
(function bindWl() {
  $('wcSlider').addEventListener('input', (e) => {
    state.wc = parseFloat(e.target.value); $('wcInput').value = e.target.value;
    setActivePresetBtn(null);
    scheduleReload();
  });
  $('wwSlider').addEventListener('input', (e) => {
    state.ww = parseFloat(e.target.value); $('wwInput').value = e.target.value;
    setActivePresetBtn(null);
    scheduleReload();
  });
  $('wcInput').addEventListener('change', (e) => {
    state.wc = parseFloat(e.target.value);
    $('wcSlider').value = clampRange($('wcSlider'), state.wc);
    setActivePresetBtn(null);
    scheduleReload();
  });
  $('wwInput').addEventListener('change', (e) => {
    state.ww = parseFloat(e.target.value);
    $('wwSlider').value = clampRange($('wwSlider'), state.ww);
    setActivePresetBtn(null);
    scheduleReload();
  });
})();

window.addEventListener('resize', () => {
  if (Math.abs(state.scale - state.fitScale) < 1e-3) fitToScreen();
});

// ===== ANNOTATION TOOLS =====

function setTool(t) {
  if (state.tool === 'poly' && t !== 'poly') cancelPolyDraw();
  if ((state.tool === 'ruler' || state.tool === 'angle') && t !== state.tool) cancelMeasureDraw();
  state.tool = t;
  $('toolSelect').classList.toggle('active', t === 'select');
  $('toolBbox').classList.toggle('active', t === 'bbox');
  $('toolPoly').classList.toggle('active', t === 'poly');
  const tr = $('toolRuler'); if (tr) tr.classList.toggle('active', t === 'ruler');
  const ta = $('toolAngle'); if (ta) ta.classList.toggle('active', t === 'angle');
  const ts = $('toolSmartClick'); if (ts) ts.classList.toggle('active', t === 'smart');
  const stack = $('imgStack');
  stack.classList.toggle('drawing', t === 'bbox');
  stack.classList.toggle('drawing-poly', t === 'poly');
  stack.classList.toggle('drawing-measure', t === 'ruler' || t === 'angle');
  $('canvasWrap').classList.toggle('drawing', ['bbox', 'poly', 'ruler', 'angle', 'smart'].includes(t));
}
$('toolSelect').addEventListener('click', () => setTool('select'));
$('toolBbox').addEventListener('click', () => setTool('bbox'));
$('toolPoly').addEventListener('click', () => setTool('poly'));
{ const b = $('toolRuler'); if (b) b.addEventListener('click', () => setTool('ruler')); }
{ const b = $('toolAngle'); if (b) b.addEventListener('click', () => setTool('angle')); }
{ const b = $('toolSmartClick'); if (b) b.addEventListener('click', () => setTool('smart')); }

function svgViewSize() {
  const svg = $('annoSvg');
  const vb = svg.viewBox.baseVal;
  return { w: vb.width || 1, h: vb.height || 1 };
}
function svgPointPx(e) {
  const svg = $('annoSvg');
  const pt = svg.createSVGPoint();
  pt.x = e.clientX; pt.y = e.clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return { x: 0, y: 0 };
  return pt.matrixTransform(ctm.inverse());
}
function svgPointNorm(e) {
  const p = svgPointPx(e);
  const { w, h } = svgViewSize();
  return { x: p.x / w, y: p.y / h };
}

// Polygon drawing
const polyDraw = { points: [], cursor: null };

// (B2) Ruler/Angle drawing state — sodda nuqtalar to'plami + kursor
const measureDraw = { points: [], cursor: null };
function cancelMeasureDraw() {
  measureDraw.points = [];
  measureDraw.cursor = null;
  renderSvg();
}
function onMeasureSvgClick(e) {
  if (state.tool !== 'ruler' && state.tool !== 'angle') return;
  e.preventDefault(); e.stopPropagation();
  const p = svgPointNorm(e);
  measureDraw.points.push([p.x, p.y]);
  const need = state.tool === 'angle' ? 3 : 2;
  if (measureDraw.points.length >= need) {
    finalizeMeasureDraw();
  } else {
    renderSvg();
  }
}

// (A4) Smart-click — bir bosish bilan polygon
async function onSmartClick(e) {
  if (state.tool !== 'smart') return;
  if (!state.current) return;
  e.preventDefault(); e.stopPropagation();
  const p = svgPointNorm(e);
  const px = clamp01(p.x), py = clamp01(p.y);
  const source = refSource(); const ref = refValue();
  if (!source || !ref) return;

  setStatus('✨ Smart-click ishlamoqda...');
  try {
    const body = {
      source, ref, frame: state.frame || 0,
      x: px, y: py,
      wc: state.wc, ww: state.ww,
      tolerance: state.smartTolerance || 25,
    };
    const res = await api('/api/inference/smart_click', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(err.replace(/^.*"detail":"?([^"}]+).*$/, '$1') || `HTTP ${res.status}`);
    }
    const data = await res.json();
    const pts = data.points || [];
    if (pts.length < 3) throw new Error('Polygon yetarli emas');
    const id = uid();
    const now = new Date().toISOString();
    const sel = $('labelSelect');
    const label = sel && sel.value || 'mass';
    state.annotations.push({
      id, type: 'polygon', label,
      bi_rads: '', note: `Smart-click (${data.n_vertices} nuqta, ${data.area_pct}%)`,
      points: pts.map(([x, y]) => [clamp01(x), clamp01(y)]),
      frame: state.frame || 0,
      created_at: now, updated_at: now,
      created_by: (state._user && state._user.username) || '',
      status: 'submitted',
    });
    state.selectedId = id;
    renderSvg(); renderAnnoList();
    scheduleAutosave();
    setStatus(`✨ Polygon yaratildi (${data.n_vertices} nuqta)`);
  } catch (err) {
    setStatus(`Smart-click xato: ${err.message || err}`);
  }
}
function onMeasureSvgMove(e) {
  if (state.tool !== 'ruler' && state.tool !== 'angle') return;
  if (measureDraw.points.length === 0) return;
  const p = svgPointNorm(e);
  measureDraw.cursor = [p.x, p.y];
  renderSvg();
}
function finalizeMeasureDraw() {
  if (measureDraw.points.length === 0) return;
  const pts = measureDraw.points.map(p => [clamp01(p[0]), clamp01(p[1])]);
  const type = state.tool === 'angle' ? 'angle' : 'ruler';
  const id = uid();
  const now = new Date().toISOString();
  state.annotations.push({
    id, type,
    label: type,
    points: pts,
    frame: state.frame,
    created_at: now,
    updated_at: now,
    created_by: state._user && state._user.username || '',
    status: 'submitted',
  });
  measureDraw.points = []; measureDraw.cursor = null;
  state.selectedId = id;
  renderSvg(); renderAnnoList();
  scheduleAutosave();
}
// O'lchov hisoblash — natural rasm pikselida × spacing_mm
function computeDistanceMm(p1, p2) {
  if (!state.spacing_mm) return null;
  const img = $('dicomImg');
  const W = img && img.naturalWidth || 1;
  const H = img && img.naturalHeight || 1;
  const dx_px = (p1[0] - p2[0]) * W;  // col
  const dy_px = (p1[1] - p2[1]) * H;  // row
  const dx_mm = dx_px * state.spacing_mm[1];  // col_spacing
  const dy_mm = dy_px * state.spacing_mm[0];  // row_spacing
  return Math.sqrt(dx_mm * dx_mm + dy_mm * dy_mm);
}
function computeAngleDeg(p1, vertex, p3) {
  // p1 -> vertex va p3 -> vertex orasidagi burchak
  const img = $('dicomImg');
  const W = img && img.naturalWidth || 1;
  const H = img && img.naturalHeight || 1;
  const v1x = (p1[0] - vertex[0]) * W, v1y = (p1[1] - vertex[1]) * H;
  const v3x = (p3[0] - vertex[0]) * W, v3y = (p3[1] - vertex[1]) * H;
  const dot = v1x * v3x + v1y * v3y;
  const mag1 = Math.sqrt(v1x * v1x + v1y * v1y);
  const mag3 = Math.sqrt(v3x * v3x + v3y * v3y);
  if (mag1 === 0 || mag3 === 0) return 0;
  const cos = Math.max(-1, Math.min(1, dot / (mag1 * mag3)));
  return Math.acos(cos) * 180 / Math.PI;
}

function cancelPolyDraw() {
  polyDraw.points = [];
  polyDraw.cursor = null;
  renderSvg();
}

function finalizePolyDraw() {
  if (polyDraw.points.length < 3) {
    cancelPolyDraw();
    return;
  }
  const labels = pendingLabels();
  const label = labels[0];
  const birads = $('biradsSelect').value || '';
  const pts = polyDraw.points.map(p => [clamp01(p[0]), clamp01(p[1])]);
  const xs = pts.map(p => p[0]);
  const ys = pts.map(p => p[1]);
  const minX = Math.min(...xs), minY = Math.min(...ys);
  const maxX = Math.max(...xs), maxY = Math.max(...ys);
  const ann = {
    id: uid(),
    type: 'polygon',
    label,
    labels,
    bi_rads: birads,
    note: '',
    frame: state.frame,
    points: pts,
    bbox: [minX, minY, maxX - minX, maxY - minY],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  state.annotations.push(ann);
  state.selectedId = ann.id;
  cancelPolyDraw();
  renderAnnoList();
  scheduleAutosave();
}

function onPolySvgClick(e) {
  if (state.tool !== 'poly') return;
  if (e.detail === 2) return;
  e.preventDefault(); e.stopPropagation();
  const p = svgPointNorm(e);
  polyDraw.points.push([p.x, p.y]);
  renderSvg();
}

function onPolySvgMove(e) {
  const p = svgPointNorm(e);
  if (state.current && _ws && _ws.readyState === 1) {
    if (p.x >= 0 && p.x <= 1 && p.y >= 0 && p.y <= 1) {
      sendCursor(p.x, p.y);
    }
  }
  if (state.tool !== 'poly' || polyDraw.points.length === 0) return;
  polyDraw.cursor = [p.x, p.y];
  renderSvg();
}

function onPolyDblClick(e) {
  if (state.tool !== 'poly') return;
  e.preventDefault(); e.stopPropagation();
  finalizePolyDraw();
}

(() => {
  const svg = $('annoSvg');
  svg.addEventListener('click', onPolySvgClick);
  svg.addEventListener('click', onMeasureSvgClick);   // (B2) Ruler/Angle
  svg.addEventListener('click', onSmartClick);        // (A4) Smart-click
  svg.addEventListener('mousemove', onPolySvgMove);
  svg.addEventListener('mousemove', onMeasureSvgMove); // (B2) Ruler/Angle preview
  svg.addEventListener('dblclick', onPolyDblClick);

  svg.addEventListener('mousedown', (e) => {
    if (state.tool !== 'bbox' || e.button !== 0) return;
    e.preventDefault(); e.stopPropagation();
    const start = svgPointNorm(e);
    const { w: VW, h: VH } = svgViewSize();
    const preview = el('rect', {
      class: 'preview',
      x: start.x * VW, y: start.y * VH, width: 0, height: 0,
    });
    svg.appendChild(preview);

    const onMove = (ev) => {
      const cur = svgPointNorm(ev);
      const x = Math.min(start.x, cur.x);
      const y = Math.min(start.y, cur.y);
      const w = Math.abs(cur.x - start.x);
      const h = Math.abs(cur.y - start.y);
      preview.setAttribute('x', x * VW);
      preview.setAttribute('y', y * VH);
      preview.setAttribute('width', w * VW);
      preview.setAttribute('height', h * VH);
    };
    const onUp = (ev) => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      preview.remove();
      const cur = svgPointNorm(ev);
      const x = clamp01(Math.min(start.x, cur.x));
      const y = clamp01(Math.min(start.y, cur.y));
      const w = Math.min(1 - x, Math.abs(cur.x - start.x));
      const h = Math.min(1 - y, Math.abs(cur.y - start.y));
      if (w < 0.005 || h < 0.005) return;
      addBox(x, y, w, h);
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  });
})();

function addBox(x, y, w, h) {
  const labels = pendingLabels();
  const label = labels[0];
  const birads = $('biradsSelect').value || '';
  const ann = {
    id: uid(),
    type: 'bbox',
    label,
    labels,
    bi_rads: birads,
    note: '',
    frame: state.frame,
    bbox: [x, y, w, h],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  state.annotations.push(ann);
  state.selectedId = ann.id;
  renderSvg(); renderAnnoList();
  scheduleAutosave();
}

function selectAnn(id) {
  state.selectedId = id;
  renderSvg();
  renderAnnoList();
}

function deleteAnn(id) {
  state.annotations = state.annotations.filter(a => a.id !== id);
  if (state.selectedId === id) state.selectedId = null;
  renderSvg(); renderAnnoList();
  scheduleAutosave();
}

function updateAnn(id, patch, opts = {}) {
  const a = state.annotations.find(x => x.id === id);
  if (!a) return;
  Object.assign(a, patch);
  a.updated_at = new Date().toISOString();
  renderSvg();
  if (!opts.skipList) renderAnnoList();
  scheduleAutosave();
}

function renderSvg() {
  const svg = $('annoSvg');
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  if (!state.current) return;
  const { w: VW, h: VH } = svgViewSize();
  const fontSize = Math.max(10, Math.round(VH * 0.012));

  let selectedAnn = null;
  for (const a of state.annotations) {
    if (a.frame !== state.frame) continue;
    const color = colorForAnn(a);
    const zoneCls = aiZoneClass(a);
    const isSel = a.id === state.selectedId;
    if (isSel) selectedAnn = a;

    let labelX, labelY;
    if ((a.type === 'ruler' || a.type === 'angle') && a.points && a.points.length >= 2) {
      // (B2) Ruler / Angle — line(s) + nuqtalar + matn (mm yoki gradus)
      const isAngle = a.type === 'angle' && a.points.length >= 3;
      const segs = isAngle ? [[a.points[0], a.points[1]], [a.points[1], a.points[2]]]
                            : [[a.points[0], a.points[1]]];
      for (const [p1, p2] of segs) {
        const line = el('line', {
          class: 'measure-line' + (isSel ? ' selected' : ''),
          x1: p1[0] * VW, y1: p1[1] * VH,
          x2: p2[0] * VW, y2: p2[1] * VH,
          stroke: color, fill: 'none',
        });
        line.dataset.id = a.id;
        svg.appendChild(line);
      }
      for (const p of a.points) {
        const r = Math.max(2.5, fontSize * 0.18);
        const dot = el('circle', { class: 'measure-dot', cx: p[0] * VW, cy: p[1] * VH, r, fill: color, stroke: '#fff' });
        dot.dataset.id = a.id;
        svg.appendChild(dot);
      }
      // O'lchov matni
      let measureText = '';
      if (isAngle) {
        const deg = computeAngleDeg(a.points[0], a.points[1], a.points[2]);
        measureText = `${deg.toFixed(1)}°`;
      } else {
        const mm = computeDistanceMm(a.points[0], a.points[1]);
        measureText = mm == null ? `${((Math.hypot((a.points[1][0]-a.points[0][0])*VW, (a.points[1][1]-a.points[0][1])*VH))).toFixed(0)} px (spacing yo'q)` : (mm >= 10 ? `${(mm/10).toFixed(2)} cm` : `${mm.toFixed(1)} mm`);
      }
      const mid = isAngle ? a.points[1] : [(a.points[0][0]+a.points[1][0])/2, (a.points[0][1]+a.points[1][1])/2];
      labelX = mid[0] * VW;
      labelY = mid[1] * VH - fontSize * 0.6;
      // matn fonini chizamiz
      const bg = el('rect', { class: 'measure-bg', x: labelX - fontSize*0.5, y: labelY - fontSize*1.1, width: measureText.length * fontSize * 0.6, height: fontSize * 1.3, fill: 'rgba(0,0,0,0.65)', rx: 3, ry: 3 });
      svg.appendChild(bg);
      const txt = el('text', { class: 'measure-text', x: labelX, y: labelY - fontSize*0.1, 'font-size': fontSize, fill: '#ffd24d' });
      txt.textContent = measureText;
      svg.appendChild(txt);
      continue; // standart "label" matnini chizmaslik
    } else if (a.type === 'polygon' && a.points && a.points.length >= 3) {
      const ptsAttr = a.points.map(p => `${p[0] * VW},${p[1] * VH}`).join(' ');
      const poly = el('polygon', {
        class: 'poly' + zoneCls + (isSel ? ' selected' : ''),
        points: ptsAttr,
        stroke: color,
        fill: color,
      });
      poly.dataset.id = a.id;
      poly.addEventListener('mousedown', (e) => onPolyAnnMouseDown(e, a));
      svg.appendChild(poly);
      labelX = Math.min(...a.points.map(p => p[0])) * VW;
      labelY = Math.min(...a.points.map(p => p[1])) * VH - fontSize * 0.3;
    } else {
      const [bx, by, bw, bh] = a.bbox;
      const rect = el('rect', {
        class: 'box' + zoneCls + (isSel ? ' selected' : ''),
        x: bx * VW, y: by * VH, width: bw * VW, height: bh * VH,
        stroke: color,
        fill: color,
      });
      rect.dataset.id = a.id;
      rect.addEventListener('mousedown', (e) => onBoxMouseDown(e, a));
      svg.appendChild(rect);
      labelX = bx * VW;
      labelY = by * VH - fontSize * 0.3;
    }

    const txt = el('text', {
      class: 'label',
      x: labelX, y: labelY,
      'font-size': fontSize,
    });
    txt.textContent = annLabelText(a) + (a.bi_rads ? ` · BI-RADS ${a.bi_rads}` : '');
    svg.appendChild(txt);
  }

  if (selectedAnn && state.tool !== 'bbox' && state.tool !== 'poly') {
    if (selectedAnn.type === 'polygon') {
      renderPolygonHandles(selectedAnn);
    } else {
      renderHandles(selectedAnn);
    }
  }

  // (B2) Ruler/Angle in-progress preview
  if ((state.tool === 'ruler' || state.tool === 'angle') && measureDraw.points.length > 0) {
    const pts = measureDraw.cursor ? [...measureDraw.points, measureDraw.cursor] : measureDraw.points;
    for (let i = 1; i < pts.length; i++) {
      const line = el('line', {
        class: 'measure-preview',
        x1: pts[i-1][0] * VW, y1: pts[i-1][1] * VH,
        x2: pts[i][0] * VW,   y2: pts[i][1] * VH,
      });
      svg.appendChild(line);
    }
    for (const p of measureDraw.points) {
      const c = el('circle', { class: 'measure-dot', cx: p[0] * VW, cy: p[1] * VH, r: 3 / Math.max(state.scale, 0.05), fill: '#ffd24d', stroke: '#fff' });
      svg.appendChild(c);
    }
  }

  if (state.tool === 'poly' && polyDraw.points.length > 0) {
    const allPts = polyDraw.cursor
      ? [...polyDraw.points, polyDraw.cursor]
      : polyDraw.points;
    const ptsAttr = allPts.map(p => `${p[0] * VW},${p[1] * VH}`).join(' ');
    const preview = el('polyline', {
      class: 'poly-preview',
      points: ptsAttr,
    });
    svg.appendChild(preview);
    for (const p of polyDraw.points) {
      const c = el('circle', {
        class: 'poly-vertex',
        cx: p[0] * VW, cy: p[1] * VH, r: 4 / Math.max(state.scale, 0.05),
      });
      svg.appendChild(c);
    }
  }

  for (const s of state.suggestions) {
    if (s.frame !== state.frame) continue;
    const [bx, by, bw, bh] = s.bbox;
    const rect = el('rect', {
      class: 'suggestion',
      x: bx * VW, y: by * VH, width: bw * VW, height: bh * VH,
    });
    rect.dataset.sid = s.id;
    rect.addEventListener('click', (e) => onSuggestionClick(e, s));
    svg.appendChild(rect);
    const txt = el('text', {
      class: 'sug-label',
      x: bx * VW, y: by * VH - fontSize * 0.3,
      'font-size': fontSize,
    });
    txt.textContent = `🤖 ${s.label} ${(s.confidence * 100).toFixed(0)}%`;
    svg.appendChild(txt);
  }
}

const HANDLE_DIRS = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
const HANDLE_CURSORS = {
  nw: 'nwse-resize', se: 'nwse-resize',
  ne: 'nesw-resize', sw: 'nesw-resize',
  n: 'ns-resize', s: 'ns-resize',
  e: 'ew-resize', w: 'ew-resize',
};

function renderHandles(ann) {
  const svg = $('annoSvg');
  const { w: VW, h: VH } = svgViewSize();
  const [bx, by, bw, bh] = ann.bbox;
  const r = 6 / Math.max(state.scale, 0.05);
  const positions = {
    nw: [bx, by],          n: [bx + bw / 2, by],          ne: [bx + bw, by],
    w:  [bx, by + bh / 2],                                 e:  [bx + bw, by + bh / 2],
    sw: [bx, by + bh],     s: [bx + bw / 2, by + bh],     se: [bx + bw, by + bh],
  };
  for (const dir of HANDLE_DIRS) {
    const [px, py] = positions[dir];
    const c = el('circle', {
      class: 'handle',
      cx: px * VW, cy: py * VH, r,
    });
    c.style.cursor = HANDLE_CURSORS[dir];
    c.addEventListener('mousedown', (e) => onHandleMouseDown(e, ann, dir));
    svg.appendChild(c);
  }
}

function onHandleMouseDown(e, ann, dir) {
  if (state.tool === 'bbox') return;
  e.preventDefault(); e.stopPropagation();
  selectAnn(ann.id);

  const start = svgPointNorm(e);
  const orig = ann.bbox.slice();
  const minSize = 0.005;
  let moved = false;

  const onMove = (ev) => {
    const cur = svgPointNorm(ev);
    const dx = cur.x - start.x;
    const dy = cur.y - start.y;
    if (Math.abs(dx) + Math.abs(dy) < 0.0005) return;
    moved = true;

    let x = orig[0], y = orig[1], w = orig[2], h = orig[3];
    const right = orig[0] + orig[2];
    const bottom = orig[1] + orig[3];

    if (dir.includes('w')) {
      let nx = clamp01(orig[0] + dx);
      if (right - nx < minSize) nx = right - minSize;
      x = nx;
      w = right - nx;
    }
    if (dir.includes('e')) {
      let nw = orig[2] + dx;
      nw = Math.max(minSize, Math.min(1 - orig[0], nw));
      w = nw;
    }
    if (dir.includes('n')) {
      let ny = clamp01(orig[1] + dy);
      if (bottom - ny < minSize) ny = bottom - minSize;
      y = ny;
      h = bottom - ny;
    }
    if (dir.includes('s')) {
      let nh = orig[3] + dy;
      nh = Math.max(minSize, Math.min(1 - orig[1], nh));
      h = nh;
    }

    ann.bbox = [x, y, w, h];
    renderSvg();
  };
  const onUp = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
    if (moved) { ann.updated_at = new Date().toISOString(); scheduleAutosave(); }
    renderAnnoList();
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}

function recomputePolyBbox(ann) {
  const xs = ann.points.map(p => p[0]);
  const ys = ann.points.map(p => p[1]);
  const minX = Math.min(...xs), minY = Math.min(...ys);
  const maxX = Math.max(...xs), maxY = Math.max(...ys);
  ann.bbox = [minX, minY, maxX - minX, maxY - minY];
}

function renderPolygonHandles(ann) {
  const svg = $('annoSvg');
  const { w: VW, h: VH } = svgViewSize();
  const r = 6 / Math.max(state.scale, 0.05);
  for (let i = 0; i < ann.points.length; i++) {
    const [px, py] = ann.points[i];
    const c = el('circle', {
      class: 'handle',
      cx: px * VW, cy: py * VH, r,
    });
    c.style.cursor = 'move';
    c.addEventListener('mousedown', (e) => onPolyVertexDown(e, ann, i));
    c.addEventListener('contextmenu', (e) => onPolyVertexRightClick(e, ann, i));
    svg.appendChild(c);
  }
  for (let i = 0; i < ann.points.length; i++) {
    const a1 = ann.points[i];
    const a2 = ann.points[(i + 1) % ann.points.length];
    const mx = (a1[0] + a2[0]) / 2;
    const my = (a1[1] + a2[1]) / 2;
    const m = el('circle', {
      class: 'handle midpoint',
      cx: mx * VW, cy: my * VH, r: r * 0.6,
      'fill-opacity': 0.5,
    });
    m.style.cursor = 'crosshair';
    m.style.fill = '#28d97f';
    m.title = "Bosish: shu chetiga yangi nuqta qo'shish";
    m.addEventListener('mousedown', (e) => onPolyEdgeMidDown(e, ann, i, mx, my));
    svg.appendChild(m);
  }
}

function onPolyVertexDown(e, ann, i) {
  if (e.button !== 0) return;
  e.preventDefault(); e.stopPropagation();
  selectAnn(ann.id);
  const start = svgPointNorm(e);
  const orig = ann.points[i].slice();
  let moved = false;
  const onMove = (ev) => {
    const cur = svgPointNorm(ev);
    const dx = cur.x - start.x;
    const dy = cur.y - start.y;
    if (Math.abs(dx) + Math.abs(dy) < 0.0005) return;
    moved = true;
    ann.points[i] = [clamp01(orig[0] + dx), clamp01(orig[1] + dy)];
    recomputePolyBbox(ann);
    renderSvg();
  };
  const onUp = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
    if (moved) { ann.updated_at = new Date().toISOString(); scheduleAutosave(); }
    renderAnnoList();
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}

function onPolyVertexRightClick(e, ann, i) {
  e.preventDefault(); e.stopPropagation();
  if (ann.points.length <= 3) {
    setStatus("Polygon kamida 3 nuqtaga ega bo'lishi kerak");
    return;
  }
  ann.points.splice(i, 1);
  recomputePolyBbox(ann);
  ann.updated_at = new Date().toISOString();
  renderSvg();
  renderAnnoList();
  scheduleAutosave();
}

function onPolyEdgeMidDown(e, ann, edgeIdx, mx, my) {
  if (e.button !== 0) return;
  e.preventDefault(); e.stopPropagation();
  selectAnn(ann.id);
  ann.points.splice(edgeIdx + 1, 0, [mx, my]);
  recomputePolyBbox(ann);
  const newIdx = edgeIdx + 1;
  const start = svgPointNorm(e);
  const orig = ann.points[newIdx].slice();
  let moved = false;
  const onMove = (ev) => {
    const cur = svgPointNorm(ev);
    const dx = cur.x - start.x;
    const dy = cur.y - start.y;
    moved = true;
    ann.points[newIdx] = [clamp01(orig[0] + dx), clamp01(orig[1] + dy)];
    recomputePolyBbox(ann);
    renderSvg();
  };
  const onUp = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
    if (moved || true) {
      ann.updated_at = new Date().toISOString();
      scheduleAutosave();
    }
    renderAnnoList();
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}

function onPolyAnnMouseDown(e, a) {
  if (state.tool === 'bbox' || state.tool === 'poly') return;
  e.preventDefault(); e.stopPropagation();
  selectAnn(a.id);

  const start = svgPointNorm(e);
  const orig = a.points.map(p => p.slice());
  let moved = false;

  const onMove = (ev) => {
    const cur = svgPointNorm(ev);
    const dx = cur.x - start.x;
    const dy = cur.y - start.y;
    if (Math.abs(dx) + Math.abs(dy) < 0.001) return;
    moved = true;
    const xs = orig.map(p => p[0] + dx);
    const ys = orig.map(p => p[1] + dy);
    let shiftX = 0, shiftY = 0;
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    if (minX < 0) shiftX = -minX;
    else if (maxX > 1) shiftX = 1 - maxX;
    if (minY < 0) shiftY = -minY;
    else if (maxY > 1) shiftY = 1 - maxY;
    a.points = orig.map(p => [p[0] + dx + shiftX, p[1] + dy + shiftY]);
    const xs2 = a.points.map(p => p[0]);
    const ys2 = a.points.map(p => p[1]);
    a.bbox = [
      Math.min(...xs2), Math.min(...ys2),
      Math.max(...xs2) - Math.min(...xs2),
      Math.max(...ys2) - Math.min(...ys2),
    ];
    renderSvg();
  };
  const onUp = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
    if (moved) { a.updated_at = new Date().toISOString(); scheduleAutosave(); }
    renderAnnoList();
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}

function onBoxMouseDown(e, a) {
  if (state.tool === 'bbox') return;
  e.preventDefault(); e.stopPropagation();
  selectAnn(a.id);

  const startNorm = svgPointNorm(e);
  const orig = a.bbox.slice();
  let moved = false;

  const onMove = (ev) => {
    const cur = svgPointNorm(ev);
    const dx = cur.x - startNorm.x;
    const dy = cur.y - startNorm.y;
    if (Math.abs(dx) + Math.abs(dy) < 0.001) return;
    moved = true;
    let nx = orig[0] + dx;
    let ny = orig[1] + dy;
    nx = Math.min(Math.max(0, nx), 1 - orig[2]);
    ny = Math.min(Math.max(0, ny), 1 - orig[3]);
    a.bbox = [nx, ny, orig[2], orig[3]];
    renderSvg();
  };
  const onUp = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
    if (moved) { a.updated_at = new Date().toISOString(); scheduleAutosave(); }
    renderAnnoList();
  };
  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
}

function renderAnnoList() {
  const list = $('annoList');
  list.innerHTML = '';
  const visible = state.annotations.filter(a => a.frame === state.frame);
  $('annoCount').textContent = state.annotations.length;
  $('annoEmpty').style.display = state.annotations.length ? 'none' : '';

  for (const a of visible) {
    const row = document.createElement('div');
    row.className = 'anno-row' + (a.id === state.selectedId ? ' selected' : '');
    row.addEventListener('click', () => selectAnn(a.id));

    const sw = document.createElement('div');
    sw.className = 'swatch';
    sw.style.background = colorFor(a.label);
    row.appendChild(sw);

    const info = document.createElement('div');
    info.className = 'info';

    const labelSel = buildLabelMultiSelect({
      selected: annLabels(a),
      compact: true,
      placeholder: 'Label',
      onChange: (arr) => {
        const labels = arr.length ? arr : [];
        // skipList: keep the dropdown open so several labels can be toggled in a row;
        // refresh the swatch + canvas in place instead of rebuilding the whole list.
        updateAnn(a.id, { labels, label: labels[0] || '' }, { skipList: true });
        sw.style.background = colorFor(labels[0]);
      },
    });
    labelSel.addEventListener('click', e => e.stopPropagation());

    const biSel = document.createElement('select');
    const empty = document.createElement('option');
    empty.value = ''; empty.textContent = 'BI-RADS —';
    biSel.appendChild(empty);
    for (const b of state.birads) {
      const o = document.createElement('option');
      o.value = b; o.textContent = b;
      if (b === a.bi_rads) o.selected = true;
      biSel.appendChild(o);
    }
    biSel.addEventListener('click', e => e.stopPropagation());
    biSel.addEventListener('change', e => updateAnn(a.id, { bi_rads: e.target.value }));

    const head = document.createElement('div');
    head.className = 'lbl';
    head.appendChild(labelSel);
    head.appendChild(biSel);
    const status = a.status || 'draft';
    const sp = document.createElement('span');
    sp.className = `status-pill status-${status}`;
    sp.textContent = status;
    head.appendChild(sp);
    info.appendChild(head);

    const audit = document.createElement('div');
    audit.className = 'audit';
    const created = a.created_by ? `${a.created_by}` : '—';
    const updated = a.updated_by && a.updated_by !== a.created_by ? ` · oxirgi: ${a.updated_by}` : '';
    const reviewed = a.reviewed_by ? ` · ${status === 'approved' ? '✓' : '✗'} ${a.reviewed_by}` : '';
    audit.textContent = `Yaratdi: ${created}${updated}${reviewed}`;
    info.appendChild(audit);

    if (a.review_note && status === 'rejected') {
      const note = document.createElement('div');
      note.className = 'review-note';
      note.textContent = `Reviewer izohi: ${a.review_note}`;
      info.appendChild(note);
    }

    const sa = document.createElement('div');
    sa.className = 'status-actions';
    if (status === 'draft') {
      if (ownAnn(a) || isReviewer()) {
        sa.appendChild(makeStatusBtn('▲ Submit', 'submit', () => changeStatus(a.id, 'submitted')));
      }
    } else if (status === 'submitted') {
      if (isReviewer()) {
        sa.appendChild(makeStatusBtn('✓ Approve', 'approve', () => changeStatus(a.id, 'approved')));
        sa.appendChild(makeStatusBtn('✗ Reject', 'reject', () => promptRejectStatus(a.id)));
      }
      if (ownAnn(a)) {
        sa.appendChild(makeStatusBtn('▼ Recall', '', () => changeStatus(a.id, 'draft')));
      }
    } else if (status === 'approved') {
      if (isReviewer()) {
        sa.appendChild(makeStatusBtn('🔓 Reopen', '', () => changeStatus(a.id, 'draft')));
      }
    } else if (status === 'rejected') {
      if (ownAnn(a) || isReviewer()) {
        sa.appendChild(makeStatusBtn('🔓 Reopen', '', () => changeStatus(a.id, 'draft')));
      }
    }
    sa.appendChild(makeStatusBtn('📜 Tarix', 'history', () => showHistoryFor(a.id)));
    sa.appendChild(makeStatusBtn('📊 Radiomika', 'history', () => showRadiomicsFor(a.id)));
    info.appendChild(sa);

    const meta = document.createElement('div');
    meta.className = 'meta-row';
    const [x, y, w, h] = a.bbox;
    const W = state.meta && state.meta.Columns ? parseInt(state.meta.Columns, 10) : null;
    const H = state.meta && state.meta.Rows ? parseInt(state.meta.Rows, 10) : null;
    const typeIcon = a.type === 'polygon' ? `⬢ ${a.points?.length || 0} nuqta · ` : '';
    if (W && H) {
      meta.textContent = `${typeIcon}(${Math.round(x * W)}, ${Math.round(y * H)}) — ${Math.round(w * W)}×${Math.round(h * H)} px`;
    } else {
      meta.textContent = `${typeIcon}(${(x*100).toFixed(1)}%, ${(y*100).toFixed(1)}%) — ${(w*100).toFixed(1)}%×${(h*100).toFixed(1)}%`;
    }
    info.appendChild(meta);
    row.appendChild(info);

    const xBtn = document.createElement('button');
    xBtn.className = 'x';
    xBtn.textContent = '✕';
    xBtn.title = "O'chirish";
    xBtn.addEventListener('click', e => { e.stopPropagation(); deleteAnn(a.id); });
    row.appendChild(xBtn);

    list.appendChild(row);
  }
}

let _saveTimer = null;
// Manual-save mode: drawing/editing only marks the work as unsaved.
// The user persists explicitly via the 💾 Saqlash button (or Ctrl+S).
function scheduleAutosave() {
  state.dirty = true;
  setSaveStatus('dirty', '● saqlanmagan');
  updateSaveBtn();
}
function setSaveStatus(cls, text) {
  const node = $('saveStatus');
  node.className = 'save-status ' + (cls || '');
  node.textContent = text || '';
}
function updateSaveBtn() {
  const b = $('saveBtn');
  if (!b) return;
  b.disabled = !(state.dirty && state.current);
  b.classList.toggle('pending', !!state.dirty);
}

function makeStatusBtn(text, cls, onClick) {
  const b = document.createElement('button');
  b.className = 'status-btn ' + cls;
  b.textContent = text;
  b.addEventListener('click', (e) => { e.stopPropagation(); onClick(); });
  return b;
}

async function changeStatus(annotationId, newStatus, note) {
  if (!state.current) return;
  try {
    const body = {
      source: refSource(),
      ref: refValue(),
      annotation_id: annotationId,
      status: newStatus,
    };
    if (note) body.note = note;
    const res = await apiJson('/api/annotations/status', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    const a = state.annotations.find(x => x.id === annotationId);
    if (a && res.snapshot) Object.assign(a, res.snapshot);
    renderSvg();
    renderAnnoList();
    setStatus(`status: ${newStatus}`);
    refreshNotifications().catch(() => {});
  } catch (e) {
    setStatus('status xatosi: ' + e.message);
  }
}

function promptRejectStatus(annotationId) {
  const note = prompt("Rejection sababi (ixtiyoriy):", "");
  if (note === null) return;
  changeStatus(annotationId, 'rejected', note);
}

async function showHistoryFor(annotationId) {
  if (!state.current) return;
  const params = new URLSearchParams({
    source: refSource(),
    ref: refValue(),
  });
  if (annotationId) params.set('annotation_id', annotationId);
  let data;
  try {
    data = await apiJson(`/api/annotations/history?${params}`);
  } catch (e) {
    setStatus("tarix xatosi: " + e.message);
    return;
  }
  const body = $('historyBody');
  body.innerHTML = '';
  if (!data.history.length) {
    body.innerHTML = '<div class="report-empty">Tarix bo\'sh.</div>';
  } else {
    for (const h of data.history) {
      const row = document.createElement('div');
      row.className = 'hist-row';
      const head = document.createElement('div');
      head.className = 'row-head';
      const ap = document.createElement('span');
      ap.className = `action-pill action-${h.action}`;
      ap.textContent = h.action;
      const who = document.createElement('span');
      who.className = 'who';
      who.textContent = h.username || '—';
      const ts = document.createElement('span');
      ts.className = 'ts';
      ts.textContent = (h.ts || '').replace('T', ' ').slice(0, 19);
      const aid = document.createElement('span');
      aid.className = 'ts';
      aid.textContent = '· ' + (h.annotation_id || '').slice(0, 12);
      head.append(ap, who, ts, aid);
      row.appendChild(head);

      if (h.action === 'status') {
        const txt = document.createElement('div');
        const oldS = h.prev_snapshot && h.prev_snapshot.status;
        const newS = h.new_snapshot && h.new_snapshot.status;
        const note = h.new_snapshot && h.new_snapshot.note;
        txt.style.marginTop = '4px';
        txt.innerHTML = `<b>${oldS || '—'}</b> → <b>${newS || '—'}</b>` + (note ? ` <i>("${note}")</i>` : '');
        row.appendChild(txt);
      } else if (h.action !== 'create' && h.prev_snapshot && h.new_snapshot) {
        const summary = annotationDiffSummary(h.prev_snapshot, h.new_snapshot);
        if (summary) {
          const txt = document.createElement('div');
          txt.style.marginTop = '4px';
          txt.style.fontSize = '11px';
          txt.textContent = summary;
          row.appendChild(txt);
        }
      } else if (h.action === 'create' && h.new_snapshot) {
        const txt = document.createElement('div');
        txt.style.marginTop = '4px';
        txt.style.fontSize = '11px';
        txt.textContent = `${h.new_snapshot.type || 'bbox'} · ${h.new_snapshot.label || ''}`;
        row.appendChild(txt);
      }
      body.appendChild(row);
    }
  }
  $('historyModal').hidden = false;
}

function annotationDiffSummary(prev, next) {
  const changed = [];
  const keys = ['label', 'bi_rads', 'note', 'frame'];
  for (const k of keys) {
    if (JSON.stringify(prev[k]) !== JSON.stringify(next[k])) {
      changed.push(`${k}: ${prev[k] ?? '—'} → ${next[k] ?? '—'}`);
    }
  }
  if (JSON.stringify(prev.bbox) !== JSON.stringify(next.bbox)) changed.push('bbox o\'zgardi');
  if (JSON.stringify(prev.points) !== JSON.stringify(next.points)) {
    const pp = (prev.points || []).length;
    const np = (next.points || []).length;
    changed.push(`points: ${pp} → ${np}`);
  }
  return changed.join(', ');
}

$('historyCloseBtn').addEventListener('click', () => { $('historyModal').hidden = true; });
$('radiomicsCloseBtn').addEventListener('click', () => { $('radiomicsModal').hidden = true; });

// Toolbar button: radiomics for the selected annotation (or the only one).
$('radiomicsBtn').addEventListener('click', () => {
  const visible = state.annotations.filter(a => a.frame === state.frame);
  if (!visible.length) {
    alert("Bu kadrda annotatsiya yo'q. Avval BBox yoki Poly bilan ROI chizing.");
    return;
  }
  let id = state.selectedId;
  if (!id || !visible.some(a => a.id === id)) {
    if (visible.length === 1) id = visible[0].id;
    else { alert("Avval annotatsiyani tanlang (ro'yxatdan yoki rasm ustida bosib)."); return; }
  }
  showRadiomicsFor(id);
});

const RADIOMICS_FAMILIES = [
  ['shape', 'Shakl (2D morfologiya)'],
  ['first_order', 'First-order (intensivlik)'],
  ['glcm', 'GLCM (tekstura — co-occurrence)'],
  ['glrlm', 'GLRLM (run-length)'],
  ['glszm', 'GLSZM (size-zone)'],
  ['ngtdm', 'NGTDM (neighbouring tone)'],
];

function fmtFeature(v) {
  if (typeof v !== 'number' || !isFinite(v)) return String(v);
  if (v !== 0 && (Math.abs(v) >= 1e4 || Math.abs(v) < 1e-3)) return v.toExponential(3);
  return v.toFixed(4);
}

async function showRadiomicsFor(annotationId, bins) {
  if (!state.current) return;
  // Radiomics runs on the saved copy; persist first in manual-save mode.
  if (state.dirty) { try { await saveAnnotations(); } catch (e) { /* try anyway */ } }
  bins = bins || 32;
  const body = $('radiomicsBody');
  body.innerHTML = '<div class="report-empty">Hisoblanmoqda…</div>';
  $('radiomicsModal').hidden = false;
  try {
    const res = await fetch(
      `/api/radiomics?source=${refSource()}&ref=${encodeURIComponent(refValue())}` +
      `&annotation_id=${encodeURIComponent(annotationId)}&bins=${bins}`,
      { headers: { 'Authorization': `Bearer ${getToken()}` } },
    );
    if (!res.ok) {
      const hint = res.status === 404 ? " (avval annotatsiyani saqlang)" :
                   res.status === 422 ? " (ROI yoki rasm o'lchami yaroqsiz)" : '';
      body.innerHTML = `<div class="report-empty">Xato: ${res.status}${hint}</div>`;
      return;
    }
    renderRadiomics(body, await res.json(), annotationId);
  } catch (e) {
    body.innerHTML = `<div class="report-empty">Tarmoq xatosi: ${e.message}</div>`;
  }
}

function renderRadiomics(body, data, annotationId) {
  const item = (data.results || [])[0];
  body.innerHTML = '';
  if (!item) { body.innerHTML = '<div class="report-empty">Natija yo\'q.</div>'; return; }

  const ctl = document.createElement('div');
  ctl.className = 'radiomics-controls';
  const info = document.createElement('div');
  info.className = 'radiomics-info';
  const sp = item.spacing_mm ? `${item.spacing_mm.map(s => s.toFixed(3)).join('×')} mm/px`
                              : "piksel o'lchami yo'q — birliklar px";
  info.innerHTML = `Label: <b>${(item.labels || [item.label]).join(' + ')}</b> · ` +
                   `tur: ${item.type} · ${sp} · bins: ${data.bins}`;
  ctl.appendChild(info);

  const binSel = document.createElement('select');
  for (const b of [16, 32, 64, 128]) {
    const o = document.createElement('option');
    o.value = b; o.textContent = `${b} bins`;
    if (b === data.bins) o.selected = true;
    binSel.appendChild(o);
  }
  binSel.title = 'Tekstura uchun intensivlik darajalari soni';
  binSel.addEventListener('change', () => showRadiomicsFor(annotationId, parseInt(binSel.value, 10)));
  ctl.appendChild(binSel);

  const csvBtn = document.createElement('button');
  csvBtn.textContent = '⤓ CSV (barcha ROI)';
  csvBtn.title = 'Shu rasmdagi barcha annotatsiyalar radiomikasini CSV qilib yuklash';
  csvBtn.addEventListener('click', () => downloadRadiomicsCsv(data.bins));
  ctl.appendChild(csvBtn);
  body.appendChild(ctl);

  for (const [fam, title] of RADIOMICS_FAMILIES) {
    const feats = item.features[fam];
    if (!feats) continue;
    const h = document.createElement('div');
    h.className = 'report-section-title';
    h.textContent = `${title} · ${Object.keys(feats).length}`;
    body.appendChild(h);
    const tbl = document.createElement('table');
    tbl.className = 'radiomics-table';
    for (const [k, v] of Object.entries(feats)) {
      const tr = document.createElement('tr');
      const td1 = document.createElement('td'); td1.textContent = k;
      const td2 = document.createElement('td'); td2.className = 'val'; td2.textContent = fmtFeature(v);
      tr.appendChild(td1); tr.appendChild(td2);
      tbl.appendChild(tr);
    }
    body.appendChild(tbl);
  }
}

async function downloadRadiomicsCsv(bins) {
  try {
    const res = await fetch(
      `/api/radiomics/csv?source=${refSource()}&ref=${encodeURIComponent(refValue())}&bins=${bins || 32}`,
      { headers: { 'Authorization': `Bearer ${getToken()}` } },
    );
    if (!res.ok) { alert('CSV xato: ' + res.status); return; }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const stem = (refValue() || 'anon').split('/').pop().replace(/\.dcm$/i, '');
    a.download = `${stem}_radiomics.csv`;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert('CSV xato: ' + e.message);
  }
}

async function saveAnnotations() {
  if (!state.current) return;
  if (state.saving) {
    _saveTimer = setTimeout(saveAnnotations, 200);
    return;
  }
  state.saving = true;
  setSaveStatus('dirty', 'saqlanmoqda…');
  try {
    const body = {
      source: refSource(),
      ref: refValue(),
      annotations: state.annotations,
      rows: parseInt(state.meta?.Rows || '0', 10) || null,
      cols: parseInt(state.meta?.Columns || '0', 10) || null,
    };
    await api('/api/annotations', {
      method: 'PUT',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    state.dirty = false;
    setSaveStatus('saved', '✓ saqlandi');
    updateSaveBtn();
    setTimeout(() => { if (!state.dirty) setSaveStatus('', ''); }, 1500);
    refreshActiveList();
  } catch (e) {
    setSaveStatus('err', 'xato!');
    updateSaveBtn();
  } finally {
    state.saving = false;
  }
}

// (A3) Uncertainty heatmap — barcha modellarni ishga tushirib, kelishmaslik
// xaritasini DICOM ustiga overlay qiladi. Qayta bosish -> o'chiradi.
async function toggleUncertaintyHeatmap() {
  if (!state.current || !state.aiAvailable) return;
  const btn = $('aiHeatmapBtn');
  const ov = $('uncertaintyOverlay');
  if (!btn || !ov) return;

  // Allaqachon ko'rsatilgan bo'lsa — o'chir
  if (btn.classList.contains('active')) {
    btn.classList.remove('active');
    ov.hidden = true;
    if (ov.src && ov.src.startsWith('blob:')) URL.revokeObjectURL(ov.src);
    ov.removeAttribute('src');
    setStatus('Uncertainty heatmap o\'chirildi');
    return;
  }

  const source = refSource();
  const ref = refValue();
  if (!source || !ref) return;

  btn.disabled = true;
  const prev = btn.textContent;
  btn.textContent = '🌡 hisoblanmoqda…';
  setStatus('Modellar ishga tushirilmoqda — bir necha sekund...');

  try {
    const conf = parseInt($('aiConfSlider').value, 10) / 100.0;
    const res = await api('/api/inference/uncertainty', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source, ref, model: '', frame: state.frame || 0,
        conf, iou: 0.5, imgsz: 1024,
      }),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(err || `HTTP ${res.status}`);
    }
    const blob = await res.blob();
    const used = res.headers.get('X-Uncertainty-Models') || '';
    const maxh = res.headers.get('X-Uncertainty-MaxHeat') || '?';
    const pct = res.headers.get('X-Uncertainty-NonzeroPct') || '?';
    const url = URL.createObjectURL(blob);
    if (ov.src && ov.src.startsWith('blob:')) URL.revokeObjectURL(ov.src);
    ov.src = url;
    ov.hidden = false;
    btn.classList.add('active');
    const nmod = used.split(',').filter(Boolean).length;
    setStatus(`Uncertainty: ${nmod} model · max=${maxh} · ${pct}% maydon`);
  } catch (e) {
    alert('Uncertainty xato: ' + (e.message || e));
    setStatus('Uncertainty xato');
  } finally {
    btn.disabled = false;
    btn.textContent = prev;
  }
}

async function runInference() {
  if (!state.current || !state.aiAvailable) return;
  const model = $('aiModelSelect').value;
  if (!model) return;
  const btn = $('aiRunBtn');
  btn.disabled = true;
  const prev = btn.textContent;
  btn.textContent = '🤖 ishlayapti…';
  setStatus(`AI tahlil (${model}) — bir necha soniya kuting…`);
  try {
    const body = {
      source: refSource(),
      ref: refValue(),
      model,
      frame: state.frame,
      conf: 0.10,
      iou: 0.5,
      imgsz: 1024,
      wc: state.wc,
      ww: state.ww,
      tta: !!($('aiTtaToggle') && $('aiTtaToggle').checked),
    };
    const res = await apiJson('/api/inference/run', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    state.allSuggestions = (res.detections || []).map((d, i) => ({
      id: 'sug_' + Date.now() + '_' + i,
      frame: state.frame,
      label: d.label,
      confidence: d.confidence,
      bbox: d.bbox,
      class_id: d.class_id,
    }));
    applyAiThreshold();
    setStatus(`AI: ${state.allSuggestions.length} ta taklif (${res.device}) — ko'rsatilmoqda: ${state.suggestions.length}`);
  } catch (e) {
    setStatus('AI xato: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = prev;
  }
}

function applyAiThreshold() {
  state.suggestions = state.allSuggestions.filter(s => s.confidence >= state.aiThreshold);
  renderSvg();
  $('aiClearBtn').hidden = state.allSuggestions.length === 0;
  $('aiAcceptAllBtn').hidden = state.suggestions.length === 0;
  $('aiAcceptAllBtn').textContent = `✓ ${state.suggestions.length} taklifni qabul`;
}

function clearSuggestions() {
  state.allSuggestions = [];
  state.suggestions = [];
  renderSvg();
  $('aiClearBtn').hidden = true;
  $('aiAcceptAllBtn').hidden = true;
}

function acceptAllSuggestions() {
  if (state.suggestions.length === 0) return;
  if (!confirm(`${state.suggestions.length} ta AI taklifini annotatsiyaga aylantirasizmi?`)) return;
  for (const s of state.suggestions) {
    let label = s.label;
    if (!state.labels.find(l => l.name === label)) {
      label = state.labels[0]?.name || 'mass';
    }
    state.annotations.push({
      id: uid(),
      type: 'bbox',
      label,
      labels: [label],
      bi_rads: '',
      note: `AI: ${s.label} ${(s.confidence * 100).toFixed(1)}%`,
      frame: state.frame,
      bbox: s.bbox.slice(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      ai_source: { label: s.label, confidence: s.confidence, class_id: s.class_id },
    });
  }
  const acceptedIds = new Set(state.suggestions.map(s => s.id));
  state.allSuggestions = state.allSuggestions.filter(s => !acceptedIds.has(s.id));
  applyAiThreshold();
  renderAnnoList();
  scheduleAutosave();
  setStatus(`${acceptedIds.size} ta taklif qabul qilindi`);
}

function onSuggestionClick(e, s) {
  e.preventDefault(); e.stopPropagation();
  const proceed = window.confirm(
    `AI taklifini qabul qilasizmi?\n\n` +
    `Label: ${s.label}\n` +
    `Confidence: ${(s.confidence * 100).toFixed(1)}%\n\n` +
    `Annotatsiyaga aylantiriladi.`
  );
  if (!proceed) return;
  let label = s.label;
  if (!state.labels.find(l => l.name === label)) {
    label = state.labels[0]?.name || 'mass';
  }
  const ann = {
    id: uid(),
    type: 'bbox',
    label,
    labels: [label],
    bi_rads: '',
    note: `AI: ${s.label} ${(s.confidence * 100).toFixed(1)}%`,
    frame: state.frame,
    bbox: s.bbox.slice(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ai_source: { label: s.label, confidence: s.confidence, class_id: s.class_id },
  };
  state.annotations.push(ann);
  state.suggestions = state.suggestions.filter(x => x.id !== s.id);
  state.selectedId = ann.id;
  $('aiClearBtn').hidden = state.suggestions.length === 0;
  renderSvg(); renderAnnoList();
  scheduleAutosave();
}

$('aiRunBtn').addEventListener('click', runInference);
// (A3) Uncertainty heatmap tugmasi
(function bindHeatmapBtn() {
  const b = document.getElementById('aiHeatmapBtn');
  if (b) b.addEventListener('click', toggleUncertaintyHeatmap);
})();

// (C1) 4-view yonma-yon proyeksiyalar
const FV_ORDER = ['LCC', 'RCC', 'LMLO', 'RMLO'];
async function toggleFourView() {
  const btn = $('fourViewBtn');
  const grid = $('fourViewGrid');
  const stack = $('imgStack');
  if (!btn || !grid || !stack) return;
  if (btn.classList.contains('active')) {
    // O'chirish
    btn.classList.remove('active');
    grid.hidden = true;
    grid.innerHTML = '';
    stack.hidden = false;
    setStatus('4-view o\'chirildi');
    return;
  }
  if (!state.current || state.current.kind !== 'upload') {
    alert('4-view faqat yuklangan fayllar uchun (study guruhi). Avval upload tanlang.');
    return;
  }
  btn.disabled = true;
  setStatus('Study proyeksiyalari qidirilmoqda...');
  try {
    const data = await apiJson(`/api/files/${state.current.id}/study_views`);
    const views = data.views || [];
    if (views.length === 0) { alert('Bu study uchun boshqa proyeksiyalar topilmadi.'); return; }
    renderFourView(views);
    stack.hidden = true;
    grid.hidden = false;
    btn.classList.add('active');
    setStatus(`4-view: ${views.length} proyeksiya (${views.map(v => v.key || '?').join(', ')})`);
  } catch (e) {
    alert('4-view xato: ' + (e.message || e));
  } finally {
    btn.disabled = false;
  }
}
function renderFourView(views) {
  const grid = $('fourViewGrid');
  grid.innerHTML = '';
  const byKey = {};
  for (const v of views) byKey[v.key] = v;
  // Yopish tugmasi
  const closeBtn = document.createElement('button');
  closeBtn.className = 'fv-close';
  closeBtn.textContent = '✕ Yopish';
  closeBtn.addEventListener('click', toggleFourView);
  grid.appendChild(closeBtn);
  // 4 ta uyacha (LCC RCC LMLO RMLO)
  for (const key of FV_ORDER) {
    const cell = document.createElement('div');
    cell.className = 'fv-cell';
    const lbl = document.createElement('div');
    lbl.className = 'fv-label';
    lbl.textContent = key;
    cell.appendChild(lbl);
    const v = byKey[key];
    if (v) {
      const img = document.createElement('img');
      const wc = state.wc != null ? `&wc=${state.wc}` : '';
      const ww = state.ww != null ? `&ww=${state.ww}` : '';
      const inv = state.invert ? '&invert=1' : '';
      img.src = `/api/files/${v.id}/image?frame=0${wc}${ww}${inv}&max_dim=1024`;
      img.alt = key;
      img.title = `${key} — bosing bitta ko'rinishga o'tish uchun`;
      img.addEventListener('click', () => {
        toggleFourView(); // grid'ni yopamiz
        openItem({ kind: 'upload', id: v.id, path: v.id });
      });
      cell.appendChild(img);
    } else {
      cell.classList.add('empty');
      const t = document.createElement('div');
      t.textContent = '(yo\'q)';
      cell.appendChild(t);
    }
    grid.appendChild(cell);
  }
}
(function bindFourView() {
  const b = $('fourViewBtn');
  if (b) b.addEventListener('click', toggleFourView);
})();

// Annotation bo'lgan fayllarni boshqa papkaga eksport
function openExportAnnModal() {
  const m = $('exportAnnModal');
  if (!m) return;
  m.hidden = false;
  const res = $('expResult');
  if (res) res.innerHTML = '';
  const dest = $('expDest');
  if (dest && !dest.value) {
    const lastDest = localStorage.getItem('mamograf_last_export_dest');
    if (lastDest) dest.value = lastDest;
  }
}
function closeExportAnnModal() {
  const m = $('exportAnnModal');
  if (m) m.hidden = true;
}
async function submitExportAnn(ev) {
  ev.preventDefault();
  const dest = ($('expDest').value || '').trim();
  if (!dest) { alert('Maqsad papkani kiriting'); return; }
  const sourceRadio = document.querySelector('input[name="expSource"]:checked');
  const source_kind = sourceRadio ? sourceRadio.value : 'upload';
  const statusesRaw = ($('expStatuses').value || '').trim();
  const statuses = statusesRaw ? statusesRaw.split(/[,\s]+/).filter(Boolean) : null;
  const body = {
    destination: dest,
    source_kind,
    require_annotations: $('expRequireAnn').checked,
    require_human: $('expRequireHuman').checked,
    statuses,
    include_annotation_json: $('expIncludeJson').checked,
    organize_by: $('expOrganize').value || 'flat',
    overwrite: $('expOverwrite').checked,
  };
  const btn = $('expSubmitBtn');
  const res = $('expResult');
  btn.disabled = true;
  const prev = btn.textContent;
  btn.textContent = '📤 Bajarilmoqda...';
  if (res) res.innerHTML = '<span style="color:var(--muted)">Fayllar qidirilmoqda...</span>';
  try {
    const r = await api('/api/export/annotated', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const t = await r.text();
      throw new Error(t.replace(/^.*"detail":"?([^"}]+).*$/, '$1') || `HTTP ${r.status}`);
    }
    const j = await r.json();
    localStorage.setItem('mamograf_last_export_dest', dest);
    const html = `
      <div style="background:var(--panel-2);border-left:3px solid #22c55e;padding:8px 12px;border-radius:3px">
        <strong>✓ Eksport tugadi</strong><br>
        Manzil: <code>${j.destination}</code><br>
        Ko'chirildi: <strong>${j.copied_count}</strong> ta fayl<br>
        ${j.skipped_count > 0 ? `O'tkazib yuborildi: ${j.skipped_count} (mavjud yoki xato)<br>` : ''}
        ${j.no_annotations_count > 0 ? `Annotation yo'q: ${j.no_annotations_count}<br>` : ''}
      </div>
      ${j.copied && j.copied.length > 0 ? `
        <details style="margin-top:8px;font-size:12px">
          <summary>Ko'chirilgan fayllar (${j.copied.length})</summary>
          <ul style="max-height:160px;overflow:auto;font-family:monospace;padding-left:20px">
            ${j.copied.slice(0, 100).map(c => `<li>${c.id} → ${c.annotations} ann ${c.annotation_json ? '· json' : ''}</li>`).join('')}
          </ul>
        </details>` : ''
      }
    `;
    if (res) res.innerHTML = html;
  } catch (e) {
    if (res) res.innerHTML = `<span style="color:#ef4444">Xato: ${e.message || e}</span>`;
  } finally {
    btn.disabled = false;
    btn.textContent = prev;
  }
}
(function bindExportAnn() {
  const b = $('exportAnnBtn');
  if (b) b.addEventListener('click', openExportAnnModal);
  const close = $('expCloseBtn');
  if (close) close.addEventListener('click', closeExportAnnModal);
  const form = $('exportAnnForm');
  if (form) form.addEventListener('submit', submitExportAnn);
})();

// Training dataset tayyorlash modali
function openTrainPrepModal() {
  const m = $('trainPrepModal');
  if (!m) return;
  m.hidden = false;
  const last = localStorage.getItem('mamograf_last_train_dest');
  if (last && $('tpDest') && !$('tpDest').value) $('tpDest').value = last;
  const res = $('tpResult');
  if (res) res.innerHTML = '';
}
function closeTrainPrepModal() {
  const m = $('trainPrepModal');
  if (m) m.hidden = true;
}
async function submitTrainPrep(ev) {
  ev.preventDefault();
  const dest = ($('tpDest').value || '').trim();
  if (!dest) { alert('Maqsad papka kiriting'); return; }
  const statusesRaw = ($('tpStatuses').value || '').trim();
  const statuses = statusesRaw ? statusesRaw.split(/[,\s]+/).filter(Boolean) : null;
  const classRaw = ($('tpClasses').value || '').trim();
  const class_list = classRaw ? classRaw.split(/[,\s]+/).filter(Boolean) : null;
  const body = {
    destination: dest,
    target_size: parseInt($('tpSize').value, 10) || 1024,
    val_frac: parseFloat($('tpValFrac').value) || 0.15,
    image_format: $('tpFormat').value || 'png',
    include_ai: $('tpIncludeAi').checked,
    statuses,
    class_list,
    seed: parseInt($('tpSeed').value, 10) || 42,
    zip_after: $('tpZip').checked,
  };
  const btn = $('tpSubmitBtn');
  const res = $('tpResult');
  btn.disabled = true;
  const prev = btn.textContent;
  btn.textContent = '🎓 Yaratilmoqda...';
  if (res) res.innerHTML = '<span style="color:var(--muted)">Annotation\'lar qayta ishlanmoqda, DICOM render qilinmoqda — bir necha sek...</span>';
  try {
    const r = await api('/api/training/prepare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const t = await r.text();
      throw new Error(t.replace(/^.*"detail":"?([^"}]+).*$/, '$1') || `HTTP ${r.status}`);
    }
    const j = await r.json();
    localStorage.setItem('mamograf_last_train_dest', dest);
    _lastDataYaml = j.data_yaml;
    const tb = $('trRunBtn'); if (tb) tb.disabled = false;
    const trs = $('trRunStatus'); if (trs) trs.textContent = `Tayyor: ${j.data_yaml}`;
    const html = `
      <div style="background:var(--panel-2);border-left:3px solid #22c55e;padding:8px 12px;border-radius:3px">
        <strong>✓ Training dataset tayyor</strong><br>
        Manzil: <code>${j.destination}</code><br>
        Klasslar (${j.classes.length}): <strong>${j.classes.join(', ')}</strong><br>
        <table style="margin-top:6px;font-size:12px;border-collapse:collapse">
          <tr><th style="text-align:left;padding:2px 8px">Split</th><th style="padding:2px 8px">Tasvirlar</th><th style="padding:2px 8px">Annotatsiyalar (label satrlari)</th></tr>
          <tr><td style="padding:2px 8px">train</td><td style="padding:2px 8px"><strong>${j.train_imgs}</strong></td><td style="padding:2px 8px">${j.train_lbls}</td></tr>
          <tr><td style="padding:2px 8px">val</td><td style="padding:2px 8px"><strong>${j.val_imgs}</strong></td><td style="padding:2px 8px">${j.val_lbls}</td></tr>
        </table>
        <div style="margin-top:6px">Patient-aware split: <strong>${j.val_groups}</strong>/<strong>${j.total_groups}</strong> guruh val'ga ketdi</div>
        ${j.zip ? `<div style="margin-top:6px">ZIP: <code>${j.zip}</code></div>` : ''}
        <div style="margin-top:8px;font-size:12px;color:var(--muted)">data.yaml: <code>${j.data_yaml}</code></div>
      </div>
      <details style="margin-top:8px;font-size:12px">
        <summary>Endi qanday o'qitish kerak?</summary>
        <pre style="background:var(--panel-2);padding:8px;border-radius:3px;overflow:auto">pip install ultralytics
yolo task=detect mode=train model=yolo11n.pt \\
    data=${j.data_yaml} \\
    epochs=100 imgsz=${body.target_size} batch=8</pre>
        <div>README_TRAIN.md ham qayd etilgan.</div>
      </details>
    `;
    if (res) res.innerHTML = html;
  } catch (e) {
    if (res) res.innerHTML = `<span style="color:#ef4444">Xato: ${e.message || e}</span>`;
  } finally {
    btn.disabled = false;
    btn.textContent = prev;
  }
}
(function bindTrainPrep() {
  const b = $('trainPrepBtn');
  if (b) b.addEventListener('click', openTrainPrepModal);
  const close = $('tpCloseBtn');
  if (close) close.addEventListener('click', closeTrainPrepModal);
  const form = $('trainPrepForm');
  if (form) form.addEventListener('submit', submitTrainPrep);
})();

// Server'da YOLO o'qitish — modal ichidagi tugma
let _lastDataYaml = null;
let _trainPollTimer = null;
async function startServerTrain() {
  if (!_lastDataYaml) { alert('Avval dataset yarating'); return; }
  const btn = $('trRunBtn');
  const status = $('trRunStatus');
  const logView = $('trLogView');
  btn.disabled = true;
  status.textContent = 'Boshlanyapti...';
  logView.style.display = 'block';
  logView.textContent = '';
  try {
    const r = await api('/api/training/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        data_yaml: _lastDataYaml,
        base_model: $('trBaseModel').value,
        epochs: parseInt($('trEpochs').value, 10) || 50,
        imgsz: parseInt($('tpSize').value, 10) || 1024,
        batch: parseInt($('trBatch').value, 10) || 8,
        deploy_after: $('trDeploy').checked,
      }),
    });
    if (!r.ok) {
      const t = await r.text();
      throw new Error(t.replace(/^.*"detail":"?([^"}]+).*$/, '$1') || `HTTP ${r.status}`);
    }
    const j = await r.json();
    status.textContent = `Run ID: ${j.run_id} · ${j.status}`;
    // Polling
    if (_trainPollTimer) clearInterval(_trainPollTimer);
    _trainPollTimer = setInterval(() => pollTrainStatus(j.run_id), 3000);
  } catch (e) {
    status.textContent = 'Xato: ' + (e.message || e);
    btn.disabled = false;
  }
}
async function pollTrainStatus(runId) {
  try {
    const r = await api(`/api/training/status/${runId}?tail=80`);
    if (!r.ok) return;
    const j = await r.json();
    const status = $('trRunStatus');
    const logView = $('trLogView');
    status.textContent = `Run ${runId} · ${j.status}` + (j.return_code != null ? ` (rc=${j.return_code})` : '');
    if (j.log_tail && j.log_tail.length) {
      logView.textContent = j.log_tail.join('\n');
      logView.scrollTop = logView.scrollHeight;
    }
    if (j.status === 'done' || j.status === 'failed') {
      clearInterval(_trainPollTimer); _trainPollTimer = null;
      $('trRunBtn').disabled = false;
      if (j.status === 'done' && j.model_deployed) {
        status.textContent += ` · Deploy: ${j.model_deployed}`;
      } else if (j.error) {
        status.textContent += ` · ${j.error}`;
      }
    }
  } catch {}
}
(function bindTrainRun() {
  const b = $('trRunBtn');
  if (b) b.addEventListener('click', startServerTrain);
})();

// Modellar dashboard
async function openModelMgrModal() {
  const m = $('modelMgrModal');
  if (!m) return;
  m.hidden = false;
  await refreshModelsTable();
  await refreshActiveLearningInModal();
}
function closeModelMgrModal() { const m = $('modelMgrModal'); if (m) m.hidden = true; }

async function refreshActiveLearningInModal() {
  const panel = $('alPanel');
  if (!panel) return;
  try {
    const j = await apiJson('/api/training/suggestion');
    const ok = j.should_retrain;
    panel.style.background = ok ? 'rgba(34,197,94,0.15)' : 'var(--panel-2)';
    panel.style.borderLeft = ok ? '3px solid #22c55e' : '3px solid var(--border)';
    panel.innerHTML = `
      <strong>${j.message}</strong><br>
      Jami annotation: ${j.total_annotations}
      · Qo'lda: ${j.human_annotations}
      · Tahrirlangan AI: ${j.edited_ai}
      · Tasdiqlangan AI: ${j.approved_ai}
      <br><span style="color:var(--muted)">Chegara: ${j.threshold} (ACTIVE_LEARNING_THRESHOLD env)</span>
    `;
  } catch (e) {
    panel.textContent = 'Active learning ma\'lumotini olib bo\'lmadi: ' + (e.message || e);
  }
}

async function refreshModelsTable() {
  const div = $('modelsTable');
  if (!div) return;
  div.innerHTML = '<span style="color:var(--muted)">yuklanmoqda…</span>';
  try {
    const j = await apiJson('/api/models/stats');
    const rows = (j.models || []).map(m => `
      <tr>
        <td style="padding:4px 8px;font-family:monospace">${m.name}</td>
        <td style="padding:4px 8px;text-align:right">${m.size_mb} MB</td>
        <td style="padding:4px 8px;text-align:right"><strong>${m.annotations_produced}</strong></td>
        <td style="padding:4px 8px;font-size:11px;color:var(--muted)">${m.added_at ? m.added_at.slice(0,19).replace('T',' ') : '—'}</td>
        <td style="padding:4px 8px">${m.is_trained_locally ? '<span style="color:#22c55e">trained</span>' : '<span style="color:var(--muted)">built-in</span>'}</td>
        <td style="padding:4px 8px">${m.is_deletable ? `<button data-mm-del="${m.name}" style="background:#ef4444;color:#fff;border:0;padding:3px 8px;border-radius:3px;cursor:pointer;font-size:11px">O'chirish</button>` : ''}</td>
      </tr>
    `).join('');
    div.innerHTML = `
      <table style="width:100%;border-collapse:collapse;border:1px solid var(--border)">
        <thead><tr style="background:var(--panel-2)">
          <th style="padding:4px 8px;text-align:left">Nom</th>
          <th style="padding:4px 8px;text-align:right">Hajm</th>
          <th style="padding:4px 8px;text-align:right">Annotation</th>
          <th style="padding:4px 8px;text-align:left">Qo'shilgan</th>
          <th style="padding:4px 8px;text-align:left">Tur</th>
          <th></th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div style="font-size:11px;color:var(--muted);margin-top:6px">Papka: ${j.models_dir}</div>
    `;
    // Delete tugmalariga ulanish
    div.querySelectorAll('[data-mm-del]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const name = btn.getAttribute('data-mm-del');
        if (!confirm(`"${name}" modelini o'chirishni xohlaysizmi?`)) return;
        try {
          const r = await api(`/api/models/${encodeURIComponent(name)}`, { method: 'DELETE' });
          if (!r.ok) { const t = await r.text(); throw new Error(t || `HTTP ${r.status}`); }
          setStatus(`✓ ${name} o'chirildi`);
          await refreshModelsTable();
          await loadAiStatus(); // toolbar dropdown'ini yangilash
        } catch (e) {
          alert('O\'chirib bo\'lmadi: ' + (e.message || e));
        }
      });
    });
  } catch (e) {
    div.textContent = 'Modellarni olib bo\'lmadi: ' + (e.message || e);
  }
}

(function bindModelMgr() {
  const b = $('modelMgrBtn');
  if (b) b.addEventListener('click', openModelMgrModal);
  const c = $('mmCloseBtn');
  if (c) c.addEventListener('click', closeModelMgrModal);
  const badge = $('activeLearnBadge');
  if (badge) badge.addEventListener('click', openModelMgrModal);
})();

// Active learning: header'da bildirishnoma (kuniga 1 marta poll)
async function pollActiveLearning() {
  if (!state._user) return;
  try {
    const j = await apiJson('/api/training/suggestion');
    const badge = $('activeLearnBadge');
    if (!badge) return;
    if (j.should_retrain) {
      badge.hidden = false;
      badge.textContent = `🎓 Train: ${j.eligible_for_training} ann`;
    } else {
      badge.hidden = true;
    }
  } catch {}
}
setInterval(pollActiveLearning, 60_000);  // har daqiqada
setTimeout(pollActiveLearning, 5_000);
$('aiClearBtn').addEventListener('click', clearSuggestions);
$('aiAcceptAllBtn').addEventListener('click', acceptAllSuggestions);
$('aiConfSlider').addEventListener('input', (e) => {
  state.aiThreshold = parseFloat(e.target.value) / 100;
  $('aiConfLabel').textContent = e.target.value;
  applyAiThreshold();
});

function downloadDatasetExport(fmt) {
  const a = document.createElement('a');
  a.href = `/api/export?format=${encodeURIComponent(fmt)}`;
  a.download = '';
  document.body.appendChild(a);
  a.click();
  a.remove();
}
$('exportBtn').addEventListener('click', () => downloadDatasetExport('coco'));
$('exportYoloBtn').addEventListener('click', () => downloadDatasetExport('yolo'));
$('exportVocBtn').addEventListener('click', () => downloadDatasetExport('voc'));
$('exportCsvBtn').addEventListener('click', () => downloadDatasetExport('csv'));

// Manual save: button + Ctrl/Cmd+S, with an unsaved-changes guard on unload.
$('saveBtn').addEventListener('click', () => { if (state.dirty) saveAnnotations(); });
window.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
    e.preventDefault();
    if (state.dirty) saveAnnotations();
  }
});
window.addEventListener('beforeunload', (e) => {
  if (state.dirty) { e.preventDefault(); e.returnValue = ''; }
});

function _zoomBy(factor) {
  const wrap = $('canvasWrap');
  const newScale = Math.max(0.05, Math.min(40, state.scale * factor));
  state.tx = state.tx * (newScale / state.scale);
  state.ty = state.ty * (newScale / state.scale);
  state.scale = newScale;
  applyTransform();
}

function _selectableAnns() {
  return state.annotations
    .filter(a => a.frame === state.frame)
    .sort((a, b) => {
      const ay = (a.bbox?.[1] || 0), by = (b.bbox?.[1] || 0);
      if (ay !== by) return ay - by;
      return (a.bbox?.[0] || 0) - (b.bbox?.[0] || 0);
    });
}

function _cycleAnn(delta) {
  const list = _selectableAnns();
  if (!list.length) return;
  const idx = state.selectedId ? list.findIndex(a => a.id === state.selectedId) : -1;
  const next = idx === -1 ? (delta > 0 ? 0 : list.length - 1) : (idx + delta + list.length) % list.length;
  state.selectedId = list[next].id;
  renderSvg();
  renderAnnoList();
}

function _quickStatus(transition) {
  if (!state.selectedId) {
    setStatus("avval annotatsiya tanlang");
    return;
  }
  const a = state.annotations.find(x => x.id === state.selectedId);
  if (!a) return;
  if (transition === 'submit') changeStatus(a.id, 'submitted');
  else if (transition === 'approve') changeStatus(a.id, 'approved');
  else if (transition === 'reject') promptRejectStatus(a.id);
  else if (transition === 'recall') changeStatus(a.id, 'draft');
}

window.addEventListener('keydown', (e) => {
  if (e.target.matches('input, textarea, select')) return;

  if ((e.ctrlKey || e.metaKey) && (e.key === 'c' || e.key === 'C')) {
    copySelectedAnns(); e.preventDefault(); return;
  }
  if ((e.ctrlKey || e.metaKey) && (e.key === 'v' || e.key === 'V')) {
    pasteAnns(); e.preventDefault(); return;
  }

  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (state.selectedId) { deleteAnn(state.selectedId); e.preventDefault(); }
  } else if (e.key === 'v' || e.key === 'V') {
    setTool('select');
  } else if (e.key === 'b' || e.key === 'B') {
    setTool('bbox');
  } else if (e.key === 'p' || e.key === 'P') {
    setTool('poly');
  } else if (e.key === 'f' || e.key === 'F') {
    fitToScreen();
  } else if (e.key === 'i' || e.key === 'I') {
    state.invert = !state.invert;
    $('invertBtn').classList.toggle('active', state.invert);
    loadImage(false);
  } else if (e.key === '+' || e.key === '=') {
    _zoomBy(1.2); e.preventDefault();
  } else if (e.key === '-' || e.key === '_') {
    _zoomBy(1 / 1.2); e.preventDefault();
  } else if (e.key === '0') {
    oneToOne();
  } else if (e.key === 'j' || e.key === 'J' || e.key === 'ArrowDown') {
    _cycleAnn(+1); e.preventDefault();
  } else if (e.key === 'k' || e.key === 'K' || e.key === 'ArrowUp') {
    _cycleAnn(-1); e.preventDefault();
  } else if (e.key === 'ArrowLeft' && state.frames > 1) {
    if (state.frame > 0) {
      state.frame--; $('frameSlider').value = state.frame;
      $('frameLabel').textContent = `${state.frame + 1} / ${state.frames}`;
      loadImage(false); renderSvg();
    }
    e.preventDefault();
  } else if (e.key === 'ArrowRight' && state.frames > 1) {
    if (state.frame < state.frames - 1) {
      state.frame++; $('frameSlider').value = state.frame;
      $('frameLabel').textContent = `${state.frame + 1} / ${state.frames}`;
      loadImage(false); renderSvg();
    }
    e.preventDefault();
  } else if (e.key === 'y' || e.key === 'Y') {
    _quickStatus('approve'); e.preventDefault();
  } else if (e.key === 'n' || e.key === 'N') {
    _quickStatus('reject'); e.preventDefault();
  } else if (e.key === 's' || e.key === 'S') {
    _quickStatus('submit'); e.preventDefault();
  } else if (e.key === 'r' || e.key === 'R') {
    _quickStatus('recall'); e.preventDefault();
  } else if (e.key === '?') {
    showHotkeysModal();
  } else if (e.key === 'h' || e.key === 'H') {
    // (A3) Heatmap toggle
    const hb = $('aiHeatmapBtn');
    if (hb && !hb.hidden) { toggleUncertaintyHeatmap(); e.preventDefault(); }
  } else if (e.key === 'm' || e.key === 'M') {
    // (B4) W/L preset: Mass
    const p = MAMMO_PRESETS.mass; if (p) applyWl(p.wc, p.ww, 'mass');
  } else if (e.key === 'c' || e.key === 'C') {
    // Ctrl+C allaqachon yuqorida — bu yerga oddiy C tushadi
    const p = MAMMO_PRESETS.calc; if (p) applyWl(p.wc, p.ww, 'calc');
  } else if (e.key === 'l' || e.key === 'L') {
    // (B4) W/L preset: Skin (L for sk-L-in, S band)
    const p = MAMMO_PRESETS.skin; if (p) applyWl(p.wc, p.ww, 'skin');
  } else if (e.shiftKey && (e.key === 'A' || e.key === 'a')) {
    // (A1/A3) AI re-run
    const ai = $('aiRunBtn');
    if (ai && !ai.hidden && !ai.disabled) { ai.click(); e.preventDefault(); }
  } else if (e.key >= '1' && e.key <= '5') {
    // (B8) Tezkor label tanlash: 1-5
    const lsel = $('labelSelect');
    if (lsel && lsel.options.length > 0) {
      const idx = parseInt(e.key, 10) - 1;
      if (idx < lsel.options.length) {
        lsel.selectedIndex = idx;
        lsel.dispatchEvent(new Event('change'));
        setStatus(`Label: ${lsel.value}`);
      }
    }
  } else if (e.key === 'Tab') {
    _cycleAnn(e.shiftKey ? -1 : +1); e.preventDefault();
  } else if (e.key === 'Enter' && state.tool === 'poly') {
    e.preventDefault();
    finalizePolyDraw();
  } else if (e.key === 'Escape') {
    if (state.tool === 'poly' && polyDraw.points.length > 0) {
      cancelPolyDraw();
    } else if ((state.tool === 'ruler' || state.tool === 'angle') && measureDraw.points.length > 0) {
      cancelMeasureDraw();
    } else {
      state.selectedId = null; renderSvg(); renderAnnoList();
    }
  }
});

const CLIPBOARD_KEY = 'mamograf_ann_clipboard';

function copySelectedAnns() {
  if (!state.annotations.length) {
    setStatus("nusxa olishga annotatsiya yo'q");
    return;
  }
  let toCopy;
  if (state.selectedId) {
    toCopy = state.annotations.filter(a => a.id === state.selectedId);
  } else {
    toCopy = state.annotations.filter(a => a.frame === state.frame);
  }
  if (!toCopy.length) {
    setStatus("nusxa olishga annotatsiya yo'q");
    return;
  }
  const stripped = toCopy.map(a => {
    const c = JSON.parse(JSON.stringify(a));
    delete c.id;
    delete c.created_by; delete c.created_at;
    delete c.updated_by; delete c.updated_at;
    delete c.reviewed_by; delete c.reviewed_at; delete c.review_note;
    delete c.status;
    return c;
  });
  try {
    localStorage.setItem(CLIPBOARD_KEY, JSON.stringify({
      ts: new Date().toISOString(),
      anns: stripped,
    }));
    setStatus(`✓ ${stripped.length} annotatsiya nusxalandi`);
  } catch (e) {
    setStatus("nusxa olish xatosi");
  }
}

function pasteAnns() {
  if (!state.current) return;
  const raw = localStorage.getItem(CLIPBOARD_KEY);
  if (!raw) { setStatus("clipboard bo'sh"); return; }
  let data;
  try { data = JSON.parse(raw); } catch (e) { setStatus("clipboard buzilgan"); return; }
  const anns = data.anns || [];
  if (!anns.length) { setStatus("clipboard bo'sh"); return; }
  let added = 0;
  const now = new Date().toISOString();
  for (const a of anns) {
    const fresh = JSON.parse(JSON.stringify(a));
    fresh.id = uid();
    fresh.frame = state.frame;
    fresh.created_at = now;
    fresh.updated_at = now;
    fresh.note = (fresh.note ? fresh.note + " " : "") + "[paste]";
    state.annotations.push(fresh);
    added++;
  }
  state.selectedId = state.annotations[state.annotations.length - 1].id;
  renderSvg();
  renderAnnoList();
  scheduleAutosave();
  setStatus(`✓ ${added} annotatsiya qo'yildi`);
}

function showHotkeysModal() {
  const lines = [
    '── ASBOBLAR ──',
    '  V        Select',
    '  B        BBox chizish',
    '  P        Polygon chizish',
    '',
    '── KO\'RINISH ──',
    '  F        Ekrunga moslash',
    '  0        1:1 piksel',
    '  + / -    Zoom',
    '  I        Invert (rang ag\'darish)',
    '',
    '── W/L PRESETLAR (mammografiya) ──',
    '  M        Mass (WC=2000 WW=4000)',
    '  C        Calc (WC=600 WW=1200, mikrokalsifikatsiya)',
    '  L        Skin (WC=2500 WW=5000)',
    '',
    '── ANNOTATSIYA ──',
    '  Tab      Keyingi annotatsiya',
    '  Shift+Tab  Oldingi annotatsiya',
    '  J / ↓    Keyingi',
    '  K / ↑    Oldingi',
    '  Delete   Tanlanganni o\'chirish',
    '  1 – 5    Tezkor label tanlash (toolbar ro\'yxatidan)',
    '  Enter    Polygon\'ni yopish',
    '  Esc      Bekor qilish / tanlovni olib tashlash',
    '',
    '── KLIPBOARD ──',
    '  Ctrl+C   Annotatsiyalarni nusxalash',
    '  Ctrl+V   Qo\'yish',
    '  Ctrl+S   Saqlash',
    '',
    '── AI ──',
    '  Shift+A  AI tahlilni qayta ishga tushirish',
    '  H        🌡 Uncertainty heatmap (yoqish/o\'chirish)',
    '',
    '── FRAME (ko\'p kadrli DICOM) ──',
    '  ← / →    Oldingi / keyingi kadr',
    '',
    '── HOLAT ──',
    '  S=Submit  Y=Approve  N=Reject  R=Recall',
    '',
    '  ?        Bu yordam oynasini ko\'rsatish',
  ];
  alert(lines.join('\n'));
}

async function loadAuthedAssets() {
  await loadLabels();
  await loadAiStatus();
  await refreshUploads();
  await refreshNotifications();
  startNotifPolling();
  setTool('select');
  if (state._user && state._user.totp_setup_required) {
    setStatus("⚠ Sizning rolingiz uchun 2FA majburiy. Iltimos, sozlang.");
    setTimeout(() => openTotpModal(), 600);
  }
}

// ===== WebSocket presence/sync =====

let _ws = null;
let _wsRetryTimer = null;
const _remoteCursors = new Map();  // user → {x, y, lastSeen}
let _cursorThrottleTs = 0;
const CURSOR_COLORS = ['#ff5050','#ffb000','#00c4ff','#a070ff','#28d97f','#ff80b4','#ffe44d'];
function colorForUser(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) & 0xffff;
  return CURSOR_COLORS[h % CURSOR_COLORS.length];
}

function wsClose() {
  if (_ws) {
    try { _ws.close(); } catch (e) {}
    _ws = null;
  }
  if (_wsRetryTimer) { clearTimeout(_wsRetryTimer); _wsRetryTimer = null; }
  state._presence = [];
  $('presencePill').hidden = true;
}

function sendCursor(x, y) {
  if (!_ws || _ws.readyState !== 1) return;
  const now = performance.now();
  if (now - _cursorThrottleTs < 50) return;
  _cursorThrottleTs = now;
  try {
    _ws.send(JSON.stringify({ type: 'cursor', x, y }));
  } catch (e) {}
}

function renderRemoteCursors() {
  const svg = $('annoSvg');
  svg.querySelectorAll('.remote-cursor, .remote-cursor-label').forEach(el => el.remove());
  if (!_remoteCursors.size) return;
  const { w: VW, h: VH } = svgViewSize();
  const fontSize = Math.max(10, Math.round(VH * 0.012));
  const r = 6 / Math.max(state.scale, 0.05);
  const now = Date.now();
  for (const [user, c] of _remoteCursors.entries()) {
    if (now - c.lastSeen > 5000) { _remoteCursors.delete(user); continue; }
    if (c.x == null || c.y == null) continue;
    const color = colorForUser(user);
    const dot = el('circle', {
      class: 'remote-cursor',
      cx: c.x * VW, cy: c.y * VH, r,
      stroke: color, fill: color,
    });
    svg.appendChild(dot);
    const txt = el('text', {
      class: 'remote-cursor-label',
      x: c.x * VW + r * 1.5, y: c.y * VH - r * 0.5,
      'font-size': fontSize, fill: color,
    });
    txt.textContent = user;
    svg.appendChild(txt);
  }
}

setInterval(() => {
  if (!_remoteCursors.size) return;
  const now = Date.now();
  let changed = false;
  for (const [user, c] of _remoteCursors.entries()) {
    if (now - c.lastSeen > 5000) { _remoteCursors.delete(user); changed = true; }
  }
  if (changed) renderRemoteCursors();
}, 2000);

function wsConnect() {
  wsClose();
  if (!state.current || !getToken()) return;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const params = new URLSearchParams({
    source: refSource(), ref: refValue(), token: getToken(),
  });
  const url = `${proto}://${location.host}/ws/dicom?${params}`;
  let ws;
  try { ws = new WebSocket(url); } catch (e) { return; }
  _ws = ws;
  ws.onmessage = (e) => {
    let m;
    try { m = JSON.parse(e.data); } catch (err) { return; }
    if (m.type === 'presence') {
      state._presence = (m.users || []).filter(u => u !== state._user?.username);
      const pill = $('presencePill');
      if (state._presence.length) {
        pill.hidden = false;
        pill.textContent = state._presence.join(', ');
      } else {
        pill.hidden = true;
      }
    } else if (m.type === 'annotations_changed' && m.by !== state._user?.username) {
      setStatus(`${m.by} annotatsiyalarni yangiladi — qayta yuklanmoqda`);
      loadAnnotations();
    } else if (m.type === 'status_changed' && m.by !== state._user?.username) {
      setStatus(`${m.by}: ${m.annotation_id} → ${m.status}`);
      loadAnnotations();
    } else if (m.type === 'cursor' && m.user !== state._user?.username) {
      _remoteCursors.set(m.user, { x: m.x, y: m.y, lastSeen: Date.now() });
      renderRemoteCursors();
    }
  };
  ws.onclose = () => {
    if (_ws !== ws) return;
    _ws = null;
    if (state.current) {
      _wsRetryTimer = setTimeout(wsConnect, 3000);
    }
  };
  ws.onerror = () => {};
}

(async function init() {
  try {
    await loadConfig();
    if (state.authRequired) {
      const ok = await attemptResumeSession();
      if (!ok) {
        showLoginModal();
        updateUserBar();
        return;
      }
    }
    updateUserBar();
    await loadAuthedAssets();
  } catch (e) {
    setStatus('ishga tushirish xatosi: ' + e.message);
  }
})();

// ===== Mammografiya hisoboti generatori =====
function _reportType(label) {
  const s = (label || '').toString().toLowerCase();
  if (/massa|mass|tumor|nodul/.test(s)) return 'mass';
  if (/kals|calc/.test(s)) return 'calcification';
  if (/asimmetr|asymmetr/.test(s)) return 'asymmetry';
  if (/arxitektura|architect|distortion/.test(s)) return 'architectural_distortion';
  return label || 'mass';
}
function buildReportDetections() {
  const m = state.meta || {};
  const lat = m.ImageLaterality || m.Laterality || '';
  const view = m.ViewPosition || '';
  return (state.annotations || []).map(a => {
    const bb = a.bbox || [0, 0, 0, 0];
    const cx = bb[0] + bb[2] / 2, cy = bb[1] + bb[3] / 2;
    const lbl = a.label || (Array.isArray(a.labels) ? a.labels[0] : '') || '';
    const conf = (typeof a.score === 'number') ? a.score
      : (typeof a.confidence === 'number') ? a.confidence : null;
    return { laterality: lat, view, cx, cy, type: _reportType(lbl), birads: a.bi_rads || '0', confidence: conf };
  });
}
async function generateReport() {
  const status = $('reportStatus');
  const dets = buildReportDetections();
  if (!dets.length) { status.textContent = "Annotatsiya yo'q — avval lezyon belgilang"; $('reportText').value = ''; return; }
  const m = state.meta || {};
  const views = [];
  const lv = (m.ImageLaterality || '') + (m.ViewPosition ? '-' + m.ViewPosition : '');
  if (lv) views.push(lv);
  $('reportRegenBtn').disabled = true;
  status.textContent = 'yaratilmoqda…';
  try {
    const j = await apiJson('/api/report/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ detections: dets, dicom_meta: { acr_density: '' }, study_views: views, mode: $('reportMode').value, lang: 'uz' }),
    });
    $('reportText').value = j.report || '';
    const modeLbl = {
      local: '🧠 Lokal AI', cloud: '🤖 Claude', llm: '🤖 Claude',
      template: '📄 Shablon', template_fallback: '📄 Shablon (lokal model topilmadi)'
    }[j.mode] || j.mode;
    $('reportModeBadge').textContent = '· ' + modeLbl + (j.model ? ' (' + j.model + ')' : '');
    const fnd = j.findings || {};
    const n = (fnd.lesions ? fnd.lesions.length : dets.length);
    $('reportFindings').textContent = n + ' ta topilma · Umumiy: BI-RADS ' + (fnd.overall_birads || j.birads || '?');
    const err = j.local_error || j.llm_error;
    status.textContent = err ? ('⚠ ' + err) : '✓';
  } catch (e) {
    status.innerHTML = '<span style="color:#ef4444">Xato: ' + (e.message || e) + '</span>';
  } finally {
    $('reportRegenBtn').disabled = false;
  }
}
async function loadReportBackends() {
  const el = $('reportBackends');
  if (!el) return;
  try {
    const j = await apiJson('/api/report/status');
    if (j.ollama) {
      const has = (j.ollama_models || []).length;
      el.innerHTML = "🧠 Lokal AI (Ollama): <span style='color:#22c55e'>tayyor</span> · "
        + (has ? j.ollama_models.join(', ') : ("model yo'q — <code>ollama pull " + j.ollama_default + "</code>"));
    } else {
      el.innerHTML = "🧠 Lokal AI (Ollama): <span style='color:#888'>topilmadi</span> — shablon ishlatiladi "
        + "(o'rnatib <code>ollama pull " + j.ollama_default + "</code> qilsangiz tabiiy matn chiqadi).";
    }
  } catch (e) { el.textContent = ''; }
}
if ($('reportBtn')) {
  $('reportBtn').addEventListener('click', () => { $('reportModal').hidden = false; loadReportBackends(); generateReport(); });
  $('reportRegenBtn').addEventListener('click', generateReport);
  $('reportMode').addEventListener('change', generateReport);
  $('reportCloseBtn').addEventListener('click', () => { $('reportModal').hidden = true; });
  $('reportCopyBtn').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText($('reportText').value); $('reportStatus').textContent = '📋 nusxa olindi'; }
    catch { $('reportStatus').textContent = 'nusxa olinmadi'; }
  });
}
