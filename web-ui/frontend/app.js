// OpenMontage Studio — 单页前端
// 所有 API 调用走 /api/...

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ===== 顶部 tab 切换 =====
$$('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    $$('.tab').forEach(t => t.classList.remove('active'));
    $$('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    $('#tab-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'gallery') loadGallery();
    if (btn.dataset.tab === 'settings') loadSettings();
    if (btn.dataset.tab === 'generate') checkLLMStatus();
  });
});

$$('.etab').forEach(btn => {
  btn.addEventListener('click', () => {
    $$('.etab').forEach(t => t.classList.remove('active'));
    $$('.editor-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    $('#epane-' + btn.dataset.etab).classList.add('active');
  });
});

// ===== 项目库 =====
async function loadGallery() {
  const grid = $('#project-grid');
  grid.innerHTML = '<div class="loading">加载中…</div>';
  try {
    const projects = await fetch('/api/projects').then(r => r.json());
    if (!projects.length) {
      grid.innerHTML = '<div class="empty">还没有项目。点上面的"+ 新建空白项目"或去"主题生成"。</div>';
      return;
    }
    grid.innerHTML = '';
    for (const p of projects) {
      const card = document.createElement('div');
      card.className = 'project-card';
      card.innerHTML = `
        <div class="poster">
          ${p.video_path
            ? `<video src="/api/media/video?path=${encodeURIComponent(p.video_path)}" muted preload="metadata"></video>`
            : '<span>暂无预览</span>'}
        </div>
        <div class="info">
          <div class="name">${escapeHtml(p.name)}</div>
          <div class="meta">
            <span>${p.topic || '—'}</span>
            <span class="status-badge status-${p.status}">${statusLabel(p.status)}</span>
          </div>
        </div>
      `;
      card.addEventListener('click', () => openEditor(p.name));
      grid.appendChild(card);
    }
  } catch (e) {
    grid.innerHTML = `<div class="empty">加载失败：${e.message}</div>`;
  }
}

function statusLabel(s) {
  return { idle: '待生成', generating: '生成中…', done: '已完成', error: '失败' }[s] || s;
}

function escapeHtml(s) {
  return String(s || '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// ===== 新建空白项目 =====
$('#btn-new-project').addEventListener('click', async () => {
  const name = prompt('项目名（英文/数字/下划线）', 'my-topic');
  if (!name) return;
  const safe = name.replace(/[^a-zA-Z0-9_\-]/g, '_');
  const blank = {
    topic: name,
    cuts: Array.from({ length: 9 }, (_, i) => ({
      id: `cut-${i + 1}`,
      type: 'hero_title',
      in_seconds: i * 4,
      out_seconds: (i + 1) * 4,
      text: `第 ${i + 1} 张`,
      subtitle: '副标题',
      backgroundColor: '#0F172A',
    })),
    overlays: [],
    subtitles: Array.from({ length: 9 }, (_, i) => ({
      start: i * 4, end: (i + 1) * 4, text: `这是第 ${i + 1} 段字幕`,
    })),
    captions: [],
    audio: {},
  };
  await fetch(`/api/projects/${encodeURIComponent(safe)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: safe, topic: name, data: blank, vertical: true }),
  });
  openEditor(safe);
});

// ===== 编辑器 =====
let currentProject = null;
let pollJob = null;

async function openEditor(name) {
  $$('.tab').forEach(t => t.classList.remove('active'));
  $$('.tab-pane').forEach(p => p.classList.remove('active'));
  $('#tab-editor').classList.add('active');
  // 强制添加一个"编辑器"tab 高亮
  document.querySelector('[data-tab="gallery"]').classList.add('active');

  const resp = await fetch(`/api/projects/${encodeURIComponent(name)}`).then(r => r.json());
  currentProject = resp.meta;
  $('#editor-title').textContent = name;
  $('#editor-topic').value = currentProject.topic || '';
  $('#editor-vertical').value = currentProject.vertical || 1;
  $('#json-editor').value = JSON.stringify(resp.data, null, 2);
  $('#job-status').textContent = `状态：${statusLabel(currentProject.status)}`;
  $('#job-log').textContent = '';
  if (currentProject.video_path) {
    $('#preview-empty').style.display = 'none';
    const v = $('#preview-video');
    v.src = `/api/media/video?path=${encodeURIComponent(currentProject.video_path)}`;
    v.style.display = 'block';
  } else {
    $('#preview-empty').style.display = 'block';
    $('#preview-video').style.display = 'none';
  }
}

$('#btn-back').addEventListener('click', () => {
  $$('.tab').forEach(t => t.classList.remove('active'));
  $$('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelector('[data-tab="gallery"]').classList.add('active');
  $('#tab-gallery').classList.add('active');
  loadGallery();
});

$('#btn-save').addEventListener('click', async () => {
  if (!currentProject) return;
  let data;
  try {
    data = JSON.parse($('#json-editor').value);
  } catch (e) {
    alert('JSON 解析失败：' + e.message);
    return;
  }
  const resp = await fetch(`/api/projects/${encodeURIComponent(currentProject.name)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: currentProject.name,
      topic: $('#editor-topic').value,
      data,
      vertical: $('#editor-vertical').value === '1',
    }),
  });
  if (resp.ok) {
    $('#job-status').textContent = '✓ 已保存';
    setTimeout(() => $('#job-status').textContent = '', 2000);
  }
});

$('#btn-generate').addEventListener('click', async () => {
  if (!currentProject) return;
  // 先保存
  await $('#btn-save').click();
  const resp = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: currentProject.name,
      vertical: $('#editor-vertical').value === '1',
    }),
  }).then(r => r.json());
  if (resp.ok) {
    $('#job-status').textContent = `▶ 任务已启动: ${resp.job_id}`;
    pollJobStatus(resp.job_id);
  } else {
    alert('启动失败：' + (resp.detail || JSON.stringify(resp)));
  }
});

$('#btn-delete').addEventListener('click', async () => {
  if (!currentProject) return;
  if (!confirm(`删除项目 "${currentProject.name}" 的所有视频和 JSON？`)) return;
  await fetch(`/api/projects/${encodeURIComponent(currentProject.name)}`, { method: 'DELETE' });
  $('#btn-back').click();
});

function pollJobStatus(jobId) {
  if (pollJob) clearInterval(pollJob);
  const logEl = $('#job-log');
  let lastLogLen = 0;
  pollJob = setInterval(async () => {
    const j = await fetch(`/api/jobs/${jobId}`).then(r => r.json());
    if (j.log && j.log.length > lastLogLen) {
      logEl.textContent = j.log;
      logEl.scrollTop = logEl.scrollHeight;
      lastLogLen = j.log.length;
    }
    $('#job-status').textContent = `▶ ${statusLabel(j.status)}`;
    if (j.status === 'done' || j.status === 'error') {
      clearInterval(pollJob);
      pollJob = null;
      if (j.status === 'done') {
        // 重新加载项目，更新 video
        const resp = await fetch(`/api/projects/${encodeURIComponent(currentProject.name)}`).then(r => r.json());
        currentProject = resp.meta;
        if (currentProject.video_path) {
          $('#preview-empty').style.display = 'none';
          const v = $('#preview-video');
          v.src = `/api/media/video?path=${encodeURIComponent(currentProject.video_path)}&t=${Date.now()}`;
          v.style.display = 'block';
          // 自动切到预览 tab
          document.querySelector('[data-etab="preview"]').click();
        }
      } else {
        $('#job-status').textContent = `✗ 失败：${j.log?.split('\n').slice(-2, -1)[0] || ''}`;
      }
    }
  }, 1000);
}

// ===== 主题生成 =====
async function checkLLMStatus() {
  const r = await fetch('/api/llm/status').then(r => r.json());
  $('#llm-status-display').innerHTML = r.configured
    ? `<span style="color: var(--ok)">✓ LLM 已配置</span>
       <pre>base_url: ${r.base_url || '(default)'}
model: ${r.model || '(default)'}
has_key: ${r.has_key}</pre>`
    : `<span style="color: var(--warn)">⚠ LLM 未配置</span>
       <p>去"设置"页面填 API key、Base URL、Model。</p>`;
}

$('#btn-llm-generate').addEventListener('click', async () => {
  const topic = $('#llm-topic').value.trim();
  if (!topic) { alert('填个主题'); return; }
  const name = $('#llm-name').value.trim();
  $('#llm-result').innerHTML = '<div class="loading">调用 LLM…</div>';
  try {
    const resp = await fetch('/api/llm/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, name }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || 'failed');
    $('#llm-result').innerHTML = `
      <h3>✓ 已生成：${escapeHtml(data.name)}</h3>
      <pre>${escapeHtml(JSON.stringify(data.data, null, 2))}</pre>
      <button id="btn-open-llm-result" class="primary">打开编辑器</button>
    `;
    $('#btn-open-llm-result').addEventListener('click', () => openEditor(data.name));
  } catch (e) {
    $('#llm-result').innerHTML = `<div class="empty">失败：${escapeHtml(e.message)}</div>`;
  }
});

// ===== 设置 =====
async function loadSettings() {
  const r = await fetch('/api/llm/status').then(r => r.json());
  $('#set-base-url').value = r.base_url || 'https://api.openai.com/v1';
  $('#set-model').value = r.model || 'gpt-4o-mini';
  $('#set-api-key').value = '';  // 不回显 key
  $('#llm-status-display').innerHTML = r.configured
    ? `<span style="color: var(--ok)">✓ 已配置</span>`
    : `<span style="color: var(--warn)">⚠ 未配置</span>`;
}

$('#btn-save-settings').addEventListener('click', async () => {
  const items = [
    ['llm_base_url', $('#set-base-url').value],
    ['llm_model', $('#set-model').value],
    ['llm_api_key', $('#set-api-key').value],
  ];
  for (const [key, value] of items) {
    if (value) {
      await fetch('/api/llm/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value }),
      });
    }
  }
  alert('已保存');
  loadSettings();
});

// 启动
loadGallery();
