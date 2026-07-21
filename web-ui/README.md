# OpenMontage Studio

OpenMontage 项目的可视化仪表板。Web UI 让你在浏览器里：
- 浏览所有生成的视频（项目库）
- 在线编辑选题 JSON
- 一键触发生成
- （可选）输入主题，用 LLM 自动出 JSON

## 启动

Windows（双击或 cmd）：
```bat
D:\workspace\OpenMontage\web-ui\start.bat
```

首次会装 FastAPI + uvicorn（10-30 秒），之后直接启动。

打开浏览器：**http://localhost:8000**

## 功能

### 📁 项目库
- 自动扫描 `OpenMontage/projects/*/` 下所有 `*-explainer.json`
- 显示已有视频的预览缩略图
- 点击卡片进入编辑器

### 编辑器
- 左侧：项目元数据（主题、方向）+ 操作按钮
- 中间 tab：
  - **JSON**：直接编辑
  - **预览**：HTML5 video 播放器
  - **日志**：实时显示生成日志
- 点 💾 保存（自动写到 `projects/<name>/<name>-explainer.json`）
- 点 🎬 生成视频（后台跑 `make_dreams_video.py`，1-3 分钟）

### ✨ 主题生成
- 输入主题（如"黑洞是什么"）
- 后端调用 LLM（OpenAI 兼容协议）生成 9 卡 + 9 字幕的 JSON
- 直接进编辑器微调 + 生成

需要先在**设置**填 API key、base_url、model。

### ⚙️ 设置
- Base URL：默认 `https://api.openai.com/v1`，可换 DeepSeek / 智谱 / 月之暗面
- Model：默认 `gpt-4o-mini`
- API Key：存在本地 SQLite `data.db` 里，不外发

## API

所有 API 走 `/api/...`：

| 端点 | 说明 |
|---|---|
| `GET  /api/projects` | 列项目 |
| `GET  /api/projects/{name}` | 读项目 JSON |
| `PUT  /api/projects/{name}` | 保存项目 |
| `DELETE /api/projects/{name}` | 删项目（含产物） |
| `POST /api/generate` | 启动生成任务，返回 `job_id` |
| `GET  /api/jobs/{job_id}` | 查任务状态和日志 |
| `GET  /api/media/video?path=...` | 视频流 |
| `GET  /api/llm/status` | LLM 配置状态 |
| `POST /api/llm/config` | 写 LLM 设置 |
| `POST /api/llm/generate` | 主题 → JSON |

## 目录

```
web-ui/
├── backend/
│   ├── server.py        FastAPI 主程序
│   ├── db.py            SQLite 项目/任务/设置
│   ├── generator.py     调 make_dreams_video.py
│   ├── llm.py           主题 → JSON
│   └── requirements.txt
├── frontend/
│   ├── index.html       单页 UI
│   ├── app.js           前端逻辑
│   └── style.css        样式
├── start.bat            Windows 启动脚本
├── data.db              SQLite 数据库（首次启动自动创建）
└── README.md
```

## 故障排查

**端口 8000 被占**：编辑 `start.bat` 改 `--port 8001`

**LLM 调用失败**：在设置页确认 base_url / model / key 正确；某些中转服务需要把 base_url 改成它提供的 URL。

**生成任务卡在 generating**：看编辑器"日志"tab，输出会一行行显示。卡超过 5 分钟说明底层 ffmpeg/remotion 出问题，把日志最后 20 行贴出来。
