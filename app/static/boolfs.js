// boolfs.js — "Xamdamov: bulcha belgilar tanlash" bo'limi (train.html)
// train.js allaqachon global $ / api / apiJson / fetchImgUrl beradi.

let _bfPoll = null;
let _bfRunId = null;
let _bfShown = null;   // natijalar panelida ko'rsatilayotgan run

const _bfFmt = (v, d = 4) => (v === null || v === undefined || Number.isNaN(v) ? '—' : Number(v).toFixed(d));
const _bfEsc = (s) => String(s === null || s === undefined ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

// ---------------------------------------------------------------- selektlar
async function bfLoadDatasets() {
  const sel = $('bfDataset');
  try {
    const j = await apiJson('/api/training/datasets');
    sel.innerHTML = '';
    const ds = j.datasets || [];
    if (!ds.length) { sel.innerHTML = '<option value="">— dataset topilmadi —</option>'; return; }
    for (const d of ds) {
      const o = document.createElement('option');
      o.value = d.yaml;
      o.textContent = `${d.yaml.split('/').slice(-2)[0]} (${d.train_count + d.val_count} tasvir)`;
      sel.appendChild(o);
    }
  } catch (e) { sel.innerHTML = `<option value="">Xato: ${_bfEsc(e.message)}</option>`; }
}

async function bfLoadWeights() {
  const sel = $('bfWeights');
  try {
    const j = await apiJson('/api/training/base_models');
    sel.innerHTML = '<option value="">— ansamblsiz (faqat boolfs) —</option>';
    // Ansambl uchun faqat LOKAL (o'qitilgan) .pt fayllar yaraydi: diskda mavjud bo'lishi shart.
    for (const m of (j.local || [])) {
      const o = document.createElement('option');
      o.value = m.path;
      o.textContent = m.label;
      sel.appendChild(o);
    }
    if (!(j.local || []).length) {
      const o = document.createElement('option');
      o.disabled = true;
      o.textContent = '— lokal o\'qitilgan model yo\'q —';
      sel.appendChild(o);
    }
  } catch (e) { sel.innerHTML = `<option value="">Xato: ${_bfEsc(e.message)}</option>`; }
}

// ---------------------------------------------------------------- ishga tushirish
async function bfStart() {
  const body = {
    data_yaml: $('bfDataset').value,
    weights: $('bfWeights').value,
    alpha: parseFloat($('bfAlpha').value) || 0.5,
    conf: parseFloat($('bfConf').value) || 0.05,
    iou: parseFloat($('bfIou').value) || 0.3,
    cv_folds: parseInt($('bfFolds').value, 10) || 5,
    split: $('bfSplit').value,
    n_star: parseInt($('bfNstar').value, 10) || 0,
    note: $('bfNote').value.trim(),
  };
  if (!body.data_yaml) { bfStatus('Avval dataset tanlang', 'failed'); return; }
  $('bfRunBtn').disabled = true;
  bfStatus('yuborilmoqda…', 'running');
  try {
    const j = await apiJson('/api/boolfs/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    _bfRunId = j.run_id;
    $('bfLog').hidden = false;
    $('bfProgWrap').hidden = false;
    $('bfStopBtn').hidden = false;
    bfPoll();
  } catch (e) {
    $('bfRunBtn').disabled = false;
    bfStatus('Xato: ' + e.message, 'failed');
  }
}

async function bfStop() {
  if (!_bfRunId) return;
  $('bfStopBtn').disabled = true;
  try {
    await apiJson(`/api/boolfs/stop/${encodeURIComponent(_bfRunId)}`, { method: 'POST' });
    bfStatus('to\'xtatilmoqda…', 'stopped');
  } catch (e) { bfStatus('Xato: ' + e.message, 'failed'); $('bfStopBtn').disabled = false; }
}

function bfStatus(text, cls) {
  const el = $('bfStatus');
  el.textContent = text;
  el.className = 'ts-status bf-st-' + (cls || 'running');
}

function bfPoll() {
  if (_bfPoll) clearInterval(_bfPoll);
  const tick = async () => {
    if (!_bfRunId) return;
    let s;
    try { s = await apiJson(`/api/boolfs/status/${encodeURIComponent(_bfRunId)}`); }
    catch { return; }
    $('bfProg').style.width = (s.progress || 0) + '%';
    const log = $('bfLog');
    log.textContent = (s.log || []).join('\n');
    log.scrollTop = log.scrollHeight;
    bfStatus(`${s.status} · ${s.progress || 0}% · ${s.message || ''}`, s.status);

    if (!s.running && s.status !== 'queued') {
      clearInterval(_bfPoll); _bfPoll = null;
      $('bfRunBtn').disabled = false;
      $('bfStopBtn').hidden = true;
      $('bfStopBtn').disabled = false;
      bfLoadRuns();
      if (s.status === 'done') bfShowRun(_bfRunId);
      _bfRunId = null;
    }
  };
  tick();
  _bfPoll = setInterval(tick, 2500);
}

// ---------------------------------------------------------------- sinovlar tarixi
async function bfLoadRuns() {
  const t = $('bfRunsTable');
  try {
    const j = await apiJson('/api/boolfs/runs');
    const runs = j.runs || [];
    if (!runs.length) { t.innerHTML = '<tr><td>Hali sinov yo\'q</td></tr>'; return; }
    let h = '<tr><th>Sinov</th><th>Model</th><th class="num">P</th><th>Holat</th></tr>';
    for (const r of runs) {
      const sm = r.summary || {};
      const best = (sm.P_ens !== null && sm.P_ens !== undefined) ? sm.P_ens : sm.P_val;
      const label = r.note || r.run_id.slice(2, 15);
      h += `<tr data-run="${_bfEsc(r.run_id)}">
        <td title="${_bfEsc(r.run_id)}">${_bfEsc(label)}</td>
        <td>${_bfEsc(r.weights || '—')}</td>
        <td class="num">${best === undefined || best === null ? '—' : _bfFmt(best, 3)}</td>
        <td class="bf-st-${_bfEsc(r.status)}">${_bfEsc(r.status)}${r.running ? ' ' + (r.progress || 0) + '%' : ''}</td>
      </tr>`;
    }
    t.innerHTML = h;
    // eski sinov ustiga bosilsa — natijasini ko'rsatamiz
    for (const tr of t.querySelectorAll('tr[data-run]')) {
      tr.addEventListener('click', () => bfShowRun(tr.dataset.run));
    }
    // sahifa ochilganda ishlayotgan sinov bo'lsa — kuzatishni tiklaymiz
    const live = runs.find((r) => r.running);
    if (live && !_bfRunId) {
      _bfRunId = live.run_id;
      $('bfLog').hidden = false; $('bfProgWrap').hidden = false;
      $('bfStopBtn').hidden = false; $('bfRunBtn').disabled = true;
      bfPoll();
    }
  } catch (e) { t.innerHTML = `<tr><td>Xato: ${_bfEsc(e.message)}</td></tr>`; }
}

// ---------------------------------------------------------------- natija
function _bfCards(res) {
  const art = res.artifacts || {};
  const ev = res.eval || {};
  const ens = res.ensemble;
  const c = [];
  c.push(['n*', art.n_star, 'informativ belgilar']);
  c.push(['P(n*)', _bfFmt(art.P_star, 4), `CV (${(res.params || {}).cv_folds || 5}-fold)`]);
  c.push(['P', _bfFmt(ev.P, 4), `boolfs yakka · ${ev.split || ''}`]);
  c.push(['ROI', art.n_roi_train, 'train belgilar']);
  let html = '';
  for (const [v, val, l] of c) {
    html += `<div class="bf-card"><div class="v">${_bfEsc(val === undefined ? '—' : val)}</div>
             <div class="l">${_bfEsc(v)} — ${_bfEsc(l)}</div></div>`;
  }
  if (ens) {
    const pY = ens.alpha_results['1.0'];
    const pE = ens.alpha_results[String(ens.best_alpha)];
    const win = pE > pY;
    html += `<div class="bf-card"><div class="v">${_bfFmt(pY, 4)}</div><div class="l">YOLO yakka (α=1)</div></div>`;
    html += `<div class="bf-card${win ? ' win' : ''}"><div class="v">${_bfFmt(pE, 4)}</div>
             <div class="l">Ansambl (α*=${ens.best_alpha})${win ? ' · +' + _bfFmt((pE - pY) * 100, 1) + ' p.p.' : ''}</div></div>`;
  }
  return html;
}

function _bfAlphaTable(ens) {
  if (!ens) return '';
  const rows = Object.keys(ens.alpha_results)
    .map(Number).sort((a, b) => a - b)
    .map((al) => {
      const p = ens.alpha_results[String(al)];
      const best = al === ens.best_alpha;
      return `<tr class="${best ? 'bf-best' : ''}"><td>α = ${al}${al === 0 ? ' (faqat boolfs)' : al === 1 ? ' (faqat YOLO)' : ''}</td>
              <td class="num">${_bfFmt(p, 4)}</td></tr>`;
    }).join('');
  return `<div style="font-size:12px;color:var(--bf-dim);margin:12px 0 2px">
            α-supurish · z<sub>p</sub> = α·YOLO<sub>p</sub> + (1−α)·s<sub>p</sub>
            · ${ens.n_matched} mos ROI (IoU ≥ ${ens.iou_thr})
          </div>
          <table class="bf-tbl"><tr><th>Aralashtirish</th><th class="num">P kriteriysi</th></tr>${rows}</table>`;
}

function _bfSelTable(art) {
  const tab = (art.selection_table || []).slice(0, 15);
  if (!tab.length) return '';
  const rows = tab.map((r) => `<tr class="${r.n === art.n_star ? 'bf-best' : ''}">
      <td class="num">${r.n}</td><td>${_bfEsc(r.feature)}</td>
      <td class="num">${_bfFmt(r.r_j, 3)}</td><td class="num">${_bfFmt(r.phi_prefix, 3)}</td>
      <td class="num">${_bfFmt((art.P_curve || [])[r.n - 1], 3)}</td></tr>`).join('');
  return `<div style="font-size:12px;color:var(--bf-dim);margin:12px 0 2px">
            Ranjirlangan qator (3.4.5): r<sub>j</sub> = a<sub>j</sub>/(b<sub>j</sub>+c<sub>j</sub>) kamayish tartibida
          </div>
          <table class="bf-tbl">
            <tr><th>n′</th><th>Belgi</th><th class="num">r<sub>j</sub></th><th class="num">Ф(n′)</th><th class="num">P(n′)</th></tr>
            ${rows}
          </table>
          <div class="bf-hint" style="margin-left:0">Yashil qator — tanlangan n* (P maksimumi). Jami ${art.selection_table.length} belgi.</div>`;
}

function _bfPerClass(ens, ev) {
  const rows = [];
  const names = (ev.class_names || []);
  const pcB = ev.per_class || [];
  const pcY = ens ? ens.per_class_yolo : null;
  const pcE = ens ? ens.per_class_ensemble : null;
  for (let i = 0; i < names.length; i++) {
    const b = pcB[i] || {};
    if (!b.support && !(pcY && pcY[i].support)) continue;
    let r = `<tr><td>${_bfEsc(names[i])}</td><td class="num">${b.support || 0}</td>
             <td class="num">${_bfFmt(b.recall, 3)}</td>`;
    if (ens) {
      const impr = pcE[i].recall > pcY[i].recall;
      r += `<td class="num">${_bfFmt(pcY[i].recall, 3)}</td>
            <td class="num" style="${impr ? 'color:#4ade80;font-weight:600' : ''}">${_bfFmt(pcE[i].recall, 3)}</td>`;
    }
    rows.push(r + '</tr>');
  }
  if (!rows.length) return '';
  const head = ens
    ? '<tr><th>Sinf</th><th class="num">n</th><th class="num">boolfs R</th><th class="num">YOLO R</th><th class="num">Ansambl R</th></tr>'
    : '<tr><th>Sinf</th><th class="num">n</th><th class="num">boolfs R</th></tr>';
  return `<div style="font-size:12px;color:var(--bf-dim);margin:12px 0 2px">Sinflar bo'yicha to'liqlik (recall)</div>
          <table class="bf-tbl">${head}${rows.join('')}</table>`;
}

async function bfShowRun(runId) {
  _bfShown = runId;
  const box = $('bfResult');
  box.innerHTML = '<div class="bf-sub">yuklanmoqda…</div>';
  $('bfSummary').innerHTML = '';
  $('bfAlphaTable').innerHTML = '';
  let res;
  try { res = await apiJson(`/api/boolfs/result/${encodeURIComponent(runId)}`); }
  catch (e) { box.innerHTML = `<div class="bf-sub">Natija yo'q: ${_bfEsc(e.message)}</div>`; return; }
  if (_bfShown !== runId) return;   // foydalanuvchi boshqasiga o'tib ketdi

  const art = res.artifacts || {};
  const ev = res.eval || {};
  const ens = res.ensemble || null;
  $('bfSummary').innerHTML = _bfCards(res);
  $('bfAlphaTable').innerHTML = _bfAlphaTable(ens);

  const p = res.params || {};
  let h = `<div class="bf-sub"><b>${_bfEsc(runId)}</b>${p.note ? ' · ' + _bfEsc(p.note) : ''}
             · dataset: ${_bfEsc((p.data_yaml || '').split('/').slice(-2)[0] || '—')}
             · model: ${_bfEsc((p.weights || '').split('/').pop() || 'yo\'q')}
             · <a href="#" id="bfRepBtn" style="color:var(--bf)">report.md yuklab olish</a></div>`;
  h += '<div class="bf-grid">';
  h += '<div>' + _bfSelTable(art) + '</div>';
  h += '<div>' + _bfPerClass(ens, ev) + '</div>';
  h += '</div><div id="bfFigs"></div>';
  box.innerHTML = h;

  const rep = $('bfRepBtn');
  if (rep) rep.addEventListener('click', (e) => { e.preventDefault(); bfDownloadReport(runId); });

  const figs = $('bfFigs');
  for (const name of (res.figures || [])) {
    try {
      const u = await fetchImgUrl(`/api/boolfs/figure/${encodeURIComponent(runId)}/${encodeURIComponent(name)}`);
      if (_bfShown !== runId) { URL.revokeObjectURL(u); return; }
      const img = document.createElement('img');
      img.src = u; img.className = 'bf-fig'; img.alt = name;
      figs.appendChild(img);
    } catch { /* rasm bo'lmasa — o'tkazib yuboramiz */ }
  }
}

async function bfDownloadReport(runId) {
  try {
    const r = await api(`/api/boolfs/report/${encodeURIComponent(runId)}`);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const url = URL.createObjectURL(await r.blob());
    const a = document.createElement('a');
    a.href = url; a.download = `boolfs_${runId}_report.md`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  } catch (e) { alert('Hisobotni yuklab bo\'lmadi: ' + e.message); }
}

// ---------------------------------------------------------------- init
document.addEventListener('DOMContentLoaded', () => {
  if (!$('bfRunBtn')) return;
  $('bfRunBtn').addEventListener('click', bfStart);
  $('bfStopBtn').addEventListener('click', bfStop);
  $('bfRefreshBtn').addEventListener('click', bfLoadRuns);
  bfLoadDatasets();
  bfLoadWeights();
  bfLoadRuns();
});
