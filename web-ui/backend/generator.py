"""调 make_dreams_video.py 跑生成。后台线程 + 日志流回 db。"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from typing import Callable

import db

ROOT = Path(__file__).resolve().parent.parent.parent  # OpenMontage 根
PYTHON_BIN = ROOT / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / (
    "python.exe" if sys.platform == "win32" else "python"
)
SCRIPT = ROOT / "projects" / "dreams" / "make_dreams_video.py"


def _resolve_python() -> str:
    if PYTHON_BIN.exists():
        return str(PYTHON_BIN)
    return sys.executable  # fallback to current python


def start_generate(project_name: str, props_path: str,
                   vertical: bool = True,
                   on_log: Callable[[str], None] | None = None) -> str:
    """启动后台生成任务。返回 job_id。"""
    job_id = uuid.uuid4().hex[:12]
    db.create_job(job_id, project_name, "generate")
    db.set_project_status(project_name, "generating")

    def _on_log(line: str) -> None:
        db.append_job_log(job_id, line.rstrip())
        if on_log:
            on_log(line)

    def run() -> None:
        try:
            cmd = [
                _resolve_python(),
                str(SCRIPT),
                "--props", props_path,
            ]
            if not vertical:
                cmd.append("--horizontal")
            _on_log(f"$ {' '.join(cmd)}")
            env = os.environ.copy()
            # ensure venv packages (piper-tts) are usable
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
                raise RuntimeError(f"make_dreams_video.py 退出码 {rc}")
            # 找最终视频
            props_name = Path(props_path).stem.replace("-explainer", "").replace("_explainer", "")
            out_dir = Path(props_path).parent
            video = out_dir / f"{props_name}_final.mp4"
            if not video.exists():
                raise RuntimeError(f"未找到最终视频: {video}")
            db.set_project_status(project_name, "done", video_path=str(video))
            db.update_job(job_id, status="done")
            _on_log(f"[OK] 最终视频: {video}")
        except Exception as e:
            db.set_project_status(project_name, "error", error=str(e))
            db.update_job(job_id, status="error", log=str(e))
            _on_log(f"[ERROR] {e}")

    threading.Thread(target=run, daemon=True).start()
    return job_id
