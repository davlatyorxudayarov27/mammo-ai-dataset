// Train Studio — alohida sahifa logikasi
const TOKEN_KEY = 'mamograf_jwt';
const $ = (id) => document.getElementById(id);

function getToken() { return localStorage.getItem(TOKEN_KEY); }
async function api(url, opts = {}) {
  const tok = getToken();
  const headers = { ...(opts.headers || {}) };
  if (tok) headers['Authorization'] = `Bearer ${tok}`;
  return fetch(url, { ...opts, headers });
}
async function apiJson(url, opts) {
  const r = await api(url, opts);
  if (r.status === 401) { window.location.href = './'; throw new Error('401'); }
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
  return r.json();
}

let _pollTimer = null;
let _currentRunId = null;

async function loadUser() {
  try {
    const u = await apiJson('/api/auth/me');
    $('userInfo').textContent = u ? `${u.display_name || u.username} (${u.role})` : '';
  } catch {}
}

async function loadDatasets() {
  const sel = $('datasetSel');
  sel.innerHTML = '<option value="">— qidirilmoqda —</option>';
  try {
    const j = await apiJson('/api/training/datasets');
    sel.innerHTML = '<option value="">— qo\'lda kiriting —</option>';
    for (const d of j.datasets || []) {
      const opt = document.createElement('option');
      opt.value = d.yaml;
      const total = d.train_count + d.val_count;
      opt.textContent = `${d.yaml} (${total} ta tasvir)`;
      opt.dataset.train = d.train_count;
      opt.dataset.val = d.val_count;
      sel.appendChild(opt);
    }
  } catch (e) {
    sel.innerHTML = '<option>Xato: ' + e.message + '</option>';
  }
}

async function loadBaseModels() {
  const sel = $('baseModelSel');
  sel.innerHTML = '';
  try {
    const j = await apiJson('/api/training/base_models');
    const grp1 = document.createElement('optgroup');
    grp1.label = 'YOLO oilasi (Ultralytics avto-yuklab oladi)';
    for (const m of j.suggested) {
      const o = document.createElement('option');
      o.value = m.name;
      o.textContent = `${m.name} — ${m.label} (~${m.size_hint_mb} MB)`;
      grp1.appendChild(o);
    }
    sel.appendChild(grp1);
    if (j.local && j.local.length) {
      const grp2 = document.createElement('optgroup');
      grp2.label = '🔧 Lokal modellar (fine-tune uchun)';
      for (const m of j.local) {
        const o = document.createElement('option');
        o.value = m.path;
        o.textContent = m.label;
        grp2.appendChild(o);
      }
      sel.appendChild(grp2);
    }
  } catch (e) {
    sel.innerHTML = '<option>Xato: ' + e.message + '</option>';
  }
}

async function loadRuns() {
  const div = $('runsTable');
  try {
    const j = await apiJson('/api/training/runs');
    const runs = j.runs || [];
    if (!runs.length) { div.textContent = 'Run yo\'q'; }
    else {
      const rows = runs.map(r => {
        const params = r.params || {};
        const metrics = r.last_metrics || {};
        const map50 = metrics['metrics/mAP50(B)'] || metrics['metrics/mAP_0.5'] || '-';
        const epochs = params.epochs || '-';
        return `
          <tr data-run-id="${r.run_id}">
            <td><code>${r.run_id.slice(0, 22)}</code></td>
            <td><span class="ts-status-${r.status}">${r.status}</span></td>
            <td>${params.base_model || '-'}</td>
            <td>${epochs}e</td>
            <td>${map50 !== '-' ? Number(map50).toFixed(3) : '-'}</td>
            <td style="font-size:10px;color:var(--muted)">${(r.started_at || r.queued_at || '').slice(0, 16).replace('T',' ')}</td>
          </tr>
        `;
      }).join('');
      div.innerHTML = `<table>
        <thead><tr><th>Run ID</th><th>Status</th><th>Model</th><th>Ep</th><th>mAP50</th><th>Boshlangan</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
      div.querySelectorAll('[data-run-id]').forEach(tr => {
        tr.addEventListener('click', () => watchRun(tr.dataset.runId));
      });
    }
    // Resume dropdown ham yangilanadi
    const resumeSel = $('resumeSel');
    const cur = resumeSel.value;
    resumeSel.innerHTML = '<option value="">— Yangi train —</option>';
    for (const r of runs) {
      if (r.status === 'done' || r.status === 'failed') {
        const o = document.createElement('option');
        o.value = r.run_id;
        o.textContent = `${r.run_id} (${r.status})`;
        resumeSel.appendChild(o);
      }
    }
    resumeSel.value = cur;
  } catch (e) {
    div.textContent = 'Xato: ' + e.message;
  }
}

$('datasetSel').addEventListener('change', () => {
  const sel = $('datasetSel');
  $('dataYamlPath').value = sel.value;
  const opt = sel.options[sel.selectedIndex];
  $('datasetInfo').textContent = opt ? `train: ${opt.dataset.train || 0} · val: ${opt.dataset.val || 0}` : '';
});

async function startTrain() {
  const data_yaml = $('dataYamlPath').value || $('datasetSel').value;
  if (!data_yaml) { alert('Avval dataset tanlang'); return; }
  const body = {
    data_yaml,
    base_model: $('baseModelSel').value,
    epochs: parseInt($('epochs').value, 10) || 50,
    batch: parseInt($('batch').value, 10) || 8,
    imgsz: parseInt($('imgsz').value, 10) || 1024,
    optimizer: $('optimizer').value,
    device: $('device').value,
    lr0: parseFloat($('lr0').value),
    lrf: parseFloat($('lrf').value),
    momentum: parseFloat($('momentum').value),
    weight_decay: parseFloat($('weight_decay').value),
    warmup_epochs: parseFloat($('warmup_epochs').value),
    cos_lr: $('cos_lr').value === 'true',
    patience: parseInt($('patience').value, 10) || 50,
    seed: parseInt($('seed').value, 10) || 0,
    hsv_h: parseFloat($('hsv_h').value),
    hsv_s: parseFloat($('hsv_s').value),
    hsv_v: parseFloat($('hsv_v').value),
    fliplr: parseFloat($('fliplr').value),
    flipud: parseFloat($('flipud').value),
    scale: parseFloat($('scale').value),
    mosaic: parseFloat($('mosaic').value),
    mixup: parseFloat($('mixup').value),
    workers: parseInt($('workers').value, 10),
    cache: $('cache').value,
    pretrained: $('pretrainedSel').value === 'true',
    deploy_after: $('deploy_after').value === 'true',
    resume: $('resumeSel').value || null,
    project_name: $('projectName').value || null,
  };
  const btn = $('startBtn');
  btn.disabled = true;
  $('startStatus').textContent = 'Boshlanyapti...';
  try {
    const r = await api('/api/training/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const t = await r.text();
      throw new Error(t.replace(/^.*"detail":"?([^"}]+).*$/, '$1') || `HTTP ${r.status}`);
    }
    const j = await r.json();
    $('startStatus').innerHTML = `✓ Boshlandi: <code>${j.run_id}</code>`;
    watchRun(j.run_id);
    setTimeout(loadRuns, 1500);
  } catch (e) {
    $('startStatus').innerHTML = `<span style="color:#ef4444">Xato: ${e.message}</span>`;
    btn.disabled = false;
  }
}

function watchRun(runId) {
  _currentRunId = runId;
  $('currentRun').innerHTML = `Kuzatilmoqda: <code>${runId}</code>`;
  $('liveLog').hidden = false;
  if (_pollTimer) clearInterval(_pollTimer);
  _pollTimer = setInterval(() => pollRun(runId), 3000);
  pollRun(runId);
}

async function pollRun(runId) {
  try {
    const j = await apiJson(`/api/training/status/${runId}?tail=120`);
    const log = $('liveLog');
    const params = j.params || {};
    const metrics = j.last_metrics || {};
    const map50 = metrics['metrics/mAP50(B)'] || metrics['metrics/mAP_0.5'] || '';
    const map95 = metrics['metrics/mAP50-95(B)'] || metrics['metrics/mAP_0.5:0.95'] || '';
    $('currentRun').innerHTML = `
      <code>${runId}</code>
      <span class="ts-status-${j.status}">[${j.status}]</span>
      ${j.return_code != null ? ` rc=${j.return_code}` : ''}
      ${params.base_model ? `<span class="ts-tag">${params.base_model}</span>` : ''}
      ${params.epochs ? `<span class="ts-tag">${params.epochs} ep</span>` : ''}
      ${map50 ? `<span class="ts-tag">mAP50=${Number(map50).toFixed(3)}</span>` : ''}
      ${map95 ? `<span class="ts-tag">mAP50-95=${Number(map95).toFixed(3)}</span>` : ''}
      ${j.model_deployed ? `<br>📦 Deploy: <code>${j.model_deployed}</code>` : ''}
      ${j.error ? `<br><span style="color:#ef4444">⚠ ${j.error}</span>` : ''}
    `;
    if (j.log_tail && j.log_tail.length) {
      log.textContent = j.log_tail.join('\n');
      log.scrollTop = log.scrollHeight;
    }
    if (j.status === 'done' || j.status === 'failed') {
      clearInterval(_pollTimer); _pollTimer = null;
      $('startBtn').disabled = false;
      loadRuns();
    }
  } catch (e) {
    console.error('poll', e);
  }
}

$('startBtn').addEventListener('click', startTrain);
$('refreshRunsBtn').addEventListener('click', loadRuns);
$('refreshAllBtn').addEventListener('click', () => { loadDatasets(); loadBaseModels(); loadRuns(); });

// Boshlash
(async () => {
  await loadUser();
  await Promise.all([loadDatasets(), loadBaseModels(), loadRuns()]);
})();
