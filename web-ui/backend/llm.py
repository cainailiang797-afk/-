"""LLM 生成 dreams-style JSON。可选 — 没配 key 就跳过。

支持 OpenAI 兼容接口（OpenAI / DeepSeek / 智谱 / 月之暗面 等）。
配 key 写到 settings 表即可。
"""
from __future__ import annotations

import json
import re
import urllib.request
from typing import Any

import db

# 默认 base_url 走 OpenAI 兼容协议（用户可在 web UI 改）
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"

PROMPT = """你是中文科普短视频编剧。给定主题，输出 9:16 竖屏短视频 JSON。

JSON 字段：
- topic: 主题
- cuts: 9 条 cut，按时间顺序
  - id: cut-1, cut-2, ...
  - type: hero_title / stat_card / bar_chart / text_card / callout / kpi_grid
  - in_seconds / out_seconds: 累计秒数（最后一条 out_seconds ≤ 40）
  - text: 主标题（hero_title/text_card） 或 stat 数值（stat_card）
  - subtitle: 副标题
  - backgroundColor: hex 颜色
- subtitles: 9 条字幕
  - start / end: 跟 cut 的 in/out 对齐
  - text: 一句口语化中文解说
- overlays: 0-2 个浮层

时长控制在 35-40 秒。内容要 4-5 个要点+开头钩子+结尾关注引导。

只输出 JSON，不要 ``` 包裹，不要解释。"""


def is_configured() -> bool:
    return bool(db.get_setting("llm_api_key"))


def generate_json(topic: str) -> dict[str, Any]:
    api_key = db.get_setting("llm_api_key") or ""
    base_url = db.get_setting("llm_base_url") or DEFAULT_BASE_URL
    model = db.get_setting("llm_model") or DEFAULT_MODEL

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"主题：{topic}\n\n输出 JSON："},
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
    # 剥掉可能存在的 ```json 包裹
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if not m:
        raise RuntimeError(f"LLM 没返回 JSON: {content[:200]}")
    return json.loads(m.group(0))
