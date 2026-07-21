"""OpenMontage 视频生成仪表板 — FastAPI 后端。

启动：uvicorn server:app --reload --port 8000
打开：http://localhost:8000
"""
from __future__ import annotations

import json
import mimetypes
import re
import shutil
import sys
from pathlib import Path
from typing import Any

# 让 `import db` / `import generator` / `import llm` 走绝对路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
import generator
import llm

ROOT = Path(__file__).resolve().parent.parent.parent
PROJECTS_DIR = ROOT / "projects"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
DEFAULT_PROPS = PROJECTS_DIR / "dreams" / "dreams-explainer.json"

app = FastAPI(title="OpenMontage Studio")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SaveProjectReq(BaseModel):
    name: str
    topic: str = ""
    data: dict[str, Any]
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


# ---------------------------------------------------------------------------
# API: projects
# ---------------------------------------------------------------------------

@app.get("/api/projects")
def api_list_projects():
    projects = db.list_projects()
    # 如果 db 为空，扫 projects/ 目录初始化
    if not projects:
        for json_path in PROJECTS_DIR.glob("*/*-explainer.json"):
            data = json.loads(json_path.read_text(encoding="utf-8"))
            name = json_path.parent.name
            db.upsert_project(
                name=name,
                topic=data.get("topic") or data.get("theme", ""),
                json_path=str(json_path),
                vertical=1,
            )
        # 自动找出已生成的视频
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
    # 删产物，但保留 .json
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


# ---------------------------------------------------------------------------
# API: jobs
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# API: media
# ---------------------------------------------------------------------------

@app.get("/api/media/video")
def api_video(path: str):
    p = Path(path)
    if not p.is_absolute():
        p = (ROOT / path).resolve()
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "video not found")
    return FileResponse(p, media_type="video/mp4")


@app.get("/api/media/poster")
def api_poster(path: str):
    """从视频抽一帧作 poster。"""
    import subprocess
    p = Path(path)
    if not p.is_absolute():
        p = (ROOT / path).resolve()
    if not p.exists():
        raise HTTPException(404, "video not found")
    out = p.with_suffix(".jpg")
    if not out.exists():
        subprocess.run([
            "ffmpeg", "-y", "-ss", "00:00:01", "-i", str(p),
            "-frames:v", "1", "-q:v", "3", str(out),
        ], check=False, capture_output=True)
    if not out.exists():
        raise HTTPException(500, "poster generation failed")
    return FileResponse(out, media_type="image/jpeg")


# ---------------------------------------------------------------------------
# API: LLM
# ---------------------------------------------------------------------------

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
        raise HTTPException(400, "LLM 未配置 — 先在 设置 页面填 API key")
    if req.base_url:
        db.set_setting("llm_base_url", req.base_url)
    if req.model:
        db.set_setting("llm_model", req.model)
    data = llm.generate_json(req.topic)
    # 落到 projects/<name>/...
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


# ---------------------------------------------------------------------------
# 静态前端
# ---------------------------------------------------------------------------

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
