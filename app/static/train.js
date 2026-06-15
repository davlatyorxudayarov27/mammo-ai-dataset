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
  validateDataset();
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
  $('stopBtn').hidden = false;
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
    fetchAndDrawMetrics(runId);
    const finished = (j.status === 'done' || j.status === 'failed' || j.status === 'stopped');
    $('stopBtn').hidden = finished || !j.is_alive;
    if (finished) {
      clearInterval(_pollTimer); _pollTimer = null;
      $('startBtn').disabled = false;
      $('stopBtn').hidden = true;
      loadRuns();
    }
  } catch (e) {
    console.error('poll', e);
  }
}

// ---------- Jonli grafiklar (canvas, CDN'siz) ----------
function _col(row, keys) {
  for (const k of keys) {
    if (row[k] !== undefined && row[k] !== '' && !isNaN(row[k])) return Number(row[k]);
  }
  return null;
}
function drawChart(canvasId, series) {
  const cv = $(canvasId);
  if (!cv) return;
  const cssW = cv.clientWidth || 600;
  if (cv.width !== cssW) cv.width = cssW;
  const W = cv.width, H = cv.height, ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, W, H);
  const padL = 42, padR = 10, padT = 18, padB = 18;
  let xs = [], ys = [];
  series.forEach(s => s.data.forEach(p => { xs.push(p.x); ys.push(p.y); }));
  if (!xs.length) {
    ctx.fillStyle = '#666'; ctx.font = '12px monospace';
    ctx.fillText("ma'lumot yo'q — train boshlanmagan", 12, H / 2);
    return;
  }
  let xmin = Math.min(...xs), xmax = Math.max(...xs);
  let ymin = Math.min(...ys), ymax = Math.max(...ys);
  if (xmin === xmax) xmax = xmin + 1;
  if (ymin === ymax) { ymin -= 0.5; ymax += 0.5; }
  const py0 = (ymax - ymin) * 0.08; ymin -= py0; ymax += py0;
  const X = x => padL + (x - xmin) / (xmax - xmin) * (W - padL - padR);
  const Y = y => H - padB - (y - ymin) / (ymax - ymin) * (H - padT - padB);
  ctx.strokeStyle = '#1e2230'; ctx.fillStyle = '#888'; ctx.font = '10px monospace'; ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const yy = ymin + (ymax - ymin) * i / 4, py = Y(yy);
    ctx.beginPath(); ctx.moveTo(padL, py); ctx.lineTo(W - padR, py); ctx.stroke();
    ctx.fillText(yy.toFixed(2), 2, py + 3);
  }
  ctx.fillText('ep ' + Math.round(xmax), W - 36, H - 5);
  series.forEach(s => {
    if (!s.data.length) return;
    ctx.strokeStyle = s.color; ctx.lineWidth = 1.6; ctx.beginPath();
    s.data.forEach((p, i) => { const px = X(p.x), py = Y(p.y); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); });
    ctx.stroke();
    const last = s.data[s.data.length - 1];
    ctx.fillStyle = s.color; ctx.beginPath(); ctx.arc(X(last.x), Y(last.y), 2.5, 0, 7); ctx.fill();
  });
  let lx = padL + 2; ctx.font = '10px monospace';
  series.forEach(s => {
    ctx.fillStyle = s.color; ctx.fillRect(lx, 6, 9, 9);
    ctx.fillStyle = '#bbb'; ctx.fillText(s.label, lx + 12, 14);
    lx += 12 + ctx.measureText(s.label).width + 14;
  });
}
function drawAllCharts(rows) {
  const ep = r => { const e = _col(r, ['epoch']); return e == null ? 0 : e; };
  const sumLoss = (r, pfx) => {
    const v = [`${pfx}/box_loss`, `${pfx}/cls_loss`, `${pfx}/dfl_loss`].map(k => _col(r, [k])).filter(x => x != null);
    return v.length ? v.reduce((a, x) => a + x, 0) : null;
  };
  const pick = (key) => rows.map(r => { const y = _col(r, key); return y == null ? null : { x: ep(r), y }; }).filter(Boolean);
  const lossTr = rows.map(r => { const y = sumLoss(r, 'train'); return y == null ? null : { x: ep(r), y }; }).filter(Boolean);
  const lossVal = rows.map(r => { const y = sumLoss(r, 'val'); return y == null ? null : { x: ep(r), y }; }).filter(Boolean);
  drawChart('chartLoss', [
    { label: 'train', color: '#4a90e2', data: lossTr },
    { label: 'val', color: '#ff8c42', data: lossVal },
  ]);
  drawChart('chartMap', [
    { label: 'mAP@50', color: '#22c55e', data: pick(['metrics/mAP50(B)', 'metrics/mAP_0.5']) },
    { label: 'mAP@50-95', color: '#a78bfa', data: pick(['metrics/mAP50-95(B)', 'metrics/mAP_0.5:0.95']) },
  ]);
  drawChart('chartPR', [
    { label: 'precision', color: '#38bdf8', data: pick(['metrics/precision(B)', 'metrics/precision']) },
    { label: 'recall', color: '#f472b6', data: pick(['metrics/recall(B)', 'metrics/recall']) },
  ]);
}
async function fetchAndDrawMetrics(runId) {
  try {
    const j = await apiJson(`/api/training/metrics/${runId}`);
    drawAllCharts(j.rows || []);
  } catch (e) { /* jim */ }
}

// ---------- GPU monitor ----------
async function loadGpu() {
  const el = $('gpuInfo');
  if (!el) return;
  try {
    const j = await apiJson('/api/system/gpu');
    if (!j.available || !j.gpus.length) {
      el.innerHTML = "GPU: <span class='ts-warn'>topilmadi</span>"
        + (j.torch_cuda === false ? " <span class='ts-bad'>⚠ CPU-torch</span>" : '');
      return;
    }
    const g = j.gpus[0];
    const usedGb = (g.mem_used_mb / 1024).toFixed(1), totGb = (g.mem_total_mb / 1024).toFixed(1);
    const pct = Math.min(100, g.mem_used_mb / g.mem_total_mb * 100);
    const cudaWarn = j.torch_cuda ? '' : " <span class='ts-bad'>⚠ CPU-torch</span>";
    el.innerHTML = `GPU: ${g.name.replace('NVIDIA ', '')} `
      + `<span class="bar-wrap"><span class="bar-fill" style="width:${pct}%"></span></span> `
      + `${usedGb}/${totGb} GB · ${g.util_pct}% · ${g.temp_c}°C${cudaWarn}`;
    window._gpuTotalMb = g.mem_total_mb;
    window._gpuFreeMb = g.mem_free_mb;
    estimateVram();
  } catch (e) {
    el.textContent = 'GPU: —';
  }
}

// ---------- Dataset tekshiruvi ----------
async function validateDataset() {
  const yaml = $('dataYamlPath').value || $('datasetSel').value;
  const box = $('datasetValidate');
  if (!yaml) { box.hidden = true; return; }
  box.hidden = false;
  box.innerHTML = '<span class="ts-hint">tekshirilmoqda…</span>';
  try {
    const j = await apiJson('/api/training/validate?yaml=' + encodeURIComponent(yaml));
    const splitHtml = (name, s) => {
      if (!s) return `<div class="vrow"><span>${name}</span><span class="ts-hint">yo'q</span></div>`;
      if (!s.exists) return `<div class="vrow"><span>${name}</span><span class="ts-bad">papka topilmadi</span></div>`;
      const warns = [];
      if (s.missing_labels) warns.push(`<span class="ts-warn">${s.missing_labels} rasm label'siz</span>`);
      if (s.orphan_labels) warns.push(`<span class="ts-warn">${s.orphan_labels} label rasmsiz</span>`);
      if (s.empty_images) warns.push(`<span class="ts-bad">${s.empty_images} bo'sh fayl</span>`);
      const cc = Object.entries(s.class_counts || {});
      const maxc = Math.max(1, ...cc.map(([, v]) => v));
      const ccHtml = cc.map(([k, v]) =>
        `<div class="vrow"><span>&nbsp;&nbsp;${k}</span><span>${v} <span class="ts-bar" style="width:${Math.round(v / maxc * 60)}px"></span></span></div>`
      ).join('');
      return `<div class="vrow"><strong>${name}</strong><span class="ts-ok">${s.images} rasm · ${s.labels} label</span></div>`
        + ccHtml
        + (warns.length ? `<div class="vrow"><span></span><span>${warns.join(' · ')}</span></div>` : '');
    };
    box.innerHTML =
      `<div class="vrow"><span>Klasslar (nc=${j.nc})</span><span>${Object.values(j.names || {}).join(', ') || '—'}</span></div>`
      + splitHtml('train', j.train)
      + splitHtml('val', j.val);
  } catch (e) {
    box.innerHTML = `<span class="ts-bad">Xato: ${e.message}</span>`;
  }
}

// ---------- Preflight VRAM taxmini ----------
function modelSizeLetter(name) {
  const m = (name || '').toLowerCase().match(/yolov?\d+([nsmlxce])/);
  if (!m) return 'm';
  return { c: 'm', e: 'x' }[m[1]] || m[1];
}
function estimateVram() {
  const el = $('vramEstimate');
  if (!el) return;
  const imgsz = parseInt($('imgsz').value, 10) || 1024;
  const batch = parseInt($('batch').value, 10) || 8;
  const dev = $('device').value;
  if (dev === 'cpu') {
    el.className = 'ts-hint';
    el.innerHTML = "🧮 CPU rejimi tanlangan — GPU ishlatilmaydi (sekin bo'ladi).";
    return;
  }
  const letter = modelSizeLetter($('baseModelSel').value);
  const perImg = { n: 0.10, s: 0.16, m: 0.30, l: 0.42, x: 0.62 }[letter] || 0.30;
  const estGb = 1.2 + perImg * batch * Math.pow(imgsz / 640, 2);
  const totGb = (window._gpuTotalMb || 0) / 1024;
  let cls = 'ts-hint', note = '';
  if (totGb > 0) {
    if (estGb > totGb * 0.92) { cls = 'ts-bad'; note = ` — ⚠ ${totGb.toFixed(1)} GB ga sig'masligi mumkin! batch yoki imgsz'ni kamaytiring`; }
    else if (estGb > totGb * 0.72) { cls = 'ts-warn'; note = ` — chegaraga yaqin (${totGb.toFixed(1)} GB)`; }
    else { cls = 'ts-ok'; note = ` — ${totGb.toFixed(1)} GB ga sig'adi`; }
  }
  el.className = cls;
  el.innerHTML = `🧮 Taxminiy VRAM: ~${estGb.toFixed(1)} GB (${letter}, imgsz ${imgsz}, batch ${batch})${note}`;
}

// ---------- Stop ----------
async function stopTrain() {
  if (!_currentRunId) return;
  if (!confirm("Train'ni to'xtatasizmi? last.pt saqlanadi — keyin Resume bilan davom ettirsa bo'ladi.")) return;
  const btn = $('stopBtn'); btn.disabled = true;
  try {
    const r = await api('/api/training/stop/' + _currentRunId, { method: 'POST' });
    if (!r.ok) throw new Error(await r.text());
    $('startStatus').innerHTML = "⏹ To'xtatilmoqda…";
  } catch (e) {
    alert('Stop xato: ' + e.message);
  } finally {
    btn.disabled = false;
  }
}

$('startBtn').addEventListener('click', startTrain);
$('stopBtn').addEventListener('click', stopTrain);
$('refreshRunsBtn').addEventListener('click', loadRuns);
$('refreshAllBtn').addEventListener('click', () => { loadDatasets(); loadBaseModels(); loadRuns(); loadGpu(); });
$('validateBtn').addEventListener('click', validateDataset);
$('dataYamlPath').addEventListener('change', validateDataset);
['imgsz', 'batch', 'device'].forEach(id => $(id).addEventListener('change', estimateVram));
$('baseModelSel').addEventListener('change', estimateVram);

// Boshlash
(async () => {
  await loadUser();
  await Promise.all([loadDatasets(), loadBaseModels(), loadRuns()]);
  drawAllCharts([]);
  await loadGpu();
  estimateVram();
  setInterval(loadGpu, 4000);
})();
