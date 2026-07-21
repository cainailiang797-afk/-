$ErrorActionPreference = "Stop"
$root = Join-Path $PSScriptRoot "web-ui"
if (-not (Test-Path $root)) { New-Item -ItemType Directory -Path $root -Force | Out-Null }

function Write-File([string]$Path, [string]$Content) {
    $dir = Split-Path -Path $Path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
    Write-Host "  ok $Path"
}

Write-Host "==> Deploying to $root"

# ---- backend/requirements.txt ----
$content = "fastapi==0.115.5`r`nuvicorn[standard]==0.32.1`r`npydantic==2.10.3"
Write-File "$root/backend/requirements.txt" $content

# ---- backend/db.py ----
$content = @'
"""SQLite project metadata + job queue."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "data.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    with get_conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                name          TEXT PRIMARY KEY,
                topic         TEXT,
                json_path     TEXT NOT NULL,
                video_path    TEXT,
                poster_path   TEXT,
                vertical      INTEGER DEFAULT 1,
                status        TEXT DEFAULT 'idle',
                error         TEXT,
                created_at    REAL NOT NULL,
                updated_at    REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id            TEXT PRIMARY KEY,
                project_name  TEXT NOT NULL,
                kind          TEXT NOT NULL,
                status        TEXT DEFAULT 'pending',
                log           TEXT DEFAULT '',
                created_at    REAL NOT NULL,
                updated_at    REAL NOT NULL,
                FOREIGN KEY (project_name) REFERENCES projects(name) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS settings (
                key           TEXT PRIMARY KEY,
                value         TEXT
            );
            """
        )


def upsert_project(name, topic, json_path, vertical=1):
    now = time.time()
    with get_conn() as c:
        c.execute(
            """INSERT INTO projects (name, topic, json_path, vertical, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                 topic=excluded.topic, json_path=excluded.json_path,
                 vertical=excluded.vertical, updated_at=excluded.updated_at""",
            (name, topic, json_path, vertical, now, now),
        )
    return get_project(name)


def set_project_status(name, status, error=None, video_path=None):
    fields = ["status=?", "updated_at=?", "error=?"]
    vals = [status, time.time(), error]
    if video_path is not None:
        fields.append("video_path=?")
        vals.append(video_path)
    vals.append(name)
    with get_conn() as c:
        c.execute(f"UPDATE projects SET {', '.join(fields)} WHERE name=?", vals)


def list_projects():
    with get_conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()]


def get_project(name):
    with get_conn() as c:
        r = c.execute("SELECT * FROM projects WHERE name=?", (name,)).fetchone()
    return dict(r) if r else None


def delete_project(name):
    with get_conn() as c:
        c.execute("DELETE FROM projects WHERE name=?", (name,))


def create_job(job_id, project_name, kind):
    now = time.time()
    with get_conn() as c:
        c.execute(
            "INSERT INTO jobs (id, project_name, kind, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'pending', ?, ?)",
            (job_id, project_name, kind, now, now),
        )


def update_job(job_id, status=None, log=None):
    fields, vals = ["updated_at=?"], [time.time()]
    if status is not None:
        fields.append("status=?")
        vals.append(status)
    if log is not None:
        fields.append("log=?")
        vals.append(log)
    vals.append(job_id)
    with get_conn() as c:
        c.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE id=?", vals)


def get_job(job_id):
    with get_conn() as c:
        r = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    return dict(r) if r else None


def append_job_log(job_id, line):
    with get_conn() as c:
        c.execute("UPDATE jobs SET log = log || ?, updated_at=? WHERE id=?",
                  (line + "\n", time.time(), job_id))


def get_setting(key):
    with get_conn() as c:
        r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return r["value"] if r else None


def set_setting(key, value):
    with get_conn() as c:
        c.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
'@
Write-File "$root/backend/db.py" $content

# ---- backend/generator.py ----
$content = @'
"""Spawn make_dreams_video.py as a background process; stream logs to db."""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Callable

import db

ROOT = Path(__file__).resolve().parent.parent.parent
PYTHON_BIN = ROOT / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / (
    "python.exe" if sys.platform == "win32" else "python"
)
SCRIPT = ROOT / "projects" / "dreams" / "make_dreams_video.py"


def _resolve_python() -> str:
    if PYTHON_BIN.exists():
        return str(PYTHON_BIN)
    return sys.executable


def start_generate(project_name, props_path, vertical=True, on_log=None):
    job_id = uuid.uuid4().hex[:12]
    db.create_job(job_id, project_name, "generate")
    db.set_project_status(project_name, "generating")

    def _on_log(line):
        db.append_job_log(job_id, line.rstrip())
        if on_log:
            on_log(line)

    def run():
        try:
            cmd = [_resolve_python(), str(SCRIPT), "--props", props_path]
            if not vertical:
                cmd.append("--horizontal")
            _on_log(f"$ {' '.join(cmd)}")
            env = os.environ.copy()
            proc = subprocess.Popen(
                cmd, cwd=str(ROOT),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, env=env,
            )
            assert proc.stdout
            for line in proc.stdout:
                _on_log(line)
            rc = proc.wait()
            if rc != 0:
                raise RuntimeError(f"make_dreams_video.py exited with {rc}")
            props_name = Path(props_path).stem.replace("-explainer", "").replace("_explainer", "")
            out_dir = Path(props_path).parent
            video = out_dir / f"{props_name}_final.mp4"
            if not video.exists():
                raise RuntimeError(f"final video not found: {video}")
            db.set_project_status(project_name, "done", video_path=str(video))
            db.update_job(job_id, status="done")
            _on_log(f"[OK] final video: {video}")
        except Exception as e:
            db.set_project_status(project_name, "error", error=str(e))
            db.update_job(job_id, status="error", log=str(e))
            _on_log(f"[ERROR] {e}")

    threading.Thread(target=run, daemon=True).start()
    return job_id
'@
Write-File "$root/backend/generator.py" $content

# ---- backend/llm.py ----
$content = @'
"""LLM JSON generation (OpenAI-compatible API). Optional."""
from __future__ import annotations

import json
import re
import urllib.request

import db

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"

PROMPT = """You are a Chinese science-explainer short video scriptwriter. Given a topic, output a 9:16 vertical short video JSON.

JSON fields:
- topic: the topic
- cuts: 9 cuts in chronological order
  - id: cut-1, cut-2, ...
  - type: hero_title / stat_card / bar_chart / text_card / callout / kpi_grid
  - in_seconds / out_seconds: cumulative seconds (last out_seconds <= 40)
  - text: main title or stat value
  - subtitle: subtitle
  - backgroundColor: hex color
- subtitles: 9 subtitles
  - start / end: aligned with cut in/out
  - text: one colloquial Chinese line
- overlays: 0-2 floating elements

Total duration 35-40s. 4-5 key points + hook + CTA.

Output ONLY the JSON, no markdown fences, no explanation."""


def is_configured():
    return bool(db.get_setting("llm_api_key"))


def generate_json(topic):
    api_key = db.get_setting("llm_api_key") or ""
    base_url = db.get_setting("llm_base_url") or DEFAULT_BASE_URL
    model = db.get_setting("llm_model") or DEFAULT_MODEL

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"Topic: {topic}\n\nOutput JSON:"},
        ],
        "temperature": 0.7,
    }
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())

    content = data["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if not m:
        raise RuntimeError(f"LLM did not return JSON: {content[:200]}")
    return json.loads(m.group(0))
'@
Write-File "$root/backend/llm.py" $content

# ---- backend/server.py ----
$content = @'
"""OpenMontage Studio - FastAPI backend."""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
import generator
import llm

ROOT = Path(__file__).resolve().parent.parent.parent
PROJECTS_DIR = ROOT / "projects"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="OpenMontage Studio")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

db.init_db()


class SaveProjectReq(BaseModel):
    name: str
    topic: str = ""
    data: dict
    vertical: bool = True


class GenerateReq(BaseModel):
    name: str
    vertical: bool = True


class LLMGenerateReq(BaseModel):
    topic: str
    name: str | None = None
    base_url: str | None = None
    model: str | None = None


class SettingReq(BaseModel):
    key: str
    value: str


@app.get("/api/projects")
def api_list_projects():
    projects = db.list_projects()
    if not projects:
        for json_path in PROJECTS_DIR.glob("*/*-explainer.json"):
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            name = json_path.parent.name
            db.upsert_project(
                name=name,
                topic=data.get("topic") or data.get("theme", ""),
                json_path=str(json_path),
                vertical=1,
            )
        for p in db.list_projects():
            for ext in ("_final.mp4", "_with_subs.mp4"):
                cand = Path(p["json_path"]).parent / (
                    Path(p["json_path"]).stem.replace("-explainer", "") + ext
                )
                if cand.exists():
                    db.set_project_status(p["name"], "done", video_path=str(cand))
                    break
        projects = db.list_projects()
    return projects


@app.get("/api/projects/{name}")
def api_get_project(name: str):
    p = db.get_project(name)
    if not p:
        raise HTTPException(404, "project not found")
    json_path = Path(p["json_path"])
    if not json_path.exists():
        raise HTTPException(404, f"json not found: {json_path}")
    return {
        "meta": p,
        "data": json.loads(json_path.read_text(encoding="utf-8")),
    }


@app.put("/api/projects/{name}")
def api_save_project(name: str, req: SaveProjectReq):
    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
    proj_dir = PROJECTS_DIR / safe_name
    proj_dir.mkdir(parents=True, exist_ok=True)
    json_path = proj_dir / f"{safe_name}-explainer.json"
    json_path.write_text(
        json.dumps(req.data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    db.upsert_project(
        name=safe_name,
        topic=req.topic or req.data.get("topic", ""),
        json_path=str(json_path),
        vertical=1 if req.vertical else 0,
    )
    return {"ok": True, "name": safe_name, "json_path": str(json_path)}


@app.delete("/api/projects/{name}")
def api_delete_project(name: str):
    p = db.get_project(name)
    if not p:
        raise HTTPException(404, "project not found")
    json_path = Path(p["json_path"])
    out_dir = json_path.parent
    for ext in ("_silent_9x16.mp4", "_silent_16x9.mp4", "_voiceover.wav",
                "_with_subs.mp4", "_final.mp4"):
        cand = out_dir / f"{name}{ext}"
        if cand.exists():
            cand.unlink()
    tts = out_dir / "tts"
    if tts.exists():
        shutil.rmtree(tts)
    if json_path.exists():
        json_path.unlink()
    db.delete_project(name)
    return {"ok": True}


@app.post("/api/generate")
def api_generate(req: GenerateReq):
    p = db.get_project(req.name)
    if not p:
        raise HTTPException(404, "project not found")
    job_id = generator.start_generate(
        project_name=req.name,
        props_path=p["json_path"],
        vertical=bool(p.get("vertical", 1)),
    )
    return {"ok": True, "job_id": job_id}


@app.get("/api/jobs/{job_id}")
def api_get_job(job_id: str):
    j = db.get_job(job_id)
    if not j:
        raise HTTPException(404, "job not found")
    return j


@app.get("/api/media/video")
def api_video(path: str):
    p = Path(path)
    if not p.is_absolute():
        p = (ROOT / path).resolve()
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "video not found")
    return FileResponse(p, media_type="video/mp4")


@app.get("/api/llm/status")
def api_llm_status():
    return {
        "configured": llm.is_configured(),
        "base_url": db.get_setting("llm_base_url"),
        "model": db.get_setting("llm_model"),
        "has_key": bool(db.get_setting("llm_api_key")),
    }


@app.post("/api/llm/config")
def api_llm_config(req: SettingReq):
    if req.key in ("llm_api_key", "llm_base_url", "llm_model"):
        db.set_setting(req.key, req.value)
        return {"ok": True}
    raise HTTPException(400, "unsupported key")


@app.post("/api/llm/generate")
def api_llm_generate(req: LLMGenerateReq):
    if not llm.is_configured():
        raise HTTPException(400, "LLM not configured - set API key in Settings")
    if req.base_url:
        db.set_setting("llm_base_url", req.base_url)
    if req.model:
        db.set_setting("llm_model", req.model)
    data = llm.generate_json(req.topic)
    name = req.name or re.sub(r"[^a-zA-Z0-9_\-]", "_", req.topic)[:32] or "topic"
    proj_dir = PROJECTS_DIR / name
    proj_dir.mkdir(parents=True, exist_ok=True)
    json_path = proj_dir / f"{name}-explainer.json"
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    db.upsert_project(name=name, topic=req.topic, json_path=str(json_path))
    return {"ok": True, "name": name, "data": data}


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/app.js")
    def app_js():
        return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")

    @app.get("/style.css")
    def app_css():
        return FileResponse(FRONTEND_DIR / "style.css", media_type="text/css")
'@
Write-File "$root/backend/server.py" $content

# ---- start.bat ----
$content = "@echo off`r`nchcp 65001 >nul`r`npushd `"%~dp0`"`r`nif not exist `"backend\__installed__`" (`r`n    echo [setup] 首次运行，安装依赖…`r`n    pushd backend`r`n    ..\..\..\.venv\Scripts\python.exe -m pip install -r requirements.txt`r`n    if errorlevel 1 (`r`n        echo [错误] 依赖安装失败`r`n        popd`r`n        popd`r`n        pause`r`n        exit /b 1`r`n    )`r`n    popd`r`n    echo. > backend\__installed__`r`n)`r`necho.`r`necho ============================================================`r`necho  OpenMontage Studio`r`necho  打开 http://localhost:8000`r`necho ============================================================`r`necho.`r`n..\.venv\Scripts\python.exe -m uvicorn backend.server:app --port 8000 --reload`r`npopd`r`npause`r`n"
Write-File "$root/start.bat" $content

# ---- frontend/index.html ----
$content = @'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OpenMontage Studio</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <header>
    <h1>OpenMontage Studio</h1>
    <nav>
      <button class="tab active" data-tab="gallery">Project Gallery</button>
      <button class="tab" data-tab="generate">Topic Generate</button>
      <button class="tab" data-tab="settings">Settings</button>
    </nav>
  </header>

  <main>
    <section id="tab-gallery" class="tab-pane active">
      <div class="toolbar">
        <h2>Project Gallery</h2>
        <button id="btn-new-project" class="primary">+ New blank project</button>
      </div>
      <div id="project-grid" class="grid">
        <div class="loading">Loading...</div>
      </div>
    </section>

    <section id="tab-editor" class="tab-pane">
      <div class="editor-layout">
        <aside class="editor-sidebar">
          <h3 id="editor-title">Project</h3>
          <div class="editor-meta">
            <label>Topic <input id="editor-topic" type="text" placeholder="Why do we dream"></label>
            <label>Orientation
              <select id="editor-vertical">
                <option value="1">9:16 vertical</option>
                <option value="0">16:9 horizontal</option>
              </select>
            </label>
          </div>
          <div class="editor-actions">
            <button id="btn-save" class="primary">Save</button>
            <button id="btn-generate" class="primary">Generate</button>
            <button id="btn-back">Back</button>
            <button id="btn-delete" class="danger">Delete</button>
          </div>
          <div id="job-status" class="job-status"></div>
        </aside>
        <div class="editor-main">
          <div class="editor-tabs">
            <button class="etab active" data-etab="json">JSON</button>
            <button class="etab" data-etab="preview">Preview</button>
            <button class="etab" data-etab="log">Log</button>
          </div>
          <div class="editor-pane active" id="epane-json">
            <textarea id="json-editor" spellcheck="false"></textarea>
          </div>
          <div class="editor-pane" id="epane-preview">
            <div id="preview-empty" class="empty">No video yet</div>
            <video id="preview-video" controls style="display:none; max-width: 360px; max-height: 640px;"></video>
          </div>
          <div class="editor-pane" id="epane-log">
            <pre id="job-log"></pre>
          </div>
        </div>
      </div>
    </section>

    <section id="tab-generate" class="tab-pane">
      <h2>Topic to Video</h2>
      <p class="hint">Enter a topic; AI auto-generates a 9-card JSON, then runs the pipeline.</p>
      <div class="form-row">
        <label>Topic <input id="llm-topic" type="text" placeholder="e.g. black holes" autofocus></label>
        <label>Project name (optional) <input id="llm-name" type="text" placeholder="defaults to topic"></label>
      </div>
      <button id="btn-llm-generate" class="primary">Generate JSON</button>
      <div id="llm-result"></div>
    </section>

    <section id="tab-settings" class="tab-pane">
      <h2>LLM Settings</h2>
      <p class="hint">OpenAI-compatible API. OpenAI / DeepSeek / Zhipu / Moonshot all work.</p>
      <div class="form-row">
        <label>Base URL <input id="set-base-url" type="text" placeholder="https://api.openai.com/v1"></label>
        <label>Model <input id="set-model" type="text" placeholder="gpt-4o-mini"></label>
        <label>API Key <input id="set-api-key" type="password" placeholder="sk-..."></label>
      </div>
      <button id="btn-save-settings" class="primary">Save</button>
      <div id="llm-status-display"></div>
    </section>
  </main>

  <script src="/app.js"></script>
</body>
</html>
'@
Write-File "$root/frontend/index.html" $content

# ---- frontend/style.css ----
$content = @'
:root {
  --bg: #0f172a;
  --bg-2: #1e293b;
  --bg-3: #334155;
  --fg: #e2e8f0;
  --fg-2: #94a3b8;
  --accent: #22d3ee;
  --danger: #ef4444;
  --ok: #34d399;
  --warn: #f59e0b;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  background: var(--bg);
  color: var(--fg);
  font-size: 14px;
  line-height: 1.5;
}
header {
  display: flex; align-items: center; gap: 24px;
  padding: 12px 24px; background: var(--bg-2);
  border-bottom: 1px solid var(--bg-3);
  position: sticky; top: 0; z-index: 10;
}
header h1 { margin: 0; font-size: 18px; }
header nav { display: flex; gap: 8px; }
.tab {
  background: transparent; color: var(--fg-2);
  border: 1px solid var(--bg-3);
  padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px;
}
.tab:hover { color: var(--fg); }
.tab.active { background: var(--accent); border-color: var(--accent); color: #0f172a; font-weight: 600; }
main { padding: 24px; max-width: 1400px; margin: 0 auto; }
.tab-pane { display: none; }
.tab-pane.active { display: block; }
button {
  background: var(--bg-2); color: var(--fg);
  border: 1px solid var(--bg-3);
  padding: 8px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; font-family: inherit;
}
button:hover { border-color: var(--accent); }
button.primary { background: var(--accent); color: #0f172a; border-color: var(--accent); font-weight: 600; }
button.primary:hover { background: #06b6d4; }
button.danger { background: var(--danger); color: #fff; border-color: var(--danger); }
button:disabled { opacity: 0.4; cursor: not-allowed; }
input, select, textarea {
  background: var(--bg); color: var(--fg);
  border: 1px solid var(--bg-3);
  padding: 6px 10px; border-radius: 4px; font-family: inherit; font-size: 13px;
}
input:focus, select:focus, textarea:focus { outline: 1px solid var(--accent); }
label { display: block; margin: 8px 0; color: var(--fg-2); }
label input, label select { display: block; margin-top: 4px; width: 100%; max-width: 480px; }
.hint { color: var(--fg-2); font-size: 12px; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.toolbar h2 { margin: 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.project-card {
  background: var(--bg-2); border: 1px solid var(--bg-3);
  border-radius: 8px; overflow: hidden; cursor: pointer;
  transition: transform 0.1s, border-color 0.1s;
}
.project-card:hover { border-color: var(--accent); transform: translateY(-2px); }
.project-card .poster {
  width: 100%; aspect-ratio: 9/16; background: #000;
  display: flex; align-items: center; justify-content: center;
  color: var(--fg-2); overflow: hidden;
}
.project-card .poster img, .project-card .poster video {
  width: 100%; height: 100%; object-fit: cover;
}
.project-card .info { padding: 10px 12px; }
.project-card .name { font-weight: 600; margin-bottom: 4px; }
.project-card .meta { display: flex; justify-content: space-between; font-size: 11px; color: var(--fg-2); }
.status-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.status-idle { background: var(--bg-3); color: var(--fg-2); }
.status-generating { background: var(--warn); color: #0f172a; }
.status-done { background: var(--ok); color: #0f172a; }
.status-error { background: var(--danger); color: #fff; }
.loading, .empty { padding: 32px; text-align: center; color: var(--fg-2); }
.editor-layout { display: grid; grid-template-columns: 280px 1fr; gap: 16px; height: calc(100vh - 130px); }
.editor-sidebar {
  background: var(--bg-2); border: 1px solid var(--bg-3);
  border-radius: 8px; padding: 16px;
  display: flex; flex-direction: column; overflow: auto;
}
.editor-sidebar h3 { margin: 0 0 12px; }
.editor-meta label { display: block; margin: 10px 0; }
.editor-meta input, .editor-meta select { width: 100%; max-width: none; }
.editor-actions { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; }
.editor-actions button { width: 100%; }
.job-status { margin-top: 16px; padding: 8px; background: var(--bg); border-radius: 4px; font-size: 12px; min-height: 32px; }
.editor-main {
  display: flex; flex-direction: column;
  background: var(--bg-2); border: 1px solid var(--bg-3);
  border-radius: 8px; overflow: hidden;
}
.editor-tabs { display: flex; gap: 4px; padding: 8px; border-bottom: 1px solid var(--bg-3); }
.etab { background: transparent; border: none; padding: 6px 12px; color: var(--fg-2); }
.etab.active { color: var(--fg); border-bottom: 2px solid var(--accent); }
.editor-pane { display: none; flex: 1; overflow: auto; }
.editor-pane.active { display: flex; flex-direction: column; }
#json-editor {
  flex: 1; width: 100%; border: none; border-radius: 0;
  padding: 12px; font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 12px; background: #0c1424; color: #cbd5e1; resize: none;
}
#epane-preview { align-items: center; justify-content: center; padding: 16px; }
#epane-log pre {
  flex: 1; margin: 0; padding: 12px;
  font-family: "JetBrains Mono", Consolas, monospace;
  font-size: 11px; color: #cbd5e1; background: #0c1424;
  white-space: pre-wrap; word-break: break-all;
}
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
#llm-result, #llm-status-display {
  margin-top: 16px; padding: 12px; background: var(--bg-2);
  border-radius: 6px; border: 1px solid var(--bg-3);
}
#llm-result pre, #llm-status-display pre {
  margin: 0; max-height: 400px; overflow: auto; font-size: 11px;
}
'@
Write-File "$root/frontend/style.css" $content

# ---- frontend/app.js ----
# Use a marker approach: write JS using regular quotes (no \" needed) to avoid heredoc escaping issues
$content = @'
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

$$(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    $$(".tab").forEach(t => t.classList.remove("active"));
    $$(".tab-pane").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    const target = document.getElementById("tab-" + btn.dataset.tab);
    if (target) target.classList.add("active");
    if (btn.dataset.tab === "gallery") loadGallery();
    if (btn.dataset.tab === "settings") loadSettings();
    if (btn.dataset.tab === "generate") checkLLMStatus();
  });
});

$$(".etab").forEach(btn => {
  btn.addEventListener("click", () => {
    $$(".etab").forEach(t => t.classList.remove("active"));
    $$(".editor-pane").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    const target = document.getElementById("epane-" + btn.dataset.etab);
    if (target) target.classList.add("active");
  });
});

async function loadGallery() {
  const grid = $("#project-grid");
  grid.innerHTML = '<div class="loading">Loading...</div>';
  try {
    const projects = await fetch("/api/projects").then(r => r.json());
    if (!projects.length) {
      grid.innerHTML = '<div class="empty">No projects yet. Click "+ New blank project" or use "Topic Generate".</div>';
      return;
    }
    grid.innerHTML = "";
    for (const p of projects) {
      const card = document.createElement("div");
      card.className = "project-card";
      const videoHtml = p.video_path
        ? '<video src="/api/media/video?path=' + encodeURIComponent(p.video_path) + '" muted preload="metadata"></video>'
        : '<span>No preview</span>';
      card.innerHTML =
        '<div class="poster">' + videoHtml + '</div>' +
        '<div class="info">' +
          '<div class="name">' + escapeHtml(p.name) + '</div>' +
          '<div class="meta">' +
            '<span>' + escapeHtml(p.topic || "-") + '</span>' +
            '<span class="status-badge status-' + p.status + '">' + statusLabel(p.status) + '</span>' +
          '</div>' +
        '</div>';
      card.addEventListener("click", () => openEditor(p.name));
      grid.appendChild(card);
    }
  } catch (e) {
    grid.innerHTML = '<div class="empty">Load failed: ' + escapeHtml(e.message) + '</div>';
  }
}

function statusLabel(s) {
  return { idle: "Pending", generating: "Generating...", done: "Done", error: "Failed" }[s] || s;
}

function escapeHtml(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

const btnNew = document.getElementById("btn-new-project");
if (btnNew) {
  btnNew.addEventListener("click", async () => {
    const name = prompt("Project name (letters/digits/underscore)", "my-topic");
    if (!name) return;
    const safe = name.replace(/[^a-zA-Z0-9_\-]/g, "_");
    const blank = {
      topic: name,
      cuts: Array.from({ length: 9 }, (_, i) => ({
        id: "cut-" + (i + 1),
        type: "hero_title",
        in_seconds: i * 4,
        out_seconds: (i + 1) * 4,
        text: "Card " + (i + 1),
        subtitle: "subtitle",
        backgroundColor: "#0F172A",
      })),
      overlays: [],
      subtitles: Array.from({ length: 9 }, (_, i) => ({
        start: i * 4, end: (i + 1) * 4, text: "Subtitle " + (i + 1),
      })),
      captions: [],
      audio: {},
    };
    await fetch("/api/projects/" + encodeURIComponent(safe), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: safe, topic: name, data: blank, vertical: true }),
    });
    openEditor(safe);
  });
}

let currentProject = null;
let pollJob = null;

async function openEditor(name) {
  $$(".tab").forEach(t => t.classList.remove("active"));
  $$(".tab-pane").forEach(p => p.classList.remove("active"));
  const editorPane = document.getElementById("tab-editor");
  if (editorPane) editorPane.classList.add("active");
  const galleryTab = document.querySelector('[data-tab="gallery"]');
  if (galleryTab) galleryTab.classList.add("active");

  const resp = await fetch("/api/projects/" + encodeURIComponent(name)).then(r => r.json());
  currentProject = resp.meta;
  document.getElementById("editor-title").textContent = name;
  document.getElementById("editor-topic").value = currentProject.topic || "";
  document.getElementById("editor-vertical").value = currentProject.vertical || 1;
  document.getElementById("json-editor").value = JSON.stringify(resp.data, null, 2);
  document.getElementById("job-status").textContent = "Status: " + statusLabel(currentProject.status);
  document.getElementById("job-log").textContent = "";
  if (currentProject.video_path) {
    document.getElementById("preview-empty").style.display = "none";
    const v = document.getElementById("preview-video");
    v.src = "/api/media/video?path=" + encodeURIComponent(currentProject.video_path);
    v.style.display = "block";
  } else {
    document.getElementById("preview-empty").style.display = "block";
    document.getElementById("preview-video").style.display = "none";
  }
}

const btnBack = document.getElementById("btn-back");
if (btnBack) {
  btnBack.addEventListener("click", () => {
    $$(".tab").forEach(t => t.classList.remove("active"));
    $$(".tab-pane").forEach(p => p.classList.remove("active"));
    const g = document.querySelector('[data-tab="gallery"]');
    if (g) g.classList.add("active");
    document.getElementById("tab-gallery").classList.add("active");
    loadGallery();
  });
}

const btnSave = document.getElementById("btn-save");
if (btnSave) {
  btnSave.addEventListener("click", async () => {
    if (!currentProject) return;
    let data;
    try {
      data = JSON.parse(document.getElementById("json-editor").value);
    } catch (e) {
      alert("JSON parse error: " + e.message);
      return;
    }
    const resp = await fetch("/api/projects/" + encodeURIComponent(currentProject.name), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: currentProject.name,
        topic: document.getElementById("editor-topic").value,
        data,
        vertical: document.getElementById("editor-vertical").value === "1",
      }),
    });
    if (resp.ok) {
      const s = document.getElementById("job-status");
      s.textContent = "Saved";
      setTimeout(() => { s.textContent = ""; }, 2000);
    }
  });
}

const btnGenerate = document.getElementById("btn-generate");
if (btnGenerate) {
  btnGenerate.addEventListener("click", async () => {
    if (!currentProject) return;
    const saveBtn = document.getElementById("btn-save");
    if (saveBtn) saveBtn.click();
    const resp = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: currentProject.name,
        vertical: document.getElementById("editor-vertical").value === "1",
      }),
    }).then(r => r.json());
    if (resp.ok) {
      document.getElementById("job-status").textContent = "Job: " + resp.job_id;
      pollJobStatus(resp.job_id);
    } else {
      alert("Start failed: " + (resp.detail || JSON.stringify(resp)));
    }
  });
}

const btnDelete = document.getElementById("btn-delete");
if (btnDelete) {
  btnDelete.addEventListener("click", async () => {
    if (!currentProject) return;
    if (!confirm('Delete project "' + currentProject.name + '" and all its outputs?')) return;
    await fetch("/api/projects/" + encodeURIComponent(currentProject.name), { method: "DELETE" });
    const back = document.getElementById("btn-back");
    if (back) back.click();
  });
}

function pollJobStatus(jobId) {
  if (pollJob) clearInterval(pollJob);
  const logEl = document.getElementById("job-log");
  let lastLogLen = 0;
  pollJob = setInterval(async () => {
    const j = await fetch("/api/jobs/" + jobId).then(r => r.json());
    if (j.log && j.log.length > lastLogLen) {
      logEl.textContent = j.log;
      logEl.scrollTop = logEl.scrollHeight;
      lastLogLen = j.log.length;
    }
    document.getElementById("job-status").textContent = statusLabel(j.status);
    if (j.status === "done" || j.status === "error") {
      clearInterval(pollJob);
      pollJob = null;
      if (j.status === "done") {
        const resp = await fetch("/api/projects/" + encodeURIComponent(currentProject.name)).then(r => r.json());
        currentProject = resp.meta;
        if (currentProject.video_path) {
          document.getElementById("preview-empty").style.display = "none";
          const v = document.getElementById("preview-video");
          v.src = "/api/media/video?path=" + encodeURIComponent(currentProject.video_path) + "&t=" + Date.now();
          v.style.display = "block";
          const previewTab = document.querySelector('[data-etab="preview"]');
          if (previewTab) previewTab.click();
        }
      } else {
        const lastLine = j.log ? (j.log.split("\n").slice(-2, -1)[0] || "") : "";
        document.getElementById("job-status").textContent = "Failed: " + lastLine;
      }
    }
  }, 1000);
}

async function checkLLMStatus() {
  const r = await fetch("/api/llm/status").then(r => r.json());
  document.getElementById("llm-status-display").innerHTML = r.configured
    ? '<span style="color: var(--ok)">LLM configured</span><pre>base_url: ' + (r.base_url || "(default)") + '\nmodel: ' + (r.model || "(default)") + '\nhas_key: ' + r.has_key + '</pre>'
    : '<span style="color: var(--warn)">LLM not configured</span><p>Fill in API key in Settings.</p>';
}

const btnLlm = document.getElementById("btn-llm-generate");
if (btnLlm) {
  btnLlm.addEventListener("click", async () => {
    const topic = document.getElementById("llm-topic").value.trim();
    if (!topic) { alert("Enter a topic"); return; }
    const name = document.getElementById("llm-name").value.trim();
    document.getElementById("llm-result").innerHTML = '<div class="loading">Calling LLM...</div>';
    try {
      const resp = await fetch("/api/llm/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, name }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "failed");
      document.getElementById("llm-result").innerHTML =
        '<h3>Generated: ' + escapeHtml(data.name) + '</h3>' +
        '<pre>' + escapeHtml(JSON.stringify(data.data, null, 2)) + '</pre>' +
        '<button id="btn-open-llm-result" class="primary">Open in editor</button>';
      document.getElementById("btn-open-llm-result").addEventListener("click", () => openEditor(data.name));
    } catch (e) {
      document.getElementById("llm-result").innerHTML = '<div class="empty">Failed: ' + escapeHtml(e.message) + '</div>';
    }
  });
}

async function loadSettings() {
  const r = await fetch("/api/llm/status").then(r => r.json());
  document.getElementById("set-base-url").value = r.base_url || "https://api.openai.com/v1";
  document.getElementById("set-model").value = r.model || "gpt-4o-mini";
  document.getElementById("set-api-key").value = "";
  document.getElementById("llm-status-display").innerHTML = r.configured
    ? '<span style="color: var(--ok)">Configured</span>'
    : '<span style="color: var(--warn)">Not configured</span>';
}

const btnSaveSet = document.getElementById("btn-save-settings");
if (btnSaveSet) {
  btnSaveSet.addEventListener("click", async () => {
    const items = [
      ["llm_base_url", document.getElementById("set-base-url").value],
      ["llm_model", document.getElementById("set-model").value],
      ["llm_api_key", document.getElementById("set-api-key").value],
    ];
    for (const [key, value] of items) {
      if (value) {
        await fetch("/api/llm/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ key, value }),
        });
      }
    }
    alert("Saved");
    loadSettings();
  });
}

loadGallery();
'@
Write-File "$root/frontend/app.js" $content

# ---- README.md ----
$content = @'
# OpenMontage Studio

Visual dashboard for the OpenMontage 9:16 explainer video pipeline.

## Quick start

1. Save this install_studio.ps1 to `D:\workspace\OpenMontage\`
2. Open PowerShell, run:
   ```
   powershell -ExecutionPolicy Bypass -File install_studio.ps1
   ```
3. Start the studio:
   ```
   web-ui\start.bat
   ```
4. Open http://localhost:8000

## Features

- **Project gallery** with auto-discovery of `projects/*/*-explainer.json`
- **Editor** with live JSON edit + video preview + real-time log
- **One-click generate** triggers the Python pipeline as a background process
- **Topic to video** uses an LLM (OpenAI-compatible) to auto-generate 9-card JSON
- **Settings** stores LLM API key, base URL, and model in local SQLite

## File layout

```
web-ui/
  backend/
    server.py      FastAPI app
    db.py          SQLite (projects/jobs/settings)
    generator.py   spawns make_dreams_video.py
    llm.py         OpenAI-compatible JSON generator
    requirements.txt
  frontend/
    index.html
    app.js
    style.css
  start.bat
  data.db          auto-created
```
'@
Write-File "$root/README.md" $content

Write-Host ""
Write-Host "==> Deploy complete"
Write-Host "    Start: web-ui\start.bat"
Write-Host "    Open:  http://localhost:8000"
